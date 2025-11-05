"""
Profile Manager - Alias for StubUserProfileManager
"""
from backend.orchestrator.memory.stub_managers import StubUserProfileManager

# Export StubUserProfileManager as ProfileManager
ProfileManager = StubUserProfileManager

__all__ = ['ProfileManager']
