import json
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent
from utils.gemini_config import GeminiConfig, DIVERSITY_CONFIG
from utils.logger import log_agent_action, log_error
from utils.json_parser import parse_llm_json_response

# Hook history for content diversity (IMP-003/IMP-004)
from utils.hook_history import HookHistoryManager, extract_hook_from_content

# Persona support
try:
    from personas import load_persona_cached, PersonaContextBuilder
    PERSONA_AVAILABLE = True
except ImportError:
    PERSONA_AVAILABLE = False
    load_persona_cached = None
    PersonaContextBuilder = None

# ═══════════════════════════════════════════════════════════════════════════════
# STYLE_DEFINITIONS: Enhanced for LinkedIn content diversity (IMP-002)
# Each style has: instructions, sentence_patterns, vocabulary, rhetorical_moves
# Optimized for LinkedIn B2B audience engagement
# ═══════════════════════════════════════════════════════════════════════════════
STYLE_DEFINITIONS = {
    "professional": {
        "name": "Professional",
        "instructions": "Use formal but accessible language. Focus on expertise and credibility. Include data points and industry insights. Maintain executive-level tone. Speak as a trusted advisor to peers and decision-makers.",
        "sentence_patterns": [
            "After leading [X] projects, here's what I've learned:",
            "The data from [X] companies reveals a pattern:",
            "What separates high-performing teams from the rest:",
            "A lesson from advising Fortune 500 leaders:",
            "The #1 mistake I see executives make:"
        ],
        "vocabulary": {
            "use": ["strategic", "insight", "framework", "ROI", "stakeholder", "alignment", "execution", "leadership"],
            "avoid": ["honestly", "literally", "like", "stuff", "things", "kinda", "sorta"]
        },
        "rhetorical_moves": ["establish credibility", "cite business evidence", "provide actionable takeaway", "invite professional dialogue"]
    },
    "technical": {
        "name": "Technical",
        "instructions": "Include specific numbers, metrics, and technical details. Use industry terminology appropriately. Focus on implementation and results. Share practical knowledge that peers can apply immediately.",
        "sentence_patterns": [
            "We reduced [metric] by X% — here's the approach:",
            "The stack that powers [outcome]:",
            "Step-by-step: How we solved [problem]",
            "Before: [old way]. After: [new way]. Results:",
            "The technical decision that saved us [X]:"
        ],
        "vocabulary": {
            "use": ["architecture", "implementation", "benchmark", "performance", "scalability", "pipeline", "automation", "integration"],
            "avoid": ["magic", "easy fix", "silver bullet", "hack", "trick"]
        },
        "rhetorical_moves": ["define the problem", "show the solution", "quantify impact", "share learnings for others"]
    },
    "inspirational": {
        "name": "Inspirational",
        "instructions": "Share authentic career lessons and growth moments. Use emotionally resonant language that connects. Focus on overcoming professional challenges. End with actionable encouragement for the reader's journey.",
        "sentence_patterns": [
            "5 years ago, I almost quit. Here's what happened:",
            "The career advice that changed my trajectory:",
            "What I wish someone told me at the start of my career:",
            "To everyone feeling stuck in their role right now:",
            "The rejection that led to my biggest opportunity:"
        ],
        "vocabulary": {
            "use": ["journey", "growth", "resilience", "breakthrough", "purpose", "potential", "mentor", "opportunity"],
            "avoid": ["hustle culture", "grind", "crush it", "boss babe", "10x"]
        },
        "rhetorical_moves": ["share professional vulnerability", "describe the turning point", "extract actionable lesson", "empower reader's career"]
    },
    "thought_leadership": {
        "name": "Thought Leadership",
        "instructions": "Take a strong, evidence-backed stance on industry trends. Challenge conventional business wisdom. Make bold but reasoned predictions. Position yourself as someone who sees what others miss.",
        "sentence_patterns": [
            "Unpopular opinion in [industry]:",
            "The industry is wrong about [X]. Here's the data:",
            "In 2-3 years, [prediction]. Here's why:",
            "Everyone's doing [X]. Smart teams are doing [Y].",
            "The hidden cost of [common practice] nobody talks about:"
        ],
        "vocabulary": {
            "use": ["paradigm shift", "disruption", "first principles", "contrarian", "evidence-based", "trend", "future-proof", "innovation"],
            "avoid": ["everyone knows", "obviously", "just my opinion", "I think maybe"]
        },
        "rhetorical_moves": ["state contrarian position", "back with evidence", "present alternative approach", "challenge reader to rethink"]
    },
    "storytelling": {
        "name": "Storytelling",
        "instructions": "Open with a specific workplace moment or career scene. Use vivid details that transport the reader. Build narrative tension around a professional challenge. Connect the story to a universal business lesson.",
        "sentence_patterns": [
            "Monday morning. The email that changed everything:",
            "3 years ago, I walked into a meeting that would define my career.",
            "The client said 3 words: '[quote]'. I'll never forget what happened next.",
            "It was my first week as [role]. I made a mistake that taught me:",
            "The conversation with my mentor that I replay in my head:"
        ],
        "vocabulary": {
            "use": ["moment", "realized", "learned", "conversation", "decision", "finally", "turning point", "lesson"],
            "avoid": ["basically", "so anyway", "long story short", "blah blah blah"]
        },
        "rhetorical_moves": ["set the workplace scene", "introduce the challenge", "build professional tension", "resolve with transferable insight"]
    }
}

class ContentAgent(BaseAgent):
    """Generates and improves post content based on a topic and historical context."""
    
    def __init__(self, supabase_client=None):
        super().__init__("ContentAgent")
        self.model = GeminiConfig.get_model("content")
        # Initialize hook history manager if supabase client provided
        self.hook_manager = HookHistoryManager(supabase_client) if supabase_client else None
    
    async def _get_prohibited_hooks_section(self, user_id: str) -> str:
        """Fetch recent hooks and format as PROHIBITED_HOOKS prompt section (IMP-004)"""
        if not self.hook_manager or not user_id:
            return ""
        try:
            recent_hooks = await self.hook_manager.get_recent_hooks(user_id, limit=5)
            return self.hook_manager.format_prohibited_hooks(recent_hooks)
        except Exception as e:
            log_error(e, "Failed to get prohibited hooks")
            return ""  # Non-critical, continue without hook exclusion
    
    async def _save_hook(self, user_id: str, post_text: str) -> None:
        """Extract and save the hook from generated content (IMP-004)"""
        if not self.hook_manager or not user_id or not post_text:
            return
        try:
            hook = extract_hook_from_content(post_text)
            if hook:
                await self.hook_manager.save_hook(user_id, hook)
                log_agent_action("ContentAgent", "[HOOK] Saved hook to history", f"Hook: {hook[:50]}...")
        except Exception as e:
            log_error(e, "Failed to save hook")  # Non-critical

    # IMP-006: Multi-candidate generation settings
    MULTI_CANDIDATE_COUNT = 2  # N=2 candidates for premium users
    
    def _score_hook_quality(self, post_text: str) -> float:
        """
        Score the hook quality of a generated post (IMP-006).
        Higher score = better hook. Used for candidate selection.
        
        Scoring factors:
        - Length (prefer 60-120 chars for first line)
        - Contains question or strong statement
        - No generic phrases
        - Proper formatting
        """
        if not post_text:
            return 0.0
        
        first_line = post_text.split("\n")[0].replace("**", "").strip()
        score = 50.0  # Base score
        
        # Length scoring (prefer 60-120 chars)
        length = len(first_line)
        if 60 <= length <= 120:
            score += 20
        elif 40 <= length <= 150:
            score += 10
        elif length < 20 or length > 200:
            score -= 10
        
        # Question hook bonus
        if "?" in first_line:
            score += 15
        
        # Strong statement markers
        strong_markers = [":", "—", "...", "here's", "this is", "the #1", "unpopular"]
        if any(marker in first_line.lower() for marker in strong_markers):
            score += 10
        
        # Penalize generic starts
        generic_starts = ["i think", "in my opinion", "hello", "hi everyone", "today i want"]
        if any(first_line.lower().startswith(start) for start in generic_starts):
            score -= 20
        
        # Has emoji (subtle bonus)
        if any(ord(c) > 127 for c in first_line):
            score += 5
        
        return max(0, min(100, score))  # Clamp to 0-100

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

    async def generate_post_text(
        self, 
        topic: str, 
        use_history: bool, 
        user_id: str, 
        style: str = "Professional", 
        profile: Dict[str, Any] = None,
        persona_id: Optional[str] = None,
        generate_candidates: bool = False  # IMP-006: Opt-in multi-candidate
    ) -> Dict[str, Any]:
        try:
            style_context = ""
            if use_history:
                # TODO: Replace this with a message bus request to the HistoryAgent
                log_agent_action("ContentAgent", "History analysis via message bus (not implemented)", f"User ID: {user_id}")

            # IMP-004: Fetch prohibited hooks to prevent repetition
            prohibited_hooks_section = await self._get_prohibited_hooks_section(user_id)

            # Get detailed style instructions
            style_instructions = self._get_style_instructions(style)
            
            # Persona-aware generation
            persona_builder: Optional[PersonaContextBuilder] = None
            persona_system_prompt = ""
            persona_hashtags = []
            
            if persona_id and PERSONA_AVAILABLE and load_persona_cached:
                persona_builder = load_persona_cached(persona_id)
                if persona_builder:
                    persona_system_prompt = persona_builder.system_prompt()
                    persona_hashtags = persona_builder.hashtag_list()
                    log_agent_action(
                        "ContentAgent", 
                        "[PERSONA] Persona loaded", 
                        f"persona_id={persona_id}, version={persona_builder.version}"
                    )
                else:
                    log_agent_action("ContentAgent", "[WARN] Persona load failed, using fallback", f"persona_id={persona_id}")
            
            # Build persona context from profile (includes onboarding data)
            persona_name = "Professional thought leader"
            persona_traits = []
            target_audience = "Business professionals"
            writing_tone = "Professional & Engaging"
            industry = ""
            primary_goal = ""
            user_topics = []
            
            if profile:
                persona_traits = profile.get('personality_traits', [])
                if persona_traits:
                    persona_name = persona_traits[0]
                target_audience = profile.get('target_audience', target_audience)
                writing_tone = profile.get('writing_tone', writing_tone)
                
                # New onboarding fields
                industry = profile.get('industry', '')
                primary_goal = profile.get('primary_goal', '')
                user_topics = profile.get('common_topics', []) or profile.get('topics', [])
                
                log_agent_action("ContentAgent", "[PROFILE] Using profile data", 
                    f"Industry: {industry}, Goal: {primary_goal}, Style: {writing_tone}")

            # Enhanced prompt for viral LinkedIn content with Gemini 2.5 Flash
            # Build hashtag instruction based on persona
            if persona_hashtags:
                hashtag_instruction = f"Include these hashtags: {', '.join(persona_hashtags)}"
            else:
                hashtag_instruction = "Include 5-7 relevant hashtags at the end"
            
            # Build industry/goal context if available
            context_lines = []
            if industry:
                context_lines.append(f"INDUSTRY: {industry}")
            if primary_goal:
                context_lines.append(f"GOAL: {primary_goal}")
            if user_topics:
                context_lines.append(f"FOCUS TOPICS: {', '.join(user_topics[:5])}")
            
            user_context = "\n".join(context_lines) if context_lines else "CONTEXT: General business professional"
            
            # Build the main prompt
            base_prompt = f"""You are an expert LinkedIn content strategist creating high-engagement posts.

TOPIC: "{topic}"

═══════════════════════════════════════════════════════════════════
STYLE: {style.title()}
STYLE INSTRUCTIONS: {style_instructions}
═══════════════════════════════════════════════════════════════════
{prohibited_hooks_section}
{user_context}
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
   - EMOJI LIMIT: Use exactly 1-2 emojis MAX in the entire post (not in every line). Too many reduces authority.
   - DO NOT USE MARKDOWN: LinkedIn does NOT render **bold**, *italic*, `code`, or any markdown. Just write plain text.
   - Use ALL CAPS sparingly for emphasis instead of asterisks (e.g., "CRITICAL:" or "GAME CHANGER:")
   - Keep total length under 1,300 characters

5. **HASHTAGS**: {hashtag_instruction}

IMPORTANT: Follow the STYLE INSTRUCTIONS exactly. The content must feel authentically {style.lower()}.

Return ONLY valid JSON:
{{
    "post_text": "your complete post here with formatting",
    "reasoning": "brief explanation of hook choice and structure"
}}

Focus ONLY on creating the best possible content. Scoring will be handled separately.
"""
            
            # Prepend persona system prompt if available (this is the key persona injection)
            if persona_system_prompt:
                prompt = f"{persona_system_prompt}\n\n---\n\nNow generate a post based on the following request:\n\n{base_prompt}"
            else:
                prompt = base_prompt

            # IMP-006: Multi-candidate generation (opt-in for premium users)
            if generate_candidates:
                import asyncio
                log_agent_action("ContentAgent", "[MULTI] Generating N=2 candidates", f"Topic: {topic}")
                
                # Generate N candidates concurrently
                tasks = [
                    self.model.generate_content_async(prompt, generation_config=DIVERSITY_CONFIG)
                    for _ in range(self.MULTI_CANDIDATE_COUNT)
                ]
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Parse and score all candidates
                candidates = []
                error_payload = {"post_text": "", "reasoning": "Failed"}
                
                for i, resp in enumerate(responses):
                    if isinstance(resp, Exception):
                        log_agent_action("ContentAgent", f"[MULTI] Candidate {i+1} failed: {resp}")
                        continue
                    parsed = parse_llm_json_response(resp.text, error_payload)
                    if parsed.get("post_text"):
                        score = self._score_hook_quality(parsed["post_text"])
                        candidates.append({"result": parsed, "score": score})
                        log_agent_action("ContentAgent", f"[MULTI] Candidate {i+1} score: {score:.1f}")
                
                # Select best candidate
                if candidates:
                    best = max(candidates, key=lambda x: x["score"])
                    result = best["result"]
                    result["candidate_count"] = len(candidates)
                    result["winning_score"] = best["score"]
                    log_agent_action("ContentAgent", f"[MULTI] Selected best candidate (score: {best['score']:.1f})")
                else:
                    result = {"post_text": "Error: All candidates failed.", "reasoning": "Multi-candidate generation failed."}
            else:
                # Standard single generation
                response = await self.model.generate_content_async(prompt, generation_config=DIVERSITY_CONFIG)
                error_payload = {"post_text": "Error generating content.", "reasoning": "JSON parsing failed."}
                result = parse_llm_json_response(response.text, error_payload)
            
            # Enhanced logging with persona info
            persona_info = f", persona={persona_id}" if persona_id else ""
            candidates_info = f", candidates={result.get('candidate_count', 1)}" if generate_candidates else ""
            log_agent_action("ContentAgent", "[OK] Post text generated with Gemini 2.5 Flash", f"Topic: {topic}, Style: {style}{persona_info}{candidates_info}")
            
            # IMP-004: Save the hook for future diversity
            if result.get("post_text") and not result.get("error"):
                await self._save_hook(user_id, result["post_text"])
            
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
            response = await self.model.generate_content_async(prompt, generation_config=DIVERSITY_CONFIG)
            error_payload = {"post_text": original_text, "reasoning": "Failed to improve content due to a parsing error."}
            result = parse_llm_json_response(response.text, error_payload)
            log_agent_action("ContentAgent", "[OK] Post text improved successfully")
            return result
        except Exception as e:
            log_error(e, "Improve post text")
            return {"error": str(e), "post_text": original_text, "reasoning": "Failed to improve content."}