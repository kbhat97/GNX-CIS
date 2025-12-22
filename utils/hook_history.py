"""
Hook History Manager (IMP-003)
Manages recent_hooks storage for content diversity.

Provides functions to:
- Fetch recent hooks for prompt injection (PROHIBITED_HOOKS)
- Save new hooks after generation
- Clear hook history if needed
"""

from typing import Optional
import logging

logger = logging.getLogger(__name__)


class HookHistoryManager:
    """Manages hook history for a user to prevent content repetition."""
    
    def __init__(self, supabase_client):
        """
        Initialize with Supabase client.
        
        Args:
            supabase_client: Initialized Supabase client instance
        """
        self.supabase = supabase_client
    
    async def get_recent_hooks(self, user_id: str, limit: int = 5) -> list[str]:
        """
        Get the last N hooks used by a user.
        
        Args:
            user_id: UUID string of the user
            limit: Maximum number of hooks to return (default 5)
            
        Returns:
            List of hook strings (may be empty)
        """
        try:
            # Note: supabase Python client is synchronous, not async
            # But we keep the method async for compatibility with async callers
            result = self.supabase.rpc(
                "get_recent_hooks", 
                {"p_user_id": user_id, "p_limit": limit}
            ).execute()
            
            if result.data:
                return result.data
            return []
            
        except Exception as e:
            # Fallback: direct query
            logger.warning(f"RPC get_recent_hooks failed, using fallback: {e}")
            try:
                result = self.supabase.table("user_profiles") \
                    .select("recent_hooks") \
                    .eq("user_id", user_id) \
                    .single() \
                    .execute()
                
                if result.data and result.data.get("recent_hooks"):
                    hooks = result.data["recent_hooks"]
                    return hooks[-limit:] if len(hooks) > limit else hooks
                return []
                
            except Exception as fallback_error:
                logger.error(f"Failed to get recent hooks: {fallback_error}")
                return []  # Graceful degradation
    
    async def save_hook(self, user_id: str, hook_text: str) -> bool:
        """
        Save a new hook to the user's history.
        
        Args:
            user_id: UUID string of the user
            hook_text: The hook/opening line to save (truncated to 150 chars)
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Truncate hook to reasonable length
            truncated_hook = hook_text[:150].strip()
            
            if not truncated_hook:
                logger.warning("Empty hook provided, not saving")
                return False
            
            # Note: supabase Python client is synchronous
            self.supabase.rpc(
                "append_recent_hook",
                {"p_user_id": user_id, "p_new_hook": truncated_hook}
            ).execute()
            
            logger.info(f"Saved hook for user {user_id[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save hook: {e}")
            return False  # Non-critical, don't break generation
    
    async def clear_hooks(self, user_id: str) -> bool:
        """
        Clear all hooks for a user (useful for testing or reset).
        
        Args:
            user_id: UUID string of the user
            
        Returns:
            True if cleared successfully, False otherwise
        """
        try:
            # Note: supabase Python client is synchronous
            self.supabase.table("user_profiles") \
                .update({"recent_hooks": []}) \
                .eq("user_id", user_id) \
                .execute()
            
            logger.info(f"Cleared hooks for user {user_id[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear hooks: {e}")
            return False
    
    def format_prohibited_hooks(self, hooks: list[str]) -> str:
        """
        Format hooks list into a prompt-ready PROHIBITED_HOOKS section.
        
        Args:
            hooks: List of hook strings
            
        Returns:
            Formatted string for prompt injection, or empty string if no hooks
        """
        if not hooks:
            return ""
        
        formatted_hooks = "\n".join(f"- \"{hook}\"" for hook in hooks)
        
        return f"""
═══════════════════════════════════════════════════════════════════
PROHIBITED HOOKS (DO NOT use these opening patterns - you've used them recently):
{formatted_hooks}

CRITICAL: Generate a DIFFERENT hook style. Be creative and vary your approach.
═══════════════════════════════════════════════════════════════════
"""


def extract_hook_from_content(post_content: str) -> Optional[str]:
    """
    Extract the hook (first line/sentence) from post content.
    
    Args:
        post_content: Full post text
        
    Returns:
        The hook string, or None if extraction fails
    """
    if not post_content:
        return None
    
    # Clean up the content
    content = post_content.strip()
    
    # Get first line FIRST (before other processing)
    first_line = content.split("\n")[0].strip()
    
    # Remove markdown bold markers from the first line
    first_line = first_line.replace("**", "")
    
    # If first line is very short, try to get first sentence from full content
    if len(first_line) < 20:
        clean_content = content.replace("**", "")
        sentences = clean_content.split(".")
        if sentences:
            first_line = sentences[0].strip()
    
    # Truncate if too long
    if len(first_line) > 150:
        first_line = first_line[:147] + "..."
    
    return first_line if first_line else None
