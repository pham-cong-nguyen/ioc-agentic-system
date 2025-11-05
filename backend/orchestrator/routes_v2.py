"""
ReAct Agent V2 Routes with Step Tracking and SSE Streaming
"""
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
import json

from backend.orchestrator.react_agent_v2 import ReactAgentV2
from backend.orchestrator.llm_service import LLMService
from backend.registry.embeddings.sentence_transformer_embedder import SentenceTransformerEmbedder
from backend.registry.embeddings.milvus_store import MilvusStore
from backend.registry.embeddings.rag_retriever import RAGRetriever
from backend.orchestrator.memory.context_builder import ContextBuilder
from backend.executor.service import APIExecutor
from backend.utils.database import get_db_session
from backend.registry.service import FunctionRegistryService
from config.settings import settings
import os

router = APIRouter(prefix="/v2", tags=["ReAct Agent V2"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class QueryRequest(BaseModel):
    """Query request for ReAct Agent V2"""
    query: str = Field(..., description="Natural language query", min_length=1)
    user_id: str = Field(default="default_user", description="User ID")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    stream: bool = Field(default=False, description="Stream step-by-step updates")


class StepInfo(BaseModel):
    """Information about a single step"""
    step_number: int
    step_type: str  # "thought", "action", "observation", "final"
    content: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None


class APICallInfo(BaseModel):
    """Information about an API call"""
    function_id: str
    function_name: str
    endpoint: str
    method: str
    parameters: Dict[str, Any]
    status: str  # "success", "failed", "pending"
    response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: float
    timestamp: datetime


class QueryResponse(BaseModel):
    """Response with step tracking"""
    success: bool
    query: str
    response: str
    conversation_id: str
    
    # Step tracking
    steps: List[StepInfo]
    api_calls: List[APICallInfo]
    
    # Metrics
    total_steps: int
    total_api_calls: int
    processing_time_ms: float
    quality_score: float
    
    # Metadata
    selection_method: str
    synthesis_strategy: str
    timestamp: datetime


# =============================================================================
# AGENT INITIALIZATION
# =============================================================================

# Global agent instance (initialized on startup)
_agent: Optional[ReactAgentV2] = None


def get_agent() -> ReactAgentV2:
    """Get or initialize the ReAct Agent V2."""
    global _agent
    
    if _agent is None:
        # Initialize components
        llm_service = LLMService()
        
        # RAG Retriever
        embedder = SentenceTransformerEmbedder(
            model_name="jinaai/jina-embeddings-v3",
            device="cuda:0" if settings.USE_GPU else "cpu"
        )
        vector_store = MilvusStore(
            host=os.getenv("MILVUS_HOST", "localhost"),
            port=int(os.getenv("MILVUS_PORT", "19530")),
            collection_name="function_embeddings",
            dimension=embedder.dimension
        )
        rag_retriever = RAGRetriever(embedder, vector_store)
        
        # Context Builder - sử dụng stub managers như trong react_agent.py
        from backend.orchestrator.memory.stub_managers import (
            StubUserProfileManager,
            StubConversationManager
        )
        
        profile_manager = StubUserProfileManager()
        conversation_manager = StubConversationManager()
        context_builder = ContextBuilder(profile_manager, conversation_manager)
        
        # Executor
        executor_service = APIExecutor()
        
        # Registry Service (will be passed per request)
        # For now, we'll pass None and handle it in the route
        
        _agent = ReactAgentV2(
            llm_service=llm_service,
            rag_retriever=rag_retriever,
            context_builder=context_builder,
            executor_service=executor_service,
            registry_service=None,  # Will be set per request
            quality_threshold=0.7,
            max_iterations=5
        )
    
    return _agent


# =============================================================================
# ROUTES
# =============================================================================

@router.post("/query/stream")
async def stream_query(request: QueryRequest):
    """
    Stream query processing with Server-Sent Events (SSE).
    
    Returns real-time updates as steps are processed:
    - event: step_start
    - event: thought
    - event: action
    - event: observation  
    - event: api_call
    - event: final_answer
    - event: complete
    """
    
    async def event_generator():
        """Generate SSE events as agent processes query."""
        try:
            # Send start event
            yield f"event: start\ndata: {json.dumps({'query': request.query, 'user_id': request.user_id})}\n\n"
            
            # Get agent
            agent = get_agent()
            
            # Set registry service
            async with get_db_session() as db:
                agent.registry_service = FunctionRegistryService(db)
                
                # Define streaming callback
                async def stream_callback(event_type: str, data: dict):
                    """Callback to yield SSE events in real-time."""
                    nonlocal event_generator
                    # This won't work directly - need different approach
                    # We'll use asyncio.Queue instead
                    pass
                
                # Use Queue for streaming
                event_queue = asyncio.Queue()
                
                async def queue_callback(event_type: str, data: dict):
                    """Put events in queue as they happen."""
                    await event_queue.put((event_type, data))
                
                # Run agent in background task
                async def run_agent():
                    try:
                        state = await agent.run(
                            user_id=request.user_id,
                            query=request.query,
                            conversation_id=request.conversation_id,
                            stream_callback=queue_callback  # ← REAL-TIME CALLBACK
                        )
                        # Send completion event
                        await event_queue.put(("complete", {
                            "success": state["status"] == "completed",
                            "total_steps": state["current_step"],
                            "total_api_calls": len(state.get("actions", [])),
                            "processing_time_ms": state.get("total_execution_time_ms", 0),
                            "quality_score": state.get("quality_score", 0.0),
                            "conversation_id": request.conversation_id or state.get("conversation_id", "")
                        }))
                    except Exception as e:
                        await event_queue.put(("error", {"error": str(e)}))
                    finally:
                        await event_queue.put((None, None))  # Signal completion
                
                # Start agent task
                agent_task = asyncio.create_task(run_agent())
                
                # Stream events from queue as they arrive
                while True:
                    event_type, data = await event_queue.get()
                    
                    if event_type is None:  # End signal
                        break
                    
                    # Yield SSE event
                    yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
                
                # Wait for agent to complete
                await agent_task
                
        except Exception as e:
            error_data = {"error": str(e)}
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Connection": "keep-alive"
        }
    )


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process query with ReAct Agent V2 and return step-by-step tracking.
    
    This endpoint provides detailed information about:
    - Each reasoning step (Thought, Action, Observation)
    - All API calls made (with parameters, status, and responses)
    - Quality metrics and performance stats
    """
    try:
        # Get agent
        agent = get_agent()
        
        # Set registry service for this request
        async with get_db_session() as db:
            agent.registry_service = FunctionRegistryService(db)
            
            # Run agent
            state = await agent.run(
                user_id=request.user_id,
                query=request.query,
                conversation_id=request.conversation_id
            )
        
        # Extract steps
        steps = []
        step_number = 1
        
        # Add thoughts - handle both AgentThought objects and strings
        for thought in state.get("thoughts", []):
            if hasattr(thought, 'content'):
                # It's an AgentThought object
                content = thought.content
            else:
                # It's a string or dict
                content = str(thought)
            
            steps.append(StepInfo(
                step_number=step_number,
                step_type="thought",
                content=content,
                timestamp=datetime.utcnow(),
                details=None
            ))
            step_number += 1
        
        # Add actions with observations
        for i, action in enumerate(state.get("actions", [])):
            # Handle AgentAction objects
            if hasattr(action, 'function_name'):
                function_id = action.function_id
                function_name = action.function_name
                parameters = action.parameters
                reasoning = action.reasoning if hasattr(action, 'reasoning') else None
            else:
                function_id = action.get("function_id", "unknown")
                function_name = action.get("function_name", "Unknown")
                parameters = action.get("parameters", {})
                reasoning = action.get("reasoning")
            
            # Action step
            steps.append(StepInfo(
                step_number=step_number,
                step_type="action",
                content=f"Execute function: {function_name}",
                timestamp=datetime.utcnow(),
                details={
                    "function_id": function_id,
                    "function_name": function_name,
                    "parameters": parameters,
                    "reasoning": reasoning
                }
            ))
            step_number += 1
            
            # Observation step
            if i < len(state.get("observations", [])):
                obs = state["observations"][i]
                
                # Handle AgentObservation objects
                if hasattr(obs, 'result'):
                    obs_content = f"Result: {str(obs.result)[:200]}"
                    obs_details = {
                        "success": obs.success,
                        "result": obs.result,
                        "error": obs.error if hasattr(obs, 'error') else None,
                        "execution_time_ms": obs.execution_time_ms if hasattr(obs, 'execution_time_ms') else 0
                    }
                else:
                    obs_content = obs.get("summary", str(obs)[:200])
                    obs_details = obs
                
                steps.append(StepInfo(
                    step_number=step_number,
                    step_type="observation",
                    content=obs_content,
                    timestamp=datetime.utcnow(),
                    details=obs_details
                ))
                step_number += 1
        
        # Add final answer
        if state.get("final_answer"):
            steps.append(StepInfo(
                step_number=step_number,
                step_type="final",
                content=state["final_answer"],
                timestamp=datetime.utcnow(),
                details={
                    "quality_score": state.get("quality_score", 0.0)
                }
            ))
        
        # Extract API calls
        api_calls = []
        for i, action in enumerate(state.get("actions", [])):
            # Handle AgentAction objects
            if hasattr(action, 'function_name'):
                function_id = action.function_id
                function_name = action.function_name
                parameters = action.parameters
            else:
                function_id = action.get("function_id", "unknown")
                function_name = action.get("function_name", "Unknown")
                parameters = action.get("parameters", {})
            
            # Find corresponding observation
            result = None
            if i < len(state.get("observations", [])):
                obs = state["observations"][i]
                
                # Handle AgentObservation objects
                if hasattr(obs, 'result'):
                    result = {
                        "success": obs.success,
                        "data": obs.result,
                        "error": obs.error if hasattr(obs, 'error') else None,
                        "execution_time_ms": obs.execution_time_ms if hasattr(obs, 'execution_time_ms') else 0
                    }
                else:
                    result = obs
            
            api_calls.append(APICallInfo(
                function_id=function_id,
                function_name=function_name,
                endpoint="",  # ReactAgentV2 doesn't store endpoint in action
                method="POST",
                parameters=parameters,
                status="success" if result and result.get("success") else "failed",
                response=result.get("data") if result else None,
                error=result.get("error") if result else None,
                execution_time_ms=result.get("execution_time_ms", 0) if result else 0,
                timestamp=datetime.utcnow()
            ))
        
        return QueryResponse(
            success=state["status"] == "completed",
            query=request.query,
            response=state.get("final_answer", ""),
            conversation_id=request.conversation_id or state.get("conversation_id") or "default_conversation",
            steps=steps,
            api_calls=api_calls,
            total_steps=len(steps),
            total_api_calls=len(api_calls),
            processing_time_ms=state.get("total_execution_time_ms", 0),
            quality_score=state.get("quality_score", 0.0),
            selection_method=str(state.get("selection_method", "unknown")),
            synthesis_strategy=str(state.get("synthesis_strategy", "unknown")),
            timestamp=datetime.utcnow()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )


@router.websocket("/query/stream")
async def stream_query(websocket: WebSocket):
    """
    Stream query processing step-by-step via WebSocket.
    
    Client sends: {"query": "...", "user_id": "...", "conversation_id": "..."}
    Server sends: {"type": "step|api_call|final", "data": {...}}
    """
    await websocket.accept()
    
    try:
        # Receive query
        data = await websocket.receive_json()
        query = data.get("query")
        user_id = data.get("user_id", "default_user")
        conversation_id = data.get("conversation_id")
        
        if not query:
            await websocket.send_json({
                "type": "error",
                "message": "Query is required"
            })
            await websocket.close()
            return
        
        # Get agent
        agent = get_agent()
        
        # Process with streaming
        async with get_db_session() as db:
            agent.registry_service = FunctionRegistryService(db)
            
            # Send start message
            await websocket.send_json({
                "type": "start",
                "data": {
                    "query": query,
                    "user_id": user_id
                }
            })
            
            # Run agent (we'll need to modify agent to support streaming)
            # For now, run normally and send updates
            state = await agent.run(user_id, query, conversation_id)
            
            # Send steps
            step_number = 1
            for thought in state.get("thoughts", []):
                await websocket.send_json({
                    "type": "step",
                    "data": {
                        "step_number": step_number,
                        "step_type": "thought",
                        "content": thought
                    }
                })
                step_number += 1
                await asyncio.sleep(0.1)  # Small delay for UX
            
            # Send actions and observations
            for i, action in enumerate(state.get("actions", [])):
                await websocket.send_json({
                    "type": "step",
                    "data": {
                        "step_number": step_number,
                        "step_type": "action",
                        "content": f"Execute: {action.get('function_name')}"
                    }
                })
                step_number += 1
                
                # Send API call details
                await websocket.send_json({
                    "type": "api_call",
                    "data": {
                        "function_name": action.get("function_name"),
                        "parameters": action.get("parameters"),
                        "status": "executing"
                    }
                })
                
                await asyncio.sleep(0.1)
                
                # Send observation
                if i < len(state.get("observations", [])):
                    obs = state["observations"][i]
                    await websocket.send_json({
                        "type": "step",
                        "data": {
                            "step_number": step_number,
                            "step_type": "observation",
                            "content": obs.get("summary", "")
                        }
                    })
                    
                    # Update API call status
                    await websocket.send_json({
                        "type": "api_call_complete",
                        "data": {
                            "function_name": action.get("function_name"),
                            "status": "success" if obs.get("success") else "failed",
                            "response": obs.get("data")
                        }
                    })
                    
                    step_number += 1
            
            # Send final answer
            await websocket.send_json({
                "type": "final",
                "data": {
                    "response": state.get("final_answer", ""),
                    "quality_score": state.get("quality_score", 0.0),
                    "processing_time_ms": state.get("total_execution_time_ms", 0)
                }
            })
        
        await websocket.close()
    
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
        await websocket.close()


@router.get("/metrics")
async def get_metrics():
    """Get agent performance metrics."""
    try:
        agent = get_agent()
        metrics = agent.get_metrics_summary()
        
        return {
            "success": True,
            "data": metrics,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting metrics: {str(e)}"
        )


@router.get("/streaming-config")
async def get_streaming_config():
    """Get streaming configuration settings for frontend."""
    return {
        "success": True,
        "data": {
            # Final answer streaming (slower, dramatic)
            "charsPerFrame": settings.STREAM_CHARS_PER_FRAME,
            "minDelay": settings.STREAM_MIN_DELAY_MS,
            "maxDelay": settings.STREAM_MAX_DELAY_MS,
            # Internal steps streaming (faster)
            "internalCharsPerFrame": settings.STREAM_INTERNAL_CHARS_PER_FRAME,
            "internalMinDelay": settings.STREAM_INTERNAL_MIN_DELAY_MS,
            "internalMaxDelay": settings.STREAM_INTERNAL_MAX_DELAY_MS
        },
        "timestamp": datetime.utcnow()
    }


@router.post("/reset")
async def reset_agent():
    """Reset agent state and metrics."""
    global _agent
    _agent = None
    
    return {
        "success": True,
        "message": "Agent reset successfully"
    }
