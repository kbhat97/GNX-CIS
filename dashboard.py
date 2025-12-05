import streamlit as st
import os
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
import json
from datetime import datetime
from typing import Dict, List, Optional
import sentry_sdk
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Sentry for error tracking
sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring
        traces_sample_rate=0.1,
        # Enable profiling
        profiles_sample_rate=0.1,
        # Add data like request headers and IP for users
        send_default_pii=True,
        # Environment
        environment="development",
        # Release version
        release="cis@1.0.0",
    )
    print("✅ Sentry initialized for error tracking")

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import authentication
from auth import init_auth, require_auth, show_user_menu, get_current_user
from agents.content_agent import ContentAgent
from agents.virality_agent import ViralityAgent
from utils.gemini_config import GeminiConfig
from utils.sanitizer import sanitize_topic, sanitize_feedback, escape_for_prompt
from utils.content_filter import is_safe_for_generation, moderate_content, ContentRiskLevel
from utils.cache import get_cache, cache_get, cache_set
from utils.rate_limiter import check_generation_limit, check_improvement_limit, format_retry_message

# Page config
st.set_page_config(
    page_title="GNX - Content Intelligence System",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"  # Hamburger menu style
)

def load_css():
    """Load custom CSS from assets/style.css"""
    css_file = os.path.join(os.path.dirname(__file__), "assets", "style.css")
    if os.path.exists(css_file):
        with open(css_file, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Load custom design system
load_css()

# Initialize authentication
init_auth()

# Require authentication - this will show login page if not authenticated
current_user = require_auth()

# Set Sentry user context for error tracking
if current_user and sentry_dsn:
    sentry_sdk.set_user({
        "id": current_user.get("user_id"),
        "email": current_user.get("email"),
        "username": f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}"
    })

# Initialize session state
def init_session_state():
    """Initialize all session state variables"""
    if 'post_history' not in st.session_state:
        st.session_state.post_history = []
    if 'gen_count' not in st.session_state:
        st.session_state.gen_count = 0
    if 'selected_post_idx' not in st.session_state:
        st.session_state.selected_post_idx = None
    if 'compare_mode' not in st.session_state:
        st.session_state.compare_mode = False
    if 'compare_posts' not in st.session_state:
        st.session_state.compare_posts = []
    if 'show_improve_form' not in st.session_state:
        st.session_state.show_improve_form = False
    
    # User preferences (persist between sessions)
    if 'user_preferences' not in st.session_state:
        st.session_state.user_preferences = {
            'default_style': 'inspirational',
            'default_tone': 'professional',
            'auto_generate_image': True,
            'show_score_details': True,
            'theme': 'dark'
        }


def get_user_preference(key: str, default=None):
    """Get a user preference value"""
    prefs = st.session_state.get('user_preferences', {})
    return prefs.get(key, default)


def set_user_preference(key: str, value):
    """Set a user preference value"""
    if 'user_preferences' not in st.session_state:
        st.session_state.user_preferences = {}
    st.session_state.user_preferences[key] = value


def add_to_history(post_data: Dict):
    """Add a generated post to history"""
    post_data['timestamp'] = datetime.now().isoformat()
    post_data['id'] = len(st.session_state.post_history)
    st.session_state.post_history.append(post_data)


def show_sidebar():
    """Show sidebar with GNX branding and post history"""
    with st.sidebar:
        # GNX Branding Header
        st.markdown("""
        <div style='text-align:center; padding: 15px 0; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px;'>
            <h2 style='margin:0; color:#a78bfa; font-size:1.5rem;'>GNX</h2>
            <p style='margin:0; color:rgba(255,255,255,0.7); font-size:0.85rem;'>Content Intelligence System</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show user menu (logout, profile)
        show_user_menu()
        
        # Quick stats row
        if st.session_state.post_history:
            total_posts = len(st.session_state.post_history)
            avg_score = sum(p.get('virality_score', 0) for p in st.session_state.post_history) / total_posts
            st.markdown(f"""
            <div style='display:flex; justify-content:space-around; padding:10px 0; margin-bottom:15px; background:rgba(255,255,255,0.05); border-radius:8px;'>
                <div style='text-align:center;'>
                    <div style='font-size:1.2rem; font-weight:bold; color:white;'>{total_posts}</div>
                    <div style='font-size:0.7rem; color:rgba(255,255,255,0.6);'>Posts</div>
                </div>
                <div style='text-align:center;'>
                    <div style='font-size:1.2rem; font-weight:bold; color:#a78bfa;'>{avg_score:.0f}</div>
                    <div style='font-size:0.7rem; color:rgba(255,255,255,0.6);'>Avg Score</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # PROMINENT COMPARE BUTTON
        if len(st.session_state.post_history) >= 2:
            if st.button("📊 Compare Posts", use_container_width=True, type="primary" if st.session_state.compare_mode else "secondary"):
                st.session_state.compare_mode = not st.session_state.compare_mode
                if not st.session_state.compare_mode:
                    st.session_state.compare_posts = []
                st.rerun()
            
            if st.session_state.compare_mode:
                st.info(f"Select {2 - len(st.session_state.compare_posts)} more posts")
        
        st.markdown("---")
        st.markdown("**📝 Post History**")
        
        if st.session_state.post_history:
            # Show history (most recent first) - Score at TOP
            for idx, post in enumerate(reversed(st.session_state.post_history)):
                actual_idx = len(st.session_state.post_history) - 1 - idx
                score = post.get('virality_score', 0)
                
                # Score badge color
                score_color = "#22c55e" if score >= 80 else "#eab308" if score >= 70 else "#ef4444"
                
                # Compact post card with score at top
                st.markdown(f"""
                <div style='background:rgba(255,255,255,0.05); border-radius:8px; padding:10px; margin-bottom:8px; border-left:3px solid {score_color};'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <span style='font-size:1.1rem; font-weight:bold; color:{score_color};'>{score}/100</span>
                        <span style='font-size:0.7rem; color:rgba(255,255,255,0.5);'>#{post['id']}</span>
                    </div>
                    <div style='font-size:0.75rem; color:rgba(255,255,255,0.7); margin-top:4px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>
                        {post.get('topic', 'N/A')[:40]}...
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("👁️ View", key=f"view_{actual_idx}", use_container_width=True):
                        st.session_state.selected_post_idx = actual_idx
                        st.session_state.compare_mode = False
                        st.rerun()
                with col2:
                    if st.session_state.compare_mode:
                        is_selected = actual_idx in st.session_state.compare_posts
                        if st.button("✓" if is_selected else "Select", key=f"select_{actual_idx}", use_container_width=True):
                            if actual_idx not in st.session_state.compare_posts:
                                st.session_state.compare_posts.append(actual_idx)
                                if len(st.session_state.compare_posts) == 2:
                                    st.rerun()
                    else:
                        if st.button("🔄", key=f"improve_{actual_idx}", use_container_width=True):
                            st.session_state.selected_post_idx = actual_idx
                            st.session_state.show_improve_form = True
                            st.rerun()
            
            # Clear history button at bottom
            st.markdown("---")
            if st.button("🗑️ Clear All", type="secondary", use_container_width=True):
                st.session_state.post_history = []
                st.session_state.selected_post_idx = None
                st.session_state.compare_posts = []
                st.session_state.compare_mode = False
                st.session_state.show_improve_form = False
                st.rerun()
        else:
            st.caption("No posts yet. Generate your first!")


def generate_post_async(
    topic: str,
    style: str,
    improvement_feedback: Optional[str] = None,
    improvement_count: int = 0,
    previous_score: int = 0
) -> Dict:
    "Generate post with smart model escalation (uses advanced model if improvement_count >= 2 and previous_score < 80)"
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            # Mock profile
            profile = {
                "writing_tone": "Professional & Insightful",
                "target_audience": "Business professionals",
                "personality_traits": ["Thought Leader"],
                "full_name": "Kunal Bhat"
            }
            
            # JSON parser
            from utils.json_parser import parse_llm_json_response
            
            # Create agents with smart model escalation
            content_agent = ContentAgent()
            virality_agent = ViralityAgent()
            
            # SMART MODEL ESCALATION: Use advanced model if struggling
            use_advanced_model = improvement_count >= 2 and previous_score < 80
            if use_advanced_model:
                # Import advanced model
                import google.generativeai as genai
                advanced_model = genai.GenerativeModel("gemini-2.0-flash-exp")
                content_agent.model = advanced_model  # Override with advanced model
                st.info("🧠 Using Gemini 2.0 Flash Exp for deeper analysis...")
            
            # Generate content using SYNC method
            if improvement_feedback:
                # IMPROVEMENT MODE: Explicitly tell AI to improve previous content
                prompt = f"""You are an expert LinkedIn content strategist improving a post.

ORIGINAL TOPIC: "{topic}"
STYLE: {style}
PERSONA: Thought Leader

IMPROVEMENT FEEDBACK: {improvement_feedback}

TASK: Rewrite and IMPROVE the post based on the feedback above. Make specific changes to address the feedback.
Do NOT just regenerate - actively incorporate the suggestions to make it better.

Return ONLY valid JSON:
{{
    "post_text": "your IMPROVED post here",
    "reasoning": "what specific improvements you made"
}}"""
            else:
                # GENERATION MODE: Create new content
                prompt = f"""You are an expert LinkedIn content strategist creating high-engagement posts.

TOPIC: "{topic}"
STYLE: {style}
PERSONA: Thought Leader

CREATE A VIRAL LINKEDIN POST WITH PROPER JSON FORMAT.
Return ONLY valid JSON:
{{
    "post_text": "your complete post here",
    "reasoning": "brief explanation"
}}"""
            
            response = content_agent.model.generate_content(prompt)
            error_payload = {"post_text": "Error generating content.", "reasoning": "JSON parsing failed."}
            draft = parse_llm_json_response(response.text, error_payload)
            post_text = draft.get("post_text", "")
            
            # Score using SYNC method - STRICT EVALUATION
            score_prompt = f"""You are a LinkedIn virality expert. Score this post STRICTLY on a 0-100 scale.

POST TO EVALUATE:
{post_text}

SCORING RUBRIC (be harsh and honest):
- 90-100: EXCEPTIONAL - Would go viral, perfect hook, compelling story, strong CTA
- 80-89: EXCELLENT - Very engaging, clear value, good structure
- 70-79: GOOD - Solid post but missing viral elements
- 60-69: AVERAGE - Generic LinkedIn content
- Below 60: NEEDS WORK - Lacks engagement potential

EVALUATE THESE 8 DIMENSIONS:
1. Hook Strength (first 2 lines grab attention?)
2. Value Delivery (actionable insights?)
3. Emotional Resonance (connects with audience?)
4. Call-to-Action (encourages engagement?)
5. Readability (easy to scan?)
6. Authority Signal (demonstrates expertise?)
7. Shareability (worth sharing?)
8. Hashtag Relevance (strategic tags?)

BE STRICT. Most posts should score 65-80. Only exceptional posts get 85+.

Return ONLY valid JSON with your ACTUAL evaluation:
{{
    "score": <your calculated score 0-100>,
    "confidence": "HIGH" or "MEDIUM" or "LOW",
    "suggestions": ["specific improvement 1", "specific improvement 2", "specific improvement 3"]
}}"""
            
            score_response = virality_agent.model.generate_content(score_prompt)
            score_result = parse_llm_json_response(
                score_response.text,
                {"score": 50, "confidence": "LOW", "suggestions": []}
            )
            
            data = {
                "content": post_text,
                "reasoning": draft.get("reasoning", ""),
                "virality_score": score_result.get("score", 0),
                "confidence": score_result.get("confidence", ""),
                "suggestions": score_result.get("suggestions", []),
                "topic": topic,
                "style": style,
                "improvement_feedback": improvement_feedback,
                "improvement_count": improvement_count,
                "previous_score": previous_score
            }
            
            # Generate image
            try:
                from utils.image_generator import create_branded_image
                st.info("🎨 Generating branded image...")
                image_url = create_branded_image(data.get("content", ""), "Kunal Bhat, PMP")
                if image_url:
                    data["image_url"] = image_url
                    st.success("✅ Image generated successfully!")
                else:
                    st.warning("⚠️ Image generation returned None - check logs")
                    data["image_url"] = None
            except Exception as img_err:
                st.error(f"❌ Image generation failed: {str(img_err)}")
                import traceback
                with st.expander("Image Error Details"):
                    st.code(traceback.format_exc())
                data["image_url"] = None
            
            return data
            
        except Exception as e:
            if attempt < max_retries - 1:
                st.warning(f"⚠️ Attempt {attempt + 1} failed. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                raise e


def show_post_detail(post: Dict, show_improve_button: bool = True):
    """Display a single post with all details"""
    # Show content
    st.markdown("### 📝 Post Content")
    st.text_area("", value=post.get("content", ""), height=300, key=f"content_detail_{post['id']}", disabled=True)
    
    # Show image if available
    if post.get("image_url"):
        st.markdown("### 🖼️ Generated Image")
        st.image(post["image_url"], width=600)
    
    # Show metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        score = post.get('virality_score', 0)
        delta = None
        if len(st.session_state.post_history) > 1:
            prev_score = st.session_state.post_history[-2].get('virality_score', 0)
            delta = score - prev_score
        st.metric("Virality Score", f"{score}/100", delta=delta)
    with col2:
        st.metric("Confidence", post.get("confidence", "N/A"))
    with col3:
        st.metric("Style", post.get("style", "N/A"))
    with col4:
        timestamp = datetime.fromisoformat(post['timestamp'])
        st.metric("Generated", timestamp.strftime('%I:%M %p'))
    
    # Show suggestions
    if post.get("suggestions"):
        st.markdown("### 💡 Improvement Suggestions")
        for i, suggestion in enumerate(post["suggestions"], 1):
            st.info(f"{i}. {suggestion}")
    
    # Show reasoning
    if post.get("reasoning"):
        with st.expander("🧠 AI Reasoning"):
            st.write(post["reasoning"])
    
    # Show improvement feedback if this was an improved version
    if post.get("improvement_feedback"):
        with st.expander("🔄 Improvement Feedback Used"):
            st.write(post["improvement_feedback"])
    
    # Improve button
    if show_improve_button:
        st.markdown("---")
        if st.button("🔄 Improve This Post", key=f"improve_detail_{post['id']}", use_container_width=True):
            st.session_state.show_improve_form = True
            st.rerun()


def show_comparison_view(post1: Dict, post2: Dict):
    """Show side-by-side comparison of two posts"""
    st.markdown("## 📊 Post Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"### Post #{post1['id']}")
        st.markdown(f"**Score:** {post1.get('virality_score', 0)}/100")
        st.markdown(f"**Style:** {post1.get('style', 'N/A')}")
        timestamp1 = datetime.fromisoformat(post1['timestamp'])
        st.caption(f"🕒 {timestamp1.strftime('%I:%M %p')}")
        
        st.markdown("**Content:**")
        st.text_area("", value=post1.get("content", ""), height=400, key="compare_1", disabled=True)
        
        if post1.get("image_url"):
            st.image(post1["image_url"], width=400)
        
        if post1.get("suggestions"):
            with st.expander("💡 Suggestions"):
                for i, s in enumerate(post1["suggestions"], 1):
                    st.write(f"{i}. {s}")
    
    with col2:
        st.markdown(f"### Post #{post2['id']}")
        st.markdown(f"**Score:** {post2.get('virality_score', 0)}/100")
        st.markdown(f"**Style:** {post2.get('style', 'N/A')}")
        timestamp2 = datetime.fromisoformat(post2['timestamp'])
        st.caption(f"🕒 {timestamp2.strftime('%I:%M %p')}")
        
        st.markdown("**Content:**")
        st.text_area("", value=post2.get("content", ""), height=400, key="compare_2", disabled=True)
        
        if post2.get("image_url"):
            st.image(post2["image_url"], width=400)
        
        if post2.get("suggestions"):
            with st.expander("💡 Suggestions"):
                for i, s in enumerate(post2["suggestions"], 1):
                    st.write(f"{i}. {s}")
    
    # Score comparison
    st.markdown("---")
    st.markdown("### 📈 Score Breakdown")
    
    score_diff = post2.get('virality_score', 0) - post1.get('virality_score', 0)
    if score_diff > 0:
        st.success(f"✅ Post #{post2['id']} scored {score_diff} points higher!")
    elif score_diff < 0:
        st.warning(f"⚠️ Post #{post1['id']} scored {abs(score_diff)} points higher!")
    else:
        st.info("📊 Both posts have the same score")
    
    # Exit comparison
    if st.button("❌ Exit Comparison", use_container_width=True):
        st.session_state.compare_mode = False
        st.session_state.compare_posts = []
        st.rerun()


def show_dashboard_header():
    """Show the glassmorphic dashboard header"""
    current_user = get_current_user()
    if not current_user:
        return

    # User avatar (use Dicebear if no image)
    avatar_url = current_user.get('image_url') or f"https://api.dicebear.com/7.x/avataaars/svg?seed={current_user.get('first_name', 'User')}"
    
    st.markdown(f"""
    <div class="glass-card animate-fade-in" style="display: flex; justify-content: space-between; align-items: center; padding: 15px 25px; margin-bottom: 30px;">
        <div style="display: flex; align-items: center; gap: 15px;">
            <div style="background: rgba(139, 92, 246, 0.2); padding: 8px; border-radius: 50%;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="#a78bfa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M2 17L12 22L22 17" stroke="#a78bfa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M2 12L12 17L22 12" stroke="#a78bfa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <div>
                <h1 style="margin: 0; font-size: 1.5rem; font-weight: 700; color: white;">CIS Dashboard</h1>
                <p style="margin: 0; font-size: 0.8rem; color: rgba(255,255,255,0.6);">Content Intelligence System</p>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 20px;">
             <div style="text-align: right;">
                <p style="margin: 0; color: white; font-weight: 600;">{current_user.get('first_name', 'User')} {current_user.get('last_name', '')}</p>
                <p style="margin: 0; font-size: 0.8rem; color: rgba(255,255,255,0.6);">{current_user.get('email', '')}</p>
            </div>
            <img src="{avatar_url}" 
                 style="width: 40px; height: 40px; border-radius: 50%; border: 2px solid rgba(139, 92, 246, 0.5);">
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics Section
    cols = st.columns(4)
    
    # Only show real metrics - just post count
    st.markdown(f"""
    <div class="glass-card animate-fade-in" style="padding: 20px; text-align: center; max-width: 300px;">
        <p style="color: rgba(255,255,255,0.6); font-size: 0.875rem; margin: 0;">Posts Generated</p>
        <p style="font-size: 2.5rem; font-weight: 700; color: white; margin: 10px 0 0 0;">{st.session_state.gen_count}</p>
    </div>
    """, unsafe_allow_html=True)


    
    st.markdown("<br>", unsafe_allow_html=True)


def show_generate_tab():
    """Show content generation interface - compact layout"""
    
    # Only show stats when posts exist (removed redundant header)

    # Check if we're in comparison mode
    if st.session_state.compare_mode and len(st.session_state.compare_posts) == 2:
        idx1, idx2 = st.session_state.compare_posts
        show_comparison_view(
            st.session_state.post_history[idx1],
            st.session_state.post_history[idx2]
        )
        return
    
    # Check if we're viewing a specific post
    if st.session_state.selected_post_idx is not None:
        # Bounds check - reset if index is out of range
        if st.session_state.selected_post_idx >= len(st.session_state.post_history):
            st.session_state.selected_post_idx = None
            st.rerun()
        
        post = st.session_state.post_history[st.session_state.selected_post_idx]
        st.markdown(f"## 👁️ Viewing Post #{post['id']}")
        
        # Show improve form if requested
        if st.session_state.get('show_improve_form', False):
            st.markdown("### 🔄 Improve This Post")
            
            with st.form(key="improve_form"):
                feedback = st.text_area(
                    "What would you like to improve?",
                    placeholder="e.g., Make it more technical, add statistics, change the hook, etc.",
                    height=100
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("🚀 Generate Improved Version", use_container_width=True)
                with col2:
                    cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
                
                if cancel:
                    st.session_state.show_improve_form = False
                    st.rerun()
                
                if submitted:
                    if not feedback or not feedback.strip():
                        st.error("❌ Please provide improvement feedback")
                    else:
                        # SECURITY: Sanitize feedback input
                        try:
                            sanitized_feedback = sanitize_feedback(feedback)
                            safe_feedback = escape_for_prompt(sanitized_feedback)
                            
                            # Track improvement iterations
                            improvement_count = post.get('improvement_count', 0) + 1
                            previous_score = post.get('virality_score', 0)
                            
                            # Show model escalation message
                            if improvement_count >= 2 and previous_score < 80:
                                st.info("🧠 Activating advanced model for deeper analysis (score-based escalation)...")
                            
                            with st.spinner("🤖 Gemini is improving your post..."):
                                try:
                                    data = generate_post_async(
                                        post.get('topic', ''),
                                        post.get('style', 'Professional'),
                                        improvement_feedback=safe_feedback,
                                        improvement_count=improvement_count,
                                        previous_score=previous_score
                                    )
                                    add_to_history(data)
                                    st.success("✅ Improved post generated successfully!")
                                    st.session_state.selected_post_idx = len(st.session_state.post_history) - 1
                                    st.session_state.show_improve_form = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error while improving post: {str(e)}")
                                    import traceback
                                    with st.expander("Error Details"):
                                        st.code(traceback.format_exc())
                        except ValueError as ve:
                            st.error(f"❌ Invalid feedback: {str(ve)}")
                            st.info("💡 Please check your feedback and try again.")
        else:
            # Normal post detail view
            show_post_detail(post)
        
        # Back button
        st.markdown("---")
        if st.button("⬅️ Back to Generator", use_container_width=True):
            st.session_state.selected_post_idx = None
            st.session_state.show_improve_form = False
            st.rerun()
        
        return
    
    # Main generation interface
    st.markdown("## Generate LinkedIn Post")
    
    with st.form(key="gen_form"):
        topic = st.text_area(
            "What do you want to post about?",
            placeholder="e.g., SAP S/4HANA migration challenges, AI in healthcare, quantum computing, etc.",
            height=100
        )
        
        col1, col2 = st.columns(2)
        with col1:
            style = st.selectbox(
                "Style",
                ["Thought Leadership", "Professional", "Casual", "Technical", "Inspirational"]
            )
        with col2:
            st.markdown("**Quick Tips:**")
            st.caption("• Be specific with your topic")
            st.caption("• Include key points you want to cover")
            st.caption("• Mention target audience if relevant")
        
        submitted = st.form_submit_button("Generate Post", use_container_width=True, type="primary")
        
        if submitted:
            if not topic or not topic.strip():
                st.error("❌ Please enter a topic for your post")
            else:
                # RATE LIMITING: Check if user can generate
                user_id = current_user.get('user_id', 'anonymous')
                is_allowed, limit_info = check_generation_limit(user_id)
                
                if not is_allowed:
                    st.error(format_retry_message(limit_info))
                    st.info(f"💡 Limit: {limit_info['limit']} posts per minute")
                else:
                    # Show remaining quota
                    st.info(f"📊 {limit_info['remaining']} generations remaining this minute")
                    
                    # SECURITY: Sanitize and validate input
                    try:
                        # Sanitize topic
                        sanitized_topic = sanitize_topic(topic)
                        
                        # Check content safety
                        is_safe, unsafe_reason = is_safe_for_generation(sanitized_topic)
                        if not is_safe:
                            st.error(f"🚫 Content moderation failed: {unsafe_reason}")
                            st.warning("Please revise your topic to comply with our content policy.")
                        else:
                            # Escape for LLM prompt to prevent prompt injection
                            safe_topic = escape_for_prompt(sanitized_topic)
                            
                            st.session_state.gen_count += 1
                            
                            with st.spinner("🤖 Gemini is crafting your viral post..."):
                                try:
                                    data = generate_post_async(safe_topic, style)
                                    
                                    # CACHING: Cache the generated post
                                    cache_key = f"post:{user_id}:{len(st.session_state.post_history)}"
                                    cache_set(cache_key, data, ttl=3600)  # Cache for 1 hour
                                    
                                    add_to_history(data)
                                    st.success("✅ Post generated successfully!")
                                    st.session_state.selected_post_idx = len(st.session_state.post_history) - 1
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                                    import traceback
                                    with st.expander("Error Details"):
                                        st.code(traceback.format_exc())
                    except ValueError as ve:
                        st.error(f"❌ Invalid input: {str(ve)}")
                        st.info("💡 Please check your input and try again.")


def show_about_tab():
    """Show about/help information"""
    st.markdown("## 📖 How CIS Works")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🔄 The Workflow
        
        1. **Generate**: Create viral LinkedIn posts with AI
        2. **Score**: Get 0-100 virality score with detailed feedback
        3. **Improve**: Iteratively refine based on suggestions
        4. **Compare**: Side-by-side comparison of versions
        5. **Export**: Download or copy your best content
        
        ### 🤖 The Models
        
        - **Content**: Gemini 2.5 Flash (Fast, creative)
        - **Scoring**: Gemini 2.0 Flash (Accurate evaluation)
        - **Images**: PIL (Professional branding)
        
        ### 📊 Scoring Criteria
        
        - **90-100**: EXCEPTIONAL - Top 1% viral content
        - **80-89**: EXCELLENT - Top 5% engagement
        - **70-79**: GOOD - Above average
        - **60-69**: AVERAGE - Typical LinkedIn post
        - **<60**: NEEDS IMPROVEMENT
        """)
    
    with col2:
        st.markdown("""
        ### 🎯 8 Scoring Dimensions
        
        1. **Hook Strength** - Grabs attention in first 2 lines
        2. **Value Delivery** - Provides actionable insights
        3. **Emotional Resonance** - Connects with audience
        4. **Call-to-Action** - Encourages engagement
        5. **Readability** - Easy to scan and understand
        6. **Authority Signal** - Demonstrates expertise
        7. **Shareability** - Worth sharing with network
        8. **Hashtag Relevance** - Strategic tag usage
        
        ### 🚀 Pro Tips
        
        - Generate 3-5 versions, compare scores
        - Use "Improve" to iterate on best version
        - Aim for 80+ score for viral potential
        - Technical content: use data & metrics
        - Thought leadership: be contrarian
        - Personal stories: be vulnerable & authentic
        """)
    
    st.markdown("---")
    st.markdown("### 🖼️ Image Features")
    st.markdown("""
    - Branded layout with professional design
    - Optimized for LinkedIn (1200x675)
    - Custom fonts (Poppins) and colors
    - Automatic text extraction and formatting
    """)


def main():
    """Main application"""
    
    # Initialize session state
    init_session_state()
    
    # Show sidebar
    show_sidebar()
    
    # Clean header with GNX branding and About in header row
    header_col1, header_col2, header_col3 = st.columns([3, 1, 1])
    with header_col1:
        st.markdown("""<h1 style='margin:0; font-size:1.8rem;'>
            <span style='color:#a78bfa;'>GNX</span> - 
            <span style='color:white;'>Content Intelligence System</span>
        </h1>
        <p style='color: rgba(255,255,255,0.6); margin:0; font-size:0.9rem;'>AI-Powered LinkedIn Content Generation</p>
        """, unsafe_allow_html=True)
    with header_col2:
        if st.button("📖 About", use_container_width=True, type="secondary"):
            st.session_state.show_about_modal = True
    with header_col3:
        current_user = get_current_user()
        if current_user:
            avatar_url = current_user.get('image_url') or f"https://api.dicebear.com/7.x/avataaars/svg?seed={current_user.get('first_name', 'User')}"
            full_name = f"{current_user.get('first_name', 'User')} {current_user.get('last_name', '')}".strip()
            email = current_user.get('email', '')
            st.markdown(f"""
            <div style='display:flex; align-items:center; justify-content:flex-end; gap:12px;'>
                <div style='text-align:right;'>
                    <span style='color:white; font-weight:600; font-size:0.95rem;'>{full_name}</span><br/>
                    <span style='color:rgba(255,255,255,0.6); font-size:0.75rem;'>{email}</span>
                </div>
                <img src="{avatar_url}" 
                     style="width:42px; height:42px; border-radius:50%; border:2px solid rgba(139, 92, 246, 0.6); background:#1e1e32;"
                     alt="User Avatar">
            </div>
            """, unsafe_allow_html=True)
    
    # Stats bar
    if st.session_state.post_history:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Posts", len(st.session_state.post_history))
        with col2:
            avg_score = sum(
                p.get('virality_score', 0) for p in st.session_state.post_history
            ) / len(st.session_state.post_history)
            st.metric("Avg Score", f"{avg_score:.1f}/100")
        with col3:
            max_score = max(p.get('virality_score', 0) for p in st.session_state.post_history)
            st.metric("Best Score", f"{max_score}/100")
        with col4:
            excellent_count = sum(
                1 for p in st.session_state.post_history if p.get('virality_score', 0) >= 80
            )
            st.metric("Excellent Posts", f"{excellent_count}/{len(st.session_state.post_history)}")
        
        st.markdown("---")
    
    # Show About modal if triggered from header button
    if st.session_state.get('show_about_modal', False):
        with st.expander("📖 About GNX Content Intelligence System", expanded=True):
            show_about_tab()
            if st.button("❌ Close", use_container_width=True):
                st.session_state.show_about_modal = False
                st.rerun()
    else:
        # Main content - Generate view
        show_generate_tab()


if __name__ == "__main__":
    main()
