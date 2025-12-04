import streamlit as st
import os
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
import json
from datetime import datetime
from typing import Dict, List, Optional

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.content_agent import ContentAgent
from agents.virality_agent import ViralityAgent
from utils.gemini_config import GeminiConfig

# Page config
st.set_page_config(
    page_title="CIS - Content Intelligence System",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)


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


def add_to_history(post_data: Dict):
    """Add a generated post to history"""
    post_data['timestamp'] = datetime.now().isoformat()
    post_data['id'] = len(st.session_state.post_history)
    st.session_state.post_history.append(post_data)


def show_sidebar():
    """Show sidebar with post history and controls"""
    with st.sidebar:
        st.markdown("## 📚 Post History")
        st.markdown(f"**Total Posts:** {len(st.session_state.post_history)}")
        
        if st.session_state.post_history:
            st.markdown("---")
            
            # Compare mode toggle
            if st.checkbox("📊 Compare Mode", value=st.session_state.compare_mode):
                st.session_state.compare_mode = True
                st.info("Select 2 posts to compare")
            else:
                st.session_state.compare_mode = False
                st.session_state.compare_posts = []
            
            st.markdown("---")
            
            # Show history (most recent first)
            for idx, post in enumerate(reversed(st.session_state.post_history)):
                actual_idx = len(st.session_state.post_history) - 1 - idx
                
                with st.expander(
                    f"Post #{post['id']} - Score: {post.get('virality_score', 0)}/100",
                    expanded=(actual_idx == 0)  # Expand most recent
                ):
                    # Show timestamp
                    timestamp = datetime.fromisoformat(post['timestamp'])
                    st.caption(f"🕒 {timestamp.strftime('%I:%M %p')}")
                    
                    # Show topic/style
                    st.caption(f"📝 {post.get('topic', 'N/A')[:50]}...")
                    st.caption(f"🎨 {post.get('style', 'N/A')}")
                    
                    # Show score with color
                    score = post.get('virality_score', 0)
                    if score >= 80:
                        st.success(f"⭐ Score: {score}/100")
                    elif score >= 70:
                        st.info(f"✓ Score: {score}/100")
                    else:
                        st.warning(f"⚠ Score: {score}/100")
                    
                    # Action buttons
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("👁️ View", key=f"view_{actual_idx}"):
                            st.session_state.selected_post_idx = actual_idx
                            st.session_state.compare_mode = False
                            st.rerun()
                    
                    with col2:
                        if st.session_state.compare_mode:
                            if st.button("✓ Select", key=f"select_{actual_idx}"):
                                if actual_idx not in st.session_state.compare_posts:
                                    st.session_state.compare_posts.append(actual_idx)
                                    if len(st.session_state.compare_posts) == 2:
                                        st.rerun()
                        else:
                            if st.button("🔄 Improve", key=f"improve_{actual_idx}"):
                                st.session_state.selected_post_idx = actual_idx
                                st.session_state.show_improve_form = True
                                st.rerun()
            
            # Clear history button
            st.markdown("---")
            if st.button("🗑️ Clear History", type="secondary"):
                st.session_state.post_history = []
                st.session_state.selected_post_idx = None
                st.session_state.compare_posts = []
                st.session_state.compare_mode = False
                st.session_state.show_improve_form = False
                st.rerun()
        else:
            st.info("No posts yet. Generate your first post!")


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


def show_generate_tab():
    """Show content generation interface"""
    
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
                
                if submitted and feedback:
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
                                improvement_feedback=feedback,
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
    st.markdown("## 🤖 Generate LinkedIn Post")
    st.info(f"🤖 **Content Model**: {GeminiConfig.CONTENT_MODEL} | **Scoring Model**: {GeminiConfig.SCORING_MODEL}")
    
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
        
        submitted = st.form_submit_button("🚀 Generate Post", use_container_width=True, type="primary")
        
        if submitted and topic:
            st.session_state.gen_count += 1
            
            with st.spinner("🤖 Gemini is crafting your viral post..."):
                try:
                    data = generate_post_async(topic, style)
                    add_to_history(data)
                    st.success("✅ Post generated successfully!")
                    st.session_state.selected_post_idx = len(st.session_state.post_history) - 1
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import traceback
                    with st.expander("Error Details"):
                        st.code(traceback.format_exc())


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
    
    # Header
    st.title("🚀 CIS - Content Intelligence System")
    st.markdown("*AI-Powered LinkedIn Content Generation with Gemini*")
    
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
    
    # Main tabs
    tab1, tab2 = st.tabs(["🤖 Generate", "📖 About"])
    
    with tab1:
        show_generate_tab()
    
    with tab2:
        show_about_tab()


if __name__ == "__main__":
    main()
