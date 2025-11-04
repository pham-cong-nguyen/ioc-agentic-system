"""
Orchestration routes for query processing
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from backend.orchestrator.graph import orchestrator
from backend.auth.service import get_current_user

router = APIRouter(prefix="/query", tags=["Query Processing"])
conversations_router = APIRouter(prefix="/conversations", tags=["Conversations"])


class ConversationSummary(BaseModel):
    """Conversation summary for listing"""
    conversation_id: str
    title: str
    last_message: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class ConversationDetail(BaseModel):
    """Full conversation details"""
    conversation_id: str
    title: str
    messages: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class QueryRequest(BaseModel):
    """Query request"""
    query: str = Field(..., description="Natural language query", min_length=1)
    language: str = Field(default="vi", description="Query language (vi/en)")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")


class QueryResponse(BaseModel):
    """Query response"""
    query_id: str
    response: str
    visualization_config: Optional[Dict[str, Any]] = None
    execution_plan: Optional[Dict[str, Any]] = None
    execution_results: List[Dict[str, Any]] = []
    insights: List[str] = []
    processing_time_ms: float
    timestamp: datetime


class FeedbackRequest(BaseModel):
    """Feedback request"""
    query_id: str = Field(..., description="Query ID to provide feedback for")
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5")
    feedback: Optional[str] = Field(None, description="Optional feedback text")


class QueryHistory(BaseModel):
    """Query history item"""
    query_id: str
    query: str
    response: str
    timestamp: datetime
    processing_time_ms: float


@router.post("/", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Process a natural language query through the orchestration graph
    
    The system will:
    1. Parse the query to understand intent
    2. Search for relevant API functions
    3. Plan execution
    4. Execute API calls
    5. Analyze results
    6. Generate natural language response
    """
    
    try:
        # Process query through orchestration graph
        final_state = await orchestrator.process_query(
            query=request.query,
            language=request.language,
            user_id=current_user["sub"],
            conversation_id=request.conversation_id
        )
        
        # Generate unique query ID
        query_id = f"q_{current_user['sub']}_{int(datetime.utcnow().timestamp())}"
        
        # Format execution plan
        execution_plan = None
        if final_state.execution_plan:
            execution_plan = {
                "function_calls": [
                    {
                        "function_id": fc.function_id,
                        "name": fc.name,
                        "parameters": fc.parameters,
                        "order": fc.order
                    }
                    for fc in final_state.execution_plan.function_calls
                ],
                "execution_mode": final_state.execution_plan.execution_mode,
                "reasoning": final_state.execution_plan.reasoning
            }
        
        # Format execution results
        execution_results = [
            {
                "function_id": r.function_id,
                "success": r.success,
                "data": r.data,
                "error": r.error,
                "execution_time_ms": r.execution_time_ms,
                "cached": r.cached
            }
            for r in final_state.execution_results
        ] if final_state.execution_results else []
        
        # TODO: Save to conversation history database
        
        return QueryResponse(
            query_id=query_id,
            response=final_state.response or "No response generated",
            visualization_config=final_state.visualization_config,
            execution_plan=execution_plan,
            execution_results=execution_results,
            insights=final_state.insights or [],
            processing_time_ms=final_state.processing_time_ms or 0,
            timestamp=datetime.utcnow()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )


@router.get("/history", response_model=List[QueryHistory])
async def get_query_history(
    conversation_id: Optional[str] = None,
    limit: int = 10,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get query history for the current user
    
    Optionally filter by conversation_id
    """
    
    # TODO: Implement database query for history
    # For now, return empty list
    
    return []


@router.get("/examples")
async def get_example_queries(
    language: str = "vi",
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get example queries for the user to try
    
    NOTE: This route MUST be defined before /{query_id} 
    to avoid being caught by the path parameter
    """
    # TODO: Implement dynamic examples based on available functions
    examples_vi = [
        {
            "query": "Mức tiêu thụ điện hôm nay là bao nhiêu?",
            "category": "energy",
            "icon": "fa-bolt"
        },
        {
            "query": "So sánh lưu lượng giao thông tuần này với tuần trước",
            "category": "traffic",
            "icon": "fa-traffic-light"
        },
        {
            "query": "Chất lượng không khí ở Hà Nội như thế nào?",
            "category": "environment",
            "icon": "fa-wind"
        },
        {
            "query": "Hiển thị biểu đồ nhiệt độ 7 ngày qua",
            "category": "weather",
            "icon": "fa-cloud-sun"
        }
    ]
    
    examples_en = [
        {
            "query": "What is today's electricity consumption?",
            "category": "energy",
            "icon": "fa-bolt"
        },
        {
            "query": "Compare this week's traffic with last week",
            "category": "traffic",
            "icon": "fa-traffic-light"
        },
        {
            "query": "What is the air quality in Hanoi?",
            "category": "environment",
            "icon": "fa-wind"
        },
        {
            "query": "Show temperature chart for the last 7 days",
            "category": "weather",
            "icon": "fa-cloud-sun"
        }
    ]
    
    return examples_vi if language == "vi" else examples_en


@router.post("/feedback")
async def submit_feedback(
    feedback_request: FeedbackRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Submit feedback for a query response
    
    Helps improve the system over time
    """
    
    # TODO: Save feedback to database
    
    return {
        "message": "Feedback submitted successfully",
        "query_id": feedback_request.query_id,
        "rating": feedback_request.rating
    }


@router.get("/{query_id}", response_model=QueryResponse)
async def get_query_result(
    query_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a specific query result by ID
    
    NOTE: This route must be defined AFTER specific routes like /examples
    because it will match any path
    """
    
    # TODO: Implement database query
    # For now, return 404
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Query {query_id} not found"
    )


@conversations_router.get("", response_model=List[ConversationSummary])
async def list_conversations(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List all conversations for the current user
    """
    # TODO: Implement database query
    # For now, return empty list
    return []


@conversations_router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get full conversation details
    """
    # TODO: Implement database query
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Conversation {conversation_id} not found"
    )


@conversations_router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a conversation
    """
    # TODO: Implement database deletion
    return {
        "message": "Conversation deleted successfully",
        "conversation_id": conversation_id
    }
