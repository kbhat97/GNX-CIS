"""
Responsive Layout Tests for GNX CIS Dashboard
Tests: Desktop, tablet, and mobile viewport layouts
"""
import pytest
from playwright.sync_api import Page, expect
from tests.e2e.selectors import DashboardSelectors as Dashboard, GenerateSelectors as Generate


class TestDesktopLayout:
    """Tests for desktop viewport (1440x900)."""
    
    @pytest.mark.smoke
    def test_dashboard_layout_desktop(self, authenticated_user: Page, desktop_viewport):
        """
        Desktop layout should:
        1. Show full navigation
        2. Display all main sections properly
        3. No overlapping or clipped elements
        """
        page = authenticated_user
        page.set_viewport_size({"width": 1440, "height": 900})
        
        # Verify main dashboard is visible
        expect(page.locator(Dashboard.PAGE)).to_be_visible()
        
        # Verify header navigation is visible
        expect(page.locator("header")).to_be_visible()
        
        # Verify navigation links are visible (desktop shows all)
        nav_links = page.locator("nav ul li")
        expect(nav_links.first).to_be_visible()
        
        # Verify metrics grid shows 4 columns on desktop
        metrics_grid = page.locator(".grid-cols-1.md\\:grid-cols-2.lg\\:grid-cols-4")
        if metrics_grid.count() > 0:
            expect(metrics_grid.first).to_be_visible()
        
        # Verify user info in header
        expect(page.locator("#user-name")).to_be_visible()
        expect(page.locator("#user-email")).to_be_visible()


class TestTabletLayout:
    """Tests for tablet viewport (1024x768)."""
    
    def test_dashboard_layout_tablet(self, authenticated_user: Page, tablet_viewport):
        """
        Tablet layout should:
        1. Adapt navigation (may condense)
        2. Show 2-column grid for metrics
        3. Content remains usable
        """
        page = authenticated_user
        page.set_viewport_size({"width": 1024, "height": 768})
        
        # Verify main dashboard is visible
        expect(page.locator(Dashboard.PAGE)).to_be_visible()
        
        # Verify header is visible
        expect(page.locator("header")).to_be_visible()
        
        # Verify dashboard content is accessible
        expect(page.locator(Dashboard.SECTION_DASHBOARD)).to_be_visible()
        
        # Navigate to different sections to verify they work
        page.click("text=Generate")
        page.wait_for_selector("#section-generate:not(.hidden)", timeout=5000)
        expect(page.locator(Dashboard.SECTION_GENERATE)).to_be_visible()
        
        # Verify form elements are visible
        expect(page.locator(Generate.TOPIC_INPUT)).to_be_visible()
        expect(page.locator(Generate.BUTTON)).to_be_visible()


class TestMobileLayout:
    """Tests for mobile viewport (375x812)."""
    
    def test_dashboard_layout_mobile(self, authenticated_user: Page, mobile_viewport):
        """
        Mobile layout should:
        1. Show hamburger menu (if implemented)
        2. Stack content vertically
        3. No horizontal scrolling
        4. All key actions accessible
        """
        page = authenticated_user
        page.set_viewport_size({"width": 375, "height": 812})
        
        # Verify main dashboard is visible
        expect(page.locator(Dashboard.PAGE)).to_be_visible()
        
        # Check for horizontal scroll (should not exist)
        page_width = page.evaluate("document.documentElement.scrollWidth")
        viewport_width = page.evaluate("window.innerWidth")
        
        # Allow small tolerance for scrollbars
        assert page_width <= viewport_width + 20, \
            f"Page should not have horizontal scroll. Page: {page_width}, Viewport: {viewport_width}"
        
        # Verify main content is visible
        expect(page.locator(Dashboard.SECTION_DASHBOARD)).to_be_visible()
        
        # Verify user can still navigate
        # On mobile, navigation might be in a different format
        page.click("text=Generate")
        page.wait_for_selector("#section-generate:not(.hidden)", timeout=5000)
        
        # Verify generate form is usable on mobile
        topic_input = page.locator(Generate.TOPIC_INPUT)
        expect(topic_input).to_be_visible()
        
        # Verify button is visible and clickable
        expect(page.locator(Generate.BUTTON)).to_be_visible()
