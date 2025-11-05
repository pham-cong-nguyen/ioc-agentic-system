"""
Pydantic schemas for Function Registry
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class HTTPMethod(str, Enum):
    """HTTP methods"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class Domain(str, Enum):
    """System domains"""
    ENERGY = "energy"
    TRAFFIC = "traffic"
    ENVIRONMENT = "environment"
    HEALTH = "health"
    SECURITY = "security"
    ANALYTICS = "analytics"


class ParameterSchema(BaseModel):
    """Parameter schema"""
    type: str = Field(..., description="Parameter type: string, number, boolean, date, array, object")
    required: bool = Field(default=False, description="Is parameter required")
    description: Optional[str] = Field(None, description="Parameter description")
    default: Optional[Any] = Field(None, description="Default value")
    enum: Optional[List[Any]] = Field(None, description="Allowed values")
    format: Optional[str] = Field(None, description="Format (e.g., date, email)")
    min_value: Optional[float] = Field(None, description="Minimum value")
    max_value: Optional[float] = Field(None, description="Maximum value")


class RateLimitConfig(BaseModel):
    """Rate limit configuration"""
    requests_per_minute: int = Field(60, description="Requests per minute")
    burst: int = Field(10, description="Burst capacity")


class FunctionMetadataBase(BaseModel):
    """Base function metadata"""
    function_id: str = Field(..., description="Unique function identifier")
    name: str = Field(..., description="Function name")
    description: Optional[str] = Field(None, description="Function description")
    domain: Domain = Field(..., description="Function domain")
    endpoint: str = Field(..., description="API endpoint URL")
    method: HTTPMethod = Field(..., description="HTTP method")
    auth_required: bool = Field(True, description="Authentication required")
    parameters: Dict[str, ParameterSchema] = Field(default_factory=dict, description="Parameters schema")
    response_schema: Optional[Dict[str, Any]] = Field(None, description="Response schema")
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig, description="Rate limit config")
    cache_ttl: int = Field(300, description="Cache TTL in seconds")
    timeout: int = Field(30, description="Request timeout in seconds")
    tags: List[str] = Field(default_factory=list, description="Tags for search")
    version: str = Field("1.0.0", description="Function version")


class FunctionMetadataCreate(FunctionMetadataBase):
    """Create function metadata"""
    created_by: Optional[str] = None


class FunctionMetadataUpdate(BaseModel):
    """Update function metadata"""
    name: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[Domain] = None
    endpoint: Optional[str] = None
    method: Optional[HTTPMethod] = None
    auth_required: Optional[bool] = None
    parameters: Optional[Dict[str, ParameterSchema]] = None
    response_schema: Optional[Dict[str, Any]] = None
    rate_limit: Optional[RateLimitConfig] = None
    cache_ttl: Optional[int] = None
    timeout: Optional[int] = None
    tags: Optional[List[str]] = None
    version: Optional[str] = None
    deprecated: Optional[bool] = None


class FunctionMetadataResponse(FunctionMetadataBase):
    """Function metadata response"""
    deprecated: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    last_called_at: Optional[datetime] = None
    call_count: int = 0
    success_rate: Optional[float] = None
    avg_response_time: Optional[float] = None
    
    class Config:
        from_attributes = True


class FunctionSearchQuery(BaseModel):
    """Function search query"""
    query: Optional[str] = Field(None, description="Search text")
    domain: Optional[Domain] = Field(None, description="Filter by domain")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    deprecated: Optional[bool] = Field(None, description="Filter by deprecated status")
    limit: int = Field(50, ge=1, le=100, description="Result limit")
    offset: int = Field(0, ge=0, description="Result offset")


class FunctionListResponse(BaseModel):
    """Function list response"""
    total: int = Field(..., description="Total count")
    items: List[FunctionMetadataResponse] = Field(..., description="Functions")
    limit: int
    offset: int


class FunctionCallLog(BaseModel):
    """Function call log"""
    function_id: str
    parameters: Dict[str, Any]
    response_code: int
    response_time: float  # milliseconds
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BulkImportRequest(BaseModel):
    """Bulk import functions request"""
    functions: List[FunctionMetadataCreate]
    overwrite: bool = Field(False, description="Overwrite existing functions")


class BulkImportResponse(BaseModel):
    """Bulk import response"""
    total: int
    successful: int
    failed: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)


class SyncResponse(BaseModel):
    """Sync functions to vector database response"""
    status: str = Field(..., description="Sync status: success, partial, failed")
    message: str = Field(..., description="Human-readable message")
    total_functions: int = Field(..., description="Total functions in PostgreSQL")
    synced_count: int = Field(..., description="Number of functions synced to Milvus")
    failed_count: int = Field(0, description="Number of functions that failed to sync")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Error details")
    duration_ms: float = Field(..., description="Sync duration in milliseconds")
