"""
Sync Service - CDC (Change Data Capture) implementation
Handles syncing PostgreSQL changes to Milvus vector database
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from backend.registry.sync_models import SyncEvent, SyncStatus, OperationType

logger = logging.getLogger(__name__)


class SyncService:
    """Service for managing sync events and processing them"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._embedder = None
        self._vector_store = None
        self._retriever = None
    
    def _init_rag_components(self):
        """Lazy initialization of RAG components (heavy dependencies)"""
        if self._retriever is not None:
            return
        
        try:
            from backend.registry.embeddings.sentence_transformer_embedder import SentenceTransformerEmbedder
            from backend.registry.embeddings.milvus_store import MilvusStore
            from backend.registry.embeddings.rag_retriever import RAGRetriever
            
            logger.info("Initializing RAG components...")
            
            self._embedder = SentenceTransformerEmbedder(
                model_name="jinaai/jina-embeddings-v3",
                device="cuda:0" if os.getenv("USE_GPU", "false").lower() == "true" else "cpu"
            )
            
            self._vector_store = MilvusStore(
                host=os.getenv("MILVUS_HOST", "localhost"),
                port=int(os.getenv("MILVUS_PORT", "19530")),
                collection_name=os.getenv("MILVUS_COLLECTION", "function_embeddings"),
                dimension=self._embedder.dimension
            )
            
            self._retriever = RAGRetriever(
                embedder=self._embedder,
                vector_store=self._vector_store
            )
            
            logger.info("RAG components initialized successfully")
            
        except ImportError as e:
            logger.error(f"Failed to import RAG components: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize RAG components: {e}")
            raise
    
    async def log_event(
        self,
        entity_type: str,
        entity_id: str,
        operation: OperationType,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None
    ) -> SyncEvent:
        """Log a sync event (application-level CDC)"""
        event = SyncEvent(
            entity_type=entity_type,
            entity_id=entity_id,
            operation=operation,
            old_data=old_data,
            new_data=new_data,
            sync_status=SyncStatus.PENDING
        )
        
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        
        logger.info(f"Logged sync event: {operation.value} {entity_type} {entity_id}")
        return event
    
    async def get_pending_events(
        self,
        limit: int = 100,
        entity_type: Optional[str] = None
    ) -> List[SyncEvent]:
        """Get pending sync events"""
        query = select(SyncEvent).where(
            or_(
                SyncEvent.sync_status == SyncStatus.PENDING,
                and_(
                    SyncEvent.sync_status == SyncStatus.FAILED,
                    SyncEvent.retry_count < SyncEvent.max_retries
                )
            )
        )
        
        if entity_type:
            query = query.where(SyncEvent.entity_type == entity_type)
        
        query = query.order_by(SyncEvent.created_at).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_sync_statistics(self) -> Dict[str, Any]:
        """Get sync statistics"""
        from sqlalchemy import func
        
        total_result = await self.db.execute(
            select(func.count()).select_from(SyncEvent)
        )
        total = total_result.scalar() or 0
        
        status_result = await self.db.execute(
            select(
                SyncEvent.sync_status,
                func.count()
            ).group_by(SyncEvent.sync_status)
        )
        by_status = {row[0].value: row[1] for row in status_result.all()}
        
        failed_result = await self.db.execute(
            select(SyncEvent)
            .where(SyncEvent.sync_status == SyncStatus.FAILED.value)
            .order_by(SyncEvent.created_at.desc())
            .limit(10)
        )
        failed_events = [event.to_dict() for event in failed_result.scalars().all()]
        
        return {
            "total_events": total,
            "by_status": by_status,
            "pending": by_status.get("pending", 0),
            "synced": by_status.get("synced", 0),
            "failed": by_status.get("failed", 0),
            "recent_failures": failed_events
        }
    
    async def process_event(self, event: SyncEvent) -> bool:
        """Process a single sync event"""
        try:
            event.sync_status = SyncStatus.PROCESSING
            event.processed_at = datetime.utcnow()
            await self.db.commit()
            
            self._init_rag_components()
            
            if event.operation == OperationType.INSERT:
                await self._process_insert(event)
            elif event.operation == OperationType.UPDATE:
                await self._process_update(event)
            elif event.operation == OperationType.DELETE:
                await self._process_delete(event)
            
            event.sync_status = SyncStatus.SYNCED
            event.synced_at = datetime.utcnow()
            event.error_message = None
            await self.db.commit()
            
            logger.info(f"Successfully processed event {event.event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process event {event.event_id}: {e}", exc_info=True)
            event.sync_status = SyncStatus.FAILED
            event.error_message = str(e)[:1000]
            event.retry_count += 1
            await self.db.commit()
            return False
    
    async def _process_insert(self, event: SyncEvent):
        """Process INSERT event"""
        if event.entity_type != "function":
            return
        
        data = event.new_data
        if not data:
            raise ValueError("No data to insert")
        
        func_dict = self._convert_to_rag_format(data)
        self._retriever.index_function(func_dict)
    
    async def _process_update(self, event: SyncEvent):
        """Process UPDATE event"""
        if event.entity_type != "function":
            return
        
        data = event.new_data
        if not data:
            raise ValueError("No data to update")
        
        func_dict = self._convert_to_rag_format(data)
        
        try:
            self._retriever.delete_function(event.entity_id)
        except:
            pass
        
        self._retriever.index_function(func_dict)
    
    async def _process_delete(self, event: SyncEvent):
        """Process DELETE event"""
        if event.entity_type != "function":
            return
        
        try:
            self._retriever.delete_function(event.entity_id)
        except Exception as e:
            logger.warning(f"Failed to delete {event.entity_id}: {e}")
    
    def _convert_to_rag_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert function data to RAG format"""
        domain_value = data.get("domain")
        if isinstance(domain_value, dict):
            domain_value = domain_value.get("value", "general")
        elif domain_value is None:
            domain_value = "general"
        
        return {
            "id": data.get("function_id"),
            "name": data.get("name", ""),
            "description": data.get("description", ""),
            "category": domain_value,
            "endpoint": data.get("endpoint", ""),
            "method": data.get("method", "GET"),
            "parameters": data.get("parameters", {}),
            "tags": data.get("tags", []),
            "auth_required": data.get("auth_required", False)
        }
    
    async def process_pending_events(
        self,
        batch_size: int = 10,
        entity_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process pending sync events in batch"""
        logger.info(f"Processing pending events (batch={batch_size})...")
        
        result = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            events = await self.get_pending_events(limit=batch_size, entity_type=entity_type)
            
            if not events:
                return result
            
            result["total_processed"] = len(events)
            
            for event in events:
                success = await self.process_event(event)
                
                if success:
                    result["successful"] += 1
                else:
                    result["failed"] += 1
                    result["errors"].append({
                        "event_id": event.event_id,
                        "entity_id": event.entity_id,
                        "error": event.error_message
                    })
            
            logger.info(f"Processed {result['successful']}/{result['total_processed']} successfully")
            
        except Exception as e:
            logger.error(f"Error processing events: {e}", exc_info=True)
            result["errors"].append({"error": str(e)})
        
        return result
