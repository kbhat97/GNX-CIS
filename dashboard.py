import streamlit as st
import requests
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").strip()
CLERK_PUBLISHABLE_KEY = os.getenv("CLERK_PUBLISHABLE_KEY", "").strip()

# Page configuration
st.set_page_config(
    page_title="🤖 LinkedIn AI Co-pilot",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding-top: 1rem;
    }
    .stButton > button {
        width: 100%;
        padding: 0.75rem;
        border-radius: 0.5rem;
        font-weight: bold;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        color: #721c24;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "onboarding_path" not in st.session_state:
    st.session_state.onboarding_path = None
if "linkedin_connected" not in st.session_state:
    st.session_state.linkedin_connected = False

# ============================================
# HELPER FUNCTIONS
# ============================================

def get_headers():
    """Get authorization headers"""
    if st.session_state.auth_token:
        return {
            "Authorization": f"Bearer {st.session_state.auth_token}",
            "Content-Type": "application/json"
        }
    return {"Content-Type": "application/json"}

def check_api_health():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def verify_auth():
    """Verify authentication with API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/auth/verify",
            headers=get_headers(),
            timeout=5
        )
        return response.status_code == 200
    except:
        return False

def check_linkedin_status():
    """Check LinkedIn connection status"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/auth/linkedin/status",
            headers=get_headers(),
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("status") == "connected"
    except:
        pass
    return False

# ============================================
# AUTH SCREENS
# ============================================

def show_login_page():
    """Show login/signup page"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("## 🚀 LinkedIn AI Co-pilot")
        st.markdown("### Smart Content Generation Powered by AI")
        st.markdown("---")
        
        # Check API health
        if not check_api_health():
            st.error("❌ API is not responding. Please try again later.")
            return
        
        st.markdown("### 🔐 Authentication")
        
        tab1, tab2 = st.tabs(["📝 Sign Up", "🔑 Log In"])
        
        with tab1:
            st.write("#### Create Your Account")
            
            signup_email = st.text_input("Email", key="signup_email")
            signup_password = st.text_input("Password", type="password", key="signup_password")
            signup_password_confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")
            
            if st.button("📧 Sign Up with Email", key="email_signup"):
                if not signup_email:
                    st.error("❌ Please enter an email")
                elif not signup_password:
                    st.error("❌ Please enter a password")
                elif signup_password != signup_password_confirm:
                    st.error("❌ Passwords don't match")
                elif len(signup_password) < 8:
                    st.error("❌ Password must be at least 8 characters")
                else:
                    st.info("📧 Please sign up using Clerk. Redirecting...")
                    st.write("👉 [Sign up with Clerk](https://accounts.clerk.com/sign-up)")
            
            st.markdown("---")
            st.write("#### Or sign up with Google")
            if st.button("🔵 Continue with Google (Sign Up)", key="google_signup"):
                st.info("🔵 Redirecting to Google OAuth...")
                st.write("👉 [Google Sign Up](https://accounts.clerk.com/sign-up)")
        
        with tab2:
            st.write("#### Log In to Your Account")
            
            login_email = st.text_input("Email", key="login_email")
            login_password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("🔑 Log In with Email", key="email_login"):
                if not login_email or not login_password:
                    st.error("❌ Please enter email and password")
                else:
                    st.info("🔑 Redirecting to Clerk login...")
                    st.write("👉 [Log in with Clerk](https://accounts.clerk.com/sign-in)")
            
            st.markdown("---")
            st.write("#### Or log in with Google")
            if st.button("🔵 Continue with Google (Log In)", key="google_login"):
                st.info("🔵 Redirecting to Google OAuth...")
                st.write("👉 [Google Sign In](https://accounts.clerk.com/sign-in)")
        
        st.markdown("---")
        st.markdown("""
        ⚠️ **For production:**
        - Use Clerk's official login component (React/Next.js)
        - Or implement OAuth callback handler
        - Store JWT token in session after authentication
        """)

# ============================================
# ONBOARDING SCREENS
# ============================================

def show_onboarding_choice():
    """Show onboarding path selection"""
    st.markdown("## 👋 Welcome to LinkedIn AI Co-pilot")
    st.markdown("Let's set up your profile so we can generate personalized content.")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 Answer Questions (2 min)", key="questionnaire_btn", use_container_width=True):
            st.session_state.onboarding_path = "questionnaire"
            st.rerun()
    
    with col2:
        if st.button("📸 Upload Your Posts (3 min)", key="content_analysis_btn", use_container_width=True):
            st.session_state.onboarding_path = "content_analysis"
            st.rerun()

def show_questionnaire_onboarding():
    """Show questionnaire onboarding"""
    st.markdown("## 📋 Tell Us About Yourself")
    st.markdown("This helps us generate content that matches your style and audience.")
    st.markdown("---")
    
    with st.form("onboarding_form"):
        q1 = st.radio(
            "1️⃣ What's your writing tone?",
            ["Professional & Formal", "Casual & Friendly", "Inspiring & Motivational", "Technical & Detailed"],
            key="q1"
        )
        
        q2 = st.text_input(
            "2️⃣ Who's your target audience?",
            placeholder="e.g., SAP Project Managers, Startup Founders...",
            key="q2"
        )
        
        q3 = st.multiselect(
            "3️⃣ What values are important to you? (select 3-5)",
            ["Innovation", "Leadership", "Authenticity", "Growth", "Community", "Excellence", "Integrity", "Creativity"],
            key="q3"
        )
        
        q4 = st.text_area(
            "4️⃣ Describe your personality as a creator",
            placeholder="e.g., I'm a thought leader who shares practical insights...",
            key="q4"
        )
        
        q5 = st.slider(
            "5️⃣ How often do you want to post?",
            1, 7, 3,
            help="posts per week",
            key="q5"
        )
        
        q6 = st.text_input(
            "6️⃣ What's your main content focus?",
            placeholder="e.g., SAP Implementation Best Practices",
            key="q6"
        )
        
        if st.form_submit_button("✅ Save Profile", use_container_width=True):
            # Validate
            if not q2 or not q3 or not q4 or not q6:
                st.error("❌ Please fill in all fields")
            elif len(q3) < 2:
                st.error("❌ Please select at least 2 values")
            else:
                # Send to API
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/onboarding/questionnaire",
                        json={
                            "writing_tone": q1,
                            "audience": q2,
                            "values": q3,
                            "personality": q4,
                            "frequency": q5,
                            "focus": q6
                        },
                        headers=get_headers(),
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        st.success("✅ Profile saved! Ready to generate content!")
                        st.session_state.onboarding_path = None
                        st.rerun()
                    else:
                        st.error(f"❌ Error saving profile: {response.text}")
                
                except Exception as e:
                    st.error(f"❌ API Error: {str(e)}")

def show_content_analysis_onboarding():
    """Show content analysis onboarding"""
    st.markdown("## 📸 Upload Your Best Posts")
    st.markdown("Paste links to your 3-5 top performing LinkedIn posts.")
    st.markdown("---")
    
    st.info("ℹ️ This feature requires LinkedIn API integration. Coming soon!")

# ============================================
# MAIN DASHBOARD
# ============================================

def show_dashboard():
    """Show main dashboard"""
    # Header
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("## 🤖 LinkedIn AI Co-pilot")
    
    with col3:
        if st.button("🚪 Log Out", key="logout_btn", use_container_width=True):
            st.session_state.auth_token = None
            st.session_state.user = None
            st.rerun()
    
    st.markdown("---")
    
    # User info
    st.markdown(f"### 👋 Welcome, {st.session_state.user.get('email', 'User')}")
    
    # Check LinkedIn status
    st.session_state.linkedin_connected = check_linkedin_status()
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["🔗 LinkedIn", "✍️ Generate", "📊 Posts"])
    
    with tab1:
        st.markdown("## 🔗 LinkedIn Connection")
        
        if st.session_state.linkedin_connected:
            st.success("✅ LinkedIn is connected")
            if st.button("🔌 Disconnect LinkedIn", use_container_width=True):
                st.info("🔌 Disconnecting...")
        else:
            st.warning("⚠️ Connect LinkedIn to enable publishing")
            if st.button("🔗 Connect LinkedIn", use_container_width=True):
                st.info("🔗 Redirecting to LinkedIn OAuth...")
                st.write("👉 [Connect with LinkedIn](https://www.linkedin.com/oauth/v2/authorization)")
    
    with tab2:
        st.markdown("## ✍️ Generate Post")
        
        with st.form("post_generation_form"):
            topic = st.text_input(
                "What topic would you like to write about?",
                placeholder="e.g., SAP Implementation Best Practices",
                key="post_topic"
            )
            
            style = st.selectbox(
                "Choose writing style (optional)",
                ["Default", "Professional", "Casual", "Inspirational", "Technical"],
                key="post_style"
            )
            
            if st.form_submit_button("🚀 Generate Post", use_container_width=True):
                if not topic:
                    st.error("❌ Please enter a topic")
                else:
                    with st.spinner("🤖 Generating post..."):
                        try:
                            response = requests.post(
                                f"{API_BASE_URL}/posts/generate",
                                json={
                                    "topic": topic,
                                    "style": style if style != "Default" else None
                                },
                                headers=get_headers(),
                                timeout=30
                            )
                            
                            if response.status_code == 200:
                                data = response.json()
                                st.success("✅ Post generated successfully!")
                                
                                st.markdown("### 📝 Generated Content:")
                                st.text_area("", value=data.get("content", ""), height=200, disabled=True)
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("📋 Copy to Clipboard", use_container_width=True):
                                        st.success("✅ Copied!")
                                with col2:
                                    if st.button("📤 Publish Now", use_container_width=True):
                                        st.info("📤 Publishing...")
                            else:
                                st.error(f"❌ Error generating post: {response.json().get('detail', 'Unknown error')}")
                        
                        except Exception as e:
                            st.error(f"❌ API Error: {str(e)}")
    
    with tab3:
        st.markdown("## 📊 Your Posts")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📋 Pending Drafts")
            try:
                response = requests.get(
                    f"{API_BASE_URL}/posts/pending",
                    headers=get_headers(),
                    timeout=10
                )
                
                if response.status_code == 200:
                    posts = response.json().get("posts", [])
                    
                    if not posts:
                        st.info("No pending posts")
                    else:
                        for post in posts:
                            with st.expander(f"📝 {post.get('topic', 'Untitled')}"):
                                st.write(post.get("content", ""))
                                st.caption(f"Created: {post.get('created_at', 'N/A')}")
                else:
                    st.error("Could not load pending posts")
            
            except Exception as e:
                st.error(f"API Error: {str(e)}")
        
        with col2:
            st.markdown("### ✅ Published Posts")
            try:
                response = requests.get(
                    f"{API_BASE_URL}/posts/published",
                    headers=get_headers(),
                    timeout=10
                )
                
                if response.status_code == 200:
                    posts = response.json().get("posts", [])
                    
                    if not posts:
                        st.info("No published posts yet")
                    else:
                        for post in posts:
                            with st.expander(f"✅ {post.get('topic', 'Untitled')}"):
                                st.write(post.get("content", ""))
                                st.caption(f"Published: {post.get('published_at', 'N/A')}")
                else:
                    st.error("Could not load published posts")
            
            except Exception as e:
                st.error(f"API Error: {str(e)}")

# ============================================
# MAIN APP LOGIC
# ============================================

def main():
    """Main app logic"""
    
    # If authenticated
    if st.session_state.auth_token and st.session_state.user:
        # Check if onboarding needed
        if st.session_state.onboarding_path == "questionnaire":
            show_questionnaire_onboarding()
        elif st.session_state.onboarding_path == "content_analysis":
            show_content_analysis_onboarding()
        elif st.session_state.onboarding_path is None:
            # Show choice or dashboard
            show_dashboard()
    
    # If not authenticated
    else:
        show_login_page()

if __name__ == "__main__":
    main()
