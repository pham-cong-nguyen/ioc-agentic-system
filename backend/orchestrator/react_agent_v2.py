"""
ReAct Agent V2 - Production-Ready with 4-Layer Architecture

Architecture:
- Layer 0: Enhanced Metadata Store
- Layer 1: Hybrid Function Selection (Rule → RAG → LLM)
- Layer 2: Multi-Strategy Parameter Synthesis
- Layer 3: Semantic DAG Planner (optional, for complex chains)
- Layer 4: Execution Monitor with Bounded Retry

Philosophy: "Think like human, execute like machine"
"""

import logging
import time
import asyncio
from typing import Dict, Any, Optional, List, Tuple, Callable
from enum import Enum
from dataclasses import dataclass
import re
import json
from datetime import datetime, timedelta

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
from .enhanced_components import (
    RetryExecutor,
    QualityValidator,
    AgentMetrics,
    EnhancedPromptBuilder
)

logger = logging.getLogger(__name__)


# =============================================================================
# LAYER 1: HYBRID FUNCTION SELECTION
# =============================================================================

class SelectionMethod(str, Enum):
    """Method used for function selection."""
    RULE_BASED = "rule_based"
    RAG_SEMANTIC = "rag_semantic"
    LLM_REASONING = "llm_reasoning"


class HybridFunctionSelector:
    """
    3-tier function selection for optimal speed/accuracy.
    
    Flow:
    1. Try RULE-BASED (fast, simple queries) - 60% cases
    2. Fall back to RAG (semantic matching) - 25% cases
    3. Fall back to LLM (complex reasoning) - 15% cases
    """
    
    def __init__(
        self,
        rag_retriever: RAGRetriever,
        llm_service: LLMService,
        rule_confidence_threshold: float = 0.85
    ):
        self.rag = rag_retriever
        self.llm = llm_service
        self.rule_threshold = rule_confidence_threshold
        
        # Rule-based keyword patterns
        self.keyword_patterns = self._build_keyword_patterns()
        
        # Statistics
        self.stats = {
            "rule_based": 0,
            "rag_semantic": 0,
            "llm_reasoning": 0
        }
    
    def _build_keyword_patterns(self) -> Dict[str, List[str]]:
        """Build keyword patterns for common query types."""
        return {
            # Energy/Power queries
            "energy_kpi": [
                r"(năng lượng|điện|energy|power).*\b(miền|region|khu vực)",
                r"(công suất|capacity|generation)",
                r"(sản lượng|output|production)",
            ],
            "comparison": [
                r"(so sánh|compare|khác biệt|difference)",
                r"(bắc.*nam|nam.*bắc|north.*south|south.*north)",
            ],
            "aggregation": [
                r"(tổng|total|sum|aggregate)",
                r"(trung bình|average|mean)",
                r"(cao nhất|thấp nhất|max|min|highest|lowest)",
            ],
            "time_based": [
                r"(hôm nay|today|hiện tại|current)",
                r"(hôm qua|yesterday|ngày hôm qua)",
                r"(tuần|week|tháng|month|năm|year)",
            ],
        }
    
    async def select_functions(
        self,
        query: str,
        context: Dict[str, Any],
        top_k: int = 5
    ) -> Tuple[List[Dict[str, Any]], SelectionMethod, float]:
        """
        Select functions using hybrid approach.
        
        Returns:
            (functions, method_used, confidence_score)
        """
        
        # ============= TIER 1: RULE-BASED =============
        logger.info("🎯 Tier 1: Trying rule-based selection...")
        
        rule_score, category = self._match_patterns(query)
        
        if rule_score >= self.rule_threshold:
            logger.info(f"✅ Rule-based match (score: {rule_score:.2f}, category: {category})")
            
            # Get functions via RAG but with high confidence from rules
            functions = await asyncio.to_thread(
                self.rag.retrieve,
                query
            )
            
            if functions:
                self.stats["rule_based"] += 1
                return functions[:top_k], SelectionMethod.RULE_BASED, rule_score
        
        # ============= TIER 2: RAG SEMANTIC =============
        logger.info("🔍 Tier 2: Falling back to RAG semantic search...")
        
        try:
            rag_results = await asyncio.wait_for(
                asyncio.to_thread(self.rag.retrieve, query),
                timeout=10.0
            )
            
            if rag_results and len(rag_results) > 0:
                confidence = self._calculate_rag_confidence(rag_results)
                
                logger.info(f"✅ RAG success (confidence: {confidence:.2f})")
                self.stats["rag_semantic"] += 1
                
                return rag_results[:top_k], SelectionMethod.RAG_SEMANTIC, confidence
        
        except asyncio.TimeoutError:
            logger.warning("⏱️ RAG timeout after 10s")
        except Exception as e:
            logger.warning(f"RAG failed: {e}")
        
        # ============= TIER 3: LLM REASONING =============
        logger.info("🤖 Tier 3: Using LLM for complex reasoning...")
        
        # Get all available functions from RAG (broader search)
        try:
            all_functions = await asyncio.to_thread(
                self.rag.retrieve,
                query
            )
            
            if all_functions:
                llm_selected = await self._llm_function_selection(
                    query,
                    all_functions,
                    context,
                    top_k
                )
                
                self.stats["llm_reasoning"] += 1
                
                return llm_selected, SelectionMethod.LLM_REASONING, 0.7
        except Exception as e:
            logger.error(f"LLM selection failed: {e}")
        
        # Fallback: return empty
        return [], SelectionMethod.RAG_SEMANTIC, 0.0
    
    def _match_patterns(self, query: str) -> Tuple[float, str]:
        """Match query against rule patterns."""
        query_lower = query.lower()
        
        best_score = 0.0
        best_category = "unknown"
        
        for category, patterns in self.keyword_patterns.items():
            matches = 0
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    matches += 1
            
            if matches > 0:
                score = min(matches / len(patterns), 1.0)
                
                # Boost if multiple patterns match
                if matches >= 2:
                    score = min(score + 0.2, 1.0)
                
                if score > best_score:
                    best_score = score
                    best_category = category
        
        return best_score, best_category
    
    def _calculate_rag_confidence(self, results: List[Dict[str, Any]]) -> float:
        """Calculate confidence from RAG scores."""
        if not results:
            return 0.0
        
        # Use similarity scores from RAG
        scores = [r.get('similarity_score', 0.5) for r in results]
        
        # Weighted average (top result more important)
        weights = [1.0, 0.7, 0.5, 0.3, 0.2][:len(scores)]
        weighted_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        
        return weighted_score
    
    async def _llm_function_selection(
        self,
        query: str,
        all_functions: List[Dict[str, Any]],
        context: Dict[str, Any],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Use LLM for complex function selection."""
        
        # Build concise function list
        func_list = "\n".join([
            f"{i+1}. {f.get('name', 'unknown')}: {f.get('description', 'No description')[:100]}"
            for i, f in enumerate(all_functions[:15])
        ])
        
        prompt = f"""Analyze this query and select the most relevant functions.

Query: {query}

Available Functions:
{func_list}

Select the top {top_k} functions needed. Consider:
1. Direct relevance to query intent
2. Data dependencies (what needs to be called first)
3. Completeness (do we have all needed functions)

Output JSON list of function names:
["function1", "function2", ...]

Selected:"""
        
        try:
            response = await self.llm.generate(prompt, max_tokens=200)
            
            # Parse LLM response
            selected_names = json.loads(response.strip())
            
            # Map names to full metadata
            name_to_func = {f.get('name'): f for f in all_functions if f.get('name')}
            selected = [
                name_to_func[name]
                for name in selected_names
                if name in name_to_func
            ]
            
            return selected[:top_k]
            
        except Exception as e:
            logger.error(f"Failed to parse LLM selection: {e}")
            # Fallback: return first k functions
            return all_functions[:top_k]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get selection method statistics."""
        total = sum(self.stats.values())
        if total == 0:
            return self.stats
        
        return {
            method: {
                "count": count,
                "percentage": round((count / total) * 100, 2)
            }
            for method, count in self.stats.items()
        }


# =============================================================================
# LAYER 2: MULTI-STRATEGY PARAMETER SYNTHESIS
# =============================================================================

class SynthesisStrategy(str, Enum):
    """Parameter synthesis strategies."""
    TEMPLATE = "template"
    EXTRACTION = "extraction"
    CONTEXT_REUSE = "context_reuse"
    LLM_GENERATION = "llm"


class ParameterSynthesizerV2:
    """
    Multi-strategy parameter synthesis.
    
    Priority:
    1. Template matching (fastest) - pre-defined patterns
    2. Regex extraction - extract from query
    3. Context reuse - use previous results
    4. LLM generation (slowest) - last resort
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
        
        # Pre-defined templates for common queries
        self.templates = self._build_templates()
        
        # Extraction patterns
        self.extractors = self._build_extractors()
        
        # Stats
        self.strategy_usage = {s: 0 for s in SynthesisStrategy}
    
    def _build_templates(self) -> Dict[str, Dict[str, Any]]:
        """Build parameter templates for common queries."""
        return {
            "energy_north_today": {
                "patterns": [
                    r"(năng lượng|điện|energy).*(miền bắc|bắc|north).*(hôm nay|today|hiện tại)",
                    r"(miền bắc|bắc|north).*(năng lượng|điện|energy).*(hôm nay|today)",
                ],
                "parameters": {
                    "region": "North",
                    "period": "today",
                    "metric": "total_energy"
                }
            },
            "energy_south_today": {
                "patterns": [
                    r"(năng lượng|điện|energy).*(miền nam|nam|south).*(hôm nay|today|hiện tại)",
                ],
                "parameters": {
                    "region": "South",
                    "period": "today",
                    "metric": "total_energy"
                }
            },
            "comparison_north_south": {
                "patterns": [
                    r"so sánh.*(bắc|north).*(nam|south)",
                    r"so sánh.*(nam|south).*(bắc|north)",
                ],
                "parameters": {
                    "regions": ["North", "South"],
                    "metric": "total_energy",
                    "period": "today"
                }
            },
        }
    
    def _build_extractors(self) -> Dict[str, List[Tuple[str, Any]]]:
        """Build regex extractors for common parameters."""
        return {
            "region": [
                (r"miền\s*bắc|bắc|north", "North"),
                (r"miền\s*nam|nam|south", "South"),
                (r"miền\s*trung|trung|central", "Central"),
            ],
            "period": [
                (r"hôm nay|today|hiện tại|current", "today"),
                (r"hôm qua|yesterday", "yesterday"),
                (r"tuần này|this week", "this_week"),
                (r"tuần trước|last week", "last_week"),
                (r"tháng này|this month", "this_month"),
            ],
            "metric": [
                (r"năng lượng|energy", "total_energy"),
                (r"công suất|power|capacity", "power_output"),
                (r"tải|load|demand", "load_demand"),
            ],
        }
    
    async def synthesize(
        self,
        function_schema: Dict[str, Any],
        query: str,
        context: Dict[str, Any],
        previous_results: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], str, SynthesisStrategy]:
        """
        Synthesize parameters using best strategy.
        
        Returns:
            (success, parameters, error_msg, strategy_used)
        """
        
        # Try strategies in order
        strategies = [
            (SynthesisStrategy.TEMPLATE, self._try_template),
            (SynthesisStrategy.EXTRACTION, self._try_extraction),
            (SynthesisStrategy.CONTEXT_REUSE, self._try_context_reuse),
            (SynthesisStrategy.LLM_GENERATION, self._try_llm)
        ]
        
        for strategy, method in strategies:
            try:
                success, params = await method(
                    function_schema,
                    query,
                    context,
                    previous_results
                )
                
                if success and params:
                    # Basic validation
                    valid, error = self._validate_parameters(params, function_schema)
                    
                    if valid:
                        logger.info(f"✅ Synthesis success with {strategy}: {params}")
                        self.strategy_usage[strategy] += 1
                        return True, params, "", strategy
                    else:
                        logger.warning(f"Validation failed for {strategy}: {error}")
                        
            except Exception as e:
                logger.warning(f"Strategy {strategy} failed: {e}")
                continue
        
        # All strategies failed
        return False, None, "All synthesis strategies failed", SynthesisStrategy.LLM_GENERATION
    
    async def _try_template(
        self,
        function_schema: Dict[str, Any],
        query: str,
        context: Dict[str, Any],
        previous_results: Optional[List]
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Try template matching."""
        query_lower = query.lower()
        
        for template_name, template in self.templates.items():
            for pattern in template["patterns"]:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    logger.info(f"📋 Template match: {template_name}")
                    
                    params = template["parameters"].copy()
                    
                    # Add context if available
                    if "user_id" in context:
                        params["user_id"] = context["user_id"]
                    
                    return True, params
        
        return False, None
    
    async def _try_extraction(
        self,
        function_schema: Dict[str, Any],
        query: str,
        context: Dict[str, Any],
        previous_results: Optional[List]
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Try regex extraction."""
        params = {}
        param_schema = function_schema.get("parameters", {})
        required_params = param_schema.get("required", [])
        properties = param_schema.get("properties", {})
        
        # Extract each parameter type we know about
        for param_type, patterns in self.extractors.items():
            # Check if this parameter type is needed
            matching_params = [
                p for p in properties.keys()
                if param_type in p.lower() or p.lower() in param_type
            ]
            
            if matching_params:
                for pattern, value in patterns:
                    if re.search(pattern, query, re.IGNORECASE):
                        # Use the first matching parameter name
                        params[matching_params[0]] = value
                        break
        
        # Check if we got all required
        has_all_required = all(p in params for p in required_params)
        
        if params and has_all_required:
            logger.info(f"🔍 Extraction success: {params}")
            return True, params
        
        return False, None
    
    async def _try_context_reuse(
        self,
        function_schema: Dict[str, Any],
        query: str,
        context: Dict[str, Any],
        previous_results: Optional[List]
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Try to reuse parameters from previous results."""
        if not previous_results:
            return False, None
        
        params = {}
        param_schema = function_schema.get("parameters", {})
        required_params = param_schema.get("required", [])
        
        # Try to find parameters in previous results
        for result in previous_results:
            if isinstance(result, dict):
                for param_name in required_params:
                    if param_name in result and param_name not in params:
                        params[param_name] = result[param_name]
        
        # Check if we got all required
        if all(p in params for p in required_params):
            logger.info(f"🔄 Context reuse success: {params}")
            return True, params
        
        return False, None
    
    async def _try_llm(
        self,
        function_schema: Dict[str, Any],
        query: str,
        context: Dict[str, Any],
        previous_results: Optional[List]
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """LLM-based parameter generation (last resort)."""
        
        # Build context string
        context_str = ""
        if previous_results:
            context_str = "\n\nPrevious results:\n" + "\n".join([
                f"- Step {i+1}: {result}"
                for i, result in enumerate(previous_results[-3:])  # Last 3 only
            ])
        
        # Format parameter schema
        param_schema = function_schema.get("parameters", {})
        props = param_schema.get("properties", {})
        required = param_schema.get("required", [])
        
        schema_str = "\n".join([
            f"- {param} ({details.get('type', 'any')}, "
            f"{'REQUIRED' if param in required else 'optional'}): "
            f"{details.get('description', 'No description')}"
            for param, details in props.items()
        ])
        
        prompt = f"""Extract parameters for this function call.

Query: {query}

Function: {function_schema.get('name', 'unknown')}
Description: {function_schema.get('description', 'No description')}

Parameters:
{schema_str}
{context_str}

Extract ONLY the needed parameters. Return valid JSON.

JSON:"""
        
        try:
            response = await self.llm.generate(prompt, max_tokens=300)
            
            # Try to extract JSON
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                params = json.loads(json_match.group(0))
                logger.info(f"🤖 LLM synthesis: {params}")
                return True, params
            else:
                params = json.loads(response.strip())
                return True, params
                
        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}")
            return False, None
    
    def _validate_parameters(
        self,
        params: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Basic parameter validation."""
        param_schema = schema.get("parameters", {})
        required = param_schema.get("required", [])
        
        # Check required parameters
        for param in required:
            if param not in params:
                return False, f"Missing required parameter: {param}"
        
        return True, None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get synthesis statistics."""
        total = sum(self.strategy_usage.values())
        if total == 0:
            return self.strategy_usage
        
        return {
            strategy: {
                "count": count,
                "percentage": round((count / total) * 100, 2)
            }
            for strategy, count in self.strategy_usage.items()
        }


# =============================================================================
# MAIN AGENT
# =============================================================================

class ReactAgentV2:
    """
    Production-ready ReAct Agent with 4-layer architecture.
    
    Features:
    - Hybrid function selection (Rule → RAG → LLM)
    - Multi-strategy parameter synthesis
    - Retry logic with exponential backoff
    - Objective quality validation
    - Comprehensive metrics
    
    Philosophy: "Think like human, execute like machine"
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        rag_retriever: RAGRetriever,
        context_builder: ContextBuilder,
        executor_service: APIExecutor,
        registry_service=None,
        quality_threshold: float = 0.75,
        max_iterations: int = 5
    ):
        """
        Initialize ReAct Agent V2.
        
        Args:
            llm_service: LLM for reasoning
            rag_retriever: RAG system for function retrieval
            context_builder: Memory and context management
            executor_service: Function execution
            registry_service: Function registry
            quality_threshold: Minimum quality score (0.75 = 75%)
            max_iterations: Maximum ReAct iterations
        """
        self.llm_service = llm_service
        self.rag_retriever = rag_retriever
        self.context_builder = context_builder
        self.executor_service = executor_service
        self.registry_service = registry_service
        self.quality_threshold = quality_threshold
        self.max_iterations = max_iterations
        
        # Initialize enhanced components
        self.hybrid_selector = HybridFunctionSelector(
            rag_retriever=rag_retriever,
            llm_service=llm_service
        )
        
        self.param_synthesizer = ParameterSynthesizerV2(
            llm_service=llm_service
        )
        
        self.retry_executor = RetryExecutor(
            executor_service=executor_service,
            max_retries=2,
            retry_delays=[1, 3]  # 1s, 3s
        )
        
        self.quality_validator = QualityValidator()
        self.metrics = AgentMetrics()
        
        logger.info("🚀 ReactAgentV2 initialized with 4-layer architecture")
    
    async def run(
        self,
        user_id: str,
        query: str,
        conversation_id: Optional[str] = None,
        stream_callback: Optional[Callable] = None  # ← NEW: Callback for streaming
    ) -> ReactAgentState:
        """
        Run the enhanced ReAct agent loop.
        
        Args:
            user_id: User identifier
            query: User query
            conversation_id: Optional conversation ID
            stream_callback: Optional async callback(event_type, data) for real-time streaming
            
        Returns:
            Final agent state with metrics
        """
        start_time = time.time()
        
        # Initialize state
        state = create_initial_state(user_id, query, conversation_id, self.max_iterations)
        
        try:
            logger.info(f"🎯 Starting ReAct V2 for query: {query}")
            
            # Stream start event
            if stream_callback:
                await stream_callback("start", {"query": query, "user_id": user_id})
            
            # Build context
            context = await self._build_context(user_id, conversation_id, query)
            state["user_profile"] = context["profile"]
            state["conversation_history"] = context["history"]
            
            # ========== HYBRID FUNCTION SELECTION ==========
            logger.info("📚 Phase 1: Hybrid Function Selection")
            
            functions, selection_method, confidence = await self.hybrid_selector.select_functions(
                query=query,
                context=context,
                top_k=5
            )
            
            state["retrieved_functions"] = functions
            state["selection_method"] = selection_method
            state["selection_confidence"] = confidence
            
            logger.info(
                f"✅ Selected {len(functions)} functions "
                f"(method: {selection_method}, confidence: {confidence:.2f})"
            )
            
            # Early exit if no functions
            if not functions:
                logger.warning("⚠️ No relevant functions found")
                return await self._handle_no_functions(state, context, start_time)
            
            # ========== REACT LOOP ==========
            logger.info("🔄 Phase 2: ReAct Loop")
            
            step_number = 0
            
            while state["current_step"] < state["max_steps"]:
                state["current_step"] += 1
                logger.info(f"--- Iteration {state['current_step']}/{state['max_steps']} ---")
                
                # THINK
                thought = await self._think(state, context)
                state["thoughts"].append(thought)
                
                # Stream thought immediately
                if stream_callback:
                    step_number += 1
                    await stream_callback("thought", {
                        "step_number": step_number,
                        "step_type": "thought",
                        "content": thought.content,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                # ACT (with enhanced synthesis)
                if self._should_act(thought):
                    action = await self._enhanced_act(state, context)
                    
                    if action:
                        state["actions"].append(action)
                        
                        # Stream action immediately
                        if stream_callback:
                            step_number += 1
                            await stream_callback("action", {
                                "step_number": step_number,
                                "step_type": "action",
                                "function_name": action.function_name,
                                "parameters": action.parameters,
                                "timestamp": datetime.utcnow().isoformat()
                            })
                        
                        # OBSERVE (with retry)
                        observation = await self._enhanced_observe(action, state)
                        state["observations"].append(observation)
                        
                        # Stream observation immediately
                        if stream_callback:
                            step_number += 1
                            await stream_callback("observation", {
                                "step_number": step_number,
                                "step_type": "observation",
                                "success": observation.success,
                                "result": str(observation.result)[:500] if observation.result else None,
                                "error": observation.error if hasattr(observation, 'error') else None,
                                "execution_time_ms": observation.execution_time_ms,
                                "timestamp": datetime.utcnow().isoformat()
                            })
                
                # REFLECT (with quality validation)
                reflection = await self._enhanced_reflect(state, context)
                state["reflections"].append(reflection)
                
                # Check completion
                if not reflection.should_continue:
                    logger.info(f"🏁 Agent completed: {reflection.content[:100]}")
                    break
            
            # ========== FINAL ANSWER ==========
            logger.info("📝 Phase 3: Generating Final Answer")
            
            state["final_answer"] = await self._generate_final_answer(state, context)
            state["final_response"] = state["final_answer"]
            
            # Stream final answer immediately
            if stream_callback:
                await stream_callback("final_answer", {
                    "step_type": "final",
                    "response": state["final_answer"],
                    "quality_score": state.get("quality_score", 0.0),
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # ========== QUALITY VALIDATION ==========
            logger.info("✅ Phase 4: Quality Validation")
            
            quality = self.quality_validator.validate_completion(query, state)
            state["quality_score"] = quality.overall
            state["quality_details"] = {
                "completeness": quality.completeness,
                "coverage": quality.coverage,
                "reliability": quality.reliability,
                "format_valid": quality.format_valid
            }
            
            # Set status based on quality
            if quality.overall >= self.quality_threshold:
                state["status"] = "completed"
                logger.info(f"✅ Quality passed: {quality.overall:.2f} >= {self.quality_threshold}")
            else:
                state["status"] = "incomplete"
                logger.warning(f"⚠️ Quality too low: {quality.overall:.2f} < {self.quality_threshold}")
            
            # Calculate metrics
            state["total_execution_time_ms"] = (time.time() - start_time) * 1000
            self.metrics.record_execution(state, quality)
            
            # Add performance stats
            state["performance_stats"] = {
                "selection_method": selection_method,
                "selection_confidence": confidence,
                "synthesis_stats": self.param_synthesizer.get_stats(),
                "selection_stats": self.hybrid_selector.get_stats(),
                "latency_ms": state["total_execution_time_ms"]
            }
            
            logger.info(
                f"🎉 ReAct V2 completed in {state['total_execution_time_ms']:.0f}ms "
                f"(quality: {quality.overall:.2f})"
            )
            
            return state
            
        except Exception as e:
            logger.error(f"❌ ReAct V2 failed: {e}", exc_info=True)
            state["status"] = "failed"
            state["error"] = str(e)
            state["total_execution_time_ms"] = (time.time() - start_time) * 1000
            self.metrics.record_execution(state)
            return state
    
    async def _build_context(
        self,
        user_id: str,
        conversation_id: Optional[str],
        query: str
    ) -> Dict[str, Any]:
        """Build context from memory."""
        if self.context_builder:
            try:
                return await self.context_builder.build_context(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    current_query=query
                )
            except Exception as e:
                logger.warning(f"Failed to build context: {e}")
        
        # Fallback minimal context
        return {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "current_query": query,
            "profile": {"user_id": user_id},
            "history": [],
            "system_instructions": "You are a helpful AI assistant."
        }
    
    def _should_act(self, thought: AgentThought) -> bool:
        """Determine if we should take an action based on thought."""
        content_lower = thought.content.lower()
        
        action_indicators = [
            "need to call",
            "should call",
            "will call",
            "execute",
            "invoke",
            "use function",
            "call the function"
        ]
        
        return any(indicator in content_lower for indicator in action_indicators)
    
    async def _think(self, state: ReactAgentState, context: Dict[str, Any]) -> AgentThought:
        """THINK: Reason about current state."""
        prompt = self._build_think_prompt(state, context)
        
        try:
            response = await asyncio.wait_for(
                self.llm_service.generate(prompt=prompt, max_tokens=500),
                timeout=15.0
            )
        except asyncio.TimeoutError:
            logger.error("⏱️ THINK timeout")
            response = "I need to analyze the query and determine which function to call."
        
        return AgentThought(
            content=response,
            step=state["current_step"]
        )
    
    async def _enhanced_act(
        self,
        state: ReactAgentState,
        context: Dict[str, Any]
    ) -> Optional[AgentAction]:
        """
        Enhanced ACT with multi-strategy parameter synthesis.
        """
        # Get LLM suggestion for which function to call
        prompt = self._build_act_prompt(state, context)
        
        try:
            response = await asyncio.wait_for(
                self.llm_service.generate(prompt=prompt, max_tokens=300),
                timeout=15.0
            )
        except asyncio.TimeoutError:
            logger.error("⏱️ ACT timeout")
            return None
        
        # Extract function name
        function_name = self._extract_function_name(response)
        
        if not function_name:
            logger.warning("❌ No function name extracted from ACT")
            return None
        
        # Find function schema
        function_schema = self._find_function_schema(function_name, state["retrieved_functions"])
        
        if not function_schema:
            logger.error(f"❌ Function not found: {function_name}")
            return None
        
        # ========== ENHANCED PARAMETER SYNTHESIS ==========
        logger.info(f"🔧 Synthesizing parameters for {function_name}...")
        
        success, params, error, strategy = await self.param_synthesizer.synthesize(
            function_schema=function_schema,
            query=state["query"],
            context=context,
            previous_results=[
                obs.result for obs in state["observations"] 
                if obs.success and obs.result
            ]
        )
        
        if not success:
            logger.error(f"❌ Parameter synthesis failed: {error}")
            return None
        
        logger.info(f"✅ Parameters synthesized via {strategy}: {params}")
        
        # Create action
        return AgentAction(
            function_id=function_schema["function_id"],
            function_name=function_name,
            parameters=params,
            reasoning=f"Synthesized via {strategy}",
            step=state["current_step"]
        )
    
    async def _enhanced_observe(
        self,
        action: AgentAction,
        state: ReactAgentState
    ) -> AgentObservation:
        """Enhanced OBSERVE with retry logic."""
        logger.info(f"⚡ Executing {action.function_name} with retry...")
        
        result = await self.retry_executor.execute_with_retry(
            function_id=action.function_id,
            parameters=action.parameters,
            registry_service=self.registry_service
        )
        
        state["api_calls_made"] += result.get("attempts", 1)
        
        return AgentObservation(
            success=result["success"],
            result=result.get("data") if result["success"] else None,
            error=result.get("error"),
            execution_time_ms=0,
            step=state["current_step"]
        )
    
    async def _enhanced_reflect(
        self,
        state: ReactAgentState,
        context: Dict[str, Any]
    ) -> AgentReflection:
        """Enhanced REFLECT with objective quality validation."""
        # Get LLM reflection
        prompt = self._build_reflect_prompt(state, context)
        
        try:
            response = await asyncio.wait_for(
                self.llm_service.generate(prompt=prompt, max_tokens=400),
                timeout=15.0
            )
        except asyncio.TimeoutError:
            logger.error("⏱️ REFLECT timeout")
            response = "Quality: 0.5\nContinue: yes\nI need more information."
        
        # Parse LLM reflection
        reflection = self._parse_reflection(response, state)
        
        # Override with objective quality validation
        quality = self.quality_validator.validate_completion(
            query=state["query"],
            state=state
        )
        
        reflection.quality_score = quality.overall
        
        # Update should_continue based on objective quality
        if quality.overall >= self.quality_threshold:
            reflection.should_continue = False
        elif state["current_step"] >= state["max_steps"]:
            reflection.should_continue = False
        
        return reflection
    
    async def _generate_final_answer(
        self,
        state: ReactAgentState,
        context: Dict[str, Any]
    ) -> str:
        """Generate final answer based on observations."""
        prompt = self._build_final_answer_prompt(state, context)
        
        try:
            response = await asyncio.wait_for(
                self.llm_service.generate(prompt=prompt, max_tokens=800),
                timeout=20.0
            )
        except asyncio.TimeoutError:
            logger.error("⏱️ FINAL_ANSWER timeout")
            response = "Xin lỗi, tôi không thể tạo câu trả lời hoàn chỉnh. Vui lòng thử lại."
        
        return response
    
    async def _handle_no_functions(
        self,
        state: ReactAgentState,
        context: Dict[str, Any],
        start_time: float
    ) -> ReactAgentState:
        """Handle case when no functions are found."""
        state["status"] = "completed"
        state["final_answer"] = (
            "Tôi không tìm thấy chức năng phù hợp để trả lời câu hỏi này. "
            "Vui lòng thử diễn đạt lại câu hỏi hoặc liên hệ hỗ trợ."
        )
        state["final_response"] = state["final_answer"]
        state["total_execution_time_ms"] = (time.time() - start_time) * 1000
        state["quality_score"] = 0.0
        return state
    
    # ========== PROMPT BUILDERS ==========
    
    def _build_think_prompt(self, state: ReactAgentState, context: Dict[str, Any]) -> str:
        """Build THINK prompt."""
        history = "\n".join([
            f"Thought {t.step}: {t.content[:100]}"
            for t in state["thoughts"][-2:]
        ])
        
        functions_str = EnhancedPromptBuilder.format_functions_detailed(
            state['retrieved_functions'][:3]
        )
        
        return f"""You are a helpful AI assistant. Think step by step.

User Query: {state['query']}

Available Functions:
{functions_str}

Previous Thoughts:
{history if history else "None"}

What should you think about next?
1. Do you understand the query?
2. Which function(s) might help?
3. What parameters are needed?

Thought:"""
    
    def _build_act_prompt(self, state: ReactAgentState, context: Dict[str, Any]) -> str:
        """Build ACT prompt."""
        latest_thought = state["thoughts"][-1].content if state["thoughts"] else "None"
        
        functions_str = "\n".join([
            f"{i+1}. {f.get('name', 'unknown')}: {f.get('description', 'No description')[:80]}"
            for i, f in enumerate(state['retrieved_functions'][:5])
        ])
        
        return f"""Based on your analysis, decide which function to call.

Query: {state['query']}
Latest Thought: {latest_thought}

Available Functions:
{functions_str}

Choose ONE function. Format:
Function: <function_name>
Reasoning: <why this function>

Action:"""
    
    def _build_reflect_prompt(self, state: ReactAgentState, context: Dict[str, Any]) -> str:
        """Build REFLECT prompt."""
        latest_obs = state["observations"][-1] if state["observations"] else None
        
        obs_str = "No observations yet"
        if latest_obs:
            if latest_obs.success:
                obs_str = f"Success: {str(latest_obs.result)[:200]}"
            else:
                obs_str = f"Failed: {latest_obs.error}"
        
        return f"""Reflect on your progress.

Query: {state['query']}
Latest Observation: {obs_str}

Evaluate:
1. Quality (0.0-1.0): Can you answer the query now?
2. Should Continue: Need more information?

Format:
Quality: <score>
Continue: <yes/no>
Reasoning: <explanation>

Reflection:"""
    
    def _build_final_answer_prompt(self, state: ReactAgentState, context: Dict[str, Any]) -> str:
        """Build final answer prompt."""
        observations = []
        for i, obs in enumerate(state["observations"], 1):
            if obs.success:
                observations.append(f"{i}. {obs.result}")
            else:
                observations.append(f"{i}. Error: {obs.error}")
        
        obs_str = "\n".join(observations) if observations else "No successful observations"
        
        return f"""Provide a complete answer based on the observations.

Query: {state['query']}

Observations:
{obs_str}

Provide a clear, helpful answer in Vietnamese:"""
    
    # ========== PARSERS ==========
    
    def _extract_function_name(self, response: str) -> Optional[str]:
        """Extract function name from LLM response."""
        # Try "Function: name" format
        match = re.search(r"Function:\s*(\w+)", response, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Fallback: look for function-like names
        words = response.split()
        for word in words:
            if '_' in word and word.replace('_', '').isalnum():
                return word
        
        return None
    
    def _find_function_schema(
        self,
        function_name: str,
        functions: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Find function schema by name."""
        function_name_lower = function_name.lower()
        
        for func in functions:
            if func.get("name", "").lower() == function_name_lower:
                return func
        
        return None
    
    def _parse_reflection(self, response: str, state: ReactAgentState) -> AgentReflection:
        """Parse reflection from LLM response."""
        quality_score = 0.5
        should_continue = True
        
        try:
            lines = response.strip().split('\n')
            for line in lines:
                if line.startswith("Quality:"):
                    score_str = line.split(":", 1)[1].strip()
                    quality_score = float(score_str)
                elif line.startswith("Continue:"):
                    cont_str = line.split(":", 1)[1].strip().lower()
                    should_continue = cont_str in ["yes", "true", "có"]
        except Exception as e:
            logger.warning(f"Failed to parse reflection: {e}")
        
        return AgentReflection(
            content=response,
            quality_score=quality_score,
            should_continue=should_continue,
            needs_clarification=False,
            step=state["current_step"]
        )
    
    # ========== METRICS ==========
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        return {
            "agent_metrics": self.metrics.get_summary(),
            "selection_stats": self.hybrid_selector.get_stats(),
            "synthesis_stats": self.param_synthesizer.get_stats()
        }
