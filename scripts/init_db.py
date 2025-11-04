"""
Database initialization script
Run this script to create initial tables
"""
import asyncio
import logging
from sqlalchemy import text

from backend.utils.database import engine, Base
from backend.registry.models import FunctionRegistry, ConversationHistory, AuditLog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_database():
    """Initialize database tables"""
    logger.info("Initializing database...")
    
    try:
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
            
            # Create indexes for better performance
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_function_domain 
                ON function_registry(domain);
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_function_search 
                ON function_registry USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_conversation_user 
                ON conversation_history(user_id, created_at DESC);
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp 
                ON audit_log(timestamp DESC);
            """))
            
            logger.info("Database indexes created successfully")
    
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


async def seed_sample_data():
    """Seed sample API functions for testing"""
    from backend.registry.service import FunctionRegistryService
    from backend.registry.schemas import FunctionMetadataCreate
    
    logger.info("Seeding sample data...")
    
    service = FunctionRegistryService()
    
    sample_functions = [
        {
            "function_id": "get_power_consumption",
            "name": "Get Power Consumption",
            "description": "Lấy dữ liệu tiêu thụ điện năng theo thời gian",
            "domain": "energy",
            "method": "GET",
            "endpoint": "https://ioc-api.gov.vn/api/v1/energy/consumption",
            "parameters": {
                "start_date": {"type": "string", "required": True, "format": "date"},
                "end_date": {"type": "string", "required": True, "format": "date"},
                "location": {"type": "string", "required": False}
            },
            "response_schema": {
                "type": "object",
                "properties": {
                    "data": {"type": "array"},
                    "total": {"type": "number"},
                    "unit": {"type": "string"}
                }
            }
        },
        {
            "function_id": "get_traffic_flow",
            "name": "Get Traffic Flow",
            "description": "Lấy dữ liệu lưu lượng giao thông theo khu vực",
            "domain": "traffic",
            "method": "GET",
            "endpoint": "https://ioc-api.gov.vn/api/v1/traffic/flow",
            "parameters": {
                "location": {"type": "string", "required": True},
                "start_time": {"type": "string", "required": True, "format": "datetime"},
                "end_time": {"type": "string", "required": True, "format": "datetime"}
            },
            "response_schema": {
                "type": "object",
                "properties": {
                    "vehicles": {"type": "number"},
                    "congestion_level": {"type": "string"}
                }
            }
        },
        {
            "function_id": "get_air_quality",
            "name": "Get Air Quality",
            "description": "Lấy dữ liệu chất lượng không khí",
            "domain": "environment",
            "method": "GET",
            "endpoint": "https://ioc-api.gov.vn/api/v1/environment/air-quality",
            "parameters": {
                "location": {"type": "string", "required": True},
                "date": {"type": "string", "required": False, "format": "date"}
            },
            "response_schema": {
                "type": "object",
                "properties": {
                    "aqi": {"type": "number"},
                    "pm25": {"type": "number"},
                    "pm10": {"type": "number"}
                }
            }
        }
    ]
    
    try:
        for func_data in sample_functions:
            func = FunctionMetadataCreate(**func_data)
            await service.create_function(func)
            logger.info(f"Created sample function: {func.function_id}")
        
        logger.info("Sample data seeded successfully")
    
    except Exception as e:
        logger.error(f"Error seeding sample data: {e}")


async def main():
    """Main initialization"""
    await init_database()
    await seed_sample_data()
    logger.info("Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(main())
