import os
import json
from typing import Dict, Any, List
from utils.gemini_config import GeminiConfig
from utils.logger import log_agent_action, log_error
from utils.json_parser import parse_llm_json_response

class ViralityAgent:
    """Enhanced virality scoring with stricter criteria for higher scores"""

    def __init__(self):
        self.model = GeminiConfig.get_model("scoring")

    async def score_post(self, post_text: str) -> Dict[str, Any]:
        """Score post virality with detailed analysis - STRICT SCORING"""
        try:
            prompt = f"""You are a STRICT LinkedIn engagement expert and data analyst. Analyze this post with RIGOROUS standards.

POST:
{post_text}

CRITICAL SCORING RULES:
- Score 90-100: EXCEPTIONAL - Top 1% of LinkedIn content, guaranteed viral
- Score 80-89: EXCELLENT - Top 5%, very high engagement potential  
- Score 70-79: GOOD - Above average, solid engagement
- Score 60-69: AVERAGE - Typical LinkedIn post
- Score <60: NEEDS IMPROVEMENT

Scoring criteria (each 0-100, be HONEST and STRICT):
1. Hook Strength: First line must STOP the scroll. Is it shocking, contrarian, or deeply relatable?
2. Value Delivery: Does it provide UNIQUE insights, not generic advice? Specific data/metrics?
3. Emotional Resonance: Does it trigger strong emotion (frustration, hope, curiosity)?
4. Call-to-Action: Clear, specific question that DEMANDS engagement?
5. Readability: Perfect formatting, optimal length (150-300 words), scannable?
6. Authority Signal: Demonstrates deep expertise with specific examples/results?
7. Shareability: Would a CTO forward this to their team? Why?
8. Hashtag Relevance: Strategic, not spammy (3-5 max)?

BONUS POINTS (+10 each, max +30):
- Uses specific metrics/data points
- Includes contrarian/unpopular opinion
- Ends with thought-provoking question
- Has clear problem→solution→result structure

LinkedIn-specific factors:
- Target audience: CTOs, Engineering Managers, Senior Engineers
- Best practices: Questions perform 2x better, lists get 1.5x engagement
- Optimal length: 150-300 words
- Avoid: Generic advice, humble brags, excessive hashtags

Return JSON (BE STRICT - most posts are 60-75):
{{
    "score": "overall_score_0_100 as integer (STRICT - average is 65)",
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
    "reasoning": "Overall assessment - be HONEST about weaknesses"
}}

Return ONLY valid JSON, no markdown. BE STRICT - don't inflate scores!"""

            response = await self.model.generate_content_async(prompt)
            
            result = parse_llm_json_response(response.text, self._default_score())

            log_agent_action("ViralityAgent", "Post scored", f"Score: {result.get('score', 0)}/100")
            return result

        except Exception as e:
            log_error(e, f"Virality scoring failed: {type(e).__name__}: {str(e)}")
            return self._default_score()

    def _default_score(self) -> Dict[str, Any]:
        """Default score when analysis fails"""
        return {
            "score": 50,
            "confidence": "LOW",
            "predicted_engagement_rate": "Unknown",
            "breakdown": {},
            "suggestions": [
                "Analysis temporarily unavailable - your post was still saved",
                "Try improving the post to trigger a new analysis",
                "Consider adding a strong hook, data points, or a clear CTA"
            ],
            "reasoning": "Scoring service temporarily unavailable - using default score"
        }