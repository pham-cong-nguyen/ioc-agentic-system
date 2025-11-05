"""
ReAct Agent Orchestrator v3 with RAG + Memory
Implements full ReAct loop with:
- RAG-based function retrieval
- User profile & conversation memory
- Self-reflection loop
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .react_agent import ReactAgent
from .memory.context_builder import ContextBuilder
from .memory.user_profile import UserProfileManager
from .memory.conversation import ConversationManager
from backend.registry.embeddings.rag_retriever import RAGRetriever
from backend.registry.embeddings.sentence_transformer_embedder import SentenceTransformerEmbedder
from backend.registry.embeddings.milvus_store import MilvusStore
from backend.utils.database import get_db_context
from config.settings import settings

logger = logging.getLogger(__name__)


class ReActOrchestrator:
    """
    ReAct-based orchestrator with RAG and Memory.
    
    Architecture:
    1. Context Builder - Load user profile + conversation history
    2. RAG Retriever - Vector search + LLM reranking
    3. ReAct Agent - THINK → ACT → OBSERVE → REFLECT loop
    4. Response Generator - Natural language + insights
    """
    
    def __init__(self):
        """Initialize all components (lazy loading)"""
        self._initialized = False
        self.embedder = None
        self.vector_store = None
        self.rag_retriever = None
        self.llm_service = None
        self.executor_service = None
        
        logger.info("⚠️  ReAct v3 orchestrator created (components will load on first use)")
    
    def _initialize_components(self):
        """Initialize RAG and memory components (lazy)"""
        if self._initialized:
            return
            
        try:
            logger.info("🔧 Initializing ReAct v3 components...")
            
            # RAG Components
            self.embedder = SentenceTransformerEmbedder(
                model_name=getattr(settings, 'EMBEDDING_MODEL', 'BAAI/bge-small-en-v1.5')
            )
            
            self.vector_store = MilvusStore(
                host=getattr(settings, 'MILVUS_HOST', 'localhost'),
                port=getattr(settings, 'MILVUS_PORT', 19530),
                collection_name=getattr(settings, 'MILVUS_COLLECTION', 'function_embeddings'),
                dimension=self.embedder.dimension
            )
            
            self.rag_retriever = RAGRetriever(
                embedder=self.embedder,
                vector_store=self.vector_store,
                initial_top_k=getattr(settings, 'RAG_STAGE1_TOP_K', 50),
                final_top_k=getattr(settings, 'RAG_STAGE2_TOP_K', 5)
            )
            
            # Import dependencies for ReactAgent
            from .llm_service import LLMService
            from ..executor.service import APIExecutor
            
            # Initialize services
            self.llm_service = LLMService()
            self.executor_service = APIExecutor()
            
            # Initialize ReAct Agent WITHOUT context_builder and registry for now
            # - context_builder: Memory system requires refactoring (asyncpg → SQLAlchemy)
            # - registry_service: Requires DB session, will use mock execution
            self.react_agent = ReactAgent(
                llm_service=self.llm_service,
                rag_retriever=self.rag_retriever,
                context_builder=None,  # Disable memory for now
                executor_service=self.executor_service,
                registry_service=None  # Will use mock execution in ReactAgent
            )
            
            self._initialized = True
            
            logger.info("✅ ReAct v3 orchestrator initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize ReAct orchestrator: {e}")
            raise
    
    async def process_query(
        self,
        query: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        language: str = "vi",
        rag_config: Optional[Dict[str, Any]] = None,
        react_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process user query with full ReAct loop.
        
        Args:
            query: User's natural language query
            user_id: User identifier
            conversation_id: Conversation ID (optional, creates new if not provided)
            language: Response language (vi/en)
            rag_config: RAG configuration overrides
            react_config: ReAct configuration overrides
            
        Returns:
            Complete response with metadata
        """
        # Lazy initialization
        self._initialize_components()
        
        start_time = datetime.now()
        
        try:
            logger.info(f"Processing query: {query}")
            logger.info(f"User: {user_id}, Conversation: {conversation_id}")
            
            # Step 1: Build context (profile + history)
            async with get_db_context() as db:
                context = await self._build_context(
                    db=db,
                    query=query,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    language=language
                )
            
            logger.info(f"Context built: {len(context.get('history', []))} history items")
            
            # Step 2: Run ReAct agent
            state = await self.react_agent.run(
                user_id=user_id,
                query=query,
                conversation_id=conversation_id
            )
            
            logger.info(f"ReAct completed: {state.get('current_step', 0)} iterations")
            
            # Step 3: Build response (skip conversation saving for now)
            processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            response = {
                "success": True,
                "data": {
                    "response": state.get('final_response') or "Processing complete",
                    "conversation_id": conversation_id,
                    "message_id": None,  # TODO: Implement conversation saving
                    
                    "metadata": {
                        "react_iterations": state.get('current_step', 0),
                        "status": state.get('status', 'unknown'),
                        "quality_score": state.get('quality_score', 0.0),
                        "processing_time_ms": processing_time_ms,
                        "functions_used": len(state.get('execution_results', []))
                    }
                }
            }
            
            logger.info(f"✅ Query processed successfully in {processing_time_ms:.2f}ms")
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "success": False,
                "error": str(e),
                "metadata": {
                    "processing_time_ms": processing_time_ms
                }
            }
    
    async def _build_context(
        self,
        db,
        query: str,
        user_id: str,
        conversation_id: Optional[str],
        language: str
    ) -> Dict[str, Any]:
        """Build full context for ReAct agent"""
        
        # For now, use a simple context without memory
        # TODO: Refactor UserProfileManager and ConversationManager to use SQLAlchemy
        context = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "current_query": query,
            "language": language,
            "profile": {
                "user_id": user_id,
                "preferences": {},
                "custom_instructions": None,
                "api_permissions": []
            },
            "history": [],
            "system_instructions": (
                "You are a helpful AI assistant that can call external APIs to help users. "
                "Follow the ReAct pattern: Think → Act → Observe → Reflect."
            )
        }
        
        return context
    
    async def _save_conversation(
        self,
        db,
        user_id: str,
        conversation_id: Optional[str],
        query: str,
        response: str,
        memory
    ) -> tuple[str, str]:
        """Save conversation turn to database"""
        
        conversation_manager = ConversationManager(db)
        
        # Create conversation if needed
        if not conversation_id:
            result = await conversation_manager.create_conversation(
                user_id=user_id,
                title=query[:100]  # First 100 chars as title
            )
            conversation_id = result.get("conversation_id")
        
        # Save user message
        user_message_result = await conversation_manager.save_message(
            conversation_id=conversation_id,
            role="user",
            content=query
        )
        user_message_id = user_message_result.get("message_id")
        
        # Save assistant message
        assistant_message_result = await conversation_manager.save_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response,
            metadata={
                "function_calls": [
                    {
                        "function_id": call.get("function_id"),
                        "success": call.get("success")
                    }
                    for call in memory.api_calls
                ] if hasattr(memory, 'api_calls') else [],
                "execution_time_ms": sum(
                    call.get("execution_time_ms", 0) 
                    for call in memory.api_calls
                ) if hasattr(memory, 'api_calls') else 0
            }
        )
        assistant_message_id = assistant_message_result.get("message_id")
        
        return conversation_id, assistant_message_id
    
    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get conversation history"""
        
        # Lazy initialization
        self._initialize_components()
        
        try:
            async with get_db_context() as db:
                conversation_manager = ConversationManager(db)
                
                history = await conversation_manager.get_recent_messages(
                    conversation_id=conversation_id,
                    limit=limit
                )
                
                return {
                    "success": True,
                    "data": {
                        "conversation_id": conversation_id,
                        "messages": history
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_user_conversations(
        self,
        user_id: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get user's conversation list"""
        
        # Lazy initialization
        self._initialize_components()
        
        try:
            async with get_db_context() as db:
                conversation_manager = ConversationManager(db)
                
                conversations = await conversation_manager.list_conversations(
                    user_id=user_id,
                    limit=limit
                )
                
                return {
                    "success": True,
                    "data": {
                        "user_id": user_id,
                        "conversations": conversations
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting user conversations: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get conversation by ID.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Conversation dict or None if not found
        """
        self._initialize_components()
        # TODO: Implement proper conversation retrieval with SQLAlchemy
        return {
            "conversation_id": conversation_id,
            "user_id": "unknown",
            "messages": [],
            "created_at": datetime.now().isoformat()
        }
    
    async def get_user_conversations(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get user's conversations.
        
        Args:
            user_id: User identifier
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversations
        """
        self._initialize_components()
        # TODO: Implement proper conversation retrieval with SQLAlchemy
        return []


# Global orchestrator instance
orchestrator_v3 = ReActOrchestrator()
