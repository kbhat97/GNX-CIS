import os
from typing import Dict, List, Any
import json
from utils.gemini_config import GeminiConfig
# --- MODIFICATION: Import the new, correct tool ---
from tools.linkedin_publisher import linkedin_publisher
from database.supabase_client import get_linkedin_token
# --------------------------------------------------
from utils.logger import log_agent_action, log_error
from utils.json_parser import parse_llm_json_response

class HistoryAgent:
    """Analyzes past LinkedIn posts to understand user's style and performance"""

    def __init__(self):
        # --- MODIFICATION: Use the single, stateless publisher instance ---
        self.linkedin_api = linkedin_publisher
        # --------------------------------------------------------------
        self.model = GeminiConfig.get_model("analysis")

    # --- MODIFICATION: This method now requires user_id to fetch the correct token ---
    async def analyze_past_posts(self, user_id: str, limit: int = 10) -> Dict[str, Any]:
        """Fetch and analyze past LinkedIn posts for a specific user."""
        try:
            log_agent_action("HistoryAgent", "Fetching past posts", f"User: {user_id}, Limit: {limit}")
            
            # Get the user-specific token
            token_data = get_linkedin_token(user_id)
            if not token_data or "linkedin_access_token" not in token_data:
                log_agent_action("HistoryAgent", "No LinkedIn token for user, using default style", user_id)
                return self._default_style_profile()
            
            access_token = token_data["linkedin_access_token"]
            
            # Call the new publisher method with the token
            # Note: This requires the 'r_member_social' scope, which is restricted by LinkedIn.
            # The method will return an empty list if it fails, which is handled gracefully.
            past_posts = self.linkedin_api.get_user_posts(access_token, limit=limit)

            if not past_posts:
                log_agent_action("HistoryAgent", "No past posts found or API failed", "Using default style")
                return self._default_style_profile()

            posts_text = self._format_posts_for_analysis(past_posts)
            analysis_prompt = f"""Analyze these LinkedIn posts and provide insights:
{posts_text}
Provide a JSON response with:
1. "writing_style": Description of the author's unique voice and tone
2. "common_topics": List of frequently discussed topics
3. "post_structures": Common patterns (storytelling, listicles, questions, etc.)
4. "engagement_patterns": What types of posts get the most engagement
5. "avg_post_length": Typical word count range
6. "hashtag_strategy": How hashtags are typically used
7. "key_phrases": Recurring phrases or signature expressions
8. "improvement_areas": Suggestions for better engagement
Return ONLY valid JSON, no markdown formatting."""

            response = await self.model.generate_content_async(analysis_prompt)
            analysis = parse_llm_json_response(response.text, self._default_style_profile())
            log_agent_action("HistoryAgent", "Analysis complete", f"Style: {analysis.get('writing_style', 'N/A')[:50]}...")
            return analysis
        except Exception as e:
            log_error(e, "Historical analysis")
            return self._default_style_profile()

    def _format_posts_for_analysis(self, posts: List[Dict]) -> str:
        # ... (no change)
        formatted = []
        for i, post in enumerate(posts, 1):
            text = post.get('text', '')
            likes = post.get('likes', 0)
            comments = post.get('comments', 0)
            formatted.append(f"POST {i}:\n{text}\n\nEngagement: {likes} likes, {comments} comments\n---")
        return "\n".join(formatted)

    def _default_style_profile(self) -> Dict[str, Any]:
        # ... (no change)
        return {
            "writing_style": "Authoritative and quantitative. Writes as a hands-on AI and SAP program leader...",
            "common_topics": ["SAP S/4HANA Migration", "GRC & Compliance", "Predictive AI for Risk Management"],
            "post_structures": ["**Bolded Title/Hook** -> Problem Statement -> Solution -> Quantifiable Result -> Question."],
            "engagement_patterns": "Posts with specific project stories and metrics perform best.",
            "avg_post_length": "100-200 words",
            "hashtag_strategy": "Mix of broad (#SAPS4HANA) and niche (#SAPGRC) tags.",
            "key_phrases": ["De-risking", "GRC Readiness", "Predictive AI"],
            "improvement_areas": ["Leverage more metric-driven stories."]
        }