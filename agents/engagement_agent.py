import google.generativeai as genai
import os
import json
from typing import Dict, List
from tools.linkedin_tools import LinkedInAPI
from database.supabase_client import supabase_client

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class EngagementAgent:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.linkedin = LinkedInAPI()
    
    async def analyze_comment(self, comment: Dict) -> Dict:
        """
        Analyze comment sentiment and determine response strategy
        
        Args:
            comment: {
                "id": "...",
                "author": "...",
                "text": "...",
                "post_context": "..."
            }
        
        Returns:
            {
                "should_respond": True/False,
                "response_text": "...",
                "reasoning": "...",
                "sentiment": "positive/neutral/negative",
                "intent": "question/praise/criticism/spam"
            }
        """
        
        prompt = f"""
        Analyze this LinkedIn comment and generate an appropriate response.
        
        COMMENT:
        Author: {comment.get('author', 'Unknown')}
        Text: "{comment['text']}"
        
        POST CONTEXT: {comment.get('post_context', 'Technical content about AI/ML')}
        
        ANALYSIS TASKS:
        1. Determine sentiment (positive/neutral/negative/spam)
        2. Identify intent (question/praise/feedback/criticism/spam)
        3. Decide if we should respond (skip spam, trolls, off-topic)
        4. If responding, generate authentic, helpful reply
        
        RESPONSE GUIDELINES:
        - Address commenter by first name if available
        - Be conversational but professional
        - Add value (answer question, share resource, or ask follow-up)
        - Keep under 100 words
        - Use "we" for team insights, "I" for personal opinions
        
        DO NOT RESPOND TO:
        - Spam or promotional comments
        - Off-topic arguments
        - Toxic or inflammatory comments
        
        OUTPUT (JSON):
        {{
          "should_respond": true/false,
          "response_text": "the actual reply (or null if not responding)",
          "reasoning": "why we are/aren't responding",
          "sentiment": "positive/neutral/negative/spam",
          "intent": "question/praise/feedback/criticism/spam",
          "confidence": 0.0-1.0
        }}
        """
        
        response = await self.model.generate_content_async(prompt)
        
        try:
            result = json.loads(response.text)
            return result
        except json.JSONDecodeError:
            return {
                "should_respond": False,
                "error": "Could not parse response",
                "raw": response.text
            }
    
    async def respond_to_comment(self, comment: Dict) -> Dict:
        """
        Process and respond to a single comment
        """
        
        # Analyze comment
        analysis = await self.analyze_comment(comment)
        
        if not analysis["should_respond"]:
            print(f"[SKIP] Skipping comment (reason: {analysis['reasoning']})")
            return {
                "responded": False,
                "reason": analysis["reasoning"]
            }
        
        # Post reply via LinkedIn API
        try:
            reply_result = self.linkedin.reply_to_comment(
                comment_urn=comment["id"],
                reply_text=analysis["response_text"]
            )
            
            if reply_result["success"]:
                # Log to database
                supabase_client.table("engagements").insert({
                    "comment_id": comment["id"],
                    "author_name": comment.get("author"),
                    "comment_text": comment["text"],
                    "our_response": analysis["response_text"],
                    "responded_at": "now()",
                    "sentiment": analysis["sentiment"],
                    "intent": analysis["intent"]
                }).execute()
                
                print(f"[OK] Replied to {comment.get('author')}")
                
                return {
                    "responded": True,
                    "response_text": analysis["response_text"]
                }
            else:
                return {
                    "responded": False,
                    "error": "LinkedIn API error"
                }
        
        except Exception as e:
            print(f"[X] Error responding: {str(e)}")
            return {
                "responded": False,
                "error": str(e)
            }
    
    async def monitor_recent_posts(self) -> List[Dict]:
        """
        Check last 3 posts for new comments
        """
        
        # Get recent published posts from database
        posts = supabase_client.table("posts") \
    .select("*") \
    .eq("status", "published") \
    .order("published_at", desc=False) \
    .limit(3) \
    .execute()
        
        all_comments = []
        
        for post in posts.data:
            if not post.get("linkedin_post_id"):
                continue
            
            # Fetch comments from LinkedIn
            comments = self.linkedin.get_comments(
                post_urn=f"urn:li:ugcPost:{post['linkedin_post_id']}"
            )
            
            for comment in comments:
                # Check if we've already responded
                existing = supabase_client.table("engagements") \
                    .select("*") \
                    .eq("comment_id", comment["id"]) \
                    .execute()
                
                if not existing.data:
                    # New comment - add to processing queue
                    all_comments.append({
                        "id": comment["id"],
                        "author": comment.get("author", {}).get("name"),
                        "text": comment.get("message", {}).get("text"),
                        "post_context": post.get("topic", "")
                    })
        
        return all_comments