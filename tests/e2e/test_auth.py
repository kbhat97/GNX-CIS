"""
Authentication Tests for GNX CIS Dashboard
Tests: UI elements, login success/failure, validation, session, logout
"""
import pytest
from playwright.sync_api import Page, expect
from tests.e2e.selectors import LoginSelectors as Login, DashboardSelectors as Dashboard


class TestLoginUI:
    """Tests for login page UI elements."""
    
    @pytest.mark.smoke
    def test_login_ui_elements(self, page: Page, base_url: str):
        """
        Verify login page has required UI elements:
        - Email input field
        - Password input field
        - Login button
        - Forgot password link
        """
        page.goto(base_url)
        
        # Verify email field
        email_input = page.locator(Login.EMAIL)
        expect(email_input).to_be_visible()
        expect(email_input).to_have_attribute("type", "email")
        expect(email_input).to_have_attribute("placeholder", "your@email.com")
        
        # Verify password field
        password_input = page.locator(Login.PASSWORD)
        expect(password_input).to_be_visible()
        expect(password_input).to_have_attribute("type", "password")
        
        # Verify login button
        login_btn = page.locator(Login.SUBMIT)
        expect(login_btn).to_be_visible()
        expect(login_btn).to_contain_text("Sign In")
        
        # Verify forgot password link (if present)
        forgot_link = page.locator(Login.FORGOT_PASSWORD_LINK)
        expect(forgot_link).to_be_visible()


class TestLoginSuccess:
    """Tests for successful login flow."""
    
    @pytest.mark.smoke
    def test_login_success_redirects_to_dashboard(self, page: Page, base_url: str):
        """
        Valid credentials should:
        1. Trigger login API call
        2. Redirect to dashboard
        3. Show dashboard elements
        """
        page.goto(base_url)
        
        # Fill valid admin credentials
        page.fill(Login.EMAIL, "kunalsbhatt@gmail.com")
        page.fill(Login.PASSWORD, "test123")  # Demo mode: any password works
        
        # Click login
        page.click(Login.SUBMIT)
        
        # Wait for dashboard to load
        page.wait_for_selector(f"{Dashboard.PAGE}:not(.hidden)", timeout=15000)
        
        # Verify dashboard elements are visible
        expect(page.locator(Dashboard.PAGE)).to_be_visible()
        
        # Verify login page is hidden
        expect(page.locator(Login.PAGE)).not_to_be_visible()


class TestLoginErrors:
    """Tests for login error handling."""
    
    def test_login_invalid_credentials_shows_error(
        self, page: Page, base_url: str, mock_login_401
    ):
        """
        Invalid credentials should:
        1. NOT redirect to dashboard
        2. Show error message
        3. Keep login button enabled
        """
        page.goto(base_url)
        
        # Fill invalid credentials
        page.fill(Login.EMAIL, "invalid@example.com")
        page.fill(Login.PASSWORD, "wrongpassword")
        
        # Click login
        page.click(Login.SUBMIT)
        
        # Wait for error to appear
        error_msg = page.locator(Login.ERROR)
        expect(error_msg).to_be_visible(timeout=5000)
        
        # Verify still on login page
        expect(page.locator(Login.PAGE)).to_be_visible()
        expect(page.locator(Dashboard.PAGE)).not_to_be_visible()
        
        # Verify login button is still usable
        expect(page.locator(Login.SUBMIT)).to_be_enabled()
    
    def test_login_field_validations(self, page: Page, base_url: str):
        """
        Submitting with empty fields should:
        1. Show validation messages (HTML5)
        2. NOT fire network request
        """
        page.goto(base_url)
        
        # Track network requests
        requests_made = []
        page.on("request", lambda req: requests_made.append(req.url))
        
        # Try to submit with empty email
        page.fill(Login.EMAIL, "")
        page.fill(Login.PASSWORD, "somepassword")
        page.click(Login.SUBMIT)
        
        # HTML5 validation should prevent submission
        # Check that no login API call was made
        login_requests = [r for r in requests_made if "auth" in r or "login" in r]
        assert len(login_requests) == 0, "Login request should not be made with invalid input"
        
        # Verify still on login page
        expect(page.locator(Login.PAGE)).to_be_visible()


class TestSession:
    """Tests for session persistence and logout."""
    
    def test_session_persists_across_reload(self, authenticated_admin: Page):
        """
        After login, reloading should:
        1. Keep user on dashboard
        2. Preserve admin UI elements
        3. NOT redirect to login
        """
        page = authenticated_admin
        
        # Verify we're on dashboard
        expect(page.locator(Dashboard.PAGE)).to_be_visible()
        
        # Reload the page
        page.reload()
        
        # Wait for page to settle
        page.wait_for_load_state("networkidle")
        
        # Verify still on dashboard (session persisted)
        expect(page.locator(Dashboard.PAGE)).to_be_visible()
        
        # Verify admin-specific elements still visible (if any)
        expect(page.locator(Dashboard.USER_NAME)).to_be_visible()
    
    @pytest.mark.smoke
    def test_logout_clears_session(self, authenticated_admin: Page, base_url: str):
        """
        Logout should:
        1. Redirect to login page
        2. Clear session/auth token
        3. Prevent dashboard access
        """
        page = authenticated_admin
        
        # Click logout button using centralized selector
        page.click(Dashboard.LOGOUT_BTN)
        
        # Wait for redirect to login
        page.wait_for_selector(f"{Login.PAGE}:not(.hidden)", timeout=10000)
        
        # Verify on login page
        expect(page.locator(Login.PAGE)).to_be_visible()
        expect(page.locator(Dashboard.PAGE)).not_to_be_visible()
        
        # Try to access dashboard directly
        page.goto(base_url)
        
        # Should be redirected back to login
        page.wait_for_selector(f"{Login.PAGE}:not(.hidden)", timeout=10000)
        expect(page.locator(Login.PAGE)).to_be_visible()


class TestForgotPassword:
    """Tests for forgot password flow."""
    
    @pytest.mark.xfail(reason="Forgot password UI not implemented in app.html - reset-password-btn, reset-success elements missing")
    def test_forgot_password_ui_flow(self, page: Page, base_url: str):
        """
        Forgot password should:
        1. Show forgot password form when clicked
        2. Accept email input
        3. Generate and display temp password
        4. Allow login with temp password
        """
        page.goto(base_url)
        
        # Click forgot password link
        page.click(Login.FORGOT_PASSWORD_LINK)
        
        # Verify forgot password form is visible
        expect(page.locator(Login.FORGOT_PASSWORD_FORM)).to_be_visible()
        expect(page.locator("#login-form")).not_to_be_visible()
        
        # Verify reset email input is visible
        expect(page.locator(Login.RESET_EMAIL)).to_be_visible()
        expect(page.locator(Login.RESET_BTN)).to_be_visible()
        
        # Fill in email
        page.fill(Login.RESET_EMAIL, "testuser@example.com")
        
        # Click reset button
        page.click(Login.RESET_BTN)
        
        # Wait for success message with temp password
        page.wait_for_selector(f"{Login.RESET_SUCCESS}:not(.hidden)", timeout=5000)
        expect(page.locator(Login.RESET_SUCCESS)).to_be_visible()
        
        # Get temp password from success message
        success_text = page.locator(Login.RESET_SUCCESS).text_content()
        assert "Temporary password" in success_text or "temp" in success_text.lower()
    
    @pytest.mark.xfail(reason="Forgot password UI not implemented in app.html")
    def test_forgot_password_back_to_login(self, page: Page, base_url: str):
        """
        User should be able to go back to login from forgot password.
        """
        page.goto(base_url)
        
        # Click forgot password
        page.click(Login.FORGOT_PASSWORD_LINK)
        expect(page.locator(Login.FORGOT_PASSWORD_FORM)).to_be_visible()
        
        # Click back to login
        page.click("text=Back to Sign In")
        
        # Verify back on login form
        expect(page.locator("#login-form")).to_be_visible()
        expect(page.locator(Login.FORGOT_PASSWORD_FORM)).not_to_be_visible()
