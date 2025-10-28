import os
from datetime import datetime
from typing import Dict, Optional
from tools.linkedin_publisher import LinkedInPublisher
from database.supabase_client import supabase_client
import asyncio

class PublisherAgent:
    def __init__(self):
        pass # LinkedInPublisher will be instantiated per-publish with the correct token
    
    async def publish_post(
        self, 
        post_text: str, 
        post_id: str,
        access_token: str,
        user_id: str,
        schedule_time: Optional[datetime] = None
    ) -> Dict:
        """
        Publish post to LinkedIn with error handling
        
        Args:
            post_text: The content to post
            post_id: UUID from database
            access_token: LinkedIn access token for the user
            user_id: User ID from Supabase
            schedule_time: Future time to post (None = post now)
        
        Returns:
            {
                "success": True/False,
                "linkedin_post_id": "...",
                "error": "..." (if failed)
            }
        """
        
        # If scheduled for future, wait
        if schedule_time:
            now = datetime.now()
            if schedule_time > now:
                wait_seconds = (schedule_time - now).total_seconds()
                print(f"⏰ Scheduled for {schedule_time}. Waiting {wait_seconds}s...")
                await asyncio.sleep(wait_seconds)
        
        try:
            # Format post for LinkedIn (handle line breaks, etc.)
            formatted_text = self._format_for_linkedin(post_text)
            
            # Instantiate LinkedInPublisher with the current access token
            linkedin_publisher_instance = LinkedInPublisher(access_token=access_token)
            
            # Publish via LinkedIn API
            result = linkedin_publisher_instance.create_post(
                text=formatted_text,
                visibility="PUBLIC"
            )
            
            if result["success"]:
                # Update database
                supabase_client.table("posts").update({
                    "status": "published",
                    "linkedin_post_id": result["post_id"],
                    "published_at": datetime.now().isoformat()
                }).eq("id", post_id).execute()
                
                print(f"✅ Published post {post_id}")
                
                return {
                    "success": True,
                    "linkedin_post_id": result["post_id"],
                    "published_at": result["created_at"]
                }
            else:
                # Log failure
                supabase_client.table("posts").update({
                    "status": "failed",
                    "error_log": result.get("error")
                }).eq("id", post_id).execute()
                
                return {
                    "success": False,
                    "error": result.get("error")
                }
        
        except Exception as e:
            print(f"❌ Publishing error: {str(e)}")
            
            # Update database with error
            supabase_client.table("posts").update({
                "status": "failed",
                "error_log": str(e)
            }).eq("id", post_id).execute()
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_for_linkedin(self, text: str) -> str:
        """
        Format text for LinkedIn's requirements
        - Preserve line breaks
        - Remove excessive spacing
        - Ensure hashtags are properly formatted
        """
        
        # Replace multiple newlines with double newline
        formatted = "\n\n".join([
            line.strip() 
            for line in text.split("\n") 
            if line.strip()
        ])
        
        # Ensure hashtags have space before them
        formatted = formatted.replace("#", " #").replace("  #", " #")
        
        return formatted.strip()
    
    async def schedule_optimal_time(self, post_text: str, post_id: str) -> Dict:
        """
        Determine optimal posting time based on audience activity
        
        LinkedIn best times: Tue-Thu, 9-11 AM ET
        """
        from datetime import timedelta
        
        now = datetime.now()
        
        # If it's before 9 AM, schedule for 9 AM today
        if now.hour < 9:
            schedule_time = now.replace(hour=9, minute=30, second=0)
        # If it's after 11 AM, schedule for 9 AM tomorrow
        elif now.hour >= 11:
            schedule_time = (now + timedelta(days=1)).replace(hour=9, minute=30, second=0)
        # Otherwise post in 5 minutes
        else:
            schedule_time = now + timedelta(minutes=5)
        
        # This method also needs access_token and user_id to call publish_post
        # For now, we'll assume it's called from main.py where these are available.
        # This part of the code needs to be updated in main.py as well.
        # For now, returning a placeholder for the call to publish_post
        return {"success": False, "error": "Schedule optimal time not fully implemented for new publish_post signature."}
