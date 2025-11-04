"""
Function Registry Service - CRUD operations
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from datetime import datetime
import logging

from backend.registry.models import FunctionRegistry
from backend.registry.schemas import (
    FunctionMetadataCreate,
    FunctionMetadataUpdate,
    FunctionSearchQuery
)
from backend.utils.cache import cache

logger = logging.getLogger(__name__)


class FunctionRegistryService:
    """Service for managing function registry"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_function(
        self, 
        function_data: FunctionMetadataCreate
    ) -> FunctionRegistry:
        """Create a new function"""
        # Check if function already exists
        existing = await self.get_function(function_data.function_id)
        if existing:
            raise ValueError(f"Function {function_data.function_id} already exists")
        
        # Create function
        db_function = FunctionRegistry(
            **function_data.model_dump()
        )
        
        self.db.add(db_function)
        await self.db.commit()
        await self.db.refresh(db_function)
        
        # Invalidate cache
        await cache.delete(f"function:{function_data.function_id}")
        await cache.delete("functions:all")
        
        logger.info(f"Created function: {function_data.function_id}")
        return db_function
    
    async def get_function(
        self, 
        function_id: str,
        use_cache: bool = True
    ) -> Optional[FunctionRegistry]:
        """Get function by ID"""
        # Try cache first
        if use_cache:
            cached = await cache.get(f"function:{function_id}")
            if cached:
                return FunctionRegistry(**cached)
        
        # Query database
        result = await self.db.execute(
            select(FunctionRegistry).where(
                FunctionRegistry.function_id == function_id
            )
        )
        function = result.scalar_one_or_none()
        
        # Cache result
        if function and use_cache:
            await cache.set(
                f"function:{function_id}",
                function.to_dict(),
                ttl=600
            )
        
        return function
    
    async def update_function(
        self,
        function_id: str,
        update_data: FunctionMetadataUpdate
    ) -> Optional[FunctionRegistry]:
        """Update function"""
        function = await self.get_function(function_id, use_cache=False)
        if not function:
            return None
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(function, field, value)
        
        function.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(function)
        
        # Invalidate cache
        await cache.delete(f"function:{function_id}")
        await cache.delete("functions:all")
        
        logger.info(f"Updated function: {function_id}")
        return function
    
    async def delete_function(self, function_id: str) -> bool:
        """Delete function"""
        function = await self.get_function(function_id, use_cache=False)
        if not function:
            return False
        
        await self.db.delete(function)
        await self.db.commit()
        
        # Invalidate cache
        await cache.delete(f"function:{function_id}")
        await cache.delete("functions:all")
        
        logger.info(f"Deleted function: {function_id}")
        return True
    
    async def list_functions(
        self,
        domain: Optional[str] = None,
        tags: Optional[List[str]] = None,
        deprecated: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[FunctionRegistry], int]:
        """List functions with filters"""
        # Build query
        query = select(FunctionRegistry)
        
        # Apply filters
        conditions = []
        if domain:
            conditions.append(FunctionRegistry.domain == domain)
        if deprecated is not None:
            conditions.append(FunctionRegistry.deprecated == deprecated)
        if tags:
            conditions.append(FunctionRegistry.tags.overlap(tags))
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        query = query.order_by(FunctionRegistry.created_at.desc())
        
        # Execute query
        result = await self.db.execute(query)
        functions = result.scalars().all()
        
        return list(functions), total
    
    async def search_functions(
        self,
        search_query: FunctionSearchQuery
    ) -> tuple[List[FunctionRegistry], int]:
        """Search functions by text query"""
        query = select(FunctionRegistry)
        
        # Text search
        if search_query.query:
            search_term = f"%{search_query.query.lower()}%"
            query = query.where(
                or_(
                    FunctionRegistry.name.ilike(search_term),
                    FunctionRegistry.description.ilike(search_term),
                    FunctionRegistry.function_id.ilike(search_term)
                )
            )
        
        # Domain filter
        if search_query.domain:
            query = query.where(FunctionRegistry.domain == search_query.domain)
        
        # Tags filter
        if search_query.tags:
            query = query.where(FunctionRegistry.tags.overlap(search_query.tags))
        
        # Deprecated filter
        if search_query.deprecated is not None:
            query = query.where(FunctionRegistry.deprecated == search_query.deprecated)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        query = query.offset(search_query.offset).limit(search_query.limit)
        query = query.order_by(FunctionRegistry.call_count.desc())
        
        # Execute query
        result = await self.db.execute(query)
        functions = result.scalars().all()
        
        return list(functions), total
    
    async def get_functions_by_domain(
        self, 
        domain: str
    ) -> List[FunctionRegistry]:
        """Get all functions in a domain"""
        result = await self.db.execute(
            select(FunctionRegistry).where(
                and_(
                    FunctionRegistry.domain == domain,
                    FunctionRegistry.deprecated == False
                )
            )
        )
        return list(result.scalars().all())
    
    async def update_usage_stats(
        self,
        function_id: str,
        response_time: float,
        success: bool
    ):
        """Update function usage statistics"""
        function = await self.get_function(function_id, use_cache=False)
        if not function:
            return
        
        # Update call count
        function.call_count = (function.call_count or 0) + 1
        function.last_called_at = datetime.utcnow()
        
        # Update average response time
        if function.avg_response_time is None:
            function.avg_response_time = response_time
        else:
            # Moving average
            function.avg_response_time = (
                (function.avg_response_time * (function.call_count - 1) + response_time) 
                / function.call_count
            )
        
        # Update success rate
        if function.success_rate is None:
            function.success_rate = 100.0 if success else 0.0
        else:
            total_calls = function.call_count
            successful_calls = (function.success_rate / 100.0) * (total_calls - 1)
            if success:
                successful_calls += 1
            function.success_rate = (successful_calls / total_calls) * 100.0
        
        await self.db.commit()
        
        # Invalidate cache
        await cache.delete(f"function:{function_id}")
    
    async def bulk_import(
        self,
        functions: List[FunctionMetadataCreate],
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """Bulk import functions"""
        results = {
            "total": len(functions),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for func_data in functions:
            try:
                existing = await self.get_function(func_data.function_id)
                
                if existing and not overwrite:
                    results["errors"].append({
                        "function_id": func_data.function_id,
                        "error": "Function already exists"
                    })
                    results["failed"] += 1
                    continue
                
                if existing and overwrite:
                    # Update existing
                    update_data = FunctionMetadataUpdate(**func_data.model_dump())
                    await self.update_function(func_data.function_id, update_data)
                else:
                    # Create new
                    await self.create_function(func_data)
                
                results["successful"] += 1
                
            except Exception as e:
                logger.error(f"Failed to import function {func_data.function_id}: {e}")
                results["errors"].append({
                    "function_id": func_data.function_id,
                    "error": str(e)
                })
                results["failed"] += 1
        
        return results
    
    async def get_domains(self) -> List[str]:
        """Get all unique domains"""
        result = await self.db.execute(
            select(FunctionRegistry.domain).distinct()
        )
        return [row[0] for row in result.all()]
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics"""
        # Total functions
        total_result = await self.db.execute(
            select(func.count()).select_from(FunctionRegistry)
        )
        total = total_result.scalar()
        
        # Active functions
        active_result = await self.db.execute(
            select(func.count()).select_from(FunctionRegistry).where(
                FunctionRegistry.deprecated == False
            )
        )
        active = active_result.scalar()
        
        # By domain
        domain_result = await self.db.execute(
            select(
                FunctionRegistry.domain,
                func.count()
            ).group_by(FunctionRegistry.domain)
        )
        by_domain = {row[0]: row[1] for row in domain_result.all()}
        
        # Most called
        most_called_result = await self.db.execute(
            select(FunctionRegistry).order_by(
                FunctionRegistry.call_count.desc()
            ).limit(10)
        )
        most_called = [f.to_dict() for f in most_called_result.scalars().all()]
        
        return {
            "total_functions": total,
            "active_functions": active,
            "deprecated_functions": total - active,
            "by_domain": by_domain,
            "most_called": most_called
        }
