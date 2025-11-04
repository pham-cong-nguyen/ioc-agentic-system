# IOC Agentic System

An intelligent Operations Center system that allows users to query data using natural language (Vietnamese/English) and receive intelligent responses by automatically selecting and calling appropriate APIs.

## 🌟 Features

- **Natural Language Processing**: Query in Vietnamese or English
- **Intelligent Function Selection**: Automatically selects the right APIs using LLM
- **Multi-Source Data Integration**: Combines data from multiple API calls
- **Advanced Analytics**: Statistical analysis, trend detection, comparisons
- **Smart Response Generation**: Natural language responses with insights
- **Caching & Performance**: Redis caching for fast responses
- **Authentication & Authorization**: JWT-based auth with role-based access control
- **Admin Interface**: Manage API registry through web interface

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Chat UI      │  │ Admin Panel  │  │ Dashboard    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP/REST
┌───────────────────────────┼─────────────────────────────────┐
│                    Backend API Layer                         │
│  ┌──────────────────────────────────────────────────┐       │
│  │           FastAPI Application (main.py)          │       │
│  └──────────────────────────────────────────────────┘       │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────┐
│               Orchestration Layer (LangGraph)                │
│  ┌──────────────────────────────────────────────────┐       │
│  │  Query Parser → Function Selector → Executor     │       │
│  │       ↓              ↓                  ↓         │       │
│  │  Analyzer → Response Generator                   │       │
│  └──────────────────────────────────────────────────┘       │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────┐
│                     Service Layer                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Registry  │  │Executor  │  │Analyzer  │  │Auth      │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────┐
│                      Data Layer                              │
│  ┌──────────────┐          ┌──────────────┐                │
│  │ PostgreSQL   │          │    Redis     │                │
│  │   Database   │          │    Cache     │                │
│  └──────────────┘          └──────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)
- LLM API Key (Google Gemini, OpenAI, or Anthropic)

### Option 1: Docker Compose (Recommended)

1. **Clone the repository**
```bash
cd /home/ubuntu/nguyenpc2/2025/akaAPIs
```

2. **Create .env file**
```bash
cp .env.example .env
# Edit .env and add your API keys
nano .env
```

3. **Start services**
```bash
docker-compose up -d
```

4. **Initialize database**
```bash
docker-compose exec backend python scripts/init_db.py
```

5. **Access the application**
- API Docs: http://localhost:8862/api/v1/docs
- Frontend: http://localhost:80
- Health Check: http://localhost:8862/health

### Option 2: Local Development

1. **Install dependencies**
```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r backend/requirements.txt
```

2. **Start PostgreSQL and Redis**
```bash
# Using system services
sudo systemctl start postgresql
sudo systemctl start redis

# Or using Docker
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=ioc_password --name ioc-postgres postgres:15
docker run -d -p 6379:6379 --name ioc-redis redis:7-alpine
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

4. **Initialize database**
```bash
python scripts/init_db.py
```

5. **Run the application**
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8862
```

## 📖 API Usage

### Authentication

```bash
# Login
curl -X POST http://localhost:8862/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Response
{
  "access_token": "eyJ0eXAi...",
  "refresh_token": "eyJ0eXAi...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Query Processing

```bash
# Process a query
curl -X POST http://localhost:8862/api/v1/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Mức tiêu thụ điện hôm nay là bao nhiêu?",
    "language": "vi"
  }'

# Response
{
  "query_id": "q_user123_1699012800",
  "response": "Hôm nay mức tiêu thụ điện là 1,234 MWh...",
  "execution_plan": {...},
  "execution_results": [...],
  "insights": ["Peak usage at 2 PM", ...],
  "processing_time_ms": 1250.5
}
```

### API Registry Management

```bash
# Create a new API function
curl -X POST http://localhost:8862/api/v1/registry/functions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "function_id": "get_temperature",
    "name": "Get Temperature",
    "description": "Lấy dữ liệu nhiệt độ",
    "domain": "environment",
    "method": "GET",
    "endpoint": "https://api.example.com/temperature",
    "parameters": {
      "location": {"type": "string", "required": true}
    }
  }'

# Search functions
curl -X GET "http://localhost:8862/api/v1/registry/functions/search?query=temperature&domain=environment" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```env
# LLM Provider (gemini, openai, anthropic)
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_api_key_here

# Database
POSTGRES_PASSWORD=secure_password_here

# JWT Secret
JWT_SECRET_KEY=generate_strong_random_key_here

# IOC API
IOC_API_BASE_URL=https://ioc-api.gov.vn/api/v1
IOC_API_KEY=your_ioc_api_key
```

### LLM Provider Setup

**Google Gemini** (Recommended):
- Get API key: https://makersuite.google.com/app/apikey
- Set `LLM_PROVIDER=gemini` and `GOOGLE_API_KEY=your_key`

**OpenAI**:
- Get API key: https://platform.openai.com/api-keys
- Set `LLM_PROVIDER=openai` and `OPENAI_API_KEY=your_key`

**Anthropic**:
- Get API key: https://console.anthropic.com/
- Set `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY=your_key`

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/test_orchestrator.py
```

## 📁 Project Structure

```
akaAPIs/
├── backend/
│   ├── main.py                 # FastAPI application entry
│   ├── requirements.txt        # Python dependencies
│   ├── orchestrator/           # LangGraph orchestration
│   │   ├── graph.py           # State graph definition
│   │   ├── llm_service.py     # LLM operations
│   │   ├── routes.py          # Query endpoints
│   │   └── state.py           # State definitions
│   ├── registry/               # Function registry
│   │   ├── models.py          # Database models
│   │   ├── schemas.py         # Pydantic schemas
│   │   ├── service.py         # Business logic
│   │   └── routes.py          # API routes
│   ├── executor/               # API executor
│   │   └── service.py         # API call execution
│   ├── analyzer/               # Data analyzer
│   │   └── service.py         # Data analysis
│   ├── auth/                   # Authentication
│   │   ├── service.py         # Auth logic
│   │   └── routes.py          # Auth endpoints
│   └── utils/                  # Utilities
│       ├── database.py        # Database connection
│       └── cache.py           # Redis cache
├── config/
│   └── settings.py            # Configuration
├── scripts/
│   └── init_db.py             # Database initialization
├── tests/                      # Test suite
├── documents/
│   └── agentic_architecture.md # Technical documentation
├── docker-compose.yml          # Docker compose config
├── Dockerfile                  # Docker image
├── .env.example               # Environment template
└── README.md                  # This file
```

## 🎯 Example Queries

**Vietnamese:**
- "Mức tiêu thụ điện hôm nay là bao nhiêu?"
- "So sánh lưu lượng giao thông tuần này với tuần trước"
- "Chất lượng không khí ở Hà Nội như thế nào?"
- "Phân tích xu hướng tiêu thụ năng lượng trong tháng qua"

**English:**
- "What's the power consumption today?"
- "Compare this week's traffic with last week"
- "How's the air quality in Hanoi?"
- "Analyze energy consumption trend for the past month"

## 📊 Monitoring

- **Health Check**: `GET /health`
- **System Status**: `GET /api/v1/status`
- **Metrics**: Prometheus metrics at `/metrics` (if enabled)

## 🔒 Security

- JWT-based authentication
- Role-based access control (RBAC)
- API rate limiting
- CORS configuration
- Password hashing with bcrypt
- Optional Keycloak integration

## 🚧 Development

### Adding New API Functions

1. Use admin interface at `/index.html#config`
2. Or use API:
```python
POST /api/v1/registry/functions
```

### Customizing LLM Prompts

Edit prompts in `backend/orchestrator/llm_service.py`

### Adding New Analysis Types

Extend `backend/analyzer/service.py` with new analysis methods

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

## 📧 Support

For issues and questions:
- GitHub Issues: [Create an issue]
- Email: support@example.com

## 🙏 Acknowledgments

- LangChain & LangGraph for orchestration framework
- FastAPI for web framework
- Google Gemini for LLM capabilities
