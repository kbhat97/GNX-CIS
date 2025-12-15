"""
Persona Loader Module

Provides:
- safe_load_persona(): Load persona JSON with error handling
- load_persona_cached(): LRU-cached persona loading
- PersonaContextBuilder: Build prompts and context from persona data
- PersonaError: Structured error object for clean downstream handling
- is_admin_user(): Admin authorization check
"""

import json
import os
import logging
from functools import lru_cache
from typing import Dict, List, Optional, Union
from pathlib import Path

from .schema import AdminPersona

logger = logging.getLogger(__name__)

# Admin authorization - email allowlist
ADMIN_EMAILS = ["kunalsbhatt@gmail.com"]

# Path to personas directory
PERSONAS_DIR = Path(__file__).parent


class PersonaError:
    """
    Structured error object for persona loading failures.
    
    Allows clean downstream logic and telemetry.
    """
    def __init__(self, message: str, persona_id: str = ""):
        self.message = message
        self.persona_id = persona_id
        self.ok = False
    
    def __repr__(self) -> str:
        return f"PersonaError(persona_id='{self.persona_id}', message='{self.message}')"


class PersonaContextBuilder:
    """
    Builds prompt context from persona data.
    
    Provides methods to extract system prompt, hashtags, and audience summary.
    """
    
    SYSTEM_PROMPT_TEMPLATE = '''You are the Admin Persona AI for "{name}" inside the GNX Social Intelligence Platform.

YOUR JOB
- Help {name} create high-signal LinkedIn posts that:
  - Reflect their real professional identity and experience
  - Match their actual LinkedIn audience demographics
  - Support their thought-leadership positioning

IDENTITY (GROUND TRUTH)
- Name: {name}
- Role: {title}
- Summary: {summary}
- Core strengths: {expertise}

AUDIENCE REALITY (WHO READS THEIR POSTS)
- Industries: {industries}
- Locations: {locations}
- Seniority mix: {seniority}
- Companies: {companies}

TONE & STYLE
- Keywords: {tone_keywords}
- Use structured, clear, professional language
- Focus on real project experience, frameworks, and practical advice
- No hype, no generic fluff
- Include checklists, bullet points, numbered lists where helpful

═══════════════════════════════════════════════════════════════════
[PROHIBITED] ABSOLUTE PROHIBITIONS (VIOLATION = FAILURE)
═══════════════════════════════════════════════════════════════════

[X] NEVER use specific percentages like "25%", "30%", "40%", "15%"
[X] NEVER invent statistics or metrics
[X] NEVER write without personal experience anchoring

If you violate any of these, the post FAILS quality check.

═══════════════════════════════════════════════════════════════════
[REQUIRED] MANDATORY REQUIREMENTS (MUST BE IN EVERY POST)
═══════════════════════════════════════════════════════════════════

1. **PERSONAL EXPERIENCE ANCHOR** (REQUIRED - pick ONE)
   You MUST start or include ONE of these phrases verbatim:
   - "In the global SAP programs I've led..."
   - "From my 10+ years in S/4HANA transformations..."
   - "Leading enterprise programs across North America and APAC..."
   - "Working with Fortune 500 clients on digital transformation..."
   - "My experience delivering $3M-$4.5M SAP programs taught me..."
   
   [!] If you don't include personal experience = POST REJECTED

2. **METRICS FRAMING** (STRICT RULE)
   Instead of percentages, use:
   [+] "significant improvements"
   [+] "measurable gains"
   [+] "reduced overhead"
   [+] "faster time-to-value"
   [+] "industry leaders report..."
   [+] "organizations are seeing..."
   
   [X] NEVER: "25% increase", "30% reduction", "40% faster"

3. **MANDATORY HASHTAGS** (MUST USE THESE EXACT HASHTAGS)
   End EVERY post with these hashtags:
   {hashtags}
   
   You may add 1-2 topic-specific hashtags, but the above are REQUIRED.

4. **AUDIENCE BALANCE**
   - Write for BOTH senior leaders (48%) AND entry-level (21.7%)
   - Strategic insights for seniors + clear explanations for juniors

═══════════════════════════════════════════════════════════════════

WHEN WRITING POSTS
- Anchor ideas in real experience (without exaggeration)
- Make content useful for both senior leaders and entry-level professionals
- Use clear structures: numbered lists, bullet points, short sections
- Include a strong hook in first 1-2 lines
- End with a reflection or question for engagement

SAFETY & HONESTY
- Do not invent roles, companies, or achievements
- Keep it authentic and grounded
- No fabricated metrics or statistics'''

    def __init__(self, persona_data: Dict):
        """Initialize with validated persona data."""
        self.data = persona_data
        self._validate()
    
    def _validate(self) -> None:
        """Validate persona data using Pydantic model."""
        try:
            AdminPersona(**self.data)
        except Exception as e:
            logger.warning(f"Persona validation warning: {e}")
    
    @property
    def persona_id(self) -> str:
        return self.data.get("id", "unknown")
    
    @property
    def version(self) -> str:
        return self.data.get("version", "1.0.0")
    
    def system_prompt(self) -> str:
        """Generate full system prompt for persona."""
        identity = self.data.get("identity", {})
        audience = self.data.get("audience_model", {})
        tone = self.data.get("tone_profile", {})
        publishing = self.data.get("publishing", {})
        
        # Build seniority string
        seniority = audience.get("seniority_distribution", {})
        seniority_str = ", ".join([f"{k}: {v}%" for k, v in seniority.items()][:3])
        
        # Build hashtags string
        hashtags = publishing.get("hashtags", [])
        hashtags_str = ", ".join(hashtags) if hashtags else "#SAP, #Leadership, #DigitalTransformation"
        
        return self.SYSTEM_PROMPT_TEMPLATE.format(
            name=identity.get("name", "Admin"),
            title=identity.get("title", "Professional"),
            summary=identity.get("summary", "")[:200],
            expertise=", ".join(identity.get("core_expertise", [])[:5]),
            industries=", ".join(audience.get("industries", [])[:4]),
            locations=", ".join(audience.get("locations", [])[:3]),
            seniority=seniority_str or "Mixed",
            companies=", ".join(audience.get("company_examples", [])[:4]),
            tone_keywords=", ".join(tone.get("keywords", [])[:5]),
            hashtags=hashtags_str
        )
    
    def hashtag_list(self) -> List[str]:
        """Get persona-specific hashtags."""
        publishing = self.data.get("publishing", {})
        return publishing.get("hashtags", [])
    
    def audience_summary(self) -> str:
        """Get brief audience summary for logging/display."""
        audience = self.data.get("audience_model", {})
        industries = audience.get("industries", [])[:2]
        locations = audience.get("locations", [])[:2]
        return f"Industries: {', '.join(industries)} | Locations: {', '.join(locations)}"
    
    def get_display_name(self) -> str:
        """Get display name for UI."""
        return self.data.get("display_name", "Admin Persona")


def safe_load_persona(persona_id: str) -> Union[Dict, PersonaError]:
    """
    Load persona JSON with error handling.
    
    Returns:
        Dict: Persona data if successful
        PersonaError: Error object if loading fails
    """
    try:
        file_path = PERSONAS_DIR / f"{persona_id}.json"
        
        if not file_path.exists():
            return PersonaError(f"Persona file not found: {file_path}", persona_id)
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Validate with Pydantic
        AdminPersona(**data)
        
        logger.info(f"[OK] Loaded persona: {persona_id} v{data.get('version', '?')}")
        return data
        
    except json.JSONDecodeError as e:
        msg = f"Invalid JSON in persona file: {e}"
        logger.error(msg)
        return PersonaError(msg, persona_id)
    except Exception as e:
        msg = f"Persona load error: {e}"
        logger.error(msg)
        return PersonaError(msg, persona_id)


@lru_cache(maxsize=5)
def load_persona_cached(persona_id: str) -> Optional[PersonaContextBuilder]:
    """
    LRU-cached persona loading.
    
    Speeds up dashboard by avoiding repeated file I/O.
    Returns PersonaContextBuilder or None on failure.
    """
    result = safe_load_persona(persona_id)
    
    if isinstance(result, PersonaError):
        logger.warning(f"Cached persona load failed: {result.message}")
        return None
    
    return PersonaContextBuilder(result)


def is_admin_user(current_user: Dict) -> bool:
    """
    Check if current user is an admin based on email allowlist.
    
    Args:
        current_user: User dict with 'email' field
        
    Returns:
        True if user is admin, False otherwise
    """
    email = current_user.get("email", "")
    return email.lower() in [e.lower() for e in ADMIN_EMAILS]


def clear_persona_cache() -> None:
    """Clear the LRU cache (useful for testing or reloading)."""
    load_persona_cached.cache_clear()
    logger.info("Persona cache cleared")
