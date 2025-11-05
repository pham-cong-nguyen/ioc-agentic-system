"""Context builder for constructing agent prompts with memory."""

import logging
from typing import Dict, Any, Optional, List

from .user_profile import UserProfileManager
from .conversation import ConversationManager

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Build rich context for agent from user profile and conversation history."""
    
    def __init__(
        self,
        profile_manager: UserProfileManager,
        conversation_manager: ConversationManager,
        max_history_messages: int = 10
    ):
        """
        Initialize context builder.
        
        Args:
            profile_manager: User profile manager
            conversation_manager: Conversation manager
            max_history_messages: Maximum number of history messages to include
        """
        self.profile_manager = profile_manager
        self.conversation_manager = conversation_manager
        self.max_history_messages = max_history_messages
    
    async def build_context(
        self,
        user_id: str,
        conversation_id: Optional[str] = None,
        current_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build complete context for agent.
        
        Args:
            user_id: User identifier
            conversation_id: Optional conversation ID for history
            current_query: Current user query
            
        Returns:
            Context dict with profile, history, and system instructions
        """
        # Get user profile
        profile = await self.profile_manager.get_or_create_profile(user_id)
        
        # Get conversation history if conversation_id provided
        history = []
        if conversation_id:
            history = await self.conversation_manager.get_recent_messages(
                conversation_id=conversation_id,
                n=self.max_history_messages
            )
        
        # Build system instructions
        system_instructions = self._build_system_instructions(profile)
        
        # Build context dict
        context = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "profile": profile,
            "history": history,
            "system_instructions": system_instructions,
            "current_query": current_query
        }
        
        logger.debug(f"Built context for user {user_id} with {len(history)} history messages")
        
        return context
    
    def _build_system_instructions(self, profile: Dict[str, Any]) -> str:
        """
        Build system instructions from user profile.
        
        Args:
            profile: User profile dict
            
        Returns:
            System instructions string
        """
        parts = [
            "You are a helpful AI assistant that can call external APIs to help users.",
            "Follow the ReAct pattern: Think → Act → Observe → Reflect.",
        ]
        
        # Add profile-specific instructions
        profile_instructions = self.profile_manager.format_instructions(profile)
        if profile_instructions:
            parts.append("\n" + profile_instructions)
        
        # Add permissions note
        permissions = profile.get("api_permissions", [])
        if permissions:
            parts.append(
                f"\nYou can only use APIs from these categories: {', '.join(permissions)}"
            )
        
        return "\n".join(parts)
    
    def build_messages_for_llm(
        self,
        context: Dict[str, Any],
        include_system: bool = True
    ) -> List[Dict[str, str]]:
        """
        Build message list for LLM from context.
        
        Args:
            context: Context dict from build_context()
            include_system: Whether to include system message
            
        Returns:
            List of messages for LLM
        """
        messages = []
        
        # Add system message
        if include_system:
            messages.append({
                "role": "system",
                "content": context["system_instructions"]
            })
        
        # Add history
        history = context.get("history", [])
        for msg in history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current query if provided
        current_query = context.get("current_query")
        if current_query:
            messages.append({
                "role": "user",
                "content": current_query
            })
        
        return messages
    
    async def save_interaction(
        self,
        user_id: str,
        conversation_id: str,
        user_message: str,
        assistant_message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Save a user-assistant interaction to conversation history.
        
        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            user_message: User's message
            assistant_message: Assistant's response
            metadata: Additional metadata (e.g., tool calls, reasoning)
        """
        # Save user message
        await self.conversation_manager.add_message(
            conversation_id=conversation_id,
            role="user",
            content=user_message
        )
        
        # Save assistant message with metadata
        await self.conversation_manager.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=assistant_message,
            metadata=metadata
        )
        
        logger.info(f"Saved interaction to conversation {conversation_id}")
    
    async def create_conversation_with_context(
        self,
        user_id: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new conversation and build initial context.
        
        Args:
            user_id: User identifier
            title: Conversation title
            
        Returns:
            Context dict for new conversation
        """
        # Create conversation
        conversation = await self.conversation_manager.create_conversation(
            user_id=user_id,
            title=title
        )
        
        # Build context
        context = await self.build_context(
            user_id=user_id,
            conversation_id=conversation["conversation_id"]
        )
        
        return context
    
    def extract_key_points(
        self,
        messages: List[Dict[str, Any]],
        max_points: int = 5
    ) -> List[str]:
        """
        Extract key points from conversation history for summarization.
        
        Args:
            messages: List of messages
            max_points: Maximum number of key points
            
        Returns:
            List of key points
        """
        # Simple extraction: get user queries and assistant confirmations
        key_points = []
        
        for i, msg in enumerate(messages):
            if msg["role"] == "user" and len(key_points) < max_points:
                # Add user's question/request
                content = msg["content"][:100]  # Truncate long messages
                key_points.append(f"User: {content}")
        
        return key_points
    
    async def get_conversation_summary(
        self,
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Get a summary of a conversation.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Summary dict with metadata
        """
        conversation = await self.conversation_manager.get_conversation(
            conversation_id
        )
        
        if not conversation:
            return None
        
        messages = await self.conversation_manager.get_messages(
            conversation_id
        )
        
        key_points = self.extract_key_points(messages)
        
        return {
            "conversation_id": conversation_id,
            "title": conversation["title"],
            "message_count": len(messages),
            "key_points": key_points,
            "created_at": conversation["created_at"],
            "updated_at": conversation["updated_at"]
        }
