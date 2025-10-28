import os
import json
from typing import Dict, Any, List
from utils.gemini_config import GeminiConfig
from utils.logger import log_agent_action, log_error
from utils.json_parser import parse_llm_json_response # <-- MODIFICATION: Import new utility

class ViralityAgent:
    """Enhanced virality scoring with detailed breakdown"""

    def __init__(self):
        self.model = GeminiConfig.get_model("scoring")

    async def score_post(self, post_text: str) -> Dict[str, Any]:
        """Score post virality with detailed analysis"""
        try:
            prompt = f"""You are a LinkedIn engagement expert. Analyze this post and score its viral potential.

POST:
{post_text}

Scoring criteria (each 0-100):
1. Hook Strength: Does it grab attention in the first line?
2. Value Delivery: Does it provide actionable insights or unique perspective?
3. Emotional Resonance: Does it connect with the audience's challenges/aspirations?
4. Call-to-Action: Does it encourage engagement (comments, shares)?
5. Readability: Is it easy to scan and digest? (formatting, length)
6. Authority Signal: Does it demonstrate expertise without being preachy?
7. Shareability: Would someone forward this to a colleague?
8. Hashtag Relevance: Are hashtags strategic and not spammy?

LinkedIn-specific factors:
- Target audience: CTOs, Engineering Managers, Senior Engineers
- Best practices: Questions perform 2x better, lists get 1.5x engagement
- Optimal length: 150-300 words
- Timing: Technical content performs best Mon–Thu

Return JSON:
{{
    "score": "overall_score_0_100 as an integer",
    "confidence": "HIGH|MEDIUM|LOW",
    "predicted_engagement_rate": "percentage estimate with explanation",
    "breakdown": {{
        "hook_strength": {{"score": "X", "explanation": "..." }},
        "value_delivery": {{"score": "X", "explanation": "..." }},
        "emotional_resonance": {{"score": "X", "explanation": "..." }},
        "call_to_action": {{"score": "X", "explanation": "..." }},
        "readability": {{"score": "X", "explanation": "..." }},
        "authority_signal": {{"score": "X", "explanation": "..." }},
        "shareability": {{"score": "X", "explanation": "..." }},
        "hashtag_relevance": {{"score": "X", "explanation": "..." }}
    }},
    "suggestions": [
        "Specific actionable improvement 1",
        "Specific actionable improvement 2",
        "Specific actionable improvement 3"
    ],
    "reasoning": "Overall assessment and key insights"
}}

Return ONLY valid JSON, no markdown."""

            response = await self.model.generate_content_async(prompt)
            
            # --- MODIFICATION: Use the centralized JSON parser ---
            result = parse_llm_json_response(response.text, self._default_score())

            log_agent_action("ViralityAgent", "Post scored", f"Score: {result.get('score', 0)}/100")
            return result

        except Exception as e:
            log_error(e, "Virality scoring")
            return self._default_score()

    def _default_score(self) -> Dict[str, Any]:
        """Default score when analysis fails"""
        return {
            "score": 50,
            "confidence": "LOW",
            "predicted_engagement_rate": "Unknown",
            "breakdown": {},
            "suggestions": ["Unable to analyze - please try again"],
            "reasoning": "Analysis failed"
        }

    # --- MODIFICATION: Removed the local _parse_json_response method ---