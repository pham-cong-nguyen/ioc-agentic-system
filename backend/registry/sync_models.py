"""
Sync Events Models - CDC (Change Data Capture) for PostgreSQL -> Milvus sync
"""
from sqlalchemy import Column, String, Enum, JSON, DateTime, Integer
from sqlalchemy.sql import func
import enum
from backend.utils.database import Base


class SyncStatus(str, enum.Enum):
    """Sync status enum - lowercase to match PostgreSQL ENUM"""
    PENDING = "pending"
    PROCESSING = "processing"
    SYNCED = "synced"
    FAILED = "failed"


class OperationType(str, enum.Enum):
    """Operation type enum - uppercase to match PostgreSQL ENUM"""
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class SyncEvent(Base):
    """
    Sync events table - logs all changes to entities that need to be synced to Milvus.
    
    This implements CDC (Change Data Capture) pattern:
    1. When function is created/updated/deleted, log event here
    2. Background worker processes pending events
    3. Updates sync_status after processing
    """
    __tablename__ = "sync_events"
    
    # Primary key
    event_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Entity information
    entity_type = Column(String(50), nullable=False, index=True)  # 'function', 'tool', etc.
    entity_id = Column(String(255), nullable=False, index=True)  # function_id, tool_id, etc.
    
    # Operation type
    operation = Column(
        Enum(OperationType, values_callable=lambda x: [e.value for e in x], name='operationtype', create_constraint=True, native_enum=True), 
        nullable=False
    )
    
    # Data snapshots (for audit trail)
    old_data = Column(JSON, nullable=True)  # Data before change (for UPDATE/DELETE)
    new_data = Column(JSON, nullable=True)  # Data after change (for INSERT/UPDATE)
    
    # Sync status
    sync_status = Column(
        Enum(SyncStatus, values_callable=lambda x: [e.value for e in x], name='syncstatus', create_constraint=True, native_enum=True), 
        nullable=False, 
        default=SyncStatus.PENDING,
        index=True
    )
    
    # Error tracking
    error_message = Column(String(1000), nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    synced_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<SyncEvent(id={self.event_id}, type={self.entity_type}, op={self.operation}, status={self.sync_status})>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "event_id": self.event_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "operation": self.operation.value if self.operation else None,
            "old_data": self.old_data,
            "new_data": self.new_data,
            "sync_status": self.sync_status.value if self.sync_status else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "synced_at": self.synced_at.isoformat() if self.synced_at else None
        }
