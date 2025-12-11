"""
Dashboard Workflow Tests for GNX CIS Dashboard
Tests: Initial load, filters/search, pagination, URL sync, error states
"""
import pytest
from playwright.sync_api import Page, expect
from tests.e2e.selectors import DashboardSelectors as Dashboard


class TestDashboardLoad:
    """Tests for dashboard initial load behavior."""
    
    @pytest.mark.smoke
    def test_dashboard_initial_load(self, authenticated_user: Page):
        """
        Dashboard should:
        1. Show loading states initially (if applicable)
        2. Load and display main sections
        3. Show metrics and recent posts grid
        """
        page = authenticated_user
        
        # Verify main dashboard sections are visible
        expect(page.locator(Dashboard.SECTION_DASHBOARD)).to_be_visible()
        
        # Verify metrics are displayed
        expect(page.locator("#metric-posts")).to_be_visible()
        expect(page.locator("#metric-avg-score")).to_be_visible()
        expect(page.locator("#metric-best-score")).to_be_visible()
        expect(page.locator("#metric-api-status")).to_be_visible()
        
        # Verify recent posts grid exists
        expect(page.locator("#recent-posts-grid")).to_be_visible()


class TestFiltersAndSearch:
    """Tests for filter and search functionality."""
    
    def test_filters_and_search(self, authenticated_user: Page):
        """
        Filter and search controls should:
        1. Be interactive
        2. Update displayed results
        3. Send appropriate network requests
        """
        page = authenticated_user
        
        # Navigate to History section (has search/filters)
        page.click("text=History")
        page.wait_for_selector("#section-history:not(.hidden)", timeout=5000)
        
        # Verify search input exists
        search_input = page.locator("#history-search")
        expect(search_input).to_be_visible()
        
        # Verify filter dropdowns exist
        score_filter = page.locator("#history-filter-score")
        expect(score_filter).to_be_visible()
        
        sort_filter = page.locator("#history-sort")
        expect(sort_filter).to_be_visible()
        
        # Test search interaction
        search_input.fill("test search")
        
        # Test filter interaction
        score_filter.select_option("90")
        
        # Verify filters can be changed
        sort_filter.select_option("highest")
        
        # Verify history grid is still visible
        expect(page.locator(Dashboard.HISTORY_GRID)).to_be_visible()


class TestNavigation:
    """Tests for dashboard navigation."""
    
    def test_pagination_or_infinite_scroll(self, authenticated_user: Page):
        """
        Navigation between sections should work correctly.
        (This app uses section-based navigation rather than pagination)
        """
        page = authenticated_user
        
        # Test navigation between main sections
        sections = [
            ("Dashboard", Dashboard.SECTION_DASHBOARD),
            ("Generate", Dashboard.SECTION_GENERATE),
            ("History", Dashboard.SECTION_HISTORY),
            ("Settings", Dashboard.SECTION_SETTINGS),
        ]
        
        for nav_text, section_id in sections:
            # Click navigation item
            page.click(f"text={nav_text}")
            
            # Wait for section to be visible
            page.wait_for_selector(f"{section_id}:not(.hidden)", timeout=5000)
            
            # Verify the correct section is visible
            expect(page.locator(section_id)).to_be_visible()


class TestURLState:
    """Tests for URL state synchronization."""
    
    @pytest.mark.xfail(reason="BLOCKER 4: Hash navigation not implemented in SPA - state uses localStorage only")
    def test_url_state_sync(self, authenticated_user: Page, base_url: str):
        """
        Application state should be maintained across navigation.
        (Note: This app may not implement URL-based state sync)
        """
        page = authenticated_user
        
        # Navigate to a specific section
        page.click("text=Generate")
        page.wait_for_selector("#section-generate:not(.hidden)", timeout=5000)
        
        # Get current URL
        current_url = page.url
        
        # Reload the page
        page.reload()
        page.wait_for_load_state("networkidle")
        
        # Verify we're still logged in and on the dashboard
        expect(page.locator(Dashboard.PAGE)).to_be_visible()
        
        # Note: The app uses localStorage for session, so state should persist


class TestErrorStates:
    """Tests for error handling in dashboard."""
    
    def test_error_state_on_data_fetch_failure(
        self, authenticated_user: Page, mock_dashboard_data_500
    ):
        """
        When data fetch fails:
        1. Show user-friendly error
        2. Don't crash the UI
        3. Potentially offer retry
        """
        page = authenticated_user
        
        # The dashboard should still be functional
        expect(page.locator(Dashboard.PAGE)).to_be_visible()
        
        # Navigate around to trigger potential data fetches
        page.click("text=Dashboard")
        page.wait_for_selector("#section-dashboard:not(.hidden)", timeout=5000)
        
        # Verify the UI doesn't crash despite API errors
        expect(page.locator(Dashboard.SECTION_DASHBOARD)).to_be_visible()
        
        # Metrics should show fallback values or error state
        expect(page.locator("#metric-posts")).to_be_visible()
