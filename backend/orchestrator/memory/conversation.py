"""Conversation management for persistent chat history."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manage persistent conversations and message history."""
    
    def __init__(self, db_pool):
        """
        Initialize conversation manager.
        
        Args:
            db_pool: Database connection pool
        """
        self.db_pool = db_pool
    
    async def create_conversation(
        self,
        user_id: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new conversation.
        
        Args:
            user_id: User identifier
            title: Conversation title
            metadata: Additional metadata
            
        Returns:
            Created conversation dict
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO conversations (user_id, title, metadata)
                VALUES ($1, $2, $3)
                RETURNING conversation_id, user_id, title, metadata,
                          created_at, updated_at
                """,
                user_id,
                title or "New Conversation",
                json.dumps(metadata or {})
            )
            
            logger.info(f"Created conversation {row['conversation_id']} for user {user_id}")
            
            return {
                "conversation_id": str(row["conversation_id"]),
                "user_id": row["user_id"],
                "title": row["title"],
                "metadata": row["metadata"] or {},
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
    
    async def get_conversation(
        self,
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get conversation by ID.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Conversation dict or None
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT conversation_id, user_id, title, metadata,
                       created_at, updated_at
                FROM conversations
                WHERE conversation_id = $1
                """,
                conversation_id
            )
            
            if not row:
                return None
            
            return {
                "conversation_id": str(row["conversation_id"]),
                "user_id": row["user_id"],
                "title": row["title"],
                "metadata": row["metadata"] or {},
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
    
    async def list_conversations(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List conversations for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of conversations
        """
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT conversation_id, user_id, title, metadata,
                       created_at, updated_at
                FROM conversations
                WHERE user_id = $1
                ORDER BY updated_at DESC
                LIMIT $2 OFFSET $3
                """,
                user_id,
                limit,
                offset
            )
            
            return [
                {
                    "conversation_id": str(row["conversation_id"]),
                    "user_id": row["user_id"],
                    "title": row["title"],
                    "metadata": row["metadata"] or {},
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }
                for row in rows
            ]
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: Conversation identifier
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Additional metadata (e.g., tool calls, reasoning)
            
        Returns:
            Created message dict
        """
        async with self.db_pool.acquire() as conn:
            # Add message
            row = await conn.fetchrow(
                """
                INSERT INTO conversation_messages 
                (conversation_id, role, content, metadata)
                VALUES ($1, $2, $3, $4)
                RETURNING message_id, conversation_id, role, content,
                          metadata, created_at
                """,
                conversation_id,
                role,
                content,
                json.dumps(metadata or {})
            )
            
            # Update conversation timestamp
            await conn.execute(
                """
                UPDATE conversations
                SET updated_at = $1
                WHERE conversation_id = $2
                """,
                datetime.utcnow(),
                conversation_id
            )
            
            logger.debug(f"Added {role} message to conversation {conversation_id}")
            
            return {
                "message_id": str(row["message_id"]),
                "conversation_id": str(row["conversation_id"]),
                "role": row["role"],
                "content": row["content"],
                "metadata": row["metadata"] or {},
                "created_at": row["created_at"]
            }
    
    async def get_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get messages from a conversation.
        
        Args:
            conversation_id: Conversation identifier
            limit: Maximum number of messages (None for all)
            offset: Offset for pagination
            
        Returns:
            List of messages in chronological order
        """
        query = """
            SELECT message_id, conversation_id, role, content,
                   metadata, created_at
            FROM conversation_messages
            WHERE conversation_id = $1
            ORDER BY created_at ASC
        """
        
        params = [conversation_id]
        
        if limit is not None:
            query += f" LIMIT ${len(params) + 1}"
            params.append(limit)
        
        if offset > 0:
            query += f" OFFSET ${len(params) + 1}"
            params.append(offset)
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
            return [
                {
                    "message_id": str(row["message_id"]),
                    "conversation_id": str(row["conversation_id"]),
                    "role": row["role"],
                    "content": row["content"],
                    "metadata": row["metadata"] or {},
                    "created_at": row["created_at"]
                }
                for row in rows
            ]
    
    async def get_recent_messages(
        self,
        conversation_id: str,
        n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get the N most recent messages from a conversation.
        
        Args:
            conversation_id: Conversation identifier
            n: Number of recent messages to retrieve
            
        Returns:
            List of recent messages
        """
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT message_id, conversation_id, role, content,
                       metadata, created_at
                FROM conversation_messages
                WHERE conversation_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                conversation_id,
                n
            )
            
            # Reverse to get chronological order
            messages = [
                {
                    "message_id": str(row["message_id"]),
                    "conversation_id": str(row["conversation_id"]),
                    "role": row["role"],
                    "content": row["content"],
                    "metadata": row["metadata"] or {},
                    "created_at": row["created_at"]
                }
                for row in rows
            ]
            
            return list(reversed(messages))
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation and all its messages.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            True if deleted successfully
        """
        async with self.db_pool.acquire() as conn:
            # Messages will be deleted by CASCADE
            result = await conn.execute(
                """
                DELETE FROM conversations
                WHERE conversation_id = $1
                """,
                conversation_id
            )
            
            deleted = result.split()[-1] == "1"
            
            if deleted:
                logger.info(f"Deleted conversation {conversation_id}")
            
            return deleted
    
    async def update_title(
        self,
        conversation_id: str,
        title: str
    ) -> bool:
        """
        Update conversation title.
        
        Args:
            conversation_id: Conversation identifier
            title: New title
            
        Returns:
            True if updated successfully
        """
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE conversations
                SET title = $1, updated_at = $2
                WHERE conversation_id = $3
                """,
                title,
                datetime.utcnow(),
                conversation_id
            )
            
            return result.split()[-1] == "1"
    
    def format_messages_for_llm(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """
        Format messages for LLM input.
        
        Args:
            messages: List of message dicts
            
        Returns:
            List of formatted messages for LLM
        """
        return [
            {
                "role": msg["role"],
                "content": msg["content"]
            }
            for msg in messages
        ]
