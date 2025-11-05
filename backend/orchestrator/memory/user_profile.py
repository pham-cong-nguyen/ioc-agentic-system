"""User profile management for personalized agent behavior."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class UserProfileManager:
    """Manage user profiles and preferences."""
    
    def __init__(self, db_pool):
        """
        Initialize user profile manager.
        
        Args:
            db_pool: Database connection pool
        """
        self.db_pool = db_pool
    
    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile.
        
        Args:
            user_id: User identifier
            
        Returns:
            User profile dict or None if not found
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT user_id, preferences, custom_instructions, 
                       api_permissions, created_at, updated_at
                FROM user_profiles
                WHERE user_id = $1
                """,
                user_id
            )
            
            if not row:
                logger.warning(f"User profile not found: {user_id}")
                return None
            
            return {
                "user_id": row["user_id"],
                "preferences": row["preferences"] or {},
                "custom_instructions": row["custom_instructions"],
                "api_permissions": row["api_permissions"] or [],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
    
    async def create_profile(
        self,
        user_id: str,
        preferences: Optional[Dict[str, Any]] = None,
        custom_instructions: Optional[str] = None,
        api_permissions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new user profile.
        
        Args:
            user_id: User identifier
            preferences: User preferences (e.g., tone, verbosity)
            custom_instructions: Custom instructions for the agent
            api_permissions: List of allowed API categories
            
        Returns:
            Created user profile
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO user_profiles 
                (user_id, preferences, custom_instructions, api_permissions)
                VALUES ($1, $2, $3, $4)
                RETURNING user_id, preferences, custom_instructions, 
                          api_permissions, created_at, updated_at
                """,
                user_id,
                json.dumps(preferences or {}),
                custom_instructions,
                api_permissions or []
            )
            
            logger.info(f"Created profile for user: {user_id}")
            
            return {
                "user_id": row["user_id"],
                "preferences": row["preferences"] or {},
                "custom_instructions": row["custom_instructions"],
                "api_permissions": row["api_permissions"] or [],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
    
    async def update_profile(
        self,
        user_id: str,
        preferences: Optional[Dict[str, Any]] = None,
        custom_instructions: Optional[str] = None,
        api_permissions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Update user profile.
        
        Args:
            user_id: User identifier
            preferences: Updated preferences
            custom_instructions: Updated instructions
            api_permissions: Updated permissions
            
        Returns:
            Updated user profile
        """
        # Build dynamic update query
        updates = []
        params = [user_id]
        param_idx = 2
        
        if preferences is not None:
            updates.append(f"preferences = ${param_idx}")
            params.append(json.dumps(preferences))
            param_idx += 1
        
        if custom_instructions is not None:
            updates.append(f"custom_instructions = ${param_idx}")
            params.append(custom_instructions)
            param_idx += 1
        
        if api_permissions is not None:
            updates.append(f"api_permissions = ${param_idx}")
            params.append(api_permissions)
            param_idx += 1
        
        if not updates:
            # No updates, just return current profile
            return await self.get_profile(user_id)
        
        updates.append(f"updated_at = ${param_idx}")
        params.append(datetime.utcnow())
        
        query = f"""
            UPDATE user_profiles
            SET {', '.join(updates)}
            WHERE user_id = $1
            RETURNING user_id, preferences, custom_instructions,
                      api_permissions, created_at, updated_at
        """
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)
            
            if not row:
                logger.warning(f"User profile not found for update: {user_id}")
                return None
            
            logger.info(f"Updated profile for user: {user_id}")
            
            return {
                "user_id": row["user_id"],
                "preferences": row["preferences"] or {},
                "custom_instructions": row["custom_instructions"],
                "api_permissions": row["api_permissions"] or [],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
    
    async def get_or_create_profile(
        self,
        user_id: str,
        default_permissions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get existing profile or create new one if not exists.
        
        Args:
            user_id: User identifier
            default_permissions: Default permissions for new users
            
        Returns:
            User profile
        """
        profile = await self.get_profile(user_id)
        
        if profile is None:
            profile = await self.create_profile(
                user_id=user_id,
                api_permissions=default_permissions
            )
        
        return profile
    
    async def has_permission(
        self,
        user_id: str,
        api_category: str
    ) -> bool:
        """
        Check if user has permission for an API category.
        
        Args:
            user_id: User identifier
            api_category: API category to check
            
        Returns:
            True if user has permission
        """
        profile = await self.get_profile(user_id)
        
        if not profile:
            return False
        
        permissions = profile.get("api_permissions", [])
        
        # Empty list means all permissions
        if not permissions:
            return True
        
        # Check if category is in permissions
        return api_category in permissions
    
    def format_instructions(self, profile: Dict[str, Any]) -> str:
        """
        Format user profile into instructions for the agent.
        
        Args:
            profile: User profile dict
            
        Returns:
            Formatted instructions string
        """
        parts = []
        
        # Custom instructions
        if profile.get("custom_instructions"):
            parts.append(f"User Instructions: {profile['custom_instructions']}")
        
        # Preferences
        preferences = profile.get("preferences", {})
        if preferences:
            pref_parts = []
            
            if preferences.get("tone"):
                pref_parts.append(f"Tone: {preferences['tone']}")
            
            if preferences.get("verbosity"):
                pref_parts.append(f"Verbosity: {preferences['verbosity']}")
            
            if preferences.get("language"):
                pref_parts.append(f"Language: {preferences['language']}")
            
            if pref_parts:
                parts.append(f"Preferences: {', '.join(pref_parts)}")
        
        # Permissions
        permissions = profile.get("api_permissions", [])
        if permissions:
            parts.append(f"Allowed APIs: {', '.join(permissions)}")
        
        return "\n".join(parts) if parts else ""
