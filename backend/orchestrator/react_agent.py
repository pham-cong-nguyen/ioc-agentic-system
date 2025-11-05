"""ReAct Agent with RAG and Memory."""

import logging
import time
import asyncio
from typing import Dict, Any, Optional, List

from .react_state import (
    ReactAgentState,
    AgentThought,
    AgentAction,
    AgentObservation,
    AgentReflection,
    create_initial_state
)
from .llm_service import LLMService
from ..registry.embeddings.rag_retriever import RAGRetriever
from .memory.context_builder import ContextBuilder
from ..executor.service import APIExecutor

logger = logging.getLogger(__name__)


class ReactAgent:
    """
    ReAct Agent with RAG-based function retrieval and persistent memory.
    
    Flow: THINK → ACT → OBSERVE → REFLECT → (repeat or complete)
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        rag_retriever: RAGRetriever,
        context_builder: ContextBuilder,
        executor_service: APIExecutor,
        registry_service = None,  # Optional for now
        quality_threshold: float = 0.8,
        max_iterations: int = 5
    ):
        """
        Initialize ReAct Agent.
        
        Args:
            llm_service: LLM for reasoning
            rag_retriever: RAG system for function retrieval
            context_builder: Memory and context management
            executor_service: Function execution (APIExecutor)
            registry_service: Function registry service (optional)
            quality_threshold: Minimum quality score to complete
            max_iterations: Maximum number of ReAct iterations
        """
        self.llm_service = llm_service
        self.rag_retriever = rag_retriever
        self.context_builder = context_builder
        self.executor_service = executor_service
        self.registry_service = registry_service
        self.quality_threshold = quality_threshold
        self.max_iterations = max_iterations
    
    async def run(
        self,
        user_id: str,
        query: str,
        conversation_id: Optional[str] = None
    ) -> ReactAgentState:
        """
        Run the ReAct agent loop.
        
        Args:
            user_id: User identifier
            query: User query
            conversation_id: Optional conversation ID for context
            
        Returns:
            Final agent state
        """
        start_time = time.time()
        
        # Initialize state
        state = create_initial_state(user_id, query, conversation_id, self.max_iterations)
        
        try:
            # Build initial context with memory (if available)
            if self.context_builder:
                logger.info(f"Building context for user {user_id}")
                print("start building context")
                context = await self.context_builder.build_context(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    current_query=query
                )
                print("context built")
                print(context)
                state["user_profile"] = context["profile"]
                state["conversation_history"] = context["history"]
            else:
                logger.warning("No context builder - running without memory")
                state["user_profile"] = {"user_id": user_id}
                state["conversation_history"] = []
                # Create minimal context for methods that expect it
                context = {
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "current_query": query,
                    "profile": state["user_profile"],
                    "history": [],
                    "system_instructions": "You are a helpful AI assistant."
                }
            
            # Retrieve relevant functions using RAG
            logger.info("Retrieving relevant functions via RAG")
            try:
                retrieved_functions = await asyncio.wait_for(
                    asyncio.to_thread(self.rag_retriever.retrieve, query),
                    timeout=10.0  # 10 second timeout for RAG
                )
                
                print(retrieved_functions)
            except asyncio.TimeoutError:
                logger.error("⏱️ RAG retrieval timeout after 10s")
                retrieved_functions = []
            
            state["retrieved_functions"] = retrieved_functions
            
            # Early exit if no functions found
            if not retrieved_functions:
                logger.warning("⚠️ No relevant functions found - generating direct response")
                state["status"] = "completed"
                state["final_answer"] = await self._generate_final_answer(state, context)
                state["final_response"] = state["final_answer"]
                state["total_execution_time_ms"] = (time.time() - start_time) * 1000
                return state
            
            logger.info(f"📚 Found {len(retrieved_functions)} relevant functions")
            
            # ReAct Loop
            while state["current_step"] < state["max_steps"]:
                state["current_step"] += 1
                logger.info(f"🔄 ReAct iteration {state['current_step']}/{state['max_steps']}")
                
                # THINK
                logger.info("💭 Starting THINK phase...")
                state["status"] = "thinking"
                thought = await self._think(state, context)
                logger.info(f"✅ THINK complete: {thought.content[:50]}...")
                state["thoughts"].append(thought)
                
                # Check if we should stop thinking and act
                if "need to call" in thought.content.lower() or "execute" in thought.content.lower():
                    # ACT
                    logger.info("🎬 Starting ACT phase...")
                    state["status"] = "acting"
                    action = await self._act(state, context)
                    logger.info(f"✅ ACT complete: {action.function_name if action else 'None'}")
                    if action:
                        state["actions"].append(action)
                        
                        # OBSERVE
                        logger.info("👀 Starting OBSERVE phase...")
                        state["status"] = "observing"
                        observation = await self._observe(action, state)
                        state["observations"].append(observation)
                        logger.info(f"✅ OBSERVE complete: success={observation.success}")
                    
                # REFLECT
                logger.info("🤔 Starting REFLECT phase...")
                state["status"] = "reflecting"
                reflection = await self._reflect(state, context)
                logger.info(f"✅ REFLECT complete")
                state["reflections"].append(reflection)
                
                logger.info(f"Reflection result: should_continue={reflection.should_continue}, "
                           f"quality_score={reflection.quality_score}, "
                           f"needs_clarification={reflection.needs_clarification}")
                
                # Check if we're done
                if not reflection.should_continue:
                    if reflection.quality_score >= self.quality_threshold:
                        logger.info(f"✅ Agent completed successfully (quality: {reflection.quality_score:.2f} >= {self.quality_threshold})")
                        state["status"] = "completed"
                        state["quality_score"] = reflection.quality_score
                        break
                    elif reflection.needs_clarification:
                        logger.info("⚠️ Agent needs clarification")
                        state["requires_clarification"] = True
                        state["status"] = "completed"
                        break
                    else:
                        logger.warning(f"❌ Agent stopped but quality too low ({reflection.quality_score:.2f} < {self.quality_threshold})")
                        state["status"] = "incomplete"
                        state["quality_score"] = reflection.quality_score
                        break
                else:
                    logger.info(f"🔄 Continuing to next iteration (quality: {reflection.quality_score:.2f})")
            
            # Generate final answer if not already set
            if not state.get("final_answer"):
                logger.info("🎯 Generating final answer...")
                state["final_answer"] = await self._generate_final_answer(state, context)
                logger.info(f"✅ Final answer generated: {state['final_answer'][:100]}...")
            
            # Set final_response for compatibility with orchestrator
            state["final_response"] = state.get("final_answer", "No answer generated")
            
            # Calculate total time
            state["total_execution_time_ms"] = (time.time() - start_time) * 1000
            
            logger.info(f"🏁 ReAct completed: {state['current_step']} steps, "
                       f"status={state['status']}, quality={state.get('quality_score', 0):.2f}")
            
            # Save to memory
            if conversation_id:
                await self._save_to_memory(state, context)
            
            return state
            
        except Exception as e:
            logger.error(f"ReAct agent failed: {e}")
            state["status"] = "failed"
            state["error"] = str(e)
            state["total_execution_time_ms"] = (time.time() - start_time) * 1000
            return state
    
    async def _think(self, state: ReactAgentState, context: Dict[str, Any]) -> AgentThought:
        """THINK: Reason about the current state."""
        prompt = self._build_think_prompt(state, context)
        
        try:
            response = await asyncio.wait_for(
                self.llm_service.generate(prompt=prompt, max_tokens=500),
                timeout=15.0  # 15 second timeout
            )
        except asyncio.TimeoutError:
            logger.error("⏱️ THINK timeout after 15s")
            response = "I need to analyze the query and available functions."
        
        return AgentThought(
            content=response,
            step=state["current_step"]
        )
    
    async def _act(self, state: ReactAgentState, context: Dict[str, Any]) -> Optional[AgentAction]:
        """ACT: Decide which function to call."""
        prompt = self._build_act_prompt(state, context)
        
        try:
            response = await asyncio.wait_for(
                self.llm_service.generate(prompt=prompt, max_tokens=300),
                timeout=15.0  # 15 second timeout
            )
        except asyncio.TimeoutError:
            logger.error("⏱️ ACT timeout after 15s")
            return None  # No action to take
        
        # Parse action from response
        action = self._parse_action(response, state)
        return action
    
    async def _observe(self, action: AgentAction, state: ReactAgentState) -> AgentObservation:
        """OBSERVE: Execute action and observe result."""
        start_time = time.time()
        
        try:
            # Execute function
            # Note: registry_service might be None, need to handle that
            if self.registry_service:
                result = await self.executor_service.execute_function(
                    function_id=action.function_id,
                    parameters=action.parameters,
                    registry_service=self.registry_service
                )
            else:
                # Mock execution without registry
                logger.warning(f"No registry service - mocking execution for {action.function_id}")
                result = {
                    "success": True,
                    "data": f"Mock result for {action.function_id}",
                    "message": "Executed without registry (mock mode)"
                }
            
            execution_time = (time.time() - start_time) * 1000
            state["api_calls_made"] += 1
            
            return AgentObservation(
                success=True,
                result=result,
                execution_time_ms=execution_time,
                step=state["current_step"]
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Action execution failed: {e}")
            
            return AgentObservation(
                success=False,
                result=None,
                error=str(e),
                execution_time_ms=execution_time,
                step=state["current_step"]
            )
    
    async def _reflect(self, state: ReactAgentState, context: Dict[str, Any]) -> AgentReflection:
        """REFLECT: Evaluate progress and decide next steps."""
        prompt = self._build_reflect_prompt(state, context)
        
        try:
            response = await asyncio.wait_for(
                self.llm_service.generate(prompt=prompt, max_tokens=400),
                timeout=15.0  # 15 second timeout
            )
        except asyncio.TimeoutError:
            logger.error("⏱️ REFLECT timeout after 15s")
            response = "Quality score: 0.5. Need to continue."
        
        # Parse reflection
        return self._parse_reflection(response, state)
    
    async def _generate_final_answer(self, state: ReactAgentState, context: Dict[str, Any]) -> str:
        """Generate final answer based on all observations."""
        prompt = self._build_final_answer_prompt(state, context)
        
        try:
            response = await asyncio.wait_for(
                self.llm_service.generate(prompt=prompt, max_tokens=800),
                timeout=20.0  # 20 second timeout (longer for final answer)
            )
        except asyncio.TimeoutError:
            logger.error("⏱️ FINAL_ANSWER timeout after 20s")
            response = "I apologize, but I was unable to generate a complete response. Please try again."
        
        return response
    
    async def _save_to_memory(self, state: ReactAgentState, context: Dict[str, Any]):
        """Save interaction to persistent memory."""
        try:
            # Build metadata
            metadata = {
                "thoughts": [t.content for t in state["thoughts"]],
                "actions": [{"function": a.function_name, "reasoning": a.reasoning} for a in state["actions"]],
                "api_calls": state["api_calls_made"],
                "execution_time_ms": state["total_execution_time_ms"]
            }
            
            await self.context_builder.save_interaction(
                user_id=state["user_id"],
                conversation_id=state["conversation_id"],
                user_message=state["query"],
                assistant_message=state.get("final_answer", ""),
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to save to memory: {e}")
    
    def _build_think_prompt(self, state: ReactAgentState, context: Dict[str, Any]) -> str:
        """Build prompt for THINK step."""
        history = "\n".join([
            f"Thought {t.step}: {t.content}" for t in state["thoughts"][-3:]
        ])
        
        return f"""You are a helpful AI assistant. Think step by step about how to answer this query.

User Query: {state['query']}

Available Functions:
{self._format_functions(state['retrieved_functions'][:5])}

Previous Thoughts:
{history if history else "None"}

What should you think about next? Consider:
1. Do you have enough information?
2. Which function(s) might help?
3. What parameters are needed?

Thought:"""
    
    def _build_act_prompt(self, state: ReactAgentState, context: Dict[str, Any]) -> str:
        """Build prompt for ACT step."""
        return f"""Based on your thoughts, decide which function to call.

Query: {state['query']}
Latest Thought: {state['thoughts'][-1].content if state['thoughts'] else 'None'}

Available Functions:
{self._format_functions(state['retrieved_functions'][:5])}

Choose ONE function to call. Format:
Function: <function_name>
Parameters: {{"param1": "value1", "param2": "value2"}}
Reasoning: <why this function>

Action:"""
    
    def _build_reflect_prompt(self, state: ReactAgentState, context: Dict[str, Any]) -> str:
        """Build prompt for REFLECT step."""
        latest_obs = state["observations"][-1] if state["observations"] else None
        
        return f"""Reflect on your progress toward answering the query.

Query: {state['query']}
Latest Observation: {latest_obs.result if latest_obs and latest_obs.success else 'No observation yet'}

Evaluate:
1. Quality Score (0.0-1.0): How well can you answer now?
2. Should Continue: Do you need more information?
3. Needs Clarification: Is the query unclear?

Format:
Quality: <score>
Continue: <yes/no>
Clarification: <yes/no>
Reasoning: <explanation>

Reflection:"""
    
    def _build_final_answer_prompt(self, state: ReactAgentState, context: Dict[str, Any]) -> str:
        """Build prompt for final answer generation."""
        observations = "\n".join([
            f"Result {i+1}: {obs.result}" for i, obs in enumerate(state["observations"]) if obs.success
        ])
        
        return f"""Based on all observations, provide a complete answer to the user's query.

Query: {state['query']}

Observations:
{observations if observations else 'No successful observations'}

Provide a clear, helpful answer:"""
    
    def _format_functions(self, functions: List[Dict[str, Any]]) -> str:
        """Format functions for prompt."""
        if not functions:
            return "No functions available"
        
        formatted = []
        for i, func in enumerate(functions, 1):
            formatted.append(
                f"{i}. {func.get('name', 'Unknown')}: {func.get('description', 'No description')}"
            )
        
        return "\n".join(formatted)
    
    def _parse_action(self, response: str, state: ReactAgentState) -> Optional[AgentAction]:
        """Parse action from LLM response."""
        # Simple parsing - in production, use structured output
        try:
            lines = response.strip().split('\n')
            function_name = None
            parameters = {}
            reasoning = ""
            
            for line in lines:
                if line.startswith("Function:"):
                    function_name = line.split(":", 1)[1].strip()
                elif line.startswith("Parameters:"):
                    # Simple JSON parsing
                    param_str = line.split(":", 1)[1].strip()
                    import json
                    parameters = json.loads(param_str)
                elif line.startswith("Reasoning:"):
                    reasoning = line.split(":", 1)[1].strip()
            
            if function_name:
                # Find function ID from retrieved functions
                func_id = None
                for func in state["retrieved_functions"]:
                    if func.get("name") == function_name:
                        func_id = func.get("function_id")
                        break
                
                if func_id:
                    return AgentAction(
                        function_id=func_id,
                        function_name=function_name,
                        parameters=parameters,
                        reasoning=reasoning,
                        step=state["current_step"]
                    )
        except Exception as e:
            logger.error(f"Failed to parse action: {e}")
        
        return None
    
    def _parse_reflection(self, response: str, state: ReactAgentState) -> AgentReflection:
        """Parse reflection from LLM response."""
        quality_score = 0.5
        should_continue = True
        needs_clarification = False
        
        try:
            lines = response.strip().split('\n')
            for line in lines:
                if line.startswith("Quality:"):
                    score_str = line.split(":", 1)[1].strip()
                    quality_score = float(score_str)
                elif line.startswith("Continue:"):
                    cont_str = line.split(":", 1)[1].strip().lower()
                    should_continue = cont_str in ["yes", "true"]
                elif line.startswith("Clarification:"):
                    clar_str = line.split(":", 1)[1].strip().lower()
                    needs_clarification = clar_str in ["yes", "true"]
        except Exception as e:
            logger.error(f"Failed to parse reflection: {e}")
        
        return AgentReflection(
            content=response,
            quality_score=quality_score,
            should_continue=should_continue,
            needs_clarification=needs_clarification,
            step=state["current_step"]
        )
