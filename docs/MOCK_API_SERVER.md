# 🎭 Mock API Server

Mock implementation của các functions đã được seeding vào database, sử dụng để test ReAct Agent mà không cần dependencies thật.

## 📦 Features

- ✅ **Realistic mock data** - Dữ liệu giả lập gần với thực tế
- ✅ **All seeded functions** - Hỗ trợ tất cả functions trong database
- ✅ **FastAPI** - Modern, fast, auto-docs
- ✅ **Flexible endpoints** - GET/POST support
- ✅ **Generic handler** - `/api/{function_name}` cho bất kỳ function nào

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install fastapi uvicorn httpx rich
```

### 2. Start Mock Server

```bash
python scripts/seed_api.py
```

Server sẽ chạy tại: **http://localhost:8155**

### 3. Test Mock Server

```bash
# Terminal khác
python scripts/test_seed_api.py
```

### 4. View API Documentation

Mở browser: **http://localhost:8155/docs**

## 📡 API Endpoints

### Health Check
```bash
GET /health
```

### Energy Endpoints

#### 1. Energy Consumption
```bash
POST /energy/consumption
Content-Type: application/json

{
  "region": "North",        # North, South, Central
  "period": "today",        # today, yesterday, this_week
  "metric": "total_energy"  # total_energy, power_output, load_demand
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "region": "North",
    "period": "today",
    "consumption_mw": 12456.78,
    "peak_load_mw": 14948.14,
    "renewable_percentage": 25.34,
    "grid_frequency_hz": 50.02,
    "status": "normal"
  }
}
```

#### 2. Energy Comparison
```bash
POST /energy/comparison
Content-Type: application/json

{
  "regions": ["North", "South", "Central"],
  "metric": "total_energy",
  "period": "today"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "metric": "total_energy",
    "regions": {
      "North": {
        "consumption_mw": 12456.78,
        "renewable_percentage": 25.34
      },
      "South": {
        "consumption_mw": 15234.56,
        "renewable_percentage": 28.91
      }
    },
    "summary": {
      "total_consumption_mw": 27691.34,
      "average_renewable_percentage": 27.13
    }
  }
}
```

#### 3. Energy Trend
```bash
POST /energy/trend
Content-Type: application/json

{
  "region": "North",
  "days": 7
}
```

### Financial Endpoints

#### 1. Budget Information
```bash
POST /financial/budget
Content-Type: application/json

{
  "period": "this_month"  # today, this_week, this_month, this_year
}
```

#### 2. Revenue Information
```bash
POST /financial/revenue
Content-Type: application/json

{
  "period": "this_month"
}
```

### IOC Endpoints

#### 1. System Status
```bash
POST /ioc/status
```

#### 2. Thu NSNN (State Budget Collection)
```bash
POST /ioc/thu_nsnn
Content-Type: application/json

{
  "region": "North",
  "period": "today"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "region": "North",
    "period": "today",
    "energy_metrics": {
      "consumption_mw": 12456.78,
      "renewable_percentage": 25.34
    },
    "financial_metrics": {
      "revenue_billion_vnd": 345.67,
      "budget_execution_rate": 89.23
    },
    "thu_nsnn": {
      "total_collection_billion_vnd": 69.13,
      "tax_revenue_billion_vnd": 51.85,
      "other_revenue_billion_vnd": 17.28
    }
  }
}
```

### Generic Endpoint

Endpoint này có thể handle **bất kỳ function nào**:

```bash
POST /api/{function_name}
Content-Type: application/json

{
  "param1": "value1",
  "param2": "value2"
}
```

## 🧪 Testing with cURL

```bash
# Test health
curl http://localhost:8155/health

# Test energy consumption
curl -X POST http://localhost:8155/energy/consumption \
  -H "Content-Type: application/json" \
  -d '{"region": "North", "period": "today"}'

# Test comparison
curl -X POST http://localhost:8155/energy/comparison \
  -H "Content-Type: application/json" \
  -d '{"regions": ["North", "South"], "metric": "total_energy"}'

# Test generic endpoint
curl -X POST http://localhost:8155/api/my_custom_function \
  -H "Content-Type: application/json" \
  -d '{"param1": "value1"}'
```

## 🔧 Integration với ReAct Agent

### 1. Update Function Registry

Khi seeding functions vào database, set `endpoint_url` trỏ tới mock server:

```python
# scripts/seed_functions.py
functions = [
    {
        "function_id": "energy_consumption_v1",
        "name": "get_energy_consumption",
        "endpoint_url": "http://localhost:8155/energy/consumption",  # Mock URL
        # ...
    }
]
```

### 2. Test với ReAct Agent V2

```python
# scripts/test_react_v2.py
import asyncio
from backend.orchestrator.react_agent_v2 import ReactAgentV2

async def test_with_mock_api():
    # Initialize agent với registry_service
    agent = ReactAgentV2(
        llm_service=llm_service,
        rag_retriever=rag_retriever,
        context_builder=context_builder,
        executor_service=executor_service,
        registry_service=registry_service,  # ✅ Now functions can execute!
        quality_threshold=0.7,
        max_iterations=3
    )
    
    # Test query
    result = await agent.run(
        user_id="test_user",
        query="Năng lượng miền Bắc hôm nay",
        conversation_id="test_conv_1"
    )
    
    print(result["final_answer"])

asyncio.run(test_with_mock_api())
```

## 📊 Mock Data Behavior

### Energy Data
- **North region**: Base ~12,000 MW ± 1,000 MW
- **South region**: Base ~15,000 MW ± 1,000 MW
- **Central region**: Base ~8,000 MW ± 1,000 MW
- **Renewable %**: 15-35% random
- **Grid frequency**: 49.9-50.1 Hz

### Financial Data
- **Revenue**: 100-500 billion VND
- **Expenses**: 80-400 billion VND
- **Profit**: 20-100 billion VND
- **Budget execution**: 85-95%

### Trend Data
- **Random variation** per day
- **Trend detection**: increasing/decreasing
- **Statistical summary**: avg, max, min

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8155
lsof -ti:8155 | xargs kill -9

# Or change port in seed_api.py
uvicorn.run(app, host="0.0.0.0", port=8156)  # Use different port
```

### Connection Refused
```bash
# Make sure server is running
python scripts/seed_api.py

# Check if server is up
curl http://localhost:8155/health
```

### Import Errors
```bash
# Install missing packages
pip install fastapi uvicorn httpx rich
```

## 📝 Extending Mock Server

### Add New Endpoint

```python
# In seed_api.py

@app.post("/your/new/endpoint")
async def your_new_function(request: Request):
    """Your function description."""
    try:
        params = await request.json()
        
        # Your logic here
        data = {
            "result": "your data"
        }
        
        return {
            "success": True,
            "data": data,
            "message": "Success message"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Add New Data Generator

```python
def generate_your_data(params) -> Dict[str, Any]:
    """Generate mock data for your use case."""
    return {
        "field1": "value1",
        "field2": random.randint(1, 100),
        "timestamp": datetime.now().isoformat()
    }
```

## 🎯 Use Cases

1. **Development**: Test agent without real APIs
2. **Testing**: Consistent, predictable data
3. **Demo**: Show capabilities without infrastructure
4. **CI/CD**: Automated testing in pipelines
5. **Debugging**: Isolate agent logic from API issues

## 🚀 Production Deployment

**⚠️ WARNING**: Đây là MOCK server, KHÔNG sử dụng trong production!

Trong production, thay thế bằng:
- Real API endpoints
- Database connections
- Authentication/Authorization
- Rate limiting
- Monitoring/Logging

## 📚 Related Files

- `seed_api.py` - Mock server implementation
- `test_seed_api.py` - Test suite
- `seed_functions.py` - Function seeding script
- `react_agent_v2.py` - Enhanced ReAct Agent

## 🤝 Contributing

Thêm endpoints mới cho functions của bạn theo template trên!

---

**Made with ❤️ for testing ReAct Agent V2**
