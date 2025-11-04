"""
State definitions for LangGraph orchestration
"""
from typing import List, Dict, Any, Optional
from typing_extensions import Annotated
from pydantic import BaseModel, Field
from datetime import datetime


class FunctionCall(BaseModel):
    """A single function call in execution plan"""
    function_id: str
    name: str
    parameters: Dict[str, Any]
    depends_on: Optional[List[str]] = None  # List of function_ids this depends on
    order: int = 0


class ExecutionPlan(BaseModel):
    """Execution plan with multiple function calls"""
    function_calls: List[FunctionCall]
    execution_mode: str = "sequential"  # sequential or parallel
    reasoning: Optional[str] = None  # LLM's reasoning for the plan


class ExecutionResult(BaseModel):
    """Result from executing a function"""
    function_id: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float
    cached: bool = False


class AgentState(BaseModel):
    """State maintained throughout the orchestration process"""
    
    # Input
    query: str = Field(..., description="User's natural language query")
    language: str = Field(default="vi", description="Query language (vi/en)")
    user_id: Optional[str] = Field(None, description="User identifier")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    
    # Query understanding
    parsed_intent: Optional[str] = None
    extracted_entities: Optional[Dict[str, Any]] = None
    query_type: Optional[str] = None  # data_query, analytics, comparison, trend
    
    # Function selection
    relevant_functions: List[Dict[str, Any]] = []
    execution_plan: Optional[ExecutionPlan] = None
    
    # Execution
    execution_results: List[ExecutionResult] = []
    
    # Analysis
    analyzed_data: Optional[Dict[str, Any]] = None
    insights: Optional[List[str]] = None
    
    # Response generation
    response: Optional[str] = None
    visualization_config: Optional[Dict[str, Any]] = None
    
    # Messages (for LangGraph message tracking)
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: Optional[float] = None
    error: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True


class ConversationContext(BaseModel):
    """Context from previous conversations"""
    conversation_id: str
    previous_queries: List[str]
    previous_results: List[Dict[str, Any]]
    user_preferences: Optional[Dict[str, Any]] = None
    domain_focus: Optional[str] = None
