"""
Pydantic schema models for Admin Persona validation.

Ensures persona JSON files have the correct structure and types.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class PersonaIdentity(BaseModel):
    """Identity section of a persona configuration."""
    name: str = Field(..., description="Full name with credentials")
    title: str = Field(..., description="Professional title")
    summary: str = Field(..., description="Professional summary")
    core_expertise: List[str] = Field(default_factory=list, description="Areas of expertise")


class PersonaAudience(BaseModel):
    """Audience model for a persona."""
    industries: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    seniority_distribution: Dict[str, float] = Field(default_factory=dict)
    company_examples: List[str] = Field(default_factory=list)


class PersonaTone(BaseModel):
    """Tone profile for content generation."""
    keywords: List[str] = Field(default_factory=list, description="Tone keywords like 'structured', 'authoritative'")
    writing_patterns: Dict[str, bool] = Field(default_factory=dict)


class PersonaContentPreferences(BaseModel):
    """Content preferences for the persona."""
    main_themes: List[str] = Field(default_factory=list)
    post_types: List[str] = Field(default_factory=list)


class PersonaPublishing(BaseModel):
    """Publishing defaults for the persona."""
    default_channel: str = "linkedin_member"
    hashtags: List[str] = Field(default_factory=list)
    timezones_primary: List[str] = Field(default_factory=list)


class AdminPersona(BaseModel):
    """
    Complete Admin Persona model with all sections.
    
    Validates the full persona JSON structure.
    """
    id: str = Field(..., description="Unique persona identifier")
    version: str = Field(default="1.0.0", description="Persona config version")
    display_name: str = Field(..., description="Human-readable persona name")
    user_id: str = Field(..., description="Associated user ID")
    role: str = Field(default="admin", description="User role")
    identity: PersonaIdentity
    audience_model: PersonaAudience
    tone_profile: PersonaTone
    content_preferences: Optional[PersonaContentPreferences] = None
    publishing: PersonaPublishing
    
    class Config:
        extra = "allow"  # Allow additional fields for extensibility
