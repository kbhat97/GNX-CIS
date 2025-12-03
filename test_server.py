import sys
import os

# Fix encoding for Windows - with proper error handling
if sys.platform == 'win32':
    try:
        import codecs
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')
    except (AttributeError, TypeError):
        # Already configured or running in a special environment
        pass

from fastapi import FastAPI, Depends, HTTPException, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import logging
import json

# Configure logging without emoji characters
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="CIS Test Server",
    description="Simplified test server for CIS",
    version="1.0.0",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Test JWT token
TEST_JWT = "dev_jwt_for_testing"

# Mock data - using timezone-aware datetime
mock_user = {
    "clerk_id": "test_user_1",
    "email": "test@example.com",
    "full_name": "Test User"
}

mock_posts = [
    {
        "id": "post_1",
        "user_id": "test_user_id_001",
        "topic": "AI in Healthcare",
        "content": "This is a test post about AI in Healthcare.",
        "status": "draft",
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": "post_2",
        "user_id": "test_user_id_001",
        "topic": "Machine Learning",
        "content": "This is a test post about Machine Learning.",
        "status": "published",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "published_at": datetime.now(timezone.utc).isoformat()
    }
]

# Authentication dependency
async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Verify JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid scheme")
        
        if token != TEST_JWT:
            raise ValueError("Invalid token")
        
        return mock_user
    
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "api": True,
        "clerk": True,
        "supabase": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "CIS Test Server",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Auth verification endpoint
@app.get("/auth/verify")
async def verify_auth(current_user: Dict = Depends(get_current_user)):
    """Verify authentication"""
    return {
        "status": "authenticated",
        "user": current_user
    }

# User profile endpoint
@app.get("/user/profile")
async def get_user_profile(current_user: Dict = Depends(get_current_user)):
    """Get user profile"""
    return {
        "status": "success",
        "id": "test_user_id_001",
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "onboarding_completed": True
    }

# Onboarding endpoint
@app.post("/onboarding/questionnaire")
async def save_questionnaire(payload: Dict[str, Any] = Body(...), current_user: Dict = Depends(get_current_user)):
    """Save onboarding questionnaire"""
    return {
        "status": "profile_created",
        "message": "Onboarding questionnaire saved successfully"
    }

# Post generation endpoint
@app.post("/posts/generate")
async def generate_post(payload: Dict[str, Any] = Body(...), current_user: Dict = Depends(get_current_user)):
    """Generate a post"""
    new_post = {
        "id": f"post_{len(mock_posts) + 1}",
        "user_id": "test_user_id_001",
        "topic": payload.get("topic", "Test Topic"),
        "content": f"This is a generated post about: {payload.get('topic', 'Test Topic')}",
        "status": "draft",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    mock_posts.append(new_post)
    
    return {
        "status": "success",
        "post_id": new_post["id"],
        "content": new_post["content"]
    }

# Pending posts endpoint
@app.get("/posts/pending")
async def get_pending_posts(current_user: Dict = Depends(get_current_user)):
    """Get pending posts"""
    drafts = [p for p in mock_posts if p["status"] == "draft"]
    
    return {
        "status": "success",
        "posts": drafts,
        "count": len(drafts)
    }

# Published posts endpoint
@app.get("/posts/published")
async def get_published_posts(current_user: Dict = Depends(get_current_user)):
    """Get published posts"""
    published = [p for p in mock_posts if p["status"] == "published"]
    
    return {
        "status": "success",
        "posts": published,
        "count": len(published)
    }

# Get post endpoint
@app.get("/posts/{post_id}")
async def get_post(post_id: str, current_user: Dict = Depends(get_current_user)):
    """Get a post"""
    post = next((p for p in mock_posts if p["id"] == post_id), None)
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return {
        "status": "success",
        "post": post
    }

# Update post endpoint
@app.put("/posts/{post_id}")
async def update_post(post_id: str, payload: Dict[str, Any] = Body(...), current_user: Dict = Depends(get_current_user)):
    """Update a post"""
    post = next((p for p in mock_posts if p["id"] == post_id), None)
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post["content"] = payload.get("content", post["content"])
    post["topic"] = payload.get("topic", post["topic"])
    post["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    return {
        "status": "success",
        "post": post
    }

# Publish post endpoint
@app.post("/posts/publish/{post_id}")
async def publish_post(post_id: str, current_user: Dict = Depends(get_current_user)):
    """Publish a post"""
    post = next((p for p in mock_posts if p["id"] == post_id), None)
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post["status"] = "published"
    post["published_at"] = datetime.now(timezone.utc).isoformat()
    
    return {
        "status": "success",
        "message": "Post published successfully"
    }

# LinkedIn status endpoint
@app.get("/auth/linkedin/status")
async def check_linkedin_status(current_user: Dict = Depends(get_current_user)):
    """Check LinkedIn connection status"""
    return {
        "status": "connected",
        "linkedin_email": "test@linkedin.com"
    }

# LinkedIn authorization endpoint
@app.get("/auth/linkedin/authorize")
async def linkedin_authorize(current_user: Dict = Depends(get_current_user)):
    """Generate LinkedIn authorization URL"""
    return {
        "auth_url": "https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=test_client_id&redirect_uri=http://localhost:8080/auth/linkedin/callback&state=test_user_id_001&scope=r_liteprofile%20r_emailaddress%20w_member_social"
    }

# LinkedIn token endpoint
@app.post("/auth/linkedin/token")
async def save_linkedin_token(payload: Dict[str, Any] = Body(...), current_user: Dict = Depends(get_current_user)):
    """Save LinkedIn OAuth token"""
    return {
        "status": "token_saved"
    }

# LinkedIn disconnect endpoint
@app.post("/auth/linkedin/disconnect")
async def disconnect_linkedin(current_user: Dict = Depends(get_current_user)):
    """Disconnect LinkedIn account"""
    return {
        "status": "disconnected"
    }

# Legacy endpoints for TestSprite
@app.post("/user/onboarding")
async def alias_user_onboarding(payload: Dict[str, Any] = Body(...), current_user: Dict = Depends(get_current_user)):
    """Alias for /onboarding/questionnaire"""
    return {
        "status": "profile_created",
        "user_id": "test_user_id_001",
        "responses": payload.get("responses", {}),
        "onboarding_completed": True
    }

@app.post("/linkedin/token")
async def alias_linkedin_token(payload: Dict[str, Any] = Body(...), current_user: Dict = Depends(get_current_user)):
    """Alias for /auth/linkedin/token"""
    return {
        "success": True,
        "user_id": "test_user_id_001"
    }

@app.get("/linkedin/status")
async def alias_linkedin_status(current_user: Dict = Depends(get_current_user)):
    """Alias for /auth/linkedin/status"""
    return {
        "connected": True
    }

@app.get("/posts")
async def alias_posts(status: Optional[str] = None, current_user: Dict = Depends(get_current_user)):
    """Alias for /posts/pending|published with query param"""
    if status == "draft":
        drafts = [p for p in mock_posts if p["status"] == "draft"]
        return drafts
    elif status == "published":
        published = [p for p in mock_posts if p["status"] == "published"]
        return published
    else:
        return {"error": "Missing or invalid status param"}

# Run the server
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8080"))
    logger.info(f"Starting CIS Test Server on port {port}")
    uvicorn.run(
        "test_server:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )