# 🧠 ReAct Agent with RAG & Memory - Technical Design

**Version:** 2.0  
**Date:** November 5, 2025  
**Author:** Phạm Quang Nhật Minh  
**Status:** Ready for Implementation

---

## 📋 Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [RAG Function Retrieval](#3-rag-function-retrieval)
4. [Memory System](#4-memory-system)
5. [ReAct Agent Loop](#5-react-agent-loop)
6. [Implementation Plan](#6-implementation-plan)
7. [API Specifications](#7-api-specifications)

---

## 1. Overview

### 1.1 Problem Statement

**Current Issues (graph_v2.py):**
- ❌ No memory/context in reasoning/planning
- ❌ No user instructions support
- ❌ Naive function search (doesn't scale to 1000+ functions)
- ❌ Linear execution flow (no self-reflection)
- ❌ No conversation history

**Target Solution:**
- ✅ ReAct Agent with self-reflection loop
- ✅ RAG-based function retrieval (Milvus + Jina)
- ✅ Persistent conversation memory
- ✅ User profile & instructions support
- ✅ Multi-tenant ready

### 1.2 Use Case Example

```
User Profile:
{
  "user_id": "admin@gov.vn",
  "organization": "Ministry of Energy",
  "preferences": {
    "data_granularity": "detailed",
    "preferred_visualization": "chart",
    "time_range_default": "last_30_days"
  },
  "instructions": "Always include year-over-year comparison"
}

Conversation History:
[
  {"role": "user", "content": "Điện năng miền Nam tuần trước?"},
  {"role": "assistant", "content": "2,450 MW, tăng 5% so với cùng kỳ năm ngoái"},
  {"role": "user", "content": "Còn miền Bắc thì sao?"}  ← Current query
]

ReAct Process:
┌──────────────────────────────────────────────────────────┐
│ ITERATION 1                                              │
│ THOUGHT: "User is asking about North region energy.     │
│           Previous context shows they want comparison.   │
│           Need to get North energy data + YoY analysis"  │
│                                                          │
│ ACTION: Search functions for "energy North"             │
│ OBSERVATION: Found [get_energy_kpi, get_energy_trend]   │
│                                                          │
│ REFLECTION: "Need more functions for YoY comparison"    │
│ DECISION: CONTINUE                                       │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ ITERATION 2                                              │
│ THOUGHT: "Need historical data for comparison"           │
│                                                          │
│ ACTION: Call get_energy_kpi(region="North")             │
│ OBSERVATION: Current = 3,100 MW                          │
│                                                          │
│ REFLECTION: "Have current data, need last year data"    │
│ DECISION: CONTINUE                                       │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ ITERATION 3                                              │
│ THOUGHT: "Get same period last year for YoY"            │
│                                                          │
│ ACTION: Call get_energy_historical(year=2024)           │
│ OBSERVATION: Last year = 2,900 MW                        │
│                                                          │
│ REFLECTION: "Have all data needed. Quality score: 0.95" │
│ DECISION: DONE ✅                                        │
└──────────────────────────────────────────────────────────┘

Final Response:
"Điện năng miền Bắc tuần trước là 3,100 MW, tăng 6.9% so với 
cùng kỳ năm ngoái (2,900 MW). Cao hơn miền Nam (2,450 MW)."
```

---

## 2. Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      API GATEWAY                            │
│           POST /api/v1/query                                │
│           {                                                 │
│             "query": "...",                                 │
│             "user_id": "...",                               │
│             "conversation_id": "..."                        │
│           }                                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              CONTEXT BUILDER                                │
│  ┌────────────────────────────────────────────────────┐    │
│  │ 1. Load User Profile (Postgres)                    │    │
│  │    • preferences, instructions, permissions        │    │
│  │                                                     │    │
│  │ 2. Load Conversation History (Postgres)            │    │
│  │    • Last 10 turns                                 │    │
│  │    • Previous API calls                            │    │
│  │                                                     │    │
│  │ 3. Build Context Window                            │    │
│  │    • Query + History + Profile + Instructions      │    │
│  └────────────────────────────────────────────────────┘    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│            RAG FUNCTION RETRIEVER                           │
│                                                             │
│  Stage 1: Vector Search (Milvus)                           │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Query → Jina Embedding → Milvus Search            │   │
│  │ Result: Top 50 candidate functions                 │   │
│  └────────────────────────────────────────────────────┘   │
│                     ↓                                       │
│  Stage 2: LLM Reranking (with full context)               │
│  ┌────────────────────────────────────────────────────┐   │
│  │ LLM analyzes candidates with:                      │   │
│  │ • User query                                        │   │
│  │ • Conversation history                              │   │
│  │ • User instructions                                 │   │
│  │ Result: Top 5 selected functions                   │   │
│  └────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              ReAct AGENT LOOP                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Loop (max_iterations=5):                           │  │
│  │                                                      │  │
│  │  1. THINK (LLM Reasoning)                           │  │
│  │     • Analyze current state                         │  │
│  │     • Decide next action                            │  │
│  │     • Context: query + memory + instructions        │  │
│  │                                                      │  │
│  │  2. ACT (Execute)                                   │  │
│  │     • Search functions (if needed)                  │  │
│  │     • Call APIs (parallel/sequential)               │  │
│  │     • Collect results                               │  │
│  │                                                      │  │
│  │  3. OBSERVE (Store results)                         │  │
│  │     • Add to working memory                         │  │
│  │     • Update execution history                      │  │
│  │                                                      │  │
│  │  4. REFLECT (Self-evaluate)                         │  │
│  │     • Check if goal achieved                        │  │
│  │     • Calculate quality score (0-1)                 │  │
│  │     • Decide: CONTINUE or DONE                      │  │
│  │                                                      │  │
│  │  IF quality_score >= 0.8 OR iterations >= 5:        │  │
│  │     BREAK                                            │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           RESPONSE GENERATOR                                │
│  • Natural language generation                             │
│  • Insights extraction                                      │
│  • Visualization suggestion                                 │
│  • Save to conversation history                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Technology Stack

```yaml
Core Components:
  - Orchestrator: LangGraph + ReAct Pattern
  - LLM: Google Gemini Pro (configurable)
  - Vector Store: Milvus 2.3+
  - Embedding: Jina AI Embeddings v2
  - Database: PostgreSQL 15 (user profiles, conversations)
  - Cache: Redis 7 (optional, for API results)

Python Dependencies:
  - langgraph>=0.2.0
  - langchain>=0.1.0
  - pymilvus>=2.3.0
  - jina>=3.20.0
  - asyncpg>=0.29.0
  - redis>=5.0.0
```

---

## 3. RAG Function Retrieval

### 3.1 Milvus Collection Schema

```python
# Collection: function_embeddings
{
  "collection_name": "function_embeddings",
  "dimension": 768,  # Jina embedding dimension
  "index_type": "IVF_FLAT",
  "metric_type": "COSINE",
  
  "schema": {
    "fields": [
      {
        "name": "function_id",
        "type": "VARCHAR",
        "max_length": 100,
        "is_primary": true
      },
      {
        "name": "embedding",
        "type": "FLOAT_VECTOR",
        "dim": 768
      },
      {
        "name": "name",
        "type": "VARCHAR",
        "max_length": 255
      },
      {
        "name": "description",
        "type": "VARCHAR",
        "max_length": 2000
      },
      {
        "name": "domain",
        "type": "VARCHAR",
        "max_length": 50
      },
      {
        "name": "tags",
        "type": "ARRAY",
        "element_type": "VARCHAR"
      },
      {
        "name": "popularity_score",
        "type": "FLOAT"
      }
    ]
  }
}
```

### 3.2 Jina Embedding Service

```python
# backend/registry/embeddings/jina_embedder.py

from jina import Client
from typing import List
import numpy as np

class JinaEmbedder:
    """Jina AI Embeddings for function retrieval"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize Jina embedder
        
        Options:
        1. Jina AI Cloud API (recommended for production)
        2. Self-hosted Jina (for on-premise)
        """
        self.api_key = api_key or os.getenv("JINA_API_KEY")
        
        if self.api_key:
            # Use Jina Cloud API
            self.client = Client(host='grpc://api.jina.ai:443', api_key=self.api_key)
        else:
            # Use local Jina server
            self.client = Client(host='grpc://localhost:51000')
    
    async def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of text strings
            
        Returns:
            Array of embeddings (N x 768)
        """
        from jina import DocumentArray, Document
        
        docs = DocumentArray([Document(text=text) for text in texts])
        embeddings = await self.client.post(
            on='/encode',
            inputs=docs,
            return_type=DocumentArray
        )
        
        return np.array([doc.embedding for doc in embeddings])
    
    async def embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for a single query"""
        embeddings = await self.embed_texts([query])
        return embeddings[0]
```

### 3.3 Milvus Vector Store

```python
# backend/registry/embeddings/milvus_store.py

from pymilvus import (
    connections, Collection, CollectionSchema, 
    FieldSchema, DataType, utility
)
from typing import List, Dict, Any, Optional
import numpy as np

class MilvusVectorStore:
    """Milvus vector store for function embeddings"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 19530,
        collection_name: str = "function_embeddings"
    ):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.collection = None
        
    async def connect(self):
        """Connect to Milvus server"""
        connections.connect(
            alias="default",
            host=self.host,
            port=self.port
        )
        
        # Create collection if not exists
        if not utility.has_collection(self.collection_name):
            await self._create_collection()
        
        self.collection = Collection(self.collection_name)
        await self._create_index()
        self.collection.load()
    
    async def _create_collection(self):
        """Create Milvus collection"""
        fields = [
            FieldSchema(name="function_id", dtype=DataType.VARCHAR, max_length=100, is_primary=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
            FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=255),
            FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="domain", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="popularity_score", dtype=DataType.FLOAT)
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description="Function embeddings for RAG retrieval"
        )
        
        Collection(name=self.collection_name, schema=schema)
    
    async def _create_index(self):
        """Create IVF_FLAT index for fast search"""
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "COSINE",
            "params": {"nlist": 128}
        }
        
        self.collection.create_index(
            field_name="embedding",
            index_params=index_params
        )
    
    async def insert(
        self,
        function_id: str,
        embedding: np.ndarray,
        name: str,
        description: str,
        domain: str,
        popularity_score: float = 0.0
    ):
        """Insert function embedding"""
        entities = [
            [function_id],
            [embedding.tolist()],
            [name],
            [description],
            [domain],
            [popularity_score]
        ]
        
        self.collection.insert(entities)
        self.collection.flush()
    
    async def batch_insert(self, functions: List[Dict[str, Any]]):
        """Batch insert function embeddings"""
        function_ids = [f["function_id"] for f in functions]
        embeddings = [f["embedding"] for f in functions]
        names = [f["name"] for f in functions]
        descriptions = [f["description"] for f in functions]
        domains = [f["domain"] for f in functions]
        scores = [f.get("popularity_score", 0.0) for f in functions]
        
        entities = [
            function_ids,
            embeddings,
            names,
            descriptions,
            domains,
            scores
        ]
        
        self.collection.insert(entities)
        self.collection.flush()
    
    async def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 50,
        domain_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Vector similarity search
        
        Args:
            query_embedding: Query vector
            top_k: Number of results
            domain_filter: Filter by domain (optional)
            
        Returns:
            List of matched functions with scores
        """
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        
        # Build filter expression
        expr = None
        if domain_filter:
            expr = f'domain == "{domain_filter}"'
        
        results = self.collection.search(
            data=[query_embedding.tolist()],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=expr,
            output_fields=["function_id", "name", "description", "domain", "popularity_score"]
        )
        
        # Format results
        matches = []
        for hits in results:
            for hit in hits:
                matches.append({
                    "function_id": hit.entity.get("function_id"),
                    "name": hit.entity.get("name"),
                    "description": hit.entity.get("description"),
                    "domain": hit.entity.get("domain"),
                    "similarity_score": hit.score,
                    "popularity_score": hit.entity.get("popularity_score")
                })
        
        return matches
    
    async def delete(self, function_id: str):
        """Delete function by ID"""
        expr = f'function_id == "{function_id}"'
        self.collection.delete(expr)
    
    async def close(self):
        """Close connection"""
        connections.disconnect("default")
```

### 3.4 RAG Retriever

```python
# backend/registry/embeddings/rag_retriever.py

from typing import List, Dict, Any, Optional
from .jina_embedder import JinaEmbedder
from .milvus_store import MilvusVectorStore
from backend.orchestrator.llm_service import llm_service

class RAGFunctionRetriever:
    """Two-stage RAG retrieval: Vector Search + LLM Reranking"""
    
    def __init__(
        self,
        embedder: JinaEmbedder,
        vector_store: MilvusVectorStore,
        stage1_top_k: int = 50,
        stage2_top_k: int = 5
    ):
        self.embedder = embedder
        self.vector_store = vector_store
        self.stage1_top_k = stage1_top_k
        self.stage2_top_k = stage2_top_k
    
    async def retrieve(
        self,
        query: str,
        context: Dict[str, Any],
        domain_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Two-stage retrieval:
        Stage 1: Semantic vector search (fast, broad)
        Stage 2: LLM reranking (accurate, narrow)
        
        Args:
            query: User query
            context: Full context (history, instructions, preferences)
            domain_filter: Filter by domain
            
        Returns:
            Top K selected functions
        """
        
        # Stage 1: Vector similarity search
        query_embedding = await self.embedder.embed_query(query)
        
        candidates = await self.vector_store.search(
            query_embedding=query_embedding,
            top_k=self.stage1_top_k,
            domain_filter=domain_filter
        )
        
        if not candidates:
            return []
        
        # Stage 2: LLM reranking with full context
        reranked = await self._llm_rerank(
            query=query,
            candidates=candidates,
            context=context,
            top_k=self.stage2_top_k
        )
        
        return reranked
    
    async def _llm_rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        context: Dict[str, Any],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Use LLM to rerank candidates with full context"""
        
        prompt = f"""
You are a function selection expert. Given a user query and conversation context, 
select the {top_k} MOST RELEVANT functions from the candidates.

**User Query:** {query}

**Conversation History:**
{self._format_history(context.get('conversation_history', []))}

**User Instructions:**
{context.get('user_instructions', 'None')}

**User Preferences:**
{context.get('user_preferences', {})}

**Candidate Functions:**
{self._format_candidates(candidates)}

**Task:**
Select the top {top_k} functions that are MOST RELEVANT to answer the user's query.
Consider:
1. Relevance to current query
2. Conversation context (what user asked before)
3. User instructions and preferences
4. Function popularity

Return ONLY the function IDs in order of relevance, as a JSON array.
Example: ["func_1", "func_3", "func_5"]
"""
        
        response = await llm_service.llm.ainvoke(prompt)
        
        # Parse LLM response
        import json
        selected_ids = json.loads(response.content)
        
        # Build result
        id_to_func = {f["function_id"]: f for f in candidates}
        selected_functions = [id_to_func[fid] for fid in selected_ids if fid in id_to_func]
        
        return selected_functions[:top_k]
    
    def _format_history(self, history: List[Dict]) -> str:
        """Format conversation history"""
        if not history:
            return "No previous conversation"
        
        formatted = []
        for turn in history[-5:]:  # Last 5 turns
            role = turn.get("role", "user")
            content = turn.get("content", "")
            formatted.append(f"- {role.upper()}: {content}")
        
        return "\n".join(formatted)
    
    def _format_candidates(self, candidates: List[Dict]) -> str:
        """Format candidate functions"""
        formatted = []
        for i, func in enumerate(candidates[:20]):  # Show top 20 to LLM
            formatted.append(
                f"{i+1}. ID: {func['function_id']}\n"
                f"   Name: {func['name']}\n"
                f"   Description: {func['description']}\n"
                f"   Domain: {func['domain']}\n"
                f"   Similarity: {func['similarity_score']:.3f}\n"
            )
        
        return "\n".join(formatted)
```

---

## 4. Memory System

### 4.1 Database Schema

```sql
-- User Profiles (multi-tenant)
CREATE TABLE user_profiles (
    user_id VARCHAR(100) PRIMARY KEY,
    organization VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    
    -- Preferences (JSONB for flexibility)
    preferences JSONB DEFAULT '{}',
    
    -- Custom instructions
    instructions TEXT,
    
    -- Permissions
    permissions TEXT[],
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Conversations (persistent chat history)
CREATE TABLE conversations (
    conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) REFERENCES user_profiles(user_id),
    
    title VARCHAR(500),
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Metadata
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_created ON conversations(created_at DESC);

-- Conversation Messages (all chat turns)
CREATE TABLE conversation_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    
    role VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    
    -- Metadata
    function_calls JSONB,  -- Which APIs were called
    execution_time_ms FLOAT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON conversation_messages(conversation_id, created_at);

-- API Call History (for analytics & learning)
CREATE TABLE api_call_history (
    call_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(conversation_id),
    message_id UUID REFERENCES conversation_messages(message_id),
    
    function_id VARCHAR(100),
    parameters JSONB,
    
    success BOOLEAN,
    response_data JSONB,
    error_message TEXT,
    
    execution_time_ms FLOAT,
    cached BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_api_calls_function ON api_call_history(function_id);
CREATE INDEX idx_api_calls_conversation ON api_call_history(conversation_id);
```

### 4.2 Memory Services

```python
# backend/orchestrator/memory/user_profile.py

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from backend.registry.models import Base
from sqlalchemy import Column, String, ARRAY, Text, Boolean, TIMESTAMP
import json

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    user_id = Column(String(100), primary_key=True)
    organization = Column(String(255))
    email = Column(String(255), unique=True)
    preferences = Column(JSONB, default={})
    instructions = Column(Text)
    permissions = Column(ARRAY(Text))
    # ... other fields

class UserProfileService:
    """Manage user profiles and preferences"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile"""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            return None
        
        return {
            "user_id": profile.user_id,
            "organization": profile.organization,
            "preferences": profile.preferences or {},
            "instructions": profile.instructions,
            "permissions": profile.permissions or []
        }
    
    async def update_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ):
        """Update user preferences"""
        await self.db.execute(
            update(UserProfile)
            .where(UserProfile.user_id == user_id)
            .values(preferences=preferences)
        )
        await self.db.commit()
```

```python
# backend/orchestrator/memory/conversation.py

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
import uuid

class ConversationMemoryService:
    """Manage conversation history (persistent)"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_conversation(
        self,
        user_id: str,
        title: Optional[str] = None
    ) -> str:
        """Create new conversation"""
        conversation_id = str(uuid.uuid4())
        
        await self.db.execute(
            f"""
            INSERT INTO conversations (conversation_id, user_id, title)
            VALUES ('{conversation_id}', '{user_id}', '{title or "New Conversation"}')
            """
        )
        await self.db.commit()
        
        return conversation_id
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        function_calls: Optional[List[Dict]] = None,
        execution_time_ms: Optional[float] = None
    ) -> str:
        """Add message to conversation"""
        message_id = str(uuid.uuid4())
        
        await self.db.execute(
            f"""
            INSERT INTO conversation_messages 
            (message_id, conversation_id, role, content, function_calls, execution_time_ms)
            VALUES (
                '{message_id}',
                '{conversation_id}',
                '{role}',
                '{content}',
                '{json.dumps(function_calls or [])}',
                {execution_time_ms or 0}
            )
            """
        )
        await self.db.commit()
        
        return message_id
    
    async def get_history(
        self,
        conversation_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get conversation history"""
        result = await self.db.execute(
            f"""
            SELECT role, content, function_calls, created_at
            FROM conversation_messages
            WHERE conversation_id = '{conversation_id}'
            ORDER BY created_at DESC
            LIMIT {limit}
            """
        )
        
        messages = []
        for row in result:
            messages.append({
                "role": row[0],
                "content": row[1],
                "function_calls": row[2],
                "created_at": row[3]
            })
        
        # Reverse to get chronological order
        return list(reversed(messages))
    
    async def get_user_conversations(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get user's conversation list"""
        result = await self.db.execute(
            f"""
            SELECT conversation_id, title, created_at, updated_at
            FROM conversations
            WHERE user_id = '{user_id}'
            ORDER BY updated_at DESC
            LIMIT {limit}
            """
        )
        
        conversations = []
        for row in result:
            conversations.append({
                "conversation_id": row[0],
                "title": row[1],
                "created_at": row[2],
                "updated_at": row[3]
            })
        
        return conversations
```

```python
# backend/orchestrator/memory/context_builder.py

from typing import Dict, Any, Optional
from .user_profile import UserProfileService
from .conversation import ConversationMemoryService

class ContextBuilder:
    """Build full context window for ReAct agent"""
    
    def __init__(
        self,
        profile_service: UserProfileService,
        conversation_service: ConversationMemoryService
    ):
        self.profile_service = profile_service
        self.conversation_service = conversation_service
    
    async def build_context(
        self,
        query: str,
        user_id: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build complete context including:
        - User query
        - User profile & instructions
        - Conversation history
        - Preferences
        """
        
        # 1. Load user profile
        profile = await self.profile_service.get_profile(user_id)
        
        if not profile:
            # Default profile for new users
            profile = {
                "user_id": user_id,
                "preferences": {},
                "instructions": None,
                "permissions": []
            }
        
        # 2. Load conversation history
        history = []
        if conversation_id:
            history = await self.conversation_service.get_history(
                conversation_id=conversation_id,
                limit=10  # Last 10 messages
            )
        
        # 3. Build context object
        context = {
            "query": query,
            "user_id": user_id,
            "conversation_id": conversation_id,
            
            # User profile
            "user_profile": profile,
            "user_instructions": profile.get("instructions"),
            "user_preferences": profile.get("preferences", {}),
            "user_permissions": profile.get("permissions", []),
            
            # Conversation
            "conversation_history": history,
            
            # Metadata
            "has_history": len(history) > 0
        }
        
        return context
```

---

## 5. ReAct Agent Loop

### 5.1 ReAct State

```python
# backend/orchestrator/state.py - UPDATE

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ReActIteration:
    """Single ReAct iteration"""
    iteration: int
    thought: str
    action: str
    action_input: Dict[str, Any]
    observation: Any
    reflection: str
    quality_score: float
    decision: str  # "continue" or "done"
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class WorkingMemory:
    """Working memory for ReAct agent"""
    query: str
    context: Dict[str, Any]
    
    # Iterations
    iterations: List[ReActIteration] = field(default_factory=list)
    
    # Retrieved functions
    available_functions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Execution results
    api_calls: List[Dict[str, Any]] = field(default_factory=list)
    observations: List[Any] = field(default_factory=list)
    
    # Analysis
    insights: List[str] = field(default_factory=list)
    analyzed_data: Optional[Dict[str, Any]] = None
    
    # Final output
    response: Optional[str] = None
    visualization_config: Optional[Dict[str, Any]] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    total_iterations: int = 0
    
    def add_iteration(self, iteration: ReActIteration):
        self.iterations.append(iteration)
        self.total_iterations += 1
    
    def get_latest_iteration(self) -> Optional[ReActIteration]:
        return self.iterations[-1] if self.iterations else None
    
    def is_complete(self) -> bool:
        latest = self.get_latest_iteration()
        return latest and latest.decision == "done"
```

### 5.2 ReAct Agent

```python
# backend/orchestrator/react_agent.py

from typing import Dict, Any, Optional
from .state import WorkingMemory, ReActIteration
from .llm_service import llm_service
from backend.registry.embeddings.rag_retriever import RAGFunctionRetriever
from backend.executor.service import executor
from backend.analyzer.service import analyzer
from backend.utils.database import get_db_context
from backend.registry.service import FunctionRegistryService
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ReActAgent:
    """ReAct Agent with Self-Reflection"""
    
    def __init__(
        self,
        rag_retriever: RAGFunctionRetriever,
        max_iterations: int = 5,
        quality_threshold: float = 0.8
    ):
        self.rag_retriever = rag_retriever
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
        self.executor = executor
        self.analyzer = analyzer
    
    async def run(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> WorkingMemory:
        """
        Run ReAct loop until goal achieved or max iterations
        
        ReAct Loop:
        1. THINK - Reason about current state
        2. ACT - Execute action
        3. OBSERVE - Collect results
        4. REFLECT - Evaluate progress
        5. Repeat until DONE
        """
        
        memory = WorkingMemory(query=query, context=context)
        
        logger.info(f"Starting ReAct loop for query: {query}")
        
        for i in range(self.max_iterations):
            logger.info(f"--- Iteration {i+1}/{self.max_iterations} ---")
            
            # 1. THINK: Reason about next action
            thought = await self._think(memory)
            logger.info(f"THOUGHT: {thought}")
            
            # 2. ACT: Execute action
            action, action_input = await self._act(memory, thought)
            logger.info(f"ACTION: {action} with input {action_input}")
            
            # 3. OBSERVE: Collect results
            observation = await self._observe(memory, action, action_input)
            logger.info(f"OBSERVATION: {observation}")
            
            # 4. REFLECT: Evaluate progress
            reflection = await self._reflect(memory, observation)
            logger.info(f"REFLECTION: {reflection}")
            
            # Create iteration record
            iteration = ReActIteration(
                iteration=i+1,
                thought=thought,
                action=action,
                action_input=action_input,
                observation=observation,
                reflection=reflection.get("reasoning"),
                quality_score=reflection.get("quality_score"),
                decision=reflection.get("decision")
            )
            
            memory.add_iteration(iteration)
            
            # Check if done
            if reflection.get("decision") == "done":
                logger.info("✅ ReAct loop completed - Goal achieved")
                break
            
            if reflection.get("quality_score", 0) >= self.quality_threshold:
                logger.info(f"✅ Quality threshold reached: {reflection.get('quality_score')}")
                break
        
        # Generate final response
        memory.response = await self._generate_final_response(memory)
        memory.completed_at = datetime.utcnow()
        
        return memory
    
    async def _think(self, memory: WorkingMemory) -> str:
        """THINK: Reason about current state and next action"""
        
        prompt = f"""
You are an intelligent agent helping to answer user queries by calling APIs.

**Original Query:** {memory.query}

**User Context:**
- Instructions: {memory.context.get('user_instructions', 'None')}
- Preferences: {memory.context.get('user_preferences', {})}

**Conversation History:**
{self._format_history(memory.context.get('conversation_history', []))}

**Previous Iterations:**
{self._format_iterations(memory.iterations)}

**Current State:**
- Available functions: {len(memory.available_functions)}
- API calls made: {len(memory.api_calls)}
- Data collected: {len(memory.observations)}

**Task:**
Think step-by-step about what to do next to answer the user's query.
What information do you still need? What action should you take?

Respond with your reasoning (2-3 sentences).
"""
        
        response = await llm_service.llm.ainvoke(prompt)
        return response.content.strip()
    
    async def _act(
        self,
        memory: WorkingMemory,
        thought: str
    ) -> tuple[str, Dict[str, Any]]:
        """ACT: Decide and execute action"""
        
        prompt = f"""
Based on your thought: "{thought}"

What action should you take?

Available actions:
1. "search_functions" - Search for relevant API functions
2. "call_apis" - Execute API calls
3. "analyze_data" - Analyze collected data
4. "done" - Finish (if you have enough information)

Respond in JSON format:
{{
  "action": "action_name",
  "input": {{...action-specific parameters...}}
}}
"""
        
        response = await llm_service.llm.ainvoke(prompt)
        
        import json
        action_data = json.loads(response.content)
        
        return action_data["action"], action_data.get("input", {})
    
    async def _observe(
        self,
        memory: WorkingMemory,
        action: str,
        action_input: Dict[str, Any]
    ) -> Any:
        """OBSERVE: Execute action and collect results"""
        
        if action == "search_functions":
            # Search for relevant functions using RAG
            functions = await self.rag_retriever.retrieve(
                query=memory.query,
                context=memory.context,
                domain_filter=action_input.get("domain")
            )
            memory.available_functions.extend(functions)
            return {
                "found_functions": len(functions),
                "functions": [f["function_id"] for f in functions]
            }
        
        elif action == "call_apis":
            # Execute API calls
            function_ids = action_input.get("function_ids", [])
            
            async with get_db_context() as db:
                registry_service = FunctionRegistryService(db)
                
                results = await self.executor.execute_parallel(
                    [{"function_id": fid, "parameters": action_input.get("parameters", {}).get(fid, {})} 
                     for fid in function_ids],
                    registry_service
                )
            
            memory.api_calls.extend(results)
            memory.observations.extend([r.get("data") for r in results if r.get("success")])
            
            return {
                "executed": len(results),
                "successful": sum(1 for r in results if r.get("success")),
                "results": results
            }
        
        elif action == "analyze_data":
            # Analyze collected data
            if memory.observations:
                analyzed = await self.analyzer.analyze(
                    data=memory.observations,
                    query_type="data_query",
                    entities={}
                )
                memory.analyzed_data = analyzed
                
                insights = await self.analyzer.generate_insights(
                    data=analyzed,
                    query_type="data_query"
                )
                memory.insights = insights
                
                return {
                    "analyzed": True,
                    "insights_count": len(insights)
                }
            
            return {"analyzed": False, "reason": "No data to analyze"}
        
        elif action == "done":
            return {"status": "complete"}
        
        else:
            return {"error": f"Unknown action: {action}"}
    
    async def _reflect(
        self,
        memory: WorkingMemory,
        observation: Any
    ) -> Dict[str, Any]:
        """REFLECT: Evaluate progress and decide next step"""
        
        prompt = f"""
You are evaluating progress on answering this query: "{memory.query}"

**User Instructions:** {memory.context.get('user_instructions', 'None')}

**What you've done so far:**
{self._format_iterations(memory.iterations)}

**Latest observation:**
{observation}

**Current state:**
- Functions found: {len(memory.available_functions)}
- APIs called: {len(memory.api_calls)}
- Data collected: {len(memory.observations)}
- Insights: {len(memory.insights)}

**Evaluate:**
1. Have you collected enough information to answer the query?
2. Is the data quality sufficient?
3. Have you followed user instructions?
4. Quality score (0.0 - 1.0): How complete is your answer?

Respond in JSON:
{{
  "reasoning": "...",
  "quality_score": 0.85,
  "decision": "continue" or "done",
  "missing": ["what's still needed"]
}}
"""
        
        response = await llm_service.llm.ainvoke(prompt)
        
        import json
        reflection = json.loads(response.content)
        
        return reflection
    
    async def _generate_final_response(self, memory: WorkingMemory) -> str:
        """Generate final natural language response"""
        
        prompt = f"""
Generate a comprehensive answer to the user's query based on all collected data.

**Query:** {memory.query}

**User Instructions:** {memory.context.get('user_instructions', 'None')}

**Data Collected:**
{memory.observations}

**Insights:**
{memory.insights}

**Analyzed Data:**
{memory.analyzed_data}

**Task:**
Write a clear, natural language answer in {"Vietnamese" if memory.context.get("language") == "vi" else "English"}.
Include specific numbers, comparisons, and insights.
"""
        
        response = await llm_service.llm.ainvoke(prompt)
        return response.content.strip()
    
    def _format_history(self, history: List[Dict]) -> str:
        """Format conversation history"""
        if not history:
            return "No previous conversation"
        
        formatted = []
        for turn in history[-5:]:
            formatted.append(f"- {turn['role'].upper()}: {turn['content']}")
        
        return "\n".join(formatted)
    
    def _format_iterations(self, iterations: List[ReActIteration]) -> str:
        """Format previous iterations"""
        if not iterations:
            return "No previous iterations"
        
        formatted = []
        for it in iterations:
            formatted.append(
                f"Iteration {it.iteration}:\n"
                f"  Thought: {it.thought}\n"
                f"  Action: {it.action}\n"
                f"  Observation: {it.observation}\n"
                f"  Reflection: {it.reflection}\n"
                f"  Quality: {it.quality_score}\n"
            )
        
        return "\n".join(formatted)
```

---

## 6. Implementation Plan

### Phase 1: Setup Infrastructure (Day 1-2)

```bash
# 1.1 Install dependencies
pip install pymilvus==2.3.4
pip install jina==3.20.0
pip install sentence-transformers==2.2.2

# 1.2 Setup Milvus (Docker)
docker-compose -f docker-compose.milvus.yml up -d

# 1.3 Database migrations
python scripts/migrations/add_memory_tables.py
```

### Phase 2: RAG Components (Day 3-4)

```
backend/registry/embeddings/
  ├── __init__.py
  ├── jina_embedder.py       ✅ Implement
  ├── milvus_store.py         ✅ Implement
  ├── rag_retriever.py        ✅ Implement
  └── sync_embeddings.py      ✅ Sync existing functions
```

### Phase 3: Memory System (Day 5-6)

```
backend/orchestrator/memory/
  ├── __init__.py
  ├── user_profile.py         ✅ Implement
  ├── conversation.py         ✅ Implement
  └── context_builder.py      ✅ Implement
```

### Phase 4: ReAct Agent (Day 7-9)

```
backend/orchestrator/
  ├── react_agent.py          ✅ Implement
  ├── state.py                ✅ Update (add ReAct state)
  ├── graph_v3.py             ✅ New orchestrator with ReAct
  └── routes.py               ✅ Update API endpoints
```

### Phase 5: Testing & Optimization (Day 10-12)

- Unit tests
- Integration tests
- Performance tuning
- Documentation

---

## 7. API Specifications

### 7.1 Query Endpoint (Updated)

```http
POST /api/v1/query
Content-Type: application/json

{
  "query": "So sánh điện năng miền Bắc vs miền Nam tuần này",
  "user_id": "admin@gov.vn",
  "conversation_id": "uuid-optional",
  "language": "vi",
  
  // Optional: Override user profile instructions
  "instructions": "Chỉ lấy dữ liệu từ năm 2024",
  
  // Optional: RAG parameters
  "rag_config": {
    "stage1_top_k": 50,
    "stage2_top_k": 5,
    "domain_filter": "energy"
  },
  
  // Optional: ReAct parameters
  "react_config": {
    "max_iterations": 5,
    "quality_threshold": 0.8
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "response": "Điện năng miền Bắc tuần này là...",
    "conversation_id": "uuid",
    "message_id": "uuid",
    
    "metadata": {
      "react_iterations": 3,
      "functions_searched": 50,
      "functions_used": 3,
      "api_calls": [
        {
          "function_id": "get_energy_kpi",
          "parameters": {"region": "North"},
          "execution_time_ms": 234,
          "cached": false
        }
      ],
      "insights": ["Insight 1", "Insight 2"],
      "quality_score": 0.92,
      "processing_time_ms": 2450
    },
    
    "visualization": {
      "type": "line_chart",
      "config": {...}
    }
  }
}
```

### 7.2 Conversation Management

```http
# Get conversation history
GET /api/v1/conversations/{conversation_id}

# Get user's conversations
GET /api/v1/users/{user_id}/conversations?limit=20

# Create new conversation
POST /api/v1/conversations
{
  "user_id": "admin@gov.vn",
  "title": "Energy Analysis Q4 2024"
}

# Delete conversation
DELETE /api/v1/conversations/{conversation_id}
```

### 7.3 User Profile Management

```http
# Get user profile
GET /api/v1/users/{user_id}/profile

# Update preferences
PATCH /api/v1/users/{user_id}/preferences
{
  "data_granularity": "detailed",
  "visualization": "chart"
}

# Update instructions
PATCH /api/v1/users/{user_id}/instructions
{
  "instructions": "Always include year-over-year comparison"
}
```

---

## 8. Configuration

```python
# config/settings.py - ADD

class Settings(BaseSettings):
    # ... existing settings ...
    
    # Milvus
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "function_embeddings"
    
    # Jina
    JINA_API_KEY: Optional[str] = None  # Use cloud API or local
    JINA_MODEL: str = "jina-embeddings-v2-base-en"
    
    # RAG
    RAG_STAGE1_TOP_K: int = 50
    RAG_STAGE2_TOP_K: int = 5
    
    # ReAct
    REACT_MAX_ITERATIONS: int = 5
    REACT_QUALITY_THRESHOLD: float = 0.8
    
    # Memory
    CONVERSATION_HISTORY_LIMIT: int = 10
```

---

## 9. Docker Compose Updates

```yaml
# docker-compose.milvus.yml

version: '3.8'

services:
  etcd:
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
    volumes:
      - etcd_data:/etcd

  minio:
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    command: minio server /minio_data
    volumes:
      - minio_data:/minio_data

  milvus:
    image: milvusdb/milvus:v2.3.4
    command: ["milvus", "run", "standalone"]
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    ports:
      - "19530:19530"
      - "9091:9091"
    depends_on:
      - etcd
      - minio
    volumes:
      - milvus_data:/var/lib/milvus

volumes:
  etcd_data:
  minio_data:
  milvus_data:
```

---

## 10. Next Steps

**Ready to implement?**

1. ✅ Review this design document
2. ✅ Confirm all requirements are met
3. ✅ Start with Phase 1 (Infrastructure setup)
4. ✅ Then proceed with Phase 2-5

**Estimated Timeline:** 10-12 days for full implementation

---

## 📚 References

- [Milvus Documentation](https://milvus.io/docs)
- [Jina AI Embeddings](https://jina.ai/embeddings)
- [ReAct Paper](https://arxiv.org/abs/2210.03629)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)

---

**© 2025 FPT Information System. All rights reserved.**
