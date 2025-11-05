"""
Function Registry API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging
from backend.registry.sync_service import SyncService
import logging

from backend.registry.service import FunctionRegistryService
from backend.registry.sync_service import SyncService
from backend.registry.schemas import (
    FunctionMetadataCreate,
    FunctionMetadataUpdate,
    FunctionMetadataResponse,
    FunctionSearchQuery,
    FunctionListResponse,
    BulkImportRequest,
    BulkImportResponse,
    Domain
)
from backend.utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/registry", tags=["Function Registry"])


@router.post(
    "/functions",
    response_model=FunctionMetadataResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_function(
    function_data: FunctionMetadataCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new function in registry"""
    service = FunctionRegistryService(db)
    
    try:
        function = await service.create_function(function_data)
        return function
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create function: {str(e)}"
        )


@router.get(
    "/functions",
    response_model=FunctionListResponse
)
async def list_functions(
    domain: Optional[Domain] = Query(None, description="Filter by domain"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    deprecated: Optional[bool] = Query(None, description="Filter by deprecated status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List functions with filters"""
    service = FunctionRegistryService(db)
    
    functions, total = await service.list_functions(
        domain=domain,
        tags=tags,
        deprecated=deprecated,
        limit=limit,
        offset=offset
    )
    
    return FunctionListResponse(
        total=total,
        items=functions,
        limit=limit,
        offset=offset
    )


@router.post(
    "/functions/search",
    response_model=FunctionListResponse
)
async def search_functions(
    search_query: FunctionSearchQuery,
    db: AsyncSession = Depends(get_db)
):
    """Search functions"""
    service = FunctionRegistryService(db)
    
    functions, total = await service.search_functions(search_query)
    
    return FunctionListResponse(
        total=total,
        items=functions,
        limit=search_query.limit,
        offset=search_query.offset
    )


@router.get(
    "/functions/search",
    response_model=FunctionListResponse
)
async def search_functions_get(
    query: Optional[str] = Query(None, description="Search text"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    deprecated: Optional[bool] = Query(None, description="Filter by deprecated status"),
    limit: int = Query(50, ge=1, le=100, description="Result limit"),
    offset: int = Query(0, ge=0, description="Result offset"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search functions (GET version for frontend compatibility)
    
    NOTE: This must be defined BEFORE /functions/{function_id}
    to avoid the path parameter catching "search" as a function_id
    """
    # Convert comma-separated tags to list
    tags_list = tags.split(',') if tags else None
    
    # Convert domain string to Domain enum if valid
    domain_enum = None
    if domain and domain != "null":
        try:
            domain_enum = Domain(domain)
        except ValueError:
            pass  # Invalid domain, ignore
    
    # Create search query object
    search_query = FunctionSearchQuery(
        query=query if query else None,
        domain=domain_enum,
        tags=tags_list,
        deprecated=deprecated,
        limit=limit,
        offset=offset
    )
    
    service = FunctionRegistryService(db)
    functions, total = await service.search_functions(search_query)
    
    return FunctionListResponse(
        total=total,
        items=functions,
        limit=limit,
        offset=offset
    )


@router.get(
    "/functions/domain/{domain}",
    response_model=List[FunctionMetadataResponse]
)
async def get_functions_by_domain(
    domain: Domain,
    db: AsyncSession = Depends(get_db)
):
    """Get all functions in a domain"""
    service = FunctionRegistryService(db)
    functions = await service.get_functions_by_domain(domain)
    return functions


@router.post(
    "/functions/bulk-import",
    response_model=BulkImportResponse
)
async def bulk_import_functions(
    import_data: BulkImportRequest,
    db: AsyncSession = Depends(get_db)
):
    """Bulk import functions"""
    service = FunctionRegistryService(db)
    
    result = await service.bulk_import(
        functions=import_data.functions,
        overwrite=import_data.overwrite
    )
    
    return BulkImportResponse(**result)


@router.get("/functions/export")
async def export_functions(
    domain: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Export all functions to JSON format
    
    NOTE: This must be defined BEFORE /functions/{function_id}
    
    TODO: Implement export functionality
    - Query all functions from database
    - Format as JSON array
    - Return as downloadable file
    """
    service = FunctionRegistryService(db)
    
    # For now, return basic structure
    # TODO: Implement full export with filtering by domain
    return {
        "functions": [],
        "exported_at": "2025-11-04T00:00:00Z",
        "total": 0,
        "domain": domain
    }


@router.get(
    "/functions/{function_id}",
    response_model=FunctionMetadataResponse
)
async def get_function(
    function_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get function by ID
    
    NOTE: This must be defined AFTER specific routes like /functions/search
    because it will match any path
    """
    service = FunctionRegistryService(db)
    function = await service.get_function(function_id)
    
    if not function:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Function {function_id} not found"
        )
    
    return function


@router.put(
    "/functions/{function_id}",
    response_model=FunctionMetadataResponse
)
async def update_function(
    function_id: str,
    update_data: FunctionMetadataUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update function"""
    service = FunctionRegistryService(db)
    function = await service.update_function(function_id, update_data)
    
    if not function:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Function {function_id} not found"
        )
    
    return function


@router.delete(
    "/functions/{function_id}",
    status_code=status.HTTP_200_OK
)
async def delete_function(
    function_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete function"""
    service = FunctionRegistryService(db)
    success = await service.delete_function(function_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Function {function_id} not found"
        )
    
    return {
        "success": True,
        "message": f"Function {function_id} deleted successfully"
    }


@router.get("/domains")
async def get_domains(db: AsyncSession = Depends(get_db)):
    """Get all unique domains"""
    service = FunctionRegistryService(db)
    domains = await service.get_domains()
    return {"domains": domains}


@router.get("/statistics")
async def get_statistics(db: AsyncSession = Depends(get_db)):
    """Get registry statistics"""
    service = FunctionRegistryService(db)
    stats = await service.get_statistics()
    return stats


@router.post("/sync")
async def sync_to_milvus(db: AsyncSession = Depends(get_db)):
    """
    Sync all functions from PostgreSQL to Milvus vector database.
    
    This endpoint:
    1. Loads all functions from PostgreSQL
    2. Generates embeddings using sentence transformers
    3. Indexes them into Milvus for semantic search
    
    Returns:
        Sync statistics including success status and count
    """
    service = FunctionRegistryService(db)
    
    try:
        result = await service.sync_to_milvus()
        
        if result["success"]:
            return {
                "status": "success",
                "message": result["message"],
                "synced_count": result["synced_count"],
                "failed_count": result["failed_count"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "message": result["message"],
                    "errors": result["errors"]
                }
            )
    except Exception as e:
        logger.error(f"Sync endpoint error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


# ============================================================================
# CDC-BASED SMART SYNC ENDPOINTS
# ============================================================================

@router.post("/sync/process")
async def process_sync_events(
    background_tasks: BackgroundTasks,
    batch_size: int = Query(10, ge=1, le=100, description="Number of events to process"),
    db: AsyncSession = Depends(get_db)
):
    """
    Process pending sync events in background.
    
    This endpoint:
    1. Finds pending sync events in sync_events table
    2. Processes them in batch (generates embeddings, syncs to Milvus)
    3. Updates sync_status accordingly
    
    Uses background tasks for async processing.
    """
    sync_service = SyncService(db)
    
    # Check if there are pending events
    stats = await sync_service.get_sync_statistics()
    pending_count = stats.get("pending", 0)
    
    if pending_count == 0:
        return {
            "success": True,
            "message": "No pending events to process",
            "pending_count": 0
        }
    
    # Process events in background
    background_tasks.add_task(
        sync_service.process_pending_events,
        batch_size=batch_size
    )
    
    return {
        "success": True,
        "message": f"Processing {min(pending_count, batch_size)} pending events in background",
        "pending_count": pending_count,
        "batch_size": batch_size
    }


@router.get("/sync/statistics")
async def get_sync_statistics(db: AsyncSession = Depends(get_db)):
    """
    Get sync statistics.
    
    Returns:
        Statistics about sync events including pending, synced, failed counts
    """
    sync_service = SyncService(db)
    stats = await sync_service.get_sync_statistics()
    return stats


@router.get("/sync/status")
async def get_sync_status(db: AsyncSession = Depends(get_db)):
    """
    Get current sync status.
    
    Returns:
        Current status of sync system including pending events count
    """
    sync_service = SyncService(db)
    stats = await sync_service.get_sync_statistics()
    
    return {
        "status": "healthy" if stats["failed"] == 0 else "degraded",
        "pending_events": stats["pending"],
        "synced_events": stats["synced"],
        "failed_events": stats["failed"],
        "recent_failures": stats["recent_failures"][:5]  # Top 5 failures
    }
