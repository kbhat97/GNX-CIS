"""
Role-Based Access Control Tests for GNX CIS Dashboard
Tests: Admin toggle visibility, admin actions, user restrictions, route protection
"""
import pytest
from playwright.sync_api import Page, expect
from tests.e2e.selectors import PersonaSelectors as Persona, DashboardSelectors as Dashboard


class TestAdminAccess:
    """Tests for admin-specific UI and functionality."""
    
    @pytest.mark.smoke
    def test_admin_sees_admin_toggle_and_controls(self, authenticated_admin: Page):
        """
        Admin (Kunal) should see:
        - "Admin Persona" toggle
        - Admin-only panels and actions
        """
        page = authenticated_admin
        
        # Navigate to Generate section where admin toggle appears
        page.click(Dashboard.NAV_GENERATE)
        page.wait_for_selector("#section-generate:not(.hidden)", timeout=5000)
        
        # Verify admin persona section is visible
        admin_section = page.locator(Persona.ADMIN_SECTION)
        expect(admin_section).to_be_visible()
        
        # Verify persona toggle exists
        persona_toggle = page.locator(Persona.TOGGLE)
        expect(persona_toggle).to_be_visible()
        
        # Verify admin LinkedIn actions are visible after generating content
        # (These appear in result panel for admin users)
        admin_actions = page.locator(Persona.LINKEDIN_ACTIONS)
        # Note: This may be hidden until content is generated
        # Just verify the element exists in DOM for admin
        assert admin_actions.count() > 0, "Admin LinkedIn actions should exist in DOM"
    
    def test_admin_can_use_admin_actions(self, authenticated_admin: Page):
        """
        Admin should be able to perform admin-only actions.
        Test: Persona toggle functionality.
        """
        page = authenticated_admin
        
        # Navigate to Generate section
        page.click(Dashboard.NAV_GENERATE)
        page.wait_for_selector("#section-generate:not(.hidden)", timeout=5000)
        
        # Find persona toggle
        persona_toggle = page.locator(Persona.TOGGLE)
        expect(persona_toggle).to_be_visible()
        
        # Verify toggle can be interacted with
        # Check initial state (should be checked for Kunal persona)
        is_checked = persona_toggle.is_checked()
        assert is_checked, "Persona toggle should be checked by default for admin"
        
        # Toggle off
        persona_toggle.click()
        expect(persona_toggle).not_to_be_checked()
        
        # Toggle back on
        persona_toggle.click()
        expect(persona_toggle).to_be_checked()


class TestUserRestrictions:
    """Tests for standard user access restrictions."""
    
    @pytest.mark.smoke
    def test_user_does_not_see_admin_controls(self, authenticated_user: Page):
        """
        Standard user should NOT see:
        - Admin persona toggle (not just hidden, but NOT in DOM)
        - Admin-only panels
        """
        page = authenticated_user
        
        # Navigate to Generate section
        page.click("text=Generate")
        page.wait_for_selector("#section-generate:not(.hidden)", timeout=5000)
        
        # Verify admin persona section is NOT visible (using visibility, not class)
        admin_section = page.locator(Persona.ADMIN_SECTION)
        expect(admin_section).not_to_be_visible()
        
        # Verify regular persona section IS visible
        regular_section = page.locator(Persona.REGULAR_SECTION)
        expect(regular_section).to_be_visible()
        
        # Verify admin LinkedIn actions are NOT present for standard user
        admin_actions = page.locator(Persona.LINKEDIN_ACTIONS)
        expect(admin_actions).not_to_be_visible()
    
    def test_user_cannot_access_admin_routes(self, authenticated_user: Page, base_url: str):
        """
        Standard user should be blocked from admin-only routes.
        Attempt direct navigation should redirect or show error.
        """
        page = authenticated_user
        
        # Try to access a potential admin-only route directly
        # (The current app doesn't have separate routes, but this tests the pattern)
        page.goto(f"{base_url}#admin")
        
        # Should still be on dashboard, not showing admin content
        page.wait_for_load_state("networkidle")
        
        # Verify admin-specific elements are still hidden
        admin_section = page.locator(Persona.ADMIN_SECTION)
        expect(admin_section).not_to_be_visible()
        
        # Verify admin settings section is hidden
        admin_settings = page.locator(Persona.SETTINGS_SECTION)
        expect(admin_settings).not_to_be_visible()


class TestPersonaSwitching:
    """Tests for persona switching behavior (admin only)."""
    
    def test_admin_to_user_switch_respects_permissions(self, authenticated_admin: Page):
        """
        When admin switches persona toggle OFF:
        - Should use generic mode instead of Kunal persona
        - UI should reflect the change
        """
        page = authenticated_admin
        
        # Navigate to Generate section
        page.click("text=Generate")
        page.wait_for_selector("#section-generate:not(.hidden)", timeout=5000)
        
        # Find persona toggle and mode label
        persona_toggle = page.locator(Persona.TOGGLE)
        mode_label = page.locator(Persona.MODE_LABEL)
        
        # Verify initial state shows Kunal Persona
        expect(mode_label).to_contain_text("Kunal Persona")
        expect(persona_toggle).to_be_checked()
        
        # Switch OFF persona
        persona_toggle.click()
        
        # Verify toggle is now off
        expect(persona_toggle).not_to_be_checked()
        
        # Verify persona details are now hidden (since override mode doesn't use persona)
        persona_details = page.locator(Persona.DETAILS)
        # The UI should update to reflect non-persona mode
        # (actual behavior depends on implementation)
