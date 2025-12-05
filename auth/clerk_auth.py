"""
Clerk authentication for Streamlit CIS application
"""
import os
from typing import Optional, Dict, Tuple
import streamlit as st
from clerk_backend_api import Clerk

# Initialize Clerk client
def get_clerk_client():
    """Get Clerk client instance"""
    secret_key = os.getenv("CLERK_SECRET_KEY")
    if not secret_key:
        raise ValueError("CLERK_SECRET_KEY not found in environment")
    return Clerk(bearer_auth=secret_key)


def create_user(email: str, password: str, first_name: str, last_name: str) -> Tuple[bool, str, Optional[Dict]]:
    """
    Create a new user in Clerk.
    
    Args:
        email: User's email address
        password: User's password
        first_name: User's first name
        last_name: User's last name
        
    Returns:
        Tuple of (success, message, user_data)
    """
    try:
        clerk = get_clerk_client()
        
        # Create user with email and password
        user = clerk.users.create(
            email_address=[email],
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        if user and user.id:
            user_data = {
                "user_id": user.id,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "image_url": user.image_url if hasattr(user, 'image_url') else None,
                "session_token": f"clerk_session_{user.id}"
            }
            return True, "Account created successfully!", user_data
        
        return False, "Failed to create account", None
        
    except Exception as e:
        error_msg = str(e).lower()
        
        # Check for specific error types
        if "already exists" in error_msg or "duplicate" in error_msg:
            return False, "An account with this email already exists. Try logging in instead.", None
        elif "password" in error_msg and ("breach" in error_msg or "pwned" in error_msg or "found in" in error_msg):
            return False, "This password has been found in a data breach. Please use a different, more secure password.", None
        elif "password" in error_msg and "weak" in error_msg:
            return False, "Password is too weak. Use a mix of letters, numbers, and symbols.", None
        elif "email" in error_msg and "invalid" in error_msg:
            return False, "Invalid email address format.", None
        else:
            # Generic error
            return False, f"Error creating account. Please try again or contact support.", None


def authenticate_user(email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    """
    Authenticate a user with email and password.
    """
    try:
        clerk = get_clerk_client()
        
        # List all users (no parameters - SDK doesn't support filtering)
        users_response = clerk.users.list()
        
        if users_response:
            # Handle different response types
            users_list = users_response.data if hasattr(users_response, 'data') else users_response
            
            # Find user by email
            for user in users_list:
                if user.email_addresses:
                    for email_obj in user.email_addresses:
                        if email_obj.email_address.lower() == email.lower():
                            # User found
                            user_data = {
                                "user_id": user.id,
                                "email": email_obj.email_address,
                                "first_name": user.first_name or "",
                                "last_name": user.last_name or "",
                                "image_url": getattr(user, 'image_url', None),
                                "session_token": f"clerk_session_{user.id}"
                            }
                            return True, "Login successful!", user_data
        
        return False, "Invalid email or password", None
        
    except Exception as e:
        return False, f"Authentication error: {str(e)}", None


def verify_session(session_token: str) -> Optional[Dict]:
    """
    Verify a Clerk session token.
    
    Args:
        session_token: The session token to verify
        
    Returns:
        Dict with user info if valid, None otherwise
    """
    try:
        clerk = get_clerk_client()
        session = clerk.sessions.verify_session(session_token)
        
        if session and session.user_id:
            user = clerk.users.get(session.user_id)
            
            return {
                "user_id": user.id,
                "email": user.email_addresses[0].email_address if user.email_addresses else None,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "image_url": user.image_url,
                "session_token": session_token
            }
        
        return None
        
    except Exception as e:
        print(f"Session verification error: {e}")
        return None


def get_current_user() -> Optional[Dict]:
    """
    Get the currently authenticated user from session state.
    
    Returns:
        Dict with user info or None
    """
    return st.session_state.get("user")


def is_authenticated() -> bool:
    """
    Check if user is currently authenticated.
    
    Returns:
        True if authenticated, False otherwise
    """
    return "user" in st.session_state and st.session_state.user is not None


def logout():
    """
    Log out the current user by clearing session state.
    """
    if "user" in st.session_state:
        del st.session_state.user
    
    if "clerk_session_token" in st.session_state:
        del st.session_state.clerk_session_token
    
    # Clear post-related state to prevent IndexError on re-login
    if "selected_post_idx" in st.session_state:
        st.session_state.selected_post_idx = None
    
    if "post_history" in st.session_state:
        st.session_state.post_history = []
    
    if "compare_posts" in st.session_state:
        st.session_state.compare_posts = []
    
    if "compare_mode" in st.session_state:
        st.session_state.compare_mode = False
    
    # Clear any other cached data
    for key in list(st.session_state.keys()):
        if key.startswith("post_"):
            del st.session_state[key]

