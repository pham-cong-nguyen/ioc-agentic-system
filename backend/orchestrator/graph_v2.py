# backend/orchestrator/graph.py - FIX DATABASE INTEGRATION

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from backend.orchestrator.state import AgentState, ExecutionPlan, FunctionCall, ExecutionResult
from backend.orchestrator.llm_service import llm_service
from backend.registry.service import FunctionRegistryService
from backend.executor.service import executor
from backend.analyzer.service import analyzer
from backend.utils.database import get_db_context

logger = logging.getLogger(__name__)


class OrchestrationGraph:
    """LangGraph orchestration for query processing"""
    
    def __init__(self):
        self.executor = executor
        self.analyzer = analyzer
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph"""
        
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("parse_query", self.parse_query_node)
        workflow.add_node("search_functions", self.search_functions_node)
        workflow.add_node("plan_execution", self.plan_execution_node)
        workflow.add_node("execute_functions", self.execute_functions_node)
        workflow.add_node("analyze_results", self.analyze_results_node)
        workflow.add_node("generate_response", self.generate_response_node)
        workflow.add_node("handle_error", self.handle_error_node)
        
        # Define edges
        workflow.set_entry_point("parse_query")
        workflow.add_edge("parse_query", "search_functions")
        workflow.add_edge("search_functions", "plan_execution")
        
        workflow.add_conditional_edges(
            "plan_execution",
            self._should_execute,
            {
                "execute": "execute_functions",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "execute_functions",
            self._execution_successful,
            {
                "analyze": "analyze_results",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("analyze_results", "generate_response")
        workflow.add_edge("generate_response", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile(checkpointer=MemorySaver())
    
    async def parse_query_node(self, state: AgentState) -> Dict[str, Any]:
        """Node: Parse user query to extract intent and entities"""
        logger.info(f"Parsing query: {state.query}")
        
        try:
            intent = await llm_service.parse_query(
                query=state.query,
                language=state.language,
                conversation_context=None
            )
            
            return {
                "parsed_intent": intent.intent,
                "extracted_entities": intent.entities,
                "query_type": intent.query_type
            }
        
        except Exception as e:
            logger.error(f"Error in parse_query_node: {e}")
            return {"error": f"Failed to parse query: {str(e)}"}
    
    async def search_functions_node(self, state: AgentState) -> Dict[str, Any]:
        """Node: Search for relevant functions - FIXED WITH DB SESSION"""
        logger.info(f"Searching functions for intent: {state.parsed_intent}")
        
        try:
            # Build search query
            search_terms = []
            
            if state.extracted_entities and state.extracted_entities.get("domain"):
                search_terms.append(state.extracted_entities["domain"])
            
            if state.query_type:
                search_terms.append(state.query_type)
            
            search_terms.append(state.parsed_intent)
            search_query = " ".join(search_terms)
            
            # 🔥 FIX: Use database context manager to get session
            async with get_db_context() as db:
                registry_service = FunctionRegistryService(db)
                
                # Search functions in database
                from backend.registry.schemas import FunctionSearchQuery, Domain
                
                # Convert domain string to enum
                domain_filter = None
                if state.extracted_entities and state.extracted_entities.get("domain"):
                    domain_str = state.extracted_entities["domain"]
                    try:
                        domain_filter = Domain(domain_str.lower())
                    except ValueError:
                        logger.warning(f"Invalid domain: {domain_str}")
                
                search_obj = FunctionSearchQuery(
                    query=search_query,
                    domain=domain_filter,
                    limit=10
                )
                
                functions_list, total = await registry_service.search_functions(search_obj)
                
                # Convert to dict format
                relevant_functions = [
                    {
                        "function_id": func.function_id,
                        "name": func.name,
                        "description": func.description,
                        "domain": func.domain,
                        "method": func.method,
                        "endpoint": func.endpoint,
                        "parameters": func.parameters,
                        "response_schema": func.response_schema
                    }
                    for func in functions_list
                ]
            
            logger.info(f"Found {len(relevant_functions)} relevant functions")
            return {"relevant_functions": relevant_functions}
        
        except Exception as e:
            logger.error(f"Error in search_functions_node: {e}", exc_info=True)
            return {"relevant_functions": [], "error": f"Failed to search functions: {str(e)}"}
    
    async def plan_execution_node(self, state: AgentState) -> Dict[str, Any]:
        """Node: Plan function execution using LLM"""
        logger.info("Planning function execution")
        
        try:
            if not state.relevant_functions:
                return {"error": "No relevant functions found for query"}
            
            # Use LLM to select functions and create plan
            from backend.orchestrator.llm_service import QueryIntent
            
            intent_obj = QueryIntent(
                intent=state.parsed_intent or "data_query",
                entities=state.extracted_entities or {},
                query_type=state.query_type or "unknown",
                confidence=0.8
            )
            
            selection = await llm_service.select_functions(
                query=state.query,
                intent=intent_obj,
                available_functions=state.relevant_functions,
                language=state.language
            )
            
            # Build execution plan
            function_calls = []
            for i, func_id in enumerate(selection.function_ids):
                func_details = next(
                    (f for f in state.relevant_functions if f["function_id"] == func_id),
                    None
                )
                
                if func_details:
                    function_calls.append(FunctionCall(
                        function_id=func_id,
                        name=func_details["name"],
                        parameters=selection.parameters.get(func_id, {}),
                        order=i
                    ))
            
            execution_plan = ExecutionPlan(
                function_calls=function_calls,
                execution_mode=selection.execution_mode,
                reasoning=selection.reasoning
            )
            
            logger.info(f"Created execution plan with {len(function_calls)} functions")
            return {"execution_plan": execution_plan}
        
        except Exception as e:
            logger.error(f"Error in plan_execution_node: {e}", exc_info=True)
            return {"error": f"Failed to plan execution: {str(e)}"}
    
    async def execute_functions_node(self, state: AgentState) -> Dict[str, Any]:
        """Node: Execute planned functions"""
        logger.info("Executing functions")
        
        try:
            if not state.execution_plan:
                return {"error": "No execution plan"}
            
            # Get registry service for executor
            async with get_db_context() as db:
                registry_service = FunctionRegistryService(db)
                
                results = []
                
                # Execute based on mode
                if state.execution_plan.execution_mode == "parallel":
                    results = await self.executor.execute_parallel(
                        [
                            {"function_id": fc.function_id, "parameters": fc.parameters}
                            for fc in state.execution_plan.function_calls
                        ],
                        registry_service
                    )
                else:
                    results = await self.executor.execute_sequential(
                        [
                            {"function_id": fc.function_id, "parameters": fc.parameters}
                            for fc in state.execution_plan.function_calls
                        ],
                        registry_service
                    )
            
            # Convert to ExecutionResult objects
            execution_results = [
                ExecutionResult(
                    function_id=r["function_id"],
                    success=r["success"],
                    data=r.get("data"),
                    error=r.get("error"),
                    execution_time_ms=r.get("execution_time", 0) * 1000,  # Convert to ms
                    cached=r.get("cached", False)
                )
                for r in results
            ]
            
            logger.info(f"Executed {len(execution_results)} functions")
            return {"execution_results": execution_results}
        
        except Exception as e:
            logger.error(f"Error in execute_functions_node: {e}", exc_info=True)
            return {"error": f"Failed to execute functions: {str(e)}"}
    
    async def analyze_results_node(self, state: AgentState) -> Dict[str, Any]:
        """Node: Analyze execution results"""
        logger.info("Analyzing results")
        
        try:
            # Combine all successful results
            combined_data = [
                result.data for result in state.execution_results
                if result.success and result.data
            ]
            
            if not combined_data:
                return {
                    "analyzed_data": None,
                    "insights": ["No data available for analysis"]
                }
            
            # Perform analysis
            analyzed_data = await self.analyzer.analyze(
                data=combined_data,
                query_type=state.query_type or "data_query",
                entities=state.extracted_entities
            )
            
            # Generate insights
            insights = await self.analyzer.generate_insights(
                data=analyzed_data,
                query_type=state.query_type or "data_query"
            )
            
            logger.info(f"Generated {len(insights)} insights")
            return {"analyzed_data": analyzed_data, "insights": insights}
        
        except Exception as e:
            logger.error(f"Error in analyze_results_node: {e}", exc_info=True)
            return {"analyzed_data": None, "insights": [f"Analysis error: {str(e)}"]}
    
    async def generate_response_node(self, state: AgentState) -> Dict[str, Any]:
        """Node: Generate natural language response"""
        logger.info("Generating response")
        
        try:
            results_summary = [
                {
                    "function_id": r.function_id,
                    "success": r.success,
                    "data": r.data,
                    "cached": r.cached
                }
                for r in state.execution_results
            ]
            
            # Generate response using LLM
            response = await llm_service.generate_response(
                query=state.query,
                execution_results=results_summary,
                insights=state.insights,
                language=state.language
            )
            
            # Suggest visualization
            visualization_config = None
            if state.analyzed_data:
                visualization_config = await llm_service.suggest_visualization(
                    data=state.analyzed_data,
                    query_type=state.query_type or "data_query"
                )
            
            processing_time = (datetime.utcnow() - state.created_at).total_seconds() * 1000
            
            logger.info("Response generated successfully")
            return {
                "response": response,
                "visualization_config": visualization_config,
                "processing_time_ms": processing_time
            }
        
        except Exception as e:
            logger.error(f"Error in generate_response_node: {e}", exc_info=True)
            return {"response": "Unable to generate response due to an error.", "error": str(e)}
    
    async def handle_error_node(self, state: AgentState) -> Dict[str, Any]:
        """Node: Handle errors gracefully"""
        logger.error(f"Handling error: {state.error}")
        
        error_message = state.error or "An unexpected error occurred"
        
        if state.language == "vi":
            response = f"Xin lỗi, đã xảy ra lỗi khi xử lý truy vấn của bạn: {error_message}"
        else:
            response = f"Sorry, an error occurred while processing your query: {error_message}"
        
        return {
            "response": response,
            "processing_time_ms": (datetime.utcnow() - state.created_at).total_seconds() * 1000
        }
    
    def _should_execute(self, state: AgentState) -> str:
        """Conditional: Check if execution plan is valid"""
        if state.error:
            return "error"
        if state.execution_plan and state.execution_plan.function_calls:
            return "execute"
        return "error"
    
    def _execution_successful(self, state: AgentState) -> str:
        """Conditional: Check if execution was successful"""
        if state.error:
            return "error"
        if state.execution_results and any(r.success for r in state.execution_results):
            return "analyze"
        return "error"
    
    async def process_query(
        self,
        query: str,
        language: str = "vi",
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> AgentState:
        """Process a user query through the orchestration graph"""
        
        initial_state = AgentState(
            query=query,
            language=language,
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        config = {"configurable": {"thread_id": conversation_id or "default"}}
        final_state = await self.graph.ainvoke(initial_state, config)
        
        return final_state
    
    async def close(self):
        """Cleanup resources"""
        await self.executor.close()


# Global orchestrator instance
orchestrator = OrchestrationGraph()

if __name__ == "__main__":
    import asyncio
    
    async def main():
        user_id = "user_123"
        conversation_id = "conv_1"
        query = "Lấy dữ liệu tiêu thụ điện năng trong tháng trước tại Hà Nội"
        # result_state = await orchestrator.process_query(query=query, language="vi", user_id=user_id, conversation_id=conversation_id)
        # print("Final Response:", result_state.response)
        # print("Insights:", result_state.insights)
        orchestrator = OrchestrationGraph()
        result_state = await orchestrator.parse_query_node(AgentState(
            query=query,
            language="vi"
        ))
        print(result_state)
    
    asyncio.run(main())