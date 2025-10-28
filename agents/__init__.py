# agents/__init__.py
"""Expose agent classes without importing them eagerly to avoid circular imports."""

__all__ = [
    "ContentAgent",
    "ViralityAgent",
    "PublisherAgent",
    "EngagementAgent",
    "ReflectorAgent",
]

# Lazy-load attributes to avoid import-time side effects and circular imports (PEP 562)
def __getattr__(name: str):
    if name == "ContentAgent":
        from .content_agent import ContentAgent
        return ContentAgent
    if name == "ViralityAgent":
        from .virality_agent import ViralityAgent
        return ViralityAgent
    if name == "PublisherAgent":
        from .publisher_agent import PublisherAgent
        return PublisherAgent
    if name == "EngagementAgent":
        from .engagement_agent import EngagementAgent
        return EngagementAgent
    if name == "ReflectorAgent":
        from .reflector_agent import ReflectorAgent
        return ReflectorAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
