import json
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from utils.gemini_config import GeminiConfig
from utils.logger import log_agent_action, log_error
from utils.json_parser import parse_llm_json_response

# Detailed style definitions to prevent hallucination
STYLE_DEFINITIONS = {
    "professional": {
        "name": "Professional",
        "instructions": "Use formal but accessible language. Focus on expertise and credibility. Include data points and industry insights. Maintain executive-level tone. Avoid slang or overly casual expressions. Write as a respected industry expert addressing peers."
    },
    "technical": {
        "name": "Technical",
        "instructions": "Include specific numbers, metrics, and technical details. Use industry terminology appropriately. Focus on how/why things work. Include frameworks, methodologies, or processes. Reference tools, technologies, or systems. Be precise and data-driven."
    },
    "inspirational": {
        "name": "Inspirational",
        "instructions": "Share personal growth stories or lessons learned. Use emotionally resonant language. Include calls to action for self-improvement. Focus on overcoming challenges. End with hope or a forward-looking message. Make readers feel motivated to take action."
    },
    "thought_leadership": {
        "name": "Thought Leadership",
        "instructions": "Take a strong, possibly controversial stance. Challenge conventional wisdom. Make bold predictions about the future. Position yourself as ahead of the curve. Back up claims with unique insights or experience. Be provocative but substantive."
    },
    "storytelling": {
        "name": "Storytelling",
        "instructions": "Open with a specific moment or scene. Use sensory details and dialogue where appropriate. Build tension and resolution. Connect personal experience to broader lessons. Make readers feel like they're there with you. Use narrative arc."
    }
}

class ContentAgent(BaseAgent):
    """Generates and improves post content based on a topic and historical context."""
    
    def __init__(self):
        super().__init__("ContentAgent")
        self.model = GeminiConfig.get_model("content")

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
    
    def _get_style_instructions(self, style: str) -> str:
        """Get detailed instructions for the requested style"""
        style_key = style.lower().replace(" ", "_")
        if style_key in STYLE_DEFINITIONS:
            return STYLE_DEFINITIONS[style_key]["instructions"]
        # Fallback to professional if unknown style
        return STYLE_DEFINITIONS["professional"]["instructions"]

    async def generate_post_text(self, topic: str, use_history: bool, user_id: str, style: str = "Professional", profile: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            style_context = ""
            if use_history:
                # TODO: Replace this with a message bus request to the HistoryAgent
                log_agent_action("ContentAgent", "History analysis via message bus (not implemented)", f"User ID: {user_id}")

            # Get detailed style instructions
            style_instructions = self._get_style_instructions(style)
            
            # Build persona context
            persona_name = "Professional thought leader"
            persona_traits = []
            target_audience = "Business professionals"
            writing_tone = "Professional & Engaging"
            
            if profile:
                persona_traits = profile.get('personality_traits', [])
                if persona_traits:
                    persona_name = persona_traits[0]
                target_audience = profile.get('target_audience', target_audience)
                writing_tone = profile.get('writing_tone', writing_tone)

            # Enhanced prompt for viral LinkedIn content with Gemini 2.5 Flash
            prompt = f"""You are an expert LinkedIn content strategist creating high-engagement posts.

TOPIC: "{topic}"

═══════════════════════════════════════════════════════════════════
STYLE: {style.title()}
STYLE INSTRUCTIONS: {style_instructions}
═══════════════════════════════════════════════════════════════════

PERSONA: {persona_name}
TONE: {writing_tone}
AUDIENCE: {target_audience}

CREATE A VIRAL LINKEDIN POST WITH:

1. **HOOK (First Line)**: CRITICAL - VARY YOUR HOOK STYLE! Choose the BEST pattern for this specific topic:
   - Shocking statistic: "95% of [industry] leaders are making this mistake..."
   - Personal story: "3 years ago, I made a decision that changed everything..."
   - Controversial take: "Unpopular opinion: [bold statement]"
   - Question hook: "What if I told you [surprising fact]?"
   - Pattern interrupt: "Stop doing [common practice]. Here's why..."
   - Curiosity gap: "I just discovered something that will change [industry]..."
   - Bold prediction: "In 2 years, [bold prediction about industry]..."
   - Confession: "I'll admit it: I was wrong about [topic]..."
   - Observation: "Something strange is happening in [industry]..."
   - Direct address: "Dear [target audience], we need to talk about [issue]..."
   - News reaction: "Everyone is talking about [news], but they're missing the real story..."
   - Myth busting: "The biggest lie in [industry]: [common belief]"
   
   **CRITICAL**: Rotate between different hooks - avoid repeating the same pattern!
   
2. **BODY (Problem → Solution → Result)**:
   - Problem: Describe a relatable pain point (2-3 lines)
   - Solution: Share your unique approach or insight (3-4 lines)
   - Result: Quantify the impact with specific metrics (2-3 lines)

3. **CALL TO ACTION**: End with an engaging question to drive comments

4. **FORMATTING**:
   - Use line breaks for readability (max 2-3 sentences per paragraph)
   - Add emojis strategically (2-3 max, not in every line)
   - Bold key phrases with **asterisks**
   - Keep total length under 1,300 characters

5. **HASHTAGS**: Include 5-7 relevant hashtags at the end

IMPORTANT: Follow the STYLE INSTRUCTIONS exactly. The content must feel authentically {style.lower()}.

Return ONLY valid JSON:
{{
    "post_text": "your complete post here with formatting",
    "reasoning": "brief explanation of hook choice and structure"
}}"""

            response = await self.model.generate_content_async(prompt)
            error_payload = {"post_text": "Error generating content.", "reasoning": "JSON parsing failed."}
            result = parse_llm_json_response(response.text, error_payload)
            log_agent_action("ContentAgent", "✅ Post text generated with Gemini 2.5 Flash", f"Topic: {topic}, Style: {style}")
            return result
        except Exception as e:
            log_error(e, "Content generation")
            return {"error": str(e), "post_text": "", "reasoning": "Failed to generate content."}

    async def improve_post_text(self, original_text: str, feedback: str) -> Dict[str, Any]:
        log_agent_action("ContentAgent", "Improving post text", f"Feedback: {feedback[:50]}...")
        prompt = f"""You are an expert LinkedIn content strategist.

YOUR TASK: Revise the following LinkedIn post based on the user's specific feedback.

ORIGINAL POST:
---
{original_text}
---

USER FEEDBACK:
---
{feedback}
---

REVISION REQUIREMENTS:
1. Apply the feedback directly and precisely
2. Maintain the engaging tone and narrative structure
3. Keep the post under 1,300 characters
4. Preserve any successful hooks or calls-to-action
5. Improve formatting and readability

Return ONLY valid JSON:
{{
    "post_text": "your revised post here",
    "reasoning": "brief explanation of changes made"
}}"""
        try:
            response = await self.model.generate_content_async(prompt)
            error_payload = {"post_text": original_text, "reasoning": "Failed to improve content due to a parsing error."}
            result = parse_llm_json_response(response.text, error_payload)
            log_agent_action("ContentAgent", "✅ Post text improved successfully")
            return result
        except Exception as e:
            log_error(e, "Improve post text")
            return {"error": str(e), "post_text": original_text, "reasoning": "Failed to improve content."}