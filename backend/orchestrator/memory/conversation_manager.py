"""
Conversation Manager - Alias for StubConversationManager
"""
from backend.orchestrator.memory.stub_managers import StubConversationManager

# Export StubConversationManager as ConversationManager
ConversationManager = StubConversationManager

__all__ = ['ConversationManager']
