# 🧠 Kiến Trúc Hệ Thống Agentic IOC APIs

**Tài liệu kỹ thuật - Phiên bản 1.0**  
**Ngày cập nhật:** 03/11/2025  
**Tác giả:** Phạm Quang Nhật Minh – FPT IS R&D / Libra AI Platform

---

## 📋 Mục Lục

1. [Tổng Quan Hệ Thống](#1-tổng-quan-hệ-thống)
2. [Kiến Trúc Tổng Thể](#2-kiến-trúc-tổng-thể)
3. [Các Thành Phần Chính](#3-các-thành-phần-chính)
4. [Luồng Xử Lý Dữ Liệu](#4-luồng-xử-lý-dữ-liệu)
5. [Function Registry Service](#5-function-registry-service)
6. [Agentic Orchestration Layer](#6-agentic-orchestration-layer)
7. [Security & Authentication](#7-security--authentication)
8. [Scalability & Performance](#8-scalability--performance)
9. [Deployment Architecture](#9-deployment-architecture)
10. [Future Roadmap](#10-future-roadmap)

---

## 1. Tổng Quan Hệ Thống

### 1.1 Giới Thiệu

**Agentic IOC System** là nền tảng Intelligent Operations Center thế hệ mới, cho phép lãnh đạo cơ quan nhà nước và doanh nghiệp truy vấn dữ liệu bằng ngôn ngữ tự nhiên (tiếng Việt/Anh) và nhận được phân tích, tổng hợp thông tin từ hàng trăm nguồn API khác nhau.

### 1.2 Mục Tiêu

- ✅ **Intelligent Query Understanding**: Hiểu câu hỏi phức tạp bằng ngôn ngữ tự nhiên
- ✅ **Dynamic API Orchestration**: Tự động chọn và gọi đúng API từ hàng trăm/hàng nghìn functions
- ✅ **Multi-Domain Integration**: Tích hợp đa lĩnh vực (Năng lượng, Giao thông, Môi trường, Y tế, An ninh)
- ✅ **Real-time Analytics**: Phân tích, so sánh và tổng hợp dữ liệu thời gian thực
- ✅ **Visualization & Insights**: Trình bày kết quả trực quan với biểu đồ và xu hướng
- ✅ **Enterprise-grade Security**: Bảo mật, phân quyền và audit log đầy đủ

### 1.3 Use Cases

**Ví dụ Câu Hỏi Điển Hình:**

```
User: "Sản lượng điện miền Nam tuần này tăng bao nhiêu so với tuần trước?"
System: 
  → Gọi API: get_energy_kpi(region="South", period="current_week")
  → Gọi API: get_energy_kpi(region="South", period="last_week")
  → Phân tích: Tăng 8.3% (2,450 MW vs 2,260 MW)
  → Trả về: Báo cáo + Biểu đồ xu hướng
```

```
User: "Có mối liên hệ nào giữa lượng điện tăng và số vụ tai nạn giao thông không?"
System:
  → Gọi API: get_energy_consumption_trend()
  → Gọi API: get_traffic_incidents()
  → Phân tích: Correlation analysis
  → Trả về: Insight + Visualization
```

---

## 2. Kiến Trúc Tổng Thể

### 2.1 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                          │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │  Web Interface   │  │  Mobile App      │                    │
│  │  (React/Next.js) │  │  (React Native)  │                    │
│  └────────┬─────────┘  └────────┬─────────┘                    │
└───────────┼────────────────────┼──────────────────────────────┘
            │                    │
            └────────┬───────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│                   API GATEWAY LAYER                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FastAPI Gateway (Reverse Proxy + Load Balancer)        │  │
│  │  • Rate Limiting                                         │  │
│  │  • Request Validation                                    │  │
│  │  • Response Caching                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│              AGENTIC ORCHESTRATION LAYER                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  LangGraph Orchestrator (Core Engine)                   │  │
│  │  ┌────────────┐  ┌────────────┐  ┌──────────────┐      │  │
│  │  │  Planner   │→ │  Executor  │→ │ Summarizer   │      │  │
│  │  │  (LLM)     │  │  (API)     │  │ (Analytics)  │      │  │
│  │  └────────────┘  └────────────┘  └──────────────┘      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Function Registry Service (Dynamic API Metadata)       │  │
│  │  • API Discovery                                         │  │
│  │  • Schema Management                                     │  │
│  │  • Runtime Tool Generation                               │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│                   SUPPORT SERVICES LAYER                        │
│  ┌──────────┐  ┌─────────┐  ┌──────────┐  ┌───────────┐       │
│  │  Redis   │  │Keycloak │  │PostgreSQL│  │  MinIO    │       │
│  │  Cache   │  │  Auth   │  │  Audit   │  │  Storage  │       │
│  └──────────┘  └─────────┘  └──────────┘  └───────────┘       │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│                     DATA SOURCE LAYER                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ IOC APIs     │  │ Oracle APIs  │  │ External APIs│         │
│  │ (Energy,     │  │ (Dashboard,  │  │ (Weather,    │         │
│  │  Traffic,    │  │  Analytics)  │  │  Government) │         │
│  │  Environment)│  │              │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Layer Responsibilities

| Layer | Responsibilities | Technologies |
|-------|-----------------|--------------|
| **Presentation** | UI/UX, User Interaction | React, Next.js, HTML5 |
| **API Gateway** | Routing, Security, Load Balancing | FastAPI, Nginx |
| **Orchestration** | AI Logic, Query Planning, Execution | LangGraph, LangChain |
| **Support Services** | Cache, Auth, Storage, Logging | Redis, Keycloak, PostgreSQL |
| **Data Sources** | External APIs, Databases | IOC APIs, Oracle, REST APIs |

---

## 3. Các Thành Phần Chính

### 3.1 LangGraph Orchestrator

**Vai trò:** Core AI engine điều phối toàn bộ luồng xử lý

**Components:**

```python
# Graph Structure
from langgraph.graph import StateGraph

class AgenticIOCGraph:
    """
    State machine for IOC query processing
    """
    def __init__(self):
        self.graph = StateGraph()
        self._build_graph()
    
    def _build_graph(self):
        # Nodes
        self.graph.add_node("parse_query", self.parse_user_query)
        self.graph.add_node("plan_actions", self.plan_api_calls)
        self.graph.add_node("execute_apis", self.execute_functions)
        self.graph.add_node("analyze_data", self.analyze_results)
        self.graph.add_node("generate_response", self.generate_answer)
        
        # Edges (Flow)
        self.graph.add_edge("parse_query", "plan_actions")
        self.graph.add_edge("plan_actions", "execute_apis")
        self.graph.add_edge("execute_apis", "analyze_data")
        self.graph.add_edge("analyze_data", "generate_response")
        
        # Conditional edges
        self.graph.add_conditional_edges(
            "plan_actions",
            self.should_continue,
            {
                "continue": "execute_apis",
                "clarify": "parse_query"
            }
        )
```

**State Management:**

```python
class AgentState(TypedDict):
    """State object passed between nodes"""
    query: str                    # User's original query
    intent: Dict[str, Any]        # Parsed intent
    api_plan: List[APICall]       # Planned API calls
    api_results: Dict[str, Any]   # Raw API responses
    analysis: Dict[str, Any]      # Analyzed data
    response: str                 # Final response
    conversation_history: List    # Context
```

### 3.2 Function Registry Service

**Vai trò:** Quản lý metadata của tất cả API functions

**Schema:**

```json
{
  "function_id": "get_energy_kpi",
  "description": "Lấy KPI năng lượng theo vùng và thời gian",
  "domain": "energy",
  "endpoint": "https://ioc-api.gov.vn/api/v1/energy/kpi",
  "method": "GET",
  "auth_required": true,
  "parameters": {
    "region": {
      "type": "string",
      "required": true,
      "enum": ["North", "Central", "South"],
      "description": "Vùng địa lý"
    },
    "start_date": {
      "type": "date",
      "required": true,
      "format": "YYYY-MM-DD"
    },
    "end_date": {
      "type": "date",
      "required": true,
      "format": "YYYY-MM-DD"
    }
  },
  "response_schema": {
    "total_consumption": "number",
    "peak_load": "number",
    "avg_load": "number",
    "growth_rate": "percentage"
  },
  "rate_limit": {
    "requests_per_minute": 60,
    "burst": 10
  },
  "cache_ttl": 300,
  "tags": ["energy", "kpi", "consumption"]
}
```

**API:**

```python
class FunctionRegistryService:
    """Service to manage function registry"""
    
    async def get_all_functions(self) -> List[FunctionMetadata]:
        """Retrieve all registered functions"""
        pass
    
    async def search_functions(self, query: str, domain: str = None) -> List[FunctionMetadata]:
        """Search functions by keyword/domain"""
        pass
    
    async def register_function(self, metadata: FunctionMetadata) -> bool:
        """Register a new function"""
        pass
    
    async def update_function(self, function_id: str, metadata: FunctionMetadata) -> bool:
        """Update existing function"""
        pass
    
    async def delete_function(self, function_id: str) -> bool:
        """Delete function"""
        pass
    
    async def get_functions_by_domain(self, domain: str) -> List[FunctionMetadata]:
        """Get all functions in a domain"""
        pass
```

### 3.3 LLM Planner

**Vai trò:** Phân tích intent và lập kế hoạch gọi API

**Input:**
```python
{
  "query": "So sánh điện năng tiêu thụ giữa miền Bắc và miền Nam tuần này",
  "context": {
    "user_id": "admin@gov.vn",
    "organization": "Ministry of Industry",
    "permissions": ["energy.*", "analytics.*"]
  }
}
```

**Processing:**
```python
class LLMPlanner:
    """AI-powered query planner"""
    
    def __init__(self, llm_model: str = "gemini-pro"):
        self.llm = ChatGoogleGenerativeAI(model=llm_model)
        self.registry = FunctionRegistryService()
    
    async def plan(self, query: str, context: Dict) -> ExecutionPlan:
        """
        1. Parse query intent
        2. Identify required data domains
        3. Select appropriate functions
        4. Generate execution plan
        """
        
        # Step 1: Intent extraction
        intent = await self._extract_intent(query)
        
        # Step 2: Function selection
        candidate_functions = await self.registry.search_functions(
            query=query,
            domain=intent.get("domain")
        )
        
        # Step 3: LLM-based selection
        selected_functions = await self._llm_select_functions(
            query=query,
            candidates=candidate_functions,
            intent=intent
        )
        
        # Step 4: Plan generation
        plan = ExecutionPlan(
            functions=selected_functions,
            execution_order=self._determine_order(selected_functions),
            parameters=self._extract_parameters(query, selected_functions)
        )
        
        return plan
```

**Output:**
```json
{
  "execution_plan": {
    "steps": [
      {
        "step": 1,
        "function": "get_energy_kpi",
        "parameters": {
          "region": "North",
          "start_date": "2025-10-27",
          "end_date": "2025-11-02"
        }
      },
      {
        "step": 2,
        "function": "get_energy_kpi",
        "parameters": {
          "region": "South",
          "start_date": "2025-10-27",
          "end_date": "2025-11-02"
        }
      },
      {
        "step": 3,
        "function": "compare_data",
        "parameters": {
          "dataset_1": "{{step_1.result}}",
          "dataset_2": "{{step_2.result}}",
          "comparison_type": "percentage"
        }
      }
    ],
    "parallel_execution": [1, 2],
    "estimated_time": "2.5s"
  }
}
```

### 3.4 API Executor

**Vai trò:** Thực thi API calls theo plan

```python
class APIExecutor:
    """Execute API calls with retry, timeout, and error handling"""
    
    def __init__(self):
        self.session = aiohttp.ClientSession()
        self.cache = RedisCache()
        
    async def execute_plan(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """Execute all API calls in the plan"""
        results = {}
        
        for step in plan.steps:
            # Check cache
            cache_key = self._generate_cache_key(step)
            cached_result = await self.cache.get(cache_key)
            
            if cached_result:
                results[step.id] = cached_result
                continue
            
            # Execute API call
            try:
                result = await self._execute_single_call(step)
                results[step.id] = result
                
                # Cache result
                await self.cache.set(cache_key, result, ttl=step.cache_ttl)
                
            except APIError as e:
                # Handle error, retry logic
                results[step.id] = await self._handle_error(step, e)
        
        return results
    
    async def _execute_single_call(self, step: APICallStep) -> Any:
        """Execute a single API call"""
        async with self.session.request(
            method=step.method,
            url=step.endpoint,
            headers=self._build_headers(step),
            json=step.parameters,
            timeout=step.timeout
        ) as response:
            response.raise_for_status()
            return await response.json()
```

### 3.5 Data Analyzer & Summarizer

**Vai trò:** Phân tích dữ liệu và tạo insights

```python
class DataAnalyzer:
    """Analyze and summarize API results"""
    
    async def analyze(self, results: Dict[str, Any], query: str) -> AnalysisResult:
        """
        Analyze raw API results and generate insights
        """
        
        # Statistical analysis
        stats = self._calculate_statistics(results)
        
        # Trend detection
        trends = self._detect_trends(results)
        
        # Comparison analysis
        comparisons = self._perform_comparisons(results)
        
        # Generate insights with LLM
        insights = await self._generate_insights_llm(
            query=query,
            data=results,
            stats=stats,
            trends=trends
        )
        
        return AnalysisResult(
            statistics=stats,
            trends=trends,
            comparisons=comparisons,
            insights=insights,
            visualizations=self._suggest_visualizations(results)
        )
```

---

## 4. Luồng Xử Lý Dữ Liệu

### 4.1 End-to-End Flow

```
┌──────────────┐
│  User Query  │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────┐
│  1. QUERY PARSING                   │
│  • Language detection (vi/en)       │
│  • Intent extraction                │
│  • Entity recognition               │
│  • Context retrieval                │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  2. PLANNING                        │
│  • Function discovery               │
│  • Function selection (LLM)         │
│  • Parameter extraction             │
│  • Execution plan generation        │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  3. EXECUTION                       │
│  • Parallel API calls               │
│  • Authentication & authorization   │
│  • Cache management                 │
│  • Error handling & retry           │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  4. ANALYSIS                        │
│  • Data aggregation                 │
│  • Statistical analysis             │
│  • Trend detection                  │
│  • Comparative analysis             │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  5. RESPONSE GENERATION             │
│  • Natural language generation      │
│  • Visualization creation           │
│  • Insight summarization            │
│  • Response formatting              │
└──────┬──────────────────────────────┘
       │
       ▼
┌──────────────┐
│   Response   │
│  to User     │
└──────────────┘
```

### 4.2 Example: Complete Flow

**User Query:**
```
"Tuần này lượng điện miền Nam tăng bao nhiêu và có ảnh hưởng gì đến giao thông không?"
```

**Step 1: Parsing**
```json
{
  "language": "vi",
  "intent": "comparison_and_correlation",
  "entities": {
    "domain": ["energy", "traffic"],
    "region": "South",
    "time_period": "this_week",
    "metric": "electricity_consumption"
  },
  "question_type": "quantitative_and_causal"
}
```

**Step 2: Planning**
```json
{
  "plan": {
    "functions": [
      "get_energy_kpi",
      "get_energy_historical",
      "get_traffic_incidents",
      "correlation_analysis"
    ],
    "sequence": "parallel[1,2,3] -> sequential[4]"
  }
}
```

**Step 3: Execution**
```json
{
  "api_calls": [
    {
      "function": "get_energy_kpi",
      "params": {"region": "South", "period": "current_week"},
      "result": {"consumption": 2450, "unit": "MW"}
    },
    {
      "function": "get_energy_historical",
      "params": {"region": "South", "period": "last_week"},
      "result": {"consumption": 2260, "unit": "MW"}
    },
    {
      "function": "get_traffic_incidents",
      "params": {"region": "South", "period": "current_week"},
      "result": {"total_incidents": 45, "severity": "medium"}
    }
  ]
}
```

**Step 4: Analysis**
```json
{
  "analysis": {
    "energy_growth": {
      "absolute": 190,
      "percentage": 8.4,
      "trend": "increasing"
    },
    "correlation": {
      "coefficient": 0.23,
      "significance": "weak_positive",
      "interpretation": "Có tương quan yếu dương"
    }
  }
}
```

**Step 5: Response**
```
📊 Phân Tích Năng Lượng & Giao Thông Miền Nam

🔋 Năng lượng:
Tuần này: 2,450 MW (tăng 8.4% so với tuần trước)
• Tăng 190 MW so với tuần trước
• Xu hướng: Tăng mạnh do thời tiết nóng

🚦 Giao thông:
• 45 vụ tai nạn (mức độ trung bình)
• Giảm 12% so với tuần trước

🔗 Mối liên hệ:
Phân tích cho thấy có tương quan dương yếu (r=0.23) giữa 
lượng điện tiêu thụ và số vụ tai nạn. Điều này có thể do:
• Thời tiết nóng → tăng hoạt động → nhiều phương tiện
• Điều kiện thời tiết khắc nghiệt ảnh hưởng cả hai lĩnh vực

💡 Khuyến nghị:
• Tăng cường giám sát giao thông trong giờ cao điểm
• Khuyến khích tiết kiệm điện
```

---

## 5. Function Registry Service

### 5.1 Storage & Management

**Database Schema:**

```sql
CREATE TABLE function_registry (
    function_id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    domain VARCHAR(50),
    endpoint VARCHAR(500) NOT NULL,
    method VARCHAR(10) NOT NULL,
    auth_required BOOLEAN DEFAULT TRUE,
    parameters JSONB,
    response_schema JSONB,
    rate_limit JSONB,
    cache_ttl INTEGER DEFAULT 300,
    tags TEXT[],
    version VARCHAR(20),
    deprecated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),
    last_called_at TIMESTAMP,
    call_count INTEGER DEFAULT 0,
    success_rate FLOAT,
    avg_response_time FLOAT
);

CREATE INDEX idx_function_domain ON function_registry(domain);
CREATE INDEX idx_function_tags ON function_registry USING GIN(tags);
CREATE INDEX idx_function_name_search ON function_registry USING GIN(to_tsvector('english', name || ' ' || description));
```

### 5.2 Dynamic Tool Loading

**Runtime Tool Generation:**

```python
class DynamicToolLoader:
    """Load function registry and generate LangChain tools"""
    
    def __init__(self, registry_service: FunctionRegistryService):
        self.registry = registry_service
        self.tools = []
    
    async def load_tools(self, domain: str = None) -> List[Tool]:
        """Load all functions as LangChain tools"""
        functions = await self.registry.get_all_functions(domain=domain)
        
        for func in functions:
            tool = self._create_tool(func)
            self.tools.append(tool)
        
        return self.tools
    
    def _create_tool(self, func_metadata: FunctionMetadata) -> Tool:
        """Create a LangChain tool from function metadata"""
        
        @tool(func_metadata.name)
        async def dynamic_tool(**kwargs) -> Any:
            """
            {func_metadata.description}
            
            Parameters:
            {self._format_parameters(func_metadata.parameters)}
            """
            executor = APIExecutor()
            return await executor.execute_single_call(
                method=func_metadata.method,
                url=func_metadata.endpoint,
                params=kwargs
            )
        
        return dynamic_tool
```

### 5.3 Auto-Discovery from OpenAPI

```python
class OpenAPIDiscovery:
    """Auto-discover functions from OpenAPI specs"""
    
    async def discover_from_openapi(self, openapi_url: str) -> List[FunctionMetadata]:
        """
        Parse OpenAPI/Swagger spec and generate function metadata
        """
        spec = await self._fetch_openapi_spec(openapi_url)
        functions = []
        
        for path, methods in spec['paths'].items():
            for method, details in methods.items():
                func_metadata = FunctionMetadata(
                    function_id=self._generate_id(path, method),
                    name=details.get('operationId', path),
                    description=details.get('summary', ''),
                    endpoint=f"{spec['servers'][0]['url']}{path}",
                    method=method.upper(),
                    parameters=self._parse_parameters(details.get('parameters', [])),
                    response_schema=self._parse_response(details.get('responses', {}))
                )
                functions.append(func_metadata)
        
        return functions
```

---

## 6. Agentic Orchestration Layer

### 6.1 Multi-Agent Architecture

**Concept:** Mỗi domain có một agent chuyên biệt

```python
class DomainAgent:
    """Specialized agent for a specific domain"""
    
    def __init__(self, domain: str, llm: BaseChatModel):
        self.domain = domain
        self.llm = llm
        self.tools = self._load_domain_tools()
        self.memory = ConversationBufferMemory()
    
    async def process_query(self, query: str) -> AgentResponse:
        """Process domain-specific query"""
        pass

class MultiAgentOrchestrator:
    """Orchestrate multiple domain agents"""
    
    def __init__(self):
        self.agents = {
            "energy": DomainAgent("energy", llm),
            "traffic": DomainAgent("traffic", llm),
            "environment": DomainAgent("environment", llm),
            "health": DomainAgent("health", llm),
            "security": DomainAgent("security", llm)
        }
        self.coordinator = CoordinatorAgent(self.agents)
    
    async def route_query(self, query: str) -> Response:
        """Route query to appropriate agent(s)"""
        domains = await self.coordinator.identify_domains(query)
        
        if len(domains) == 1:
            # Single-domain query
            agent = self.agents[domains[0]]
            return await agent.process_query(query)
        else:
            # Multi-domain query - coordinate
            return await self.coordinator.coordinate(query, domains)
```

### 6.2 Memory & Context Management

```python
class ConversationMemory:
    """Manage conversation history and context"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
    
    async def save_turn(self, session_id: str, turn: ConversationTurn):
        """Save conversation turn"""
        key = f"conversation:{session_id}"
        await self.redis.lpush(key, turn.to_json())
        await self.redis.expire(key, 3600)  # 1 hour TTL
    
    async def get_history(self, session_id: str, n: int = 10) -> List[ConversationTurn]:
        """Retrieve last N conversation turns"""
        key = f"conversation:{session_id}"
        history = await self.redis.lrange(key, 0, n-1)
        return [ConversationTurn.from_json(h) for h in history]
    
    async def get_context_window(self, session_id: str) -> str:
        """Get formatted context for LLM"""
        history = await self.get_history(session_id)
        return self._format_context(history)
```

---

## 7. Security & Authentication

### 7.1 Authentication Flow

```
┌──────────┐
│  User    │
└────┬─────┘
     │ 1. Login
     ▼
┌─────────────────┐
│   Keycloak      │
│   (IAM)         │
└────┬────────────┘
     │ 2. JWT Token
     ▼
┌─────────────────┐
│  API Gateway    │
│  (Verify Token) │
└────┬────────────┘
     │ 3. Authorized Request
     ▼
┌─────────────────┐
│  Orchestrator   │
└─────────────────┘
```

### 7.2 Authorization & RBAC

```python
class PermissionManager:
    """Role-based access control"""
    
    def __init__(self):
        self.permissions = {
            "admin": ["*"],
            "analyst": ["energy.*", "traffic.*", "analytics.*"],
            "viewer": ["energy.read", "traffic.read"],
            "energy_manager": ["energy.*"],
            "traffic_manager": ["traffic.*"]
        }
    
    def check_permission(self, user_role: str, function_id: str) -> bool:
        """Check if user has permission to call function"""
        user_perms = self.permissions.get(user_role, [])
        
        # Check wildcard
        if "*" in user_perms:
            return True
        
        # Check exact match
        if function_id in user_perms:
            return True
        
        # Check pattern match (e.g., energy.*)
        domain = function_id.split('.')[0]
        if f"{domain}.*" in user_perms:
            return True
        
        return False
```

### 7.3 Audit Logging

```python
class AuditLogger:
    """Log all system activities for compliance"""
    
    async def log_api_call(self, event: AuditEvent):
        """Log API call event"""
        await self.db.execute("""
            INSERT INTO audit_log (
                timestamp, user_id, organization, 
                function_id, parameters, response_code,
                execution_time, ip_address, user_agent
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """, 
            event.timestamp, event.user_id, event.organization,
            event.function_id, json.dumps(event.parameters),
            event.response_code, event.execution_time,
            event.ip_address, event.user_agent
        )
```

---

## 8. Scalability & Performance

### 8.1 Horizontal Scaling

```yaml
# Kubernetes Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ioc-orchestrator
spec:
  replicas: 5  # Auto-scale based on load
  selector:
    matchLabels:
      app: ioc-orchestrator
  template:
    metadata:
      labels:
        app: ioc-orchestrator
    spec:
      containers:
      - name: orchestrator
        image: ioc-orchestrator:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ioc-orchestrator-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ioc-orchestrator
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 8.2 Caching Strategy

**Multi-Level Cache:**

```python
class CacheManager:
    """Multi-level caching strategy"""
    
    def __init__(self):
        self.l1_cache = {}  # In-memory (fast, small)
        self.l2_cache = RedisCache()  # Redis (medium, medium)
        self.l3_cache = DatabaseCache()  # DB (slow, large)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get from cache with fallback"""
        # L1: In-memory
        if key in self.l1_cache:
            return self.l1_cache[key]
        
        # L2: Redis
        value = await self.l2_cache.get(key)
        if value:
            self.l1_cache[key] = value  # Promote to L1
            return value
        
        # L3: Database
        value = await self.l3_cache.get(key)
        if value:
            await self.l2_cache.set(key, value)  # Promote to L2
            self.l1_cache[key] = value  # Promote to L1
            return value
        
        return None
```

### 8.3 Performance Optimization

**Parallel Execution:**

```python
async def execute_parallel_calls(api_calls: List[APICall]) -> Dict[str, Any]:
    """Execute multiple API calls in parallel"""
    tasks = [execute_single_call(call) for call in api_calls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return {
        call.id: result 
        for call, result in zip(api_calls, results)
        if not isinstance(result, Exception)
    }
```

**Connection Pooling:**

```python
# HTTP Client with connection pooling
connector = aiohttp.TCPConnector(
    limit=100,  # Total connections
    limit_per_host=30,  # Per host
    ttl_dns_cache=300
)
session = aiohttp.ClientSession(connector=connector)
```

---

## 9. Deployment Architecture

### 9.1 Container Architecture

```yaml
version: '3.8'

services:
  # API Gateway
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
  
  # Orchestrator Service
  orchestrator:
    build: ./orchestrator
    replicas: 3
    environment:
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://user:pass@postgres:5432/ioc
    depends_on:
      - redis
      - postgres
      - keycloak
  
  # Function Registry Service
  registry:
    build: ./registry
    environment:
      - POSTGRES_URL=postgresql://user:pass@postgres:5432/ioc
  
  # Cache
  redis:
    image: redis:alpine
    volumes:
      - redis_data:/data
  
  # Database
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ioc
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  # Authentication
  keycloak:
    image: quay.io/keycloak/keycloak:latest
    environment:
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: admin
    ports:
      - "8080:8080"
  
  # Object Storage
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data

volumes:
  redis_data:
  postgres_data:
  minio_data:
```

### 9.2 Monitoring & Observability

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

api_calls_total = Counter('ioc_api_calls_total', 'Total API calls', ['function', 'status'])
api_duration = Histogram('ioc_api_duration_seconds', 'API call duration', ['function'])
active_sessions = Gauge('ioc_active_sessions', 'Number of active user sessions')
llm_tokens = Counter('ioc_llm_tokens_total', 'Total LLM tokens used', ['model'])
```

---

## 10. Future Roadmap

### Q1 2026
- ✅ Auto-generate Function Registry from OpenAPI specs
- ✅ Multi-agent architecture (domain-specific agents)
- ✅ Advanced visualization (ECharts, Plotly integration)
- ✅ Voice input support

### Q2 2026
- 📊 Real-time streaming data support (WebSocket)
- 🤖 Reinforcement learning from user feedback
- 🔐 PDPL-compliant data protection (Vietnam)
- 📈 Advanced web-based visualization

### Q3 2026
- 🌐 Multi-language support (English, Vietnamese, Thai, etc.)
- 🔗 Integration with more government systems
- 📈 Predictive analytics & forecasting
- 🎯 Personalized recommendations

### Q4 2026
- 🧠 Advanced RAG (Retrieval-Augmented Generation)
- 🔄 Workflow automation
- 🌍 Cross-border data integration (ASEAN)
- 📊 Executive dashboard & BI tools

---

## 📦 Technology Stack (Web-Based)

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Orchestration:** LangGraph + LangChain
- **Database:** PostgreSQL 15
- **Cache:** Redis 7
- **Auth:** Keycloak / JWT
- **LLM:** Google Gemini / Anthropic Claude / OpenAI GPT-4

### Frontend
- **Framework:** React 18 + TypeScript
- **Styling:** Tailwind CSS
- **State Management:** Zustand / Redux Toolkit
- **API Client:** Axios
- **Charts:** ECharts / Recharts
- **UI Components:** Ant Design / Material-UI

### DevOps
- **Containerization:** Docker + Docker Compose
- **Reverse Proxy:** Nginx
- **Monitoring:** Prometheus + Grafana
- **Logging:** ELK Stack (Elasticsearch, Logstash, Kibana)

---

## 📚 References

- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [Redis Documentation](https://redis.io/documentation)

---

## 📧 Contact

**Tác giả:** Phạm Quang Nhật Minh  
**Email:** minh.pham@fpt.com.vn  
**Organization:** FPT IS R&D / Libra AI Platform  
**Last Updated:** November 3, 2025

---

**© 2025 FPT Information System. All rights reserved.**
