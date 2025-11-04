"""
Function Registry API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from backend.registry.service import FunctionRegistryService
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
    status_code=status.HTTP_204_NO_CONTENT
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
    
    return None


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
