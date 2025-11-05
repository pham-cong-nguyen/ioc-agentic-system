"""Stub implementations for memory managers for testing without database."""

from typing import Dict, Any, Optional, List
from datetime import datetime


class StubUserProfileManager:
    """Stub user profile manager for testing."""
    
    def __init__(self, db=None):
        self.profiles = {}
    
    async def get_or_create_profile(self, user_id: str) -> Dict[str, Any]:
        """Get or create a stub profile."""
        if user_id not in self.profiles:
            self.profiles[user_id] = {
                "user_id": user_id,
                "preferences": {},
                "custom_instructions": None,
                "api_permissions": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        return self.profiles[user_id]
    
    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a stub profile."""
        return await self.get_or_create_profile(user_id)
    
    def format_instructions(self, profile: Dict[str, Any]) -> str:
        """Format profile-specific instructions."""
        return ""


class StubConversationManager:
    """Stub conversation manager for testing."""
    
    def __init__(self, db=None):
        self.conversations = {}
        self.messages = {}
    
    async def get_recent_messages(
        self,
        conversation_id: str,
        n: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent messages from a conversation."""
        return self.messages.get(conversation_id, [])[-n:]
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID."""
        return self.conversations.get(conversation_id)
    
    async def get_user_conversations(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get user's conversations."""
        return []
