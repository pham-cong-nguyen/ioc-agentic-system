"""
Database models for Function Registry
"""
from sqlalchemy import Column, String, Integer, Boolean, JSON, DateTime, Float, ARRAY, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class FunctionRegistry(Base):
    """Function metadata registry table"""
    
    __tablename__ = "function_registry"
    
    # Primary Key
    function_id = Column(String(100), primary_key=True, index=True)
    
    # Basic Info
    name = Column(String(255), nullable=False)
    description = Column(Text)
    domain = Column(String(50), index=True)
    
    # API Details
    endpoint = Column(String(500), nullable=False)
    method = Column(String(10), nullable=False)  # GET, POST, PUT, DELETE
    auth_required = Column(Boolean, default=True)
    
    # Schema
    parameters = Column(JSON)  # Parameter schema
    response_schema = Column(JSON)  # Response schema
    
    # Performance & Limits
    rate_limit = Column(JSON)  # Rate limit configuration
    cache_ttl = Column(Integer, default=300)  # Cache TTL in seconds
    timeout = Column(Integer, default=30)  # Request timeout
    
    # Metadata
    tags = Column(ARRAY(String))  # Tags for search
    version = Column(String(20), default="1.0.0")
    deprecated = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Usage Stats
    created_by = Column(String(100))
    last_called_at = Column(DateTime(timezone=True))
    call_count = Column(Integer, default=0)
    success_rate = Column(Float)  # Percentage
    avg_response_time = Column(Float)  # Milliseconds
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "function_id": self.function_id,
            "name": self.name,
            "description": self.description,
            "domain": self.domain,
            "endpoint": self.endpoint,
            "method": self.method,
            "auth_required": self.auth_required,
            "parameters": self.parameters,
            "response_schema": self.response_schema,
            "rate_limit": self.rate_limit,
            "cache_ttl": self.cache_ttl,
            "timeout": self.timeout,
            "tags": self.tags,
            "version": self.version,
            "deprecated": self.deprecated,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "last_called_at": self.last_called_at.isoformat() if self.last_called_at else None,
            "call_count": self.call_count,
            "success_rate": self.success_rate,
            "avg_response_time": self.avg_response_time
        }


class ConversationHistory(Base):
    """Conversation history table"""
    
    __tablename__ = "conversation_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), index=True, nullable=False)
    user_id = Column(String(100), index=True)
    
    # Message
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # Metadata
    function_calls = Column(JSON)  # Functions called in this turn
    tokens_used = Column(Integer)
    execution_time = Column(Float)  # Seconds
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "role": self.role,
            "content": self.content,
            "function_calls": self.function_calls,
            "tokens_used": self.tokens_used,
            "execution_time": self.execution_time,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class AuditLog(Base):
    """Audit log table"""
    
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # User Info
    user_id = Column(String(100), index=True)
    organization = Column(String(100))
    
    # Action
    action = Column(String(50), nullable=False)  # api_call, query, config_change
    function_id = Column(String(100), index=True)
    parameters = Column(JSON)
    
    # Response
    response_code = Column(Integer)
    response_size = Column(Integer)  # Bytes
    execution_time = Column(Float)  # Seconds
    
    # Request Info
    ip_address = Column(String(50))
    user_agent = Column(String(255))
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "organization": self.organization,
            "action": self.action,
            "function_id": self.function_id,
            "parameters": self.parameters,
            "response_code": self.response_code,
            "response_size": self.response_size,
            "execution_time": self.execution_time,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
