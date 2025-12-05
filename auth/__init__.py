"""
Authentication module for CIS
"""

from auth.clerk_auth import (
    get_clerk_client,
    create_user,
    authenticate_user,
    verify_session,
    get_current_user,
    is_authenticated,
    logout
)

from auth.streamlit_auth import (
    require_auth,
    show_login_page,
    show_user_menu,
    init_auth
)

__all__ = [
    'get_clerk_client',
    'create_user',
    'authenticate_user',
    'verify_session',
    'get_current_user',
    'is_authenticated',
    'logout',
    'require_auth',
    'show_login_page',
    'show_user_menu',
    'init_auth'
]

