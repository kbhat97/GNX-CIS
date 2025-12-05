"""
Streamlit authentication middleware and UI components
"""
import streamlit as st
from typing import Dict, Optional
from datetime import datetime, timedelta
from auth.clerk_auth import verify_session, get_current_user, is_authenticated, logout

# Session timeout in minutes
SESSION_TIMEOUT_MINUTES = 30


def check_session_timeout() -> bool:
    """
    Check if the session has timed out due to inactivity.
    
    Returns:
        True if session is still valid, False if timed out
    """
    if "last_activity" not in st.session_state:
        st.session_state.last_activity = datetime.now()
        return True
    
    last_activity = st.session_state.last_activity
    timeout_threshold = timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    
    if datetime.now() - last_activity > timeout_threshold:
        # Session timed out
        return False
    
    # Update last activity
    st.session_state.last_activity = datetime.now()
    return True


def require_auth() -> Dict:
    """
    Require authentication for the current page.
    Shows login UI if not authenticated and stops execution.
    
    Returns:
        Dict with user info if authenticated
    """
    # Check if already authenticated
    if is_authenticated():
        # Check for session timeout
        if not check_session_timeout():
            logout()
            st.warning("⏰ Your session has expired due to inactivity. Please log in again.")
            show_login_page()
            st.stop()
        
        return get_current_user()
    
    # Try to get session token from query params
    session_token = st.query_params.get("__clerk_session_token")
    
    if session_token:
        user = verify_session(session_token)
        if user:
            st.session_state.user = user
            st.session_state.clerk_session_token = session_token
            st.session_state.last_activity = datetime.now()
            st.rerun()
    
    # Not authenticated - show login UI
    show_login_page()
    st.stop()


def show_login_page():
    """
    Display the login page UI with embedded login/signup forms
    """
    import os
    
    # Add spacing
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Split layout: Hero (Left) | Login (Right)
    col_hero, col_form = st.columns([1.2, 1])
    
    # Left Hero Section
    with col_hero:
        st.markdown("""
        <div class="animate-fade-in" style="padding: 40px;">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
                <span style="font-size: 2rem; font-weight: 800; color: #a78bfa;">GNX</span>
                <span style="font-size: 1.25rem; font-weight: 600; color: white;">Content Intelligence System</span>
            </div>
            <h1 style="font-size: 3.5rem; font-weight: 900; line-height: 1.2; color: white; margin-bottom: 20px;">
                Ignite Your <br>
                <span class="animated-gradient-text">Creativity</span>
            </h1>
            <p style="font-size: 1.125rem; color: #d1d5db; max-width: 450px; line-height: 1.6;">
                Unlock the power of AI to generate compelling LinkedIn content with viral potential, all with a single click.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Right Login Form (no glass-card wrapper - Streamlit tabs handle their own styling)
    with col_form:
        # Tabs for Login/Signup/Forgot Password
        tab1, tab2, tab3 = st.tabs(["Log In", "Sign Up", "Recovery"])
        
        with tab1:
            st.markdown("<h3 style='text-align: center; margin-bottom: 5px;'>Welcome Back</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.6); margin-bottom: 20px;'>Sign in to access your dashboard</p>", unsafe_allow_html=True)
            
            with st.form("login_form"):
                email = st.text_input("Email Address", placeholder="your@email.com", key="login_email")
                password = st.text_input("Password", type="password", placeholder="••••••••", key="login_password")
                
                remember = st.checkbox("Remember me")
                
                submit = st.form_submit_button("Log In", type="primary", use_container_width=True)
                
                if submit:
                    if email and password:
                        from auth.clerk_auth import authenticate_user
                        with st.spinner("Logging in..."):
                            success, message, user_data = authenticate_user(email, password)
                        
                        if success and user_data:
                            st.session_state.user = user_data
                            st.success(f"✅ {message}")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.error("Please enter both email and password")
        
        with tab2:
            st.markdown("<h3 style='text-align: center;'>Create Account</h3>", unsafe_allow_html=True)
            
            with st.form("signup_form"):
                col_f, col_l = st.columns(2)
                with col_f:
                    first_name = st.text_input("First Name", placeholder="John", key="signup_first")
                with col_l:
                    last_name = st.text_input("Last Name", placeholder="Doe", key="signup_last")
                
                email = st.text_input("Email", placeholder="your@email.com", key="signup_email")
                password = st.text_input("Password", type="password", placeholder="••••••••", key="signup_password")
                
                agree = st.checkbox("I agree to Terms & Privacy")
                
                submit = st.form_submit_button("Create Account", type="primary", use_container_width=True)
                
                if submit:
                    if not all([first_name, last_name, email, password]):
                        st.error("Please fill in all fields")
                    elif len(password) < 8:
                        st.error("Password must be at least 8 characters")
                    elif not agree:
                        st.error("Please agree to the Terms")
                    else:
                        from auth.clerk_auth import create_user
                        with st.spinner("Creating account..."):
                            success, message, user_data = create_user(email, password, first_name, last_name)
                        
                        if success and user_data:
                            st.session_state.user = user_data
                            st.success(f"✅ {message}")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
        
        with tab3:
            st.markdown("<h3 style='text-align: center;'>Reset Password</h3>", unsafe_allow_html=True)
            st.info("Enter your email to receive a reset link.")
            
            with st.form("forgot_password_form"):
                email = st.text_input("Email", placeholder="your@email.com", key="forgot_email")
                submit = st.form_submit_button("Send Link", type="primary", use_container_width=True)
                
                if submit:
                    if email:
                        st.success(f"✅ Reset link sent to **{email}**")
                    else:
                        st.error("Please enter your email")

def show_user_menu():
    """
    Display user menu in sidebar with logout option
    """
    user = get_current_user()
    
    if not user:
        return
    
    with st.sidebar:
        st.markdown("---")
        
        # User info
        col1, col2 = st.columns([1, 3])
        with col1:
            if user.get("image_url"):
                st.image(user["image_url"], width=50)
            else:
                st.markdown("👤")
        
        with col2:
            st.markdown(f"**{user.get('first_name', '')} {user.get('last_name', '')}**")
            st.caption(user.get('email', ''))
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.success("✅ Logged out successfully")
            st.rerun()


def init_auth():
    """
    Initialize authentication state.
    Call this at the start of your Streamlit app.
    """
    # Initialize session state
    if "user" not in st.session_state:
        st.session_state.user = None
    
    if "clerk_session_token" not in st.session_state:
        st.session_state.clerk_session_token = None
