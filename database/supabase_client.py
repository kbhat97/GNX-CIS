import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
from config import config
from utils.logger import log_agent_action, log_error
import logging

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Production-ready, multi-tenant Supabase client with comprehensive database operations"""
    
    def __init__(self):
        """Initialize Supabase client with service key for admin operations"""
        try:
            self.client: Client = create_client(
                config.SUPABASE_URL, 
                config.SUPABASE_SERVICE_KEY
            )
            logger.info("✅ Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase client: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Check Supabase connection health"""
        try:
            # Simple query to test connection
            result = self.client.table("posts").select("count", count="exact").limit(1).execute()
            return {
                "healthy": True,
                "message": "Database connection successful",
                "total_posts": result.count if hasattr(result, 'count') else 0
            }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Database connection failed: {str(e)}"
            }
    
    # POST MANAGEMENT METHODS
    
    def save_draft_post(self, user_id: str, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save a draft post to database"""
        try:
            # Prepare post data
            insert_data = {
                "user_id": user_id,
                "topic": post_data.get("topic", ""),
                "post_text": post_data.get("post_text", ""),
                "reasoning": post_data.get("reasoning", ""),
                "virality_score": post_data.get("virality_score", 0),
                "suggestions": post_data.get("suggestions", {}),
                "status": "draft",
                "image_path": post_data.get("image_path"),
                "created_at": datetime.now().isoformat()
            }
            
            result = self.client.table("posts").insert(insert_data).execute()
            
            if result.data:
                post = result.data[0]
                log_agent_action("Database", "Draft post saved", post["id"])
                return post
            else:
                raise Exception("No data returned from insert operation")
                
        except Exception as e:
            log_error(e, "Save draft post")
            raise
    
    def get_pending_approvals(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all pending draft posts for a user"""
        try:
            result = (
                self.client.table("posts")
                .select("*")
                .eq("user_id", user_id)
                .eq("status", "draft")
                .order("created_at", desc=True)
                .execute()
            )
            
            posts = result.data or []
            log_agent_action("Database", "Fetched pending approvals", f"Count: {len(posts)}")
            return posts
            
        except Exception as e:
            log_error(e, "Get pending approvals")
            return []
    
    def get_published_posts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all published posts for a user"""
        try:
            result = (
                self.client.table("posts")
                .select("*")
                .eq("user_id", user_id)
                .eq("status", "published")
                .order("published_at", desc=True)
                .execute()
            )
            
            posts = result.data or []
            log_agent_action("Database", "Fetched published posts", f"Count: {len(posts)}")
            return posts
            
        except Exception as e:
            log_error(e, "Get published posts")
            return []
    
    def get_post(self, user_id: str, post_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific post by ID (with user authorization)"""
        try:
            result = (
                self.client.table("posts")
                .select("*")
                .eq("id", post_id)
                .eq("user_id", user_id)
                .single()
                .execute()
            )
            
            if result.data:
                log_agent_action("Database", "Fetched post", post_id)
                return result.data
            return None
            
        except Exception as e:
            log_error(e, f"Get post {post_id}")
            return None
    
    def update_draft_post(self, user_id: str, post_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a draft post"""
        try:
            # Add updated timestamp
            updates["updated_at"] = datetime.now().isoformat()
            
            result = (
                self.client.table("posts")
                .update(updates)
                .eq("id", post_id)
                .eq("user_id", user_id)
                .eq("status", "draft")  # Only update drafts
                .execute()
            )
            
            if result.data:
                post = result.data[0]
                log_agent_action("Database", "Updated draft post", post_id)
                return post
            else:
                raise Exception("Post not found or not a draft")
                
        except Exception as e:
            log_error(e, f"Update draft post {post_id}")
            raise
    
    def mark_post_published(self, user_id: str, post_id: str, linkedin_post_id: str) -> Dict[str, Any]:
        """Mark a post as published with LinkedIn post ID"""
        try:
            updates = {
                "status": "published",
                "linkedin_post_id": linkedin_post_id,
                "published_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            result = (
                self.client.table("posts")
                .update(updates)
                .eq("id", post_id)
                .eq("user_id", user_id)
                .execute()
            )
            
            if result.data:
                post = result.data[0]
                log_agent_action("Database", "Marked post as published", post_id)
                return post
            else:
                raise Exception("Post not found")
                
        except Exception as e:
            log_error(e, f"Mark post published {post_id}")
            raise
    
    def delete_post(self, user_id: str, post_id: str) -> bool:
        """Delete a post (only drafts can be deleted)"""
        try:
            result = (
                self.client.table("posts")
                .delete()
                .eq("id", post_id)
                .eq("user_id", user_id)
                .eq("status", "draft")
                .execute()
            )
            
            success = len(result.data) > 0 if result.data else False
            if success:
                log_agent_action("Database", "Deleted draft post", post_id)
            
            return success
            
        except Exception as e:
            log_error(e, f"Delete post {post_id}")
            return False
    
    # LINKEDIN TOKEN MANAGEMENT
    
    def save_linkedin_token(self, user_id: str, token_data: Dict[str, Any]) -> bool:
        """Save LinkedIn OAuth token data for a user"""
        try:
            # Prepare token data
            insert_data = {
                "user_id": user_id,
                "linkedin_access_token": token_data.get("access_token"),
                "token_type": token_data.get("token_type", "Bearer"),
                "expires_in": token_data.get("expires_in"),
                "scope": token_data.get("scope"),
                "created_at": datetime.now().isoformat()
            }
            
            # Upsert (insert or update)
            result = (
                self.client.table("linkedin_tokens")
                .upsert(insert_data, on_conflict="user_id")
                .execute()
            )
            
            success = len(result.data) > 0 if result.data else False
            if success:
                log_agent_action("Database", "Saved LinkedIn token", user_id)
            
            return success
            
        except Exception as e:
            log_error(e, f"Save LinkedIn token for user {user_id}")
            return False
    
    def get_linkedin_token(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get LinkedIn token data for a user"""
        try:
            result = (
                self.client.table("linkedin_tokens")
                .select("*")
                .eq("user_id", user_id)
                .single()
                .execute()
            )
            
            if result.data:
                log_agent_action("Database", "Retrieved LinkedIn token", user_id)
                return result.data
            return None
            
        except Exception as e:
            log_error(e, f"Get LinkedIn token for user {user_id}")
            return None
    
    def remove_linkedin_token(self, user_id: str) -> bool:
        """Remove LinkedIn token for a user"""
        try:
            result = (
                self.client.table("linkedin_tokens")
                .delete()
                .eq("user_id", user_id)
                .execute()
            )
            
            success = len(result.data) > 0 if result.data else False
            if success:
                log_agent_action("Database", "Removed LinkedIn token", user_id)
            
            return success
            
        except Exception as e:
            log_error(e, f"Remove LinkedIn token for user {user_id}")
            return False
    
    # ANALYTICS AND INSIGHTS
    
    def get_user_posts_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's post history for style analysis"""
        try:
            result = (
                self.client.table("posts")
                .select("*")
                .eq("user_id", user_id)
                .in_("status", ["published", "draft"])
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            
            posts = result.data or []
            log_agent_action("Database", "Fetched user post history", f"Count: {len(posts)}")
            return posts
            
        except Exception as e:
            log_error(e, f"Get user posts history for {user_id}")
            return []
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            # Count posts by status
            draft_count = self._count_posts_by_status(user_id, "draft")
            published_count = self._count_posts_by_status(user_id, "published")
            
            # Get recent activity
            recent_posts = (
                self.client.table("posts")
                .select("created_at, status")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(10)
                .execute()
            )
            
            stats = {
                "total_posts": draft_count + published_count,
                "draft_posts": draft_count,
                "published_posts": published_count,
                "recent_activity": recent_posts.data or []
            }
            
            log_agent_action("Database", "Generated user stats", user_id)
            return stats
            
        except Exception as e:
            log_error(e, f"Get user stats for {user_id}")
            return {
                "total_posts": 0,
                "draft_posts": 0,
                "published_posts": 0,
                "recent_activity": []
            }
    
    def _count_posts_by_status(self, user_id: str, status: str) -> int:
        """Helper method to count posts by status"""
        try:
            result = (
                self.client.table("posts")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .eq("status", status)
                .execute()
            )
            
            return result.count if hasattr(result, 'count') else 0
            
        except Exception as e:
            log_error(e, f"Count posts by status {status}")
            return 0
    
    # SYSTEM UTILITIES
    
    def cleanup_old_drafts(self, days_old: int = 30) -> int:
        """Clean up old draft posts (system maintenance)"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            
            result = (
                self.client.table("posts")
                .delete()
                .eq("status", "draft")
                .lt("created_at", cutoff_date)
                .execute()
            )
            
            deleted_count = len(result.data) if result.data else 0
            log_agent_action("Database", "Cleaned up old drafts", f"Deleted: {deleted_count}")
            return deleted_count
            
        except Exception as e:
            log_error(e, "Cleanup old drafts")
            return 0

# Global instance (for backward compatibility)
supabase_client = SupabaseClient()

# Helper functions for backward compatibility
def save_draft_post(user_id: str, post_data: Dict[str, Any]) -> Dict[str, Any]:
    """Backward compatible function"""
    return supabase_client.save_draft_post(user_id, post_data)

def get_pending_approvals(user_id: str) -> List[Dict[str, Any]]:
    """Backward compatible function"""
    return supabase_client.get_pending_approvals(user_id)

def get_published_posts(user_id: str) -> List[Dict[str, Any]]:
    """Backward compatible function"""
    return supabase_client.get_published_posts(user_id)

def get_post(user_id: str, post_id: str) -> Optional[Dict[str, Any]]:
    """Backward compatible function"""
    return supabase_client.get_post(user_id, post_id)

def update_draft_post(user_id: str, post_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Backward compatible function"""
    return supabase_client.update_draft_post(user_id, post_id, updates)

def mark_post_published(user_id: str, post_id: str, linkedin_post_id: str) -> Dict[str, Any]:
    """Backward compatible function"""
    return supabase_client.mark_post_published(user_id, post_id, linkedin_post_id)

def get_linkedin_token(user_id: str) -> Optional[Dict[str, Any]]:
    """Backward compatible function"""
    return supabase_client.get_linkedin_token(user_id)

def save_linkedin_token(user_id: str, token_data: Dict[str, Any]) -> bool:
    """Backward compatible function"""
    return supabase_client.save_linkedin_token(user_id, token_data)
