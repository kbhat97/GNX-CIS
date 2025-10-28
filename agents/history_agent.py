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

            if no41	                log_agent_action("HistoryAgent", "No past posts found or API failed", "Using default style")
42	                return self._default_style_profile()
43	
44	            posts_text = self._format_posts_for_analysis(past_posts)
45	            analysis_prompt = f"""Analyze these LinkedIn posts and provide insights:
46	{posts_text}
47	Provide a JSON response with:
48	1. "brand_voice_summary": A 1-2 sentence summary of the author's overall persona and voice.
49	2. "writing_style": Description of the author's unique voice and tone.
50	3. "common_topics": List of frequently discussed topics.
51	4. "post_structures": Common patterns (storytelling, listicles, questions, etc.)
52	5. "engagement_patterns": What types of posts get the most engagement.
53	6. "avg_post_length": Typical word count range.
54	7. "hashtag_strategy": How hashtags are typically used.
55	8. "key_phrases": Recurring phrases or signature expressions.
56	9. "improvement_areas": Suggestions for better engagement.
57	Return ONLY valid JSON, no markdown formatting.
58	The final JSON object MUST also include: "personality_vector": [0.1, 0.2, 0.3] (placeholder for vector embedding)"""
59	            response = await self.model.generate_content_async(analysis_prompt)
60	            analysis = parse_llm_json_response(response.text, self._default_style_profile())toryAgent", "Analysis complete", f"Style: {analysis.get('writing_style', 'N/A')[:50]}...")
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