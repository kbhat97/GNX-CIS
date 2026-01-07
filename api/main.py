"""
FastAPI Backend for GNX Content Intelligence System
Provides REST API endpoints for the glassmorphic frontend
"""
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.content_agent import ContentAgent
from agents.virality_agent import ViralityAgent
from utils.gemini_config import GeminiConfig
from utils.sanitizer import sanitize_topic, sanitize_feedback
from utils.content_filter import is_safe_for_generation
from utils.image_generator import create_branded_image, generate_ai_image

# URL validation for image security
from urllib.parse import urlparse

# Trusted domains for external image URLs
TRUSTED_IMAGE_DOMAINS = [
    "ijwmgwirhorksepabgpj.supabase.co",  # Your Supabase project
    # Add other trusted CDN domains as needed
]


def is_trusted_url(url: str) -> bool:
    """Validate that URL is from a trusted domain."""
    try:
        parsed = urlparse(url)
        return parsed.netloc in TRUSTED_IMAGE_DOMAINS
    except Exception:
        return False


def resolve_image_url(image_path: str) -> str:
    """
    Convert image path to URL with security validation.
    
    Args:
        image_path: Either a full URL or local file path
        
    Returns:
        Safe URL to serve to clients
        
    Raises:
        ValueError: If URL is from an untrusted domain
    """
    if image_path.startswith('http://') or image_path.startswith('https://'):
        if not is_trusted_url(image_path):
            # Log the untrusted URL for monitoring but don't expose to client
            print(f"[SECURITY] Untrusted image URL domain detected: {urlparse(image_path).netloc}")
            raise ValueError(f"Untrusted image URL domain")
        return image_path
    else:
        # Local path - convert to static URL
        filename = os.path.basename(image_path)
        return f"/static/outputs/{filename}"


def safe_resolve_image_url(image_path: str) -> str:
    """
    Safely resolve image URL with fallback to local path.
    
    For external URLs from untrusted domains, falls back to constructing
    a local static path. Note: This may result in a 404 if the file doesn't
    exist locally, but this is safe from a security perspective - it prevents
    serving content from untrusted external sources.
    
    Args:
        image_path: Either a full URL or local file path
        
    Returns:
        Safe URL - either the validated external URL or a local static path
    """
    try:
        return resolve_image_url(image_path)
    except ValueError as url_err:
        print(f"[SECURITY] {url_err} - falling back to local path")
        filename = os.path.basename(image_path)
        return f"/static/outputs/{filename}"

# Initialize FastAPI app
app = FastAPI(
    title="GNX Content Intelligence API",
    description="AI-Powered LinkedIn Content Generation API",
    version="2.1.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving generated images
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
os.makedirs(os.path.join(static_dir, "outputs"), exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Initialize agents
content_agent = None
virality_agent = None

def get_agents():
    """Initialize agents lazily"""
    global content_agent, virality_agent
    if content_agent is None:
        content_agent = ContentAgent()
        virality_agent = ViralityAgent()
    return content_agent, virality_agent


# ═══════════════════════════════════════════════════════════════════
# Request/Response Models
# ═══════════════════════════════════════════════════════════════════

class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=2000, description="Topic to generate content about")
    style: str = Field(default="professional", description="Writing style")
    persona: Optional[str] = Field(default=None, description="Optional persona to write as")
    generate_image: bool = Field(default=False, description="Whether to generate AI image (set True only on final confirmation)")

class ImproveRequest(BaseModel):
    original_content: str = Field(..., description="Original post content to improve")
    feedback: str = Field(..., description="Feedback for improvement")

class GenerateImageRequest(BaseModel):
    content: str = Field(..., description="Post content to create image for")
    style: str = Field(default="professional", description="Writing style for image template")

class PostResponse(BaseModel):
    id: str
    content: str
    hook: str
    virality_score: int
    score_breakdown: Dict[str, Any]
    suggestions: List[str]
    timestamp: str
    topic: str
    style: str
    image_url: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


# ═══════════════════════════════════════════════════════════════════
# API Endpoints
# ═══════════════════════════════════════════════════════════════════

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="2.1.0",
        timestamp=datetime.now().isoformat()
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """Simple health check for frontend"""
    return HealthResponse(
        status="healthy",
        version="2.1.0",
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """API health check"""
    return HealthResponse(
        status="healthy",
        version="2.1.0",
        timestamp=datetime.now().isoformat()
    )


@app.post("/api/generate", response_model=PostResponse)
async def generate_post(request: GenerateRequest):
    """
    Generate a new LinkedIn post with virality scoring
    """
    try:
        # Sanitize input
        clean_topic = sanitize_topic(request.topic)
        
        # Check content safety
        is_safe, reason = is_safe_for_generation(clean_topic)
        if not is_safe:
            raise HTTPException(status_code=400, detail=f"Content rejected: {reason}")
        
        # Get agents
        content_agent, virality_agent = get_agents()
        
        # Build profile from persona if provided
        profile = None
        if request.persona:
            profile = {
                "personality_traits": [request.persona],
                "writing_tone": request.style,
                "target_audience": "Business professionals"
            }
        
        # Generate content (async method)
        post_result = await content_agent.generate_post_text(
            topic=clean_topic,
            use_history=False,
            user_id="api_user",
            style=request.style,
            profile=profile
        )
        
        post_text = post_result.get("post_text", "")
        if not post_text:
            raise HTTPException(status_code=500, detail="Failed to generate content")
        
        # Score the content (async method)
        score_result = await virality_agent.score_post(post_text)
        
        # Generate image ONLY if explicitly requested (deferred generation for cost savings)
        image_url = None
        if request.generate_image:
            try:
                author_name = request.persona or "GNX Content Intelligence"
                hook = post_text.split('\n')[0] if post_text else ""
                
                # Try Nano Banana AI image generation first (with full content for dynamic prompts)
                print(f"[IMAGE] User requested image generation for style: {request.style}")
                image_path = await generate_ai_image(
                    hook_text=hook,
                    topic=clean_topic,
                    style=request.style,
                    full_content=post_text  # Pass full content for smarter image generation
                )
                
                # Fallback to static branded image if AI fails
                if not image_path:
                    print("Falling back to static branded image")
                    image_path = create_branded_image(
                        text=post_text,
                        author_name=author_name,
                        subtitle=f"{request.style.title()} Content | AI Generated"
                    )
                
                if image_path:
                    # Use secure URL resolver with domain validation
                    image_url = safe_resolve_image_url(image_path)
            except Exception as img_err:
                print(f"Image generation warning: {img_err}")
        else:
            print("[POST] Skipping image generation (deferred mode - user can generate later)")
        
        # Create response
        post_id = f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return PostResponse(
            id=post_id,
            content=post_text,
            hook=post_text.split('\n')[0] if post_text else "",
            virality_score=score_result.get("score", 50),
            score_breakdown=score_result.get("breakdown", {}),
            suggestions=score_result.get("suggestions", []),
            timestamp=datetime.now().isoformat(),
            topic=clean_topic,
            style=request.style,
            image_url=image_url
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")


@app.post("/api/improve", response_model=PostResponse)
async def improve_post(request: ImproveRequest):
    """
    Improve an existing post based on feedback
    """
    try:
        # Sanitize feedback
        clean_feedback = sanitize_feedback(request.feedback)
        
        # Get agents
        content_agent, virality_agent = get_agents()
        
        # Improve content (async method)
        improved_result = await content_agent.improve_post_text(
            original_text=request.original_content,
            feedback=clean_feedback
        )
        
        improved_text = improved_result.get("post_text", "")
        if not improved_text:
            raise HTTPException(status_code=500, detail="Failed to improve content")
        
        # Score the improved content (async method)
        score_result = await virality_agent.score_post(improved_text)
        
        # Create response
        post_id = f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}_improved"
        
        return PostResponse(
            id=post_id,
            content=improved_text,
            hook=improved_text.split('\n')[0] if improved_text else "",
            virality_score=score_result.get("score", 50),
            score_breakdown=score_result.get("breakdown", {}),
            suggestions=score_result.get("suggestions", []),
            timestamp=datetime.now().isoformat(),
            topic="Improved Post",
            style="improved"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Improvement error: {str(e)}")


@app.post("/api/generate-image")
async def generate_image_for_post(request: GenerateImageRequest):
    """
    Generate an AI image for finalized post content (on-demand).
    Use this after post is confirmed to save API costs.
    """
    try:
        hook = request.content.split('\n')[0] if request.content else ""
        
        print(f"[IMAGE] On-demand image generation for style: {request.style}")
        image_path = await generate_ai_image(
            hook_text=hook,
            topic="User finalized post",
            style=request.style,
            full_content=request.content
        )
        
        # Fallback to static branded image if AI fails
        if not image_path:
            print("Falling back to static branded image")
            image_path = create_branded_image(
                text=request.content,
                author_name="GNX Content Intelligence",
                subtitle=f"{request.style.title()} Content | AI Generated"
            )
        
        if image_path:
            # Use secure URL resolver with domain validation
            image_url = safe_resolve_image_url(image_path)
            return {"image_url": image_url, "success": True}
        else:
            raise HTTPException(status_code=500, detail="Image generation failed")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation error: {str(e)}")

@app.get("/api/styles")
async def get_styles():
    """Get available writing styles with detailed definitions"""
    return {
        "styles": [
            {
                "id": "professional", 
                "name": "Professional", 
                "description": "Polished, authoritative, and business-appropriate",
                "instructions": "Use formal but accessible language. Focus on expertise and credibility. Include data points and industry insights. Maintain executive-level tone. Avoid slang or overly casual expressions."
            },
            {
                "id": "technical", 
                "name": "Technical", 
                "description": "Data-driven with specific metrics and details",
                "instructions": "Include specific numbers, metrics, and technical details. Use industry terminology appropriately. Focus on how/why things work. Include frameworks, methodologies, or processes. Reference tools, technologies, or systems."
            },
            {
                "id": "inspirational", 
                "name": "Inspirational", 
                "description": "Motivating, empowering, and uplifting",
                "instructions": "Share personal growth stories or lessons learned. Use emotionally resonant language. Include calls to action for self-improvement. Focus on overcoming challenges. End with hope or a forward-looking message."
            },
            {
                "id": "thought_leadership", 
                "name": "Thought Leadership", 
                "description": "Bold, contrarian, and industry-defining",
                "instructions": "Take a strong, possibly controversial stance. Challenge conventional wisdom. Make bold predictions about the future. Position yourself as ahead of the curve. Back up claims with unique insights or experience."
            },
            {
                "id": "storytelling", 
                "name": "Storytelling", 
                "description": "Narrative-driven with personal anecdotes",
                "instructions": "Open with a specific moment or scene. Use sensory details and dialogue. Build tension and resolution. Connect personal experience to broader lessons. Make readers feel like they're there with you."
            }
        ]
    }


# ═══════════════════════════════════════════════════════════════════
# Admin Endpoints (Phase A - Security Guards)
# ═══════════════════════════════════════════════════════════════════

class AdminPostRequest(BaseModel):
    """Request model for admin posting actions."""
    content: str = Field(..., description="Post content to publish")
    schedule_at: Optional[str] = Field(default=None, description="ISO8601 timestamp for scheduled posting")
    draft: bool = Field(default=False, description="Save as draft instead of publishing")
    platforms: List[str] = Field(default=["linkedin"], description="Target platforms")

class AdminPostResponse(BaseModel):
    """Response model for admin posting actions."""
    id: str
    status: str  # queued | posted | failed | draft
    message: Optional[str] = None


def verify_admin_role(role_header: Optional[str] = None) -> bool:
    """
    Verify admin role from request headers.
    In production, this should verify JWT token or session.
    For now, accept test_admin header for E2E testing.
    """
    # TODO: Implement proper JWT/session-based role verification
    return role_header == "admin"


@app.post("/api/admin/post", response_model=AdminPostResponse)
async def admin_post(
    request: AdminPostRequest,
    x_user_role: Optional[str] = Header(default=None, alias="X-User-Role")
):
    """
    Admin-only endpoint for LinkedIn posting actions.
    Returns 403 for non-admin users.
    
    Currently stubbed - returns mock responses for E2E testing.
    """
    # Verify admin role (stub implementation)
    # In production: verify from JWT token or session
    if not verify_admin_role(x_user_role):
        raise HTTPException(
            status_code=403, 
            detail="Forbidden: Admin access required"
        )
    
    # Generate post ID
    from uuid import uuid4
    post_id = str(uuid4())
    
    # Handle different action types
    if request.draft:
        return AdminPostResponse(
            id=post_id,
            status="draft",
            message="Draft saved successfully (stub implementation)"
        )
    elif request.schedule_at:
        return AdminPostResponse(
            id=post_id,
            status="queued",
            message=f"Post scheduled for {request.schedule_at} (stub implementation)"
        )
    else:
        return AdminPostResponse(
            id=post_id,
            status="queued",
            message="Post queued for immediate publishing (stub implementation)"
        )


@app.get("/api/admin/persona-status")
async def admin_persona_status(user_email: Optional[str] = None):
    """
    Get admin persona status for settings display.
    Returns persona details if admin persona is loaded.
    """
    try:
        from personas.persona_loader import safe_load_persona, PersonaContextBuilder, ADMIN_EMAILS
        
        # Check if user is admin
        is_admin = user_email and user_email.lower() in [e.lower() for e in ADMIN_EMAILS]
        
        # Try to load the admin persona (persona_admin_kunal matches the filename)
        persona_data = safe_load_persona("persona_admin_kunal")
        
        # Check if it's an error
        if hasattr(persona_data, 'ok') and not persona_data.ok:
            return {
                "persona_exists": False,
                "error": persona_data.message,
                "is_admin": is_admin,
                "current_user_email": user_email
            }
        
        # Build context from persona
        builder = PersonaContextBuilder(persona_data)
        
        # Extract identity info
        identity = persona_data.get("identity", {})
        
        return {
            "persona_exists": True,
            "persona_id": persona_data.get("id", persona_data.get("persona_id", "admin_kunal")),
            "version": persona_data.get("version", "unknown"),
            "display_name": builder.get_display_name(),
            "role": identity.get("title", "Unknown"),
            "identity": {
                "name": identity.get("name", "Unknown"),
                "title": identity.get("title", "Unknown")
            },
            "admin_emails": ADMIN_EMAILS,
            "current_user_email": user_email,
            "is_admin": is_admin,
            "hashtags": builder.hashtag_list()
        }
        
    except Exception as e:
        return {
            "persona_exists": False,
            "error": str(e),
            "current_user_email": user_email
        }



# ═══════════════════════════════════════════════════════════════════
# Run with: uvicorn api.main:app --reload --port 8080
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)
