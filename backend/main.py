"""
Main FastAPI application entry point
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, status, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
import jwt
from typing import Optional

from config.settings import settings
from backend.registry.routes import router as registry_router
from backend.orchestrator.routes import router as orchestrator_router, conversations_router
from backend.auth.routes import router as auth_router
from backend.utils.database import init_db, close_db
from backend.utils.cache import cache

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting IOC Agentic System...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")
        
        # Test cache connection
        await cache.set("health_check", "ok", ttl=10)
        logger.info("Cache connection established")
        
        logger.info("Application startup complete")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down IOC Agentic System...")
    
    try:
        # Close database connections
        await close_db()
        logger.info("Database connections closed")
        
        # Close orchestrator resources
        from backend.orchestrator.graph import orchestrator
        await orchestrator.close()
        logger.info("Orchestrator resources closed")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")
    
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intelligent Operations Center Agentic System - Natural language query processing for IOC APIs",
    lifespan=lifespan,
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    redirect_slashes=True
)


# CORS middleware
# Allow all origins in development, specific origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# # Request logging middleware
# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     """Log all requests"""
#     logger.info(f"{request.method} {request.url.path}")
#     response = await call_next(request)
#     logger.info(f"Status: {response.status_code}")
#     return response


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path,
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "status_code": 422,
            "path": request.url.path,
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "path": request.url.path,
            "message": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


# Register routers
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(registry_router, prefix=settings.API_PREFIX)
app.include_router(orchestrator_router, prefix=settings.API_PREFIX)
app.include_router(conversations_router, prefix=settings.API_PREFIX)


# Mount static files for frontend
frontend_path = Path(__file__).parent.parent / "frontend"
if (frontend_path.exists()):
    app.mount("/src", StaticFiles(directory=str(frontend_path / "src")), name="frontend-src")
    app.mount("/public", StaticFiles(directory=str(frontend_path / "public")), name="frontend-public")
    logger.info(f"Mounted frontend static files from {frontend_path}")


# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# WebSocket endpoint for streaming responses
@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time streaming of LLM responses
    
    Query parameters:
        token: JWT authentication token (optional for demo)
    """
    await websocket.accept()
    logger.info(f"WebSocket connection established")
    
    try:
        # Validate token if provided (optional in demo mode)
        if token:
            try:
                from jwt.exceptions import DecodeError, InvalidTokenError
                payload = jwt.decode(
                    token,
                    settings.JWT_SECRET_KEY,
                    algorithms=["HS256"]
                )
                username = payload.get("username", "anonymous")
                logger.info(f"WebSocket authenticated as {username}")
            except (DecodeError, InvalidTokenError) as e:
                logger.warning(f"WebSocket auth failed: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Authentication failed"
                })
                await websocket.close(code=1008)
                return
        
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket connection established",
            "timestamp": "2025-11-04T00:00:00Z"
        })
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()
                message_type = data.get("type")
                
                if message_type == "ping":
                    # Respond to ping with pong
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": "2025-11-04T00:00:00Z"
                    })
                
                elif message_type == "query":
                    # Handle query streaming (to be implemented)
                    query = data.get("query", "")
                    logger.info(f"Received query via WebSocket: {query}")
                    
                    # Send acknowledgment
                    await websocket.send_json({
                        "type": "query_received",
                        "query": query,
                        "timestamp": "2025-11-04T00:00:00Z"
                    })
                    
                    # TODO: Integrate with orchestrator for streaming responses
                    # For now, send a placeholder response
                    await websocket.send_json({
                        "type": "response",
                        "message": "WebSocket streaming not fully implemented yet. Use REST API for queries.",
                        "timestamp": "2025-11-04T00:00:00Z"
                    })
                
                else:
                    # Unknown message type
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    })
                    
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected")
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                break
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        logger.info("WebSocket connection closed")


@app.get("/")
async def root():
    """Serve frontend index.html"""
    frontend_index = frontend_path / "index.html"
    if frontend_index.exists():
        return FileResponse(str(frontend_index))
    
    # Fallback to API info if frontend not found
    return {
        "message": "IOC Agentic System API",
        "version": settings.APP_VERSION,
        "docs": f"{settings.API_PREFIX}/docs",
        "health": "/health"
    }


@app.get(f"{settings.API_PREFIX}/status")
async def system_status():
    """System status endpoint"""
    try:
        # Check database
        from backend.utils.database import engine
        db_healthy = engine is not None
        
        # Check cache
        cache_test = await cache.get("health_check")
        cache_healthy = cache_test is not None
        
        return {
            "status": "operational" if db_healthy and cache_healthy else "degraded",
            "components": {
                "database": "healthy" if db_healthy else "unhealthy",
                "cache": "healthy" if cache_healthy else "unhealthy",
                "llm": "configured"
            },
            "timestamp": "2025-11-03T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS
    )
