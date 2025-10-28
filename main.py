# ============================================
# LOAD ENVIRONMENT VARIABLES FIRST
# ============================================
import os
from dotenv import load_dotenv

# Load .env file IMMEDIATELY
load_dotenv()

# ============================================
# IMPORTS
# ============================================
from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime
import json
import jwt
import requests

# Supabase ONLY (Clerk works via JWT validation)
from supabase import create_client

# ============================================
# CONFIGURATION
# ============================================

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration from environment
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")
CLERK_PUBLISHABLE_KEY = os.getenv("CLERK_PUBLISHABLE_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8501")

ALLOWED_ORIGINS = [
    FRONTEND_URL,
    "http://localhost:8501",
    "http://localhost:3000",
    "https://cis-frontend-666167524553.us-central1.run.app"
]

# Debug: Show what we loaded
logger.info(f"📝 Loaded Configuration:")
logger.info(f"   CLERK_SECRET_KEY: {'✅ SET' if CLERK_SECRET_KEY else '❌ NOT SET'}")
logger.info(f"   SUPABASE_URL: {'✅ SET' if SUPABASE_URL else '❌ NOT SET'}")
logger.info(f"   SUPABASE_KEY: {'✅ SET' if SUPABASE_KEY else '❌ NOT SET'}")

# ============================================
# INITIALIZE SERVICES
# ============================================

# Supabase (always initialize)
supabase = None
SUPABASE_READY = False

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Supabase initialized successfully")
        SUPABASE_READY = True
    except Exception as e:
        logger.error(f"❌ Supabase initialization failed: {e}")
else:
    logger.warning("⚠️ SUPABASE_URL or SUPABASE_KEY not set")

# Clerk (JWT validation, no SDK)
CLERK_READY = bool(CLERK_SECRET_KEY)
if CLERK_READY:
    logger.info("✅ Clerk Secret Key configured")
else:
    logger.warning("⚠️ CLERK_SECRET_KEY not set - Auth disabled")

# ============================================
# FASTAPI APP SETUP
# ============================================

app = FastAPI(
    title="CIS Content Intelligence System API",
    description="AI-powered LinkedIn content generation with Clerk auth",
    version="2.0.0",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# MODELS
# ============================================

class OnboardingQuestionnaireRequest(BaseModel):
    writing_tone: str
    audience: str
    values: List[str]
    personality: str
    frequency: int
    focus: str

class PostGenerationRequest(BaseModel):
    topic: str
    style: Optional[str] = None

class LinkedInTokenRequest(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[str] = None

# ============================================
# AUTHENTICATION DEPENDENCY (JWT VALIDATION)
# ============================================

async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Verify JWT token from Clerk and return user info
    Calls Clerk API directly (no SDK issues)
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # Extract token
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid scheme")
        
        # Verify token with Clerk API
        headers = {
            "Authorization": f"Bearer {CLERK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        
        # Call Clerk to verify token
        response = requests.post(
            "https://api.clerk.com/v1/tokens/verify",
            json={"token": token},
            headers=headers,
            timeout=5
        )
        
        if response.status_code != 200:
            logger.error(f"Clerk verification failed: {response.text}")
            raise Exception("Token verification failed")
        
        token_data = response.json()
        
        logger.info(f"✅ User authenticated: {token_data.get('sub', 'unknown')}")
        
        return {
            "clerk_id": token_data.get("sub"),
            "email": token_data.get("email", ""),
            "full_name": token_data.get("name", ""),
            "raw_token_data": token_data
        }
    
    except Exception as e:
        logger.error(f"❌ Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def get_db_user(current_user: Dict = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get or create user in Supabase linked to Clerk
    """
    if not SUPABASE_READY:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        clerk_id = current_user["clerk_id"]
        
        # Check if user exists
        result = supabase.table("users").select("*").eq("clerk_id", clerk_id).execute()
        
        if not result.data:
            # Create new user in Supabase
            logger.info(f"Creating new user in Supabase for Clerk ID: {clerk_id}")
            
            new_user = {
                "clerk_id": clerk_id,
                "email": current_user["email"],
                "full_name": current_user["full_name"],
                "created_at": datetime.utcnow().isoformat(),
                "onboarding_completed": False
            }
            
            insert_result = supabase.table("users").insert(new_user).execute()
            if not insert_result.data:
                raise Exception("Failed to create user in Supabase")
            
            return insert_result.data[0]
        
        return result.data[0]
    
    except Exception as e:
        logger.error(f"❌ Failed to get/create DB user: {e}")
        raise HTTPException(status_code=500, detail="User database error")

# ============================================
# HEALTH CHECK ENDPOINTS
# ============================================

@app.get("/health")
async def health_check_endpoint():
    """System health check"""
    try:
        checks = {
            "api": True,
            "clerk": CLERK_READY,
            "supabase": SUPABASE_READY,
        }
        return {
            "status": "healthy" if all(checks.values()) else "degraded",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "CIS Content Intelligence System API",
        "version": "2.0.0",
        "status": "running",
        "auth": "Clerk (JWT)",
        "database": "Supabase",
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

@app.post("/auth/callback")
async def auth_callback(clerk_user_id: str, email: str, full_name: Optional[str] = None):
    """
    Callback after Clerk authentication
    Creates/updates user in Supabase
    """
    if not SUPABASE_READY:
        return {"status": "error", "message": "Database not available"}
    
    try:
        # Check if user exists
        result = supabase.table("users").select("*").eq("clerk_id", clerk_user_id).execute()
        
        if not result.data:
            # Create new user
            new_user = {
                "clerk_id": clerk_user_id,
                "email": email,
                "full_name": full_name,
                "created_at": datetime.utcnow().isoformat(),
                "onboarding_completed": False
            }
            
            insert_result = supabase.table("users").insert(new_user).execute()
            logger.info(f"Created user: {clerk_user_id}")
            
            return {
                "status": "user_created",
                "user_id": insert_result.data[0]["id"] if insert_result.data else None
            }
        
        logger.info(f"User logged in: {clerk_user_id}")
        return {
            "status": "user_exists",
            "user_id": result.data[0]["id"]
        }
    
    except Exception as e:
        logger.error(f"Auth callback error: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/auth/verify")
async def verify_auth(current_user: Dict = Depends(get_current_user)):
    """Verify user is authenticated"""
    return {
        "status": "authenticated",
        "user": {
            "clerk_id": current_user["clerk_id"],
            "email": current_user["email"],
            "full_name": current_user["full_name"]
        }
    }

# ============================================
# ONBOARDING ENDPOINTS
# ============================================

@app.post("/onboarding/questionnaire")
async def save_questionnaire(
    request: OnboardingQuestionnaireRequest,
    db_user: Dict = Depends(get_db_user)
):
    """Save onboarding questionnaire responses"""
    if not SUPABASE_READY:
        return {"status": "error", "message": "Database not available"}
    
    try:
        user_id = db_user["id"]
        
        # Save questionnaire
        questionnaire_data = {
            "user_id": user_id,
            "question_1_writing_tone": request.writing_tone,
            "question_2_audience": request.audience,
            "question_3_values": request.values,
            "question_4_personality": request.personality,
            "question_5_frequency": request.frequency,
            "question_6_focus": request.focus,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("onboarding_questionnaire").insert(questionnaire_data).execute()
        
        # Create user profile
        profile_data = {
            "user_id": user_id,
            "writing_tone": request.writing_tone,
            "target_audience": request.audience,
            "key_values": request.values,
            "personality_traits": [request.personality],
            "posting_frequency": request.frequency,
            "content_focus": request.focus,
            "brand_voice_summary": f"User creates {request.writing_tone} content about {request.focus}"
        }
        
        supabase.table("user_profiles").insert(profile_data).execute()
        
        # Mark onboarding complete
        supabase.table("users").update({
            "onboarding_completed": True,
            "onboarding_path": "questionnaire"
        }).eq("id", user_id).execute()
        
        logger.info(f"Onboarding completed for user: {user_id}")
        
        return {
            "status": "profile_created",
            "message": "Onboarding questionnaire saved successfully"
        }
    
    except Exception as e:
        logger.error(f"Questionnaire save error: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/user/profile")
async def get_user_profile(db_user: Dict = Depends(get_db_user)):
    """Get user's profile"""
    if not SUPABASE_READY:
        return {"status": "error", "message": "Database not available"}
    
    try:
        result = supabase.table("user_profiles").select("*").eq("user_id", db_user["id"]).execute()
        
        if not result.data:
            return {"status": "no_profile", "message": "User has not completed onboarding"}
        
        return {
            "status": "success",
            "profile": result.data[0]
        }
    
    except Exception as e:
        logger.error(f"Profile fetch error: {e}")
        return {"status": "error", "message": str(e)}

# ============================================
# LINKEDIN ENDPOINTS
# ============================================

@app.post("/auth/linkedin/token")
async def save_linkedin_token(
    request: LinkedInTokenRequest,
    db_user: Dict = Depends(get_db_user)
):
    """Save LinkedIn OAuth token"""
    if not SUPABASE_READY:
        return {"status": "error", "message": "Database not available"}
    
    try:
        user_id = db_user["id"]
        
        token_data = {
            "user_id": user_id,
            "access_token": request.access_token,
            "refresh_token": request.refresh_token,
            "expires_at": request.expires_at or datetime.utcnow().isoformat()
        }
        
        # Check if token exists
        existing = supabase.table("linkedin_tokens").select("*").eq("user_id", user_id).execute()
        
        if existing.data:
            supabase.table("linkedin_tokens").update(token_data).eq("user_id", user_id).execute()
        else:
            supabase.table("linkedin_tokens").insert(token_data).execute()
        
        logger.info(f"LinkedIn token saved for user: {user_id}")
        
        return {"status": "token_saved"}
    
    except Exception as e:
        logger.error(f"LinkedIn token save error: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/auth/linkedin/status")
async def check_linkedin_status(db_user: Dict = Depends(get_db_user)):
    """Check if user has LinkedIn connected"""
    if not SUPABASE_READY:
        return {"status": "error", "message": "Database not available"}
    
    try:
        user_id = db_user["id"]
        
        result = supabase.table("linkedin_tokens").select("*").eq("user_id", user_id).execute()
        
        if result.data:
            return {
                "status": "connected",
                "linkedin_email": result.data[0].get("linkedin_email")
            }
        
        return {"status": "not_connected"}
    
    except Exception as e:
        logger.error(f"LinkedIn status check error: {e}")
        return {"status": "error", "message": str(e)}

# ============================================
# POST ENDPOINTS
# ============================================

@app.post("/posts/generate")
async def generate_post(
    request: PostGenerationRequest,
    db_user: Dict = Depends(get_db_user)
):
    """Generate a LinkedIn post"""
    if not SUPABASE_READY:
        return {"status": "error", "message": "Database not available"}
    
    try:
        user_id = db_user["id"]
        
        # Get user profile
        profile_result = supabase.table("user_profiles").select("*").eq("user_id", user_id).execute()
        if not profile_result.data:
            return {"status": "error", "message": "User profile not found. Please complete onboarding."}
        
        # Generate placeholder content
        content = f"This is a generated post about: {request.topic}\n\nGenerated by CIS AI System"
        
        # Save as draft
        post_data = {
            "user_id": user_id,
            "content": content,
            "topic": request.topic,
            "status": "draft",
            "generated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("posts").insert(post_data).execute()
        
        logger.info(f"Post generated for user: {user_id}, topic: {request.topic}")
        
        return {
            "status": "success",
            "post_id": result.data[0]["id"] if result.data else None,
            "content": content
        }
    
    except Exception as e:
        logger.error(f"Post generation error: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/posts/pending")
async def get_pending_posts(db_user: Dict = Depends(get_db_user)):
    """Get user's pending posts"""
    if not SUPABASE_READY:
        return {"status": "error", "message": "Database not available"}
    
    try:
        user_id = db_user["id"]
        result = supabase.table("posts").select("*").eq("user_id", user_id).eq("status", "draft").execute()
        
        return {
            "status": "success",
            "posts": result.data or [],
            "count": len(result.data) if result.data else 0
        }
    
    except Exception as e:
        logger.error(f"Fetch pending posts error: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/posts/published")
async def get_published_posts(db_user: Dict = Depends(get_db_user)):
    """Get user's published posts"""
    if not SUPABASE_READY:
        return {"status": "error", "message": "Database not available"}
    
    try:
        user_id = db_user["id"]
        result = supabase.table("posts").select("*").eq("user_id", user_id).eq("status", "published").execute()
        
        return {
            "status": "success",
            "posts": result.data or [],
            "count": len(result.data) if result.data else 0
        }
    
    except Exception as e:
        logger.error(f"Fetch published posts error: {e}")
        return {"status": "error", "message": str(e)}

# ============================================
# ERROR HANDLERS
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "timestamp": datetime.utcnow().isoformat()},
    )

# ============================================
# STARTUP/SHUTDOWN
# ============================================

@app.on_event("startup")
async def startup_event():
    """Run startup checks"""
    logger.info("🚀 Starting CIS API...")
    logger.info(f"✅ Clerk: {'Ready' if CLERK_READY else 'Not configured'}")
    logger.info(f"✅ Supabase: {'Ready' if SUPABASE_READY else 'Not available'}")
    logger.info("=" * 50)

@app.on_event("shutdown")
async def shutdown_event():
    """Run shutdown tasks"""
    logger.info("🛑 Shutting down CIS API...")

# ============================================
# RUN
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
