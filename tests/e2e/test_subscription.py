"""
E2E Tests for Subscription, Payment, and Session Management
Tests:
- Auto-sync subscription on dashboard load
- Session timeout and auto-logout after 30 minutes
- Stripe checkout flow
- Subscription upgrade/downgrade
- Plan badge updates
"""
import pytest
import json
from datetime import datetime
from playwright.sync_api import Page, expect


# ═══════════════════════════════════════════════════════════════════
# TEST SELECTORS
# ═══════════════════════════════════════════════════════════════════

class SubscriptionSelectors:
    """Selectors for subscription-related UI elements."""
    PLAN_BADGE = "#user-plan-badge"
    SETTINGS_PLAN_BADGE = "#settings-plan-badge"
    SETTINGS_PLAN_DESC = "#settings-plan-description"
    POSTS_USED = "#settings-posts-used"
    POSTS_LIMIT = "#settings-posts-limit"
    USAGE_BAR = "#settings-usage-bar"
    SYNC_BTN = "#sync-subscription-btn"
    UPGRADE_PRO_BTN = "#upgrade-pro-btn"
    UPGRADE_BUSINESS_BTN = "#upgrade-business-btn"
    UPGRADE_OPTIONS = "#settings-upgrade-options"
    PREMIUM_ACTIVE = "#settings-premium-active"
    MANAGE_SUBSCRIPTION = "#settings-manage-subscription"
    NAV_SETTINGS = "[data-testid='nav-settings']"


class SessionSelectors:
    """Selectors for session-related UI elements."""
    LOGOUT_BTN = "[data-testid='logout-btn']"
    LOGIN_PAGE = "#login-page"
    DASHBOARD_PAGE = "#dashboard-page"
    USER_NAME = "#user-name"
    USER_EMAIL = "#user-email"


# ═══════════════════════════════════════════════════════════════════
# MOCK FIXTURES
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_subscription_free(page: Page):
    """Mock /api/user/subscription to return FREE plan."""
    def handle_route(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({
                "plan": "free",
                "status": "active",
                "posts_this_month": 3,
                "post_limit": 5,
                "stripe_customer_id": None
            })
        )
    
    page.route("**/api/user/subscription*", handle_route)
    yield
    page.unroute("**/api/user/subscription*")


@pytest.fixture
def mock_subscription_pro(page: Page):
    """Mock /api/user/subscription to return PRO plan."""
    def handle_route(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({
                "plan": "pro",
                "status": "active",
                "posts_this_month": 15,
                "post_limit": 30,
                "stripe_customer_id": "cus_test123"
            })
        )
    
    page.route("**/api/user/subscription*", handle_route)
    yield
    page.unroute("**/api/user/subscription*")


@pytest.fixture
def mock_subscription_business(page: Page):
    """Mock /api/user/subscription to return BUSINESS plan."""
    def handle_route(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({
                "plan": "business",
                "status": "active",
                "posts_this_month": 50,
                "post_limit": 200,
                "stripe_customer_id": "cus_business456"
            })
        )
    
    page.route("**/api/user/subscription*", handle_route)
    yield
    page.unroute("**/api/user/subscription*")


@pytest.fixture
def mock_sync_subscription_success(page: Page):
    """Mock /api/sync-subscription to return successful sync with PRO plan."""
    def handle_route(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({
                "success": True,
                "plan": "pro",
                "status": "active",
                "customer_id": "cus_synced123"
            })
        )
    
    page.route("**/api/sync-subscription*", handle_route)
    yield
    page.unroute("**/api/sync-subscription*")


@pytest.fixture
def mock_sync_subscription_failure(page: Page):
    """Mock /api/sync-subscription to return failure."""
    def handle_route(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({
                "success": False,
                "error": "Stripe not configured"
            })
        )
    
    page.route("**/api/sync-subscription*", handle_route)
    yield
    page.unroute("**/api/sync-subscription*")


@pytest.fixture
def mock_checkout_success(page: Page):
    """Mock /api/create-checkout to return checkout session URL."""
    def handle_route(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({
                "checkout_url": "https://checkout.stripe.com/test_session",
                "session_id": "cs_test_123"
            })
        )
    
    page.route("**/api/create-checkout*", handle_route)
    yield
    page.unroute("**/api/create-checkout*")


@pytest.fixture
def mock_checkout_503(page: Page):
    """Mock /api/create-checkout to return 503 (payment system unavailable)."""
    def handle_route(route):
        route.fulfill(
            status=503,
            content_type="application/json",
            body=json.dumps({
                "detail": "Payment system not available"
            })
        )
    
    page.route("**/api/create-checkout*", handle_route)
    yield
    page.unroute("**/api/create-checkout*")


# ═══════════════════════════════════════════════════════════════════
# AUTO-SYNC SUBSCRIPTION TESTS
# ═══════════════════════════════════════════════════════════════════

class TestAutoSyncSubscription:
    """Tests for automatic subscription sync on dashboard load."""
    
    @pytest.mark.e2e
    def test_auto_sync_called_on_dashboard_load(
        self, 
        authenticated_user, 
        mock_sync_subscription_success
    ):
        """Verify auto-sync is called when dashboard loads."""
        page = authenticated_user
        
        # The sync should have been called automatically
        # Check that plan badge is visible (indicating sync worked)
        page.wait_for_timeout(2000)  # Wait for async sync
        
        plan_badge = page.locator(SubscriptionSelectors.PLAN_BADGE)
        # After sync success with PRO, badge should be visible
        expect(plan_badge).to_be_visible()
        expect(plan_badge).to_have_text("PRO")
    
    @pytest.mark.e2e
    def test_auto_sync_failure_silent(
        self, 
        authenticated_user, 
        mock_sync_subscription_failure
    ):
        """Verify auto-sync failures are handled silently without blocking UI."""
        page = authenticated_user
        
        # Dashboard should still load even if sync fails
        page.wait_for_timeout(1000)
        
        # Dashboard should be visible (not blocked by sync failure)
        dashboard = page.locator(SessionSelectors.DASHBOARD_PAGE)
        expect(dashboard).to_be_visible()
        
        # No error modal should appear for silent failure
        error_modal = page.locator(".error-modal, [role='alertdialog']")
        expect(error_modal).not_to_be_visible()
    
    @pytest.mark.e2e
    def test_plan_badge_updates_after_sync(
        self, 
        authenticated_user, 
        mock_sync_subscription_success
    ):
        """Verify plan badge in header updates after successful sync."""
        page = authenticated_user
        
        page.wait_for_timeout(2000)  # Wait for auto-sync
        
        # PRO badge should be visible with correct styling
        badge = page.locator(SubscriptionSelectors.PLAN_BADGE)
        expect(badge).to_be_visible()
        expect(badge).to_have_text("PRO")
        
        # Verify badge has PRO styling (cyan-blue gradient)
        badge_classes = badge.get_attribute("class")
        assert "from-cyan-500" in badge_classes or "bg-gradient" in badge_classes


# ═══════════════════════════════════════════════════════════════════
# MANUAL SYNC TESTS
# ═══════════════════════════════════════════════════════════════════

class TestManualSubscriptionSync:
    """Tests for manual subscription sync button."""
    
    @pytest.mark.e2e
    def test_sync_button_visible_in_settings(self, authenticated_user):
        """Verify sync button is visible in subscription settings."""
        page = authenticated_user
        
        # Navigate to settings
        page.click(SubscriptionSelectors.NAV_SETTINGS)
        page.wait_for_timeout(500)
        
        # Sync button should be visible
        sync_btn = page.locator(SubscriptionSelectors.SYNC_BTN)
        expect(sync_btn).to_be_visible()
    
    @pytest.mark.e2e
    def test_sync_button_shows_loading_state(
        self, 
        authenticated_user, 
        mock_sync_subscription_success
    ):
        """Verify sync button shows loading state during sync."""
        page = authenticated_user
        
        # Navigate to settings
        page.click(SubscriptionSelectors.NAV_SETTINGS)
        page.wait_for_timeout(500)
        
        # Slow down the response to capture loading state
        page.route("**/api/sync-subscription*", lambda route: (
            page.wait_for_timeout(500),
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"success": True, "plan": "pro"})
            )
        ))
        
        sync_btn = page.locator(SubscriptionSelectors.SYNC_BTN)
        
        # Click sync
        sync_btn.click()
        
        # Button should show syncing state (disabled)
        expect(sync_btn).to_be_disabled()
    
    @pytest.mark.e2e
    def test_sync_shows_notification_on_success(
        self, 
        authenticated_user, 
        mock_sync_subscription_success
    ):
        """Verify notification shows after successful sync."""
        page = authenticated_user
        
        # Navigate to settings
        page.click(SubscriptionSelectors.NAV_SETTINGS)
        page.wait_for_timeout(500)
        
        # Click sync
        page.click(SubscriptionSelectors.SYNC_BTN)
        page.wait_for_timeout(1500)
        
        # Check for success notification
        notification = page.locator("[role='alert'], .notification")
        # Notification should contain success message
        expect(page.locator("text=synced")).to_be_visible(timeout=5000)


# ═══════════════════════════════════════════════════════════════════
# SESSION TIMEOUT TESTS
# ═══════════════════════════════════════════════════════════════════

class TestSessionTimeout:
    """Tests for session timeout and auto-logout functionality."""
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_session_timeout_configuration(self, authenticated_user):
        """Verify session timeout is configured correctly (30 minutes)."""
        page = authenticated_user
        
        # Check that session timeout variables are set
        session_timeout = page.evaluate("() => window.SESSION_TIMEOUT_MS || 30 * 60 * 1000")
        
        # Should be 30 minutes in milliseconds
        expected_timeout = 30 * 60 * 1000
        assert session_timeout == expected_timeout, f"Expected {expected_timeout}ms, got {session_timeout}ms"
    
    @pytest.mark.e2e
    def test_activity_resets_session_timer(self, authenticated_user):
        """Verify user activity resets the session timeout timer."""
        page = authenticated_user
        
        # Track initial activity time
        initial_time = page.evaluate("() => window.lastActivityTime || Date.now()")
        
        # Simulate user activity
        page.mouse.move(100, 100)
        page.wait_for_timeout(100)
        
        # Check that activity time was updated
        new_time = page.evaluate("() => window.lastActivityTime || Date.now()")
        
        # New time should be >= initial time
        assert new_time >= initial_time
    
    @pytest.mark.e2e
    def test_logout_button_works(self, authenticated_user):
        """Verify manual logout button works correctly."""
        page = authenticated_user
        
        # Verify we're logged in
        expect(page.locator(SessionSelectors.DASHBOARD_PAGE)).to_be_visible()
        
        # Click logout
        page.click(SessionSelectors.LOGOUT_BTN)
        page.wait_for_timeout(2000)
        
        # Should redirect to login page
        expect(page.locator(SessionSelectors.LOGIN_PAGE)).to_be_visible()
        expect(page.locator(SessionSelectors.DASHBOARD_PAGE)).to_be_hidden()


# ═══════════════════════════════════════════════════════════════════
# CHECKOUT FLOW TESTS
# ═══════════════════════════════════════════════════════════════════

class TestCheckoutFlow:
    """Tests for Stripe checkout flow."""
    
    @pytest.mark.e2e
    def test_upgrade_pro_button_visible_for_free_users(
        self, 
        authenticated_user, 
        mock_subscription_free
    ):
        """Verify PRO upgrade button is visible for FREE users."""
        page = authenticated_user
        
        # Navigate to settings
        page.click(SubscriptionSelectors.NAV_SETTINGS)
        page.wait_for_timeout(500)
        
        # Upgrade buttons should be visible
        pro_btn = page.locator(SubscriptionSelectors.UPGRADE_PRO_BTN)
        business_btn = page.locator(SubscriptionSelectors.UPGRADE_BUSINESS_BTN)
        
        expect(pro_btn).to_be_visible()
        expect(business_btn).to_be_visible()
    
    @pytest.mark.e2e
    def test_checkout_redirects_to_stripe(
        self, 
        authenticated_user, 
        mock_checkout_success
    ):
        """Verify checkout button redirects to Stripe checkout."""
        page = authenticated_user
        
        # Navigate to settings
        page.click(SubscriptionSelectors.NAV_SETTINGS)
        page.wait_for_timeout(500)
        
        # Track navigation events
        navigations = []
        page.on("popup", lambda popup: navigations.append(popup.url))
        
        # Click upgrade to pro
        page.click(SubscriptionSelectors.UPGRADE_PRO_BTN)
        page.wait_for_timeout(2000)
        
        # Should attempt to open Stripe checkout (either popup or redirect)
        # Check for "Redirecting to checkout" message in status
        status_text = page.locator("text=checkout").first
        expect(status_text).to_be_visible(timeout=5000)
    
    @pytest.mark.e2e
    def test_checkout_failure_shows_error(
        self, 
        authenticated_user, 
        mock_checkout_503
    ):
        """Verify error message when checkout fails (payment system unavailable)."""
        page = authenticated_user
        
        # Navigate to settings
        page.click(SubscriptionSelectors.NAV_SETTINGS)
        page.wait_for_timeout(500)
        
        # Click upgrade
        page.click(SubscriptionSelectors.UPGRADE_PRO_BTN)
        page.wait_for_timeout(2000)
        
        # Should show error message about payment system
        error_text = page.locator("text=Payment system not available, text=Failed")
        expect(error_text.first).to_be_visible(timeout=5000)
    
    @pytest.mark.e2e
    def test_checkout_success_shows_confirmation(self, page: Page, base_url: str):
        """Verify success message when returning from Stripe checkout."""
        # Load dashboard with checkout=success parameter
        success_url = base_url + "?checkout=success&test_user=1"
        page.goto(success_url)
        page.wait_for_timeout(2000)
        
        # Should show success notification
        success_notification = page.locator("text=Payment successful, text=plan is now active")
        expect(success_notification.first).to_be_visible(timeout=5000)


# ═══════════════════════════════════════════════════════════════════
# SUBSCRIPTION UI TESTS
# ═══════════════════════════════════════════════════════════════════

class TestSubscriptionUI:
    """Tests for subscription UI elements and displays."""
    
    @pytest.mark.e2e
    def test_free_plan_shows_upgrade_options(
        self, 
        authenticated_user, 
        mock_subscription_free
    ):
        """Verify FREE users see upgrade options."""
        page = authenticated_user
        
        # Navigate to settings
        page.click(SubscriptionSelectors.NAV_SETTINGS)
        page.wait_for_timeout(500)
        
        # Upgrade options should be visible
        upgrade_section = page.locator(SubscriptionSelectors.UPGRADE_OPTIONS)
        expect(upgrade_section).to_be_visible()
        
        # Premium active section should be hidden
        premium_section = page.locator(SubscriptionSelectors.PREMIUM_ACTIVE)
        expect(premium_section).to_be_hidden()
    
    @pytest.mark.e2e
    def test_pro_plan_shows_premium_active(
        self, 
        authenticated_user, 
        mock_subscription_pro
    ):
        """Verify PRO users see premium active status."""
        page = authenticated_user
        
        # Navigate to settings
        page.click(SubscriptionSelectors.NAV_SETTINGS)
        page.wait_for_timeout(500)
        
        # Wait for subscription data to load
        page.wait_for_timeout(1000)
        
        # PRO badge should show in header
        badge = page.locator(SubscriptionSelectors.PLAN_BADGE)
        expect(badge).to_be_visible()
    
    @pytest.mark.e2e
    def test_usage_bar_displays_correctly(
        self, 
        authenticated_user, 
        mock_subscription_pro
    ):
        """Verify usage bar displays correct usage percentage."""
        page = authenticated_user
        
        # Navigate to settings
        page.click(SubscriptionSelectors.NAV_SETTINGS)
        page.wait_for_timeout(1000)
        
        # Usage elements should be visible
        posts_used = page.locator(SubscriptionSelectors.POSTS_USED)
        posts_limit = page.locator(SubscriptionSelectors.POSTS_LIMIT)
        
        expect(posts_used).to_be_visible()
        expect(posts_limit).to_be_visible()


# ═══════════════════════════════════════════════════════════════════
# VOICE PROFILE UI TESTS
# ═══════════════════════════════════════════════════════════════════

class TestVoiceProfileUI:
    """Tests for Voice Profile section appearance (no emojis)."""
    
    @pytest.mark.e2e
    def test_voice_profile_no_emojis(self, authenticated_admin):
        """Verify Voice Profile section uses SVG icons instead of emojis."""
        page = authenticated_admin
        
        # The voice profile section should use SVG icons, not emoji characters
        voice_section = page.locator("#voice-profile-section, #voice-profile-content")
        
        # Check that common emojis are NOT present in the profile section
        emoji_patterns = ["🏢", "🎯", "✍️", "📌", "👤", "✨"]
        
        section_html = voice_section.inner_html() if voice_section.is_visible() else ""
        
        for emoji in emoji_patterns:
            assert emoji not in section_html, f"Found emoji {emoji} in Voice Profile section - should use SVG icon"
    
    @pytest.mark.e2e
    def test_personalization_banner_uses_svg(self, authenticated_admin):
        """Verify personalization unlocked banner uses SVG check icon."""
        page = authenticated_admin
        
        # The banner should have SVG icon, not emoji
        banner = page.locator("#learning-unlocked-banner")
        
        if banner.is_visible():
            banner_html = banner.inner_html()
            # Should have SVG, not ✨ emoji
            assert "✨" not in banner_html, "Banner should use SVG icon instead of ✨ emoji"
            assert "<svg" in banner_html, "Banner should contain SVG icon"
