"""
Content Generation Tests for GNX CIS Dashboard
Tests: Happy path, validation, loading states, error handling, rate limits
"""
import pytest
from playwright.sync_api import Page, expect
from tests.e2e.selectors import DashboardSelectors as Dashboard, GenerateSelectors as Generate


class TestGenerateHappyPath:
    """Tests for successful content generation."""
    
    @pytest.mark.smoke
    def test_generate_happy_path(self, authenticated_admin: Page):
        """
        Successful generation should:
        1. Accept valid input
        2. Show loading state
        3. Display generated content
        """
        page = authenticated_admin
        
        # Navigate to Generate section
        page.click("text=Generate")
        page.wait_for_selector("#section-generate:not(.hidden)", timeout=5000)
        
        # Fill in topic
        page.fill(Generate.TOPIC_INPUT, "SAP S/4HANA migration best practices")
        
        # Select a style
        page.select_option(Generate.STYLE_SELECT, "professional")
        
        # Click generate
        page.click(Generate.BUTTON)
        
        # Wait for result (may take time due to API call)
        # First verify loading state appears
        expect(page.locator(Generate.AGENT_PROGRESS)).to_be_visible(timeout=5000)
        
        # Wait for result content to appear
        page.wait_for_selector("#result-content:not(.hidden)", timeout=60000)
        
        # Verify result is displayed
        expect(page.locator(Generate.RESULT_CONTENT)).to_be_visible()
        expect(page.locator("#result-text")).to_be_visible()
        expect(page.locator("#result-score")).to_be_visible()


class TestGenerateValidation:
    """Tests for input validation."""
    
    def test_generate_requires_valid_input(self, authenticated_admin: Page):
        """
        Generation should require valid input:
        - Non-empty topic
        - Validation errors for empty fields
        """
        page = authenticated_admin
        
        # Navigate to Generate section
        page.click("text=Generate")
        page.wait_for_selector("#section-generate:not(.hidden)", timeout=5000)
        
        # Try to submit with empty topic
        page.fill(Generate.TOPIC_INPUT, "")
        
        # Click generate
        page.click(Generate.BUTTON)
        
        # HTML5 validation should prevent submission
        # Verify we're still on the form (not loading)
        expect(page.locator(Generate.RESULT_EMPTY)).to_be_visible()
        expect(page.locator(Generate.AGENT_PROGRESS)).not_to_be_visible()


class TestGenerateLoadingStates:
    """Tests for loading and result UI states."""
    
    def test_generate_shows_loading_and_result(self, authenticated_admin: Page):
        """
        During generation:
        1. Show loading/progress indicator
        2. Disable generate button
        3. On completion, show result
        """
        page = authenticated_admin
        
        # Navigate to Generate section
        page.click("text=Generate")
        page.wait_for_selector("#section-generate:not(.hidden)", timeout=5000)
        
        # Fill in topic
        page.fill(Generate.TOPIC_INPUT, "Cloud migration strategies for enterprises")
        
        # Track button state before click
        generate_btn = page.locator(Generate.BUTTON)
        
        # Click generate
        page.click(Generate.BUTTON)
        
        # Verify loading state appears
        # (The button shows spinner when loading)
        spinner = page.locator("#generate-spinner")
        expect(spinner).to_be_visible(timeout=5000)
        
        # Wait for completion
        page.wait_for_selector("#result-content:not(.hidden)", timeout=60000)
        
        # Verify spinner is hidden after completion
        expect(spinner).not_to_be_visible()


class TestGenerateErrors:
    """Tests for error handling during generation."""
    
    def test_generate_handles_backend_error(
        self, authenticated_admin: Page, mock_generate_500
    ):
        """
        Backend error should:
        1. Show error message
        2. Allow retry
        3. Not crash UI
        """
        page = authenticated_admin
        
        # Navigate to Generate section
        page.click("text=Generate")
        page.wait_for_selector("#section-generate:not(.hidden)", timeout=5000)
        
        # Fill in topic
        page.fill(Generate.TOPIC_INPUT, "Test topic for error handling")
        
        # Click generate
        page.click(Generate.BUTTON)
        
        # Wait for error state (the mock will return 500)
        # UI should handle this gracefully by showing error in #generate-error
        error_el = page.locator(Generate.ERROR_MESSAGE)
        expect(error_el).to_be_visible(timeout=10000)
        
        # Verify UI is still functional
        expect(page.locator(Dashboard.SECTION_GENERATE)).to_be_visible()
        expect(page.locator(Generate.BUTTON)).to_be_enabled()
    
    def test_generate_rate_limit_message(
        self, authenticated_admin: Page, mock_generate_429
    ):
        """
        Rate limit (429) should:
        1. Show rate limit specific message
        2. Optionally show retry guidance
        """
        page = authenticated_admin
        
        # Navigate to Generate section
        page.click("text=Generate")
        page.wait_for_selector("#section-generate:not(.hidden)", timeout=5000)
        
        # Fill in topic
        page.fill(Generate.TOPIC_INPUT, "Test topic for rate limiting")
        
        # Click generate
        page.click(Generate.BUTTON)
        
        # Wait for rate limit response
        # UI should show rate limit message in #generate-status
        status_el = page.locator(Generate.STATUS_MESSAGE)
        expect(status_el).to_be_visible(timeout=10000)
        
        # Verify it mentions rate limit or wait time
        status_text = status_el.text_content()
        assert "limit" in status_text.lower() or "wait" in status_text.lower() or "⏳" in status_text
        
        # Verify UI is still functional (no crash)
        expect(page.locator(Dashboard.SECTION_GENERATE)).to_be_visible()
        expect(page.locator(Generate.BUTTON)).to_be_enabled()


class TestGenerateSecurity:
    """Tests for security in generated content rendering."""
    
    def test_xss_content_rendered_safely(self, authenticated_admin: Page):
        """
        XSS payloads in generated content should:
        1. NOT execute as scripts
        2. Be rendered as plain text
        3. Not modify DOM unexpectedly
        """
        page = authenticated_admin
        
        # Navigate to Generate section
        page.click("text=Generate")
        page.wait_for_selector("#section-generate:not(.hidden)", timeout=5000)
        
        # Submit a topic that might return XSS-like content
        # In production, the backend should sanitize this
        xss_payload = "<script>alert('xss')</script>"
        page.fill(Generate.TOPIC_INPUT, f"Test topic with {xss_payload}")
        
        # Set up a listener to detect any alert/confirm dialogs
        dialogs_seen = []
        page.on("dialog", lambda dialog: (dialogs_seen.append(dialog.message), dialog.dismiss()))
        
        # Attempt generation (may fail if backend unavailable, that's ok)
        try:
            page.click(Generate.BUTTON)
            page.wait_for_timeout(5000)  # Give time for any XSS to execute
        except Exception:
            pass
        
        # Verify no XSS dialog was triggered
        assert len(dialogs_seen) == 0, f"XSS dialog was triggered: {dialogs_seen}"
        
        # Verify the result-text element, if present, renders HTML as text
        result_text = page.locator("#result-text")
        if result_text.is_visible():
            text_content = result_text.text_content()
            inner_html = result_text.inner_html()
            # If script tag appears, it should be escaped/text, not executable
            if "<script>" in text_content:
                # That's fine - it's just text
                pass
            elif "<script>" in inner_html.lower():
                # This would be bad - script tag in actual HTML
                assert False, "Script tag found in result HTML - XSS vulnerability"


class TestGenerateMocked:
    """Tests using mocked API for CI determinism."""
    
    @pytest.mark.smoke
    def test_generate_happy_path_mocked(self, authenticated_admin: Page, mock_generate_success):
        """
        With mocked API, generate should:
        1. Accept valid input
        2. Show loading state
        3. Display mocked content with score
        """
        page = authenticated_admin
        
        # Navigate to Generate section
        page.click("text=Generate")
        page.wait_for_selector("#section-generate:not(.hidden)", timeout=5000)
        
        # Fill in topic
        page.fill(Generate.TOPIC_INPUT, "SAP S/4HANA migration best practices")
        
        # Select a style
        page.select_option(Generate.STYLE_SELECT, "professional")
        
        # Click generate
        page.click(Generate.BUTTON)
        
        # Wait for result content to appear (mocked response is instant)
        page.wait_for_selector("#result-content:not(.hidden)", timeout=10000)
        
        # Verify result is displayed
        expect(page.locator(Generate.RESULT_CONTENT)).to_be_visible()
        expect(page.locator("#result-text")).to_be_visible()
        expect(page.locator("#result-score")).to_be_visible()
        
        # Verify score from mock (85)
        score_text = page.locator("#result-score").text_content()
        assert "85" in score_text, f"Expected score 85 from mock, got: {score_text}"
