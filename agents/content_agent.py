import json
from typing import Dict, Any, List
from utils.gemini_config import GeminiConfig
from agents.history_agent import HistoryAgent
from utils.logger import log_agent_action, log_error
from utils.json_parser import parse_llm_json_response

class ContentAgent:
    """Generates and improves post content based on a topic and historical context."""
    
    def __init__(self):
        self.model = GeminiConfig.get_model("content")
        self.history_agent = HistoryAgent()

    def _flatten_list(self, data: List[Any]) -> List[str]:
        flat_list = []
        if not isinstance(data, list): return []
        for item in data:
            if isinstance(item, str): flat_list.append(item)
            elif isinstance(item, dict):
                for value in item.values():
                    flat_list.append(str(value))
                    break
        return flat_list

    async def generate_post_text(self, topic: str, use_history: bool, user_id: str) -> Dict[str, Any]:
        try:
            style_context = ""
            if use_history:
                style_profile = await self.history_agent.analyze_past_posts(user_id, limit=10)
                common_topics = self._flatten_list(style_profile.get('common_topics', []))
                post_structures = self._flatten_list(style_profile.get('post_structures', []))
                key_phrases = self._flatten_list(style_profile.get('key_phrases', []))
                style_context = f"""
HISTORICAL STYLE PROFILE (HOW I WRITE):
- Writing Style: {style_profile.get('writing_style', 'Professional')}
- Common Topics: {', '.join(common_topics)}
- Typical Structure: {', '.join(post_structures)}
- Engagement Patterns: {style_profile.get('engagement_patterns', 'Not available')}
- Average Length: {style_profile.get('avg_post_length', '150-250 words')}
- Hashtag Strategy: {style_profile.get('hashtag_strategy', 'Mix of broad and niche technical tags')}
- Key Phrases: {', '.join(key_phrases) or 'None identified'}
"""
            
            # --- THIS IS THE FIX: Remove the draconian limit, restore intelligence ---
            prompt = f"""You are KUNAL BHAT, PMP — an expert SAP transformation leader.
YOUR TASK: Create a high-impact, viral-potential LinkedIn post about: "{topic}"

POST REQUIREMENTS:
1. Narrative Structure: Start with a bold hook. Describe a clear business problem, the specific solution implemented, and the quantifiable result. End with a question.
2. Persona: Write in an authoritative, quantitative, and results-focused voice.
3. No Trigger Keywords: Do NOT use the literal words "Problem:", "Solution:", or "Result:". Weave these concepts into a natural narrative.
4. CRITICAL LENGTH GUIDELINE: The entire post must be under 1,300 characters to maximize readability and avoid API issues.
5. Hashtags: Include 5-7 strategic hashtags.

Return your response as a single, valid JSON object:
{{
    "post_text": "...",
    "reasoning": "..."
}}
Return ONLY the JSON object..."""
            # -----------------------------------------------------------------------

            response = await self.model.generate_content_async(prompt)
            error_payload = {"post_text": "Error generating content.", "reasoning": "JSON parsing failed."}
            result = parse_llm_json_response(response.text, error_payload)
            log_agent_action("ContentAgent", "Post text generated", f"Topic: {topic}")
            return result
        except Exception as e:
            log_error(e, "Content generation")
            return {"error": str(e), "post_text": "", "reasoning": "Failed to generate content."}

    async def improve_post_text(self, original_text: str, feedback: str) -> Dict[str, Any]:
        log_agent_action("ContentAgent", "Improving post text", f"Feedback: {feedback[:50]}...")
        prompt = f"""You are KUNAL BHAT, PMP...
YOUR TASK: Revise the following LinkedIn post based on the user's specific feedback...
ORIGINAL POST:\n---\n{original_text}\n---\nUSER FEEDBACK:\n---\n{feedback}\n---
REVISION REQUIREMENTS:
1. Apply the feedback directly.
2. Maintain the persona and narrative structure.
3. CRITICAL LENGTH GUIDELINE: Ensure the revised post is under 1,300 characters.

Return your response as a single, valid JSON object..."""
        try:
            response = await self.model.generate_content_async(prompt)
            error_payload = {"post_text": original_text, "reasoning": "Failed to improve content due to a parsing error."}
            result = parse_llm_json_response(response.text, error_payload)
            log_agent_action("ContentAgent", "Post text improved successfully")
            return result
        except Exception as e:
            log_error(e, "Improve post text")
            return {"error": str(e), "post_text": original_text, "reasoning": "Failed to improve content."}