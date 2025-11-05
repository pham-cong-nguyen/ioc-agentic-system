"""
Configuration settings for IOC Agentic System
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "IOC Agentic System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True  # Enable debug mode for development
    API_PREFIX: str = "/api/v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8862
    WORKERS: int = 4
    
    # Database
    DATABASE_URL: Optional[str] = None  # Can be set directly via env var
    POSTGRES_USER: str = "ioc_user"
    POSTGRES_PASSWORD: str = "ioc_password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "ioc_db"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # If DATABASE_URL not set, build from components
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # JWT Authentication
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    
    # Keycloak (Optional)
    KEYCLOAK_URL: Optional[str] = None
    KEYCLOAK_REALM: Optional[str] = None
    KEYCLOAK_CLIENT_ID: Optional[str] = None
    KEYCLOAK_CLIENT_SECRET: Optional[str] = None
    
    # LLM Configuration
    LLM_PROVIDER: str = "openai"  # gemini, openai, anthropic
    
    # Google Gemini
    GOOGLE_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-pro"
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # Anthropic
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    
    # Cache
    CACHE_TTL: int = 300  # 5 minutes
    CACHE_ENABLED: bool = True
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080,http://localhost:8862,http://127.0.0.1:8862"
    CORS_ALLOW_CREDENTIALS: bool = False
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]
    
    @property
    def cors_origins_list(self) -> list:
        """Convert comma-separated origins to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # IOC API Configuration (Example)
    IOC_API_BASE_URL: str = "https://ioc-api.gov.vn/api/v1"
    IOC_API_KEY: Optional[str] = None
    IOC_API_TIMEOUT: int = 30
    
    # Milvus Vector Database
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "function_embeddings"
    
    # RAG Configuration
    EMBEDDING_MODEL: str = "jinaai/jina-embeddings-v3"
    RAG_STAGE1_TOP_K: int = 50
    RAG_STAGE2_TOP_K: int = 5
    USE_GPU: bool = True  # Set to True to use GPU for embeddings
    
    # Character Streaming Configuration (Frontend)
    # These settings control the character-by-character streaming effect
    
    # Final Answer Streaming (slower, more dramatic)
    STREAM_CHARS_PER_FRAME: int = 3  # Number of characters to display per animation frame
    STREAM_MIN_DELAY_MS: int = 15  # Minimum delay between frames (milliseconds)
    STREAM_MAX_DELAY_MS: int = 35  # Maximum delay between frames (milliseconds)
    
    # Internal Steps Streaming (faster, less waiting)
    STREAM_INTERNAL_CHARS_PER_FRAME: int = 5  # Faster for thoughts/observations
    STREAM_INTERNAL_MIN_DELAY_MS: int = 5
    STREAM_INTERNAL_MAX_DELAY_MS: int = 15
    
    # For faster streaming (like ChatGPT):
    # STREAM_CHARS_PER_FRAME: int = 5
    # STREAM_MIN_DELAY_MS: int = 10
    # STREAM_MAX_DELAY_MS: int = 20
    
    # For slower, more dramatic streaming:
    # STREAM_CHARS_PER_FRAME: int = 2
    # STREAM_MIN_DELAY_MS: int = 25
    # STREAM_MAX_DELAY_MS: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
