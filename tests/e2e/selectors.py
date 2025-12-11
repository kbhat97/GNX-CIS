"""
Centralized selectors for E2E tests.

WHY: Updating an HTML ID currently requires changing 20+ places across 7 files.
With this file, change it once here and all tests update automatically.

Update this file when app.html DOM changes.
"""

class LoginSelectors:
    """Login page element selectors."""
    PAGE = "#login-page"
    EMAIL = "#login-email"
    PASSWORD = "#login-password"
    SUBMIT = "#login-btn"
    ERROR = "#login-error"
    FORGOT_PASSWORD_LINK = "text=Forgot password"
    
    # Forgot password form
    FORGOT_PASSWORD_FORM = "#forgot-password-form"
    RESET_EMAIL = "#reset-email"
    RESET_BTN = "#reset-password-btn"
    RESET_SUCCESS = "#reset-success"


class DashboardSelectors:
    """Dashboard page element selectors."""
    PAGE = "#dashboard-page"
    USER_NAME = "#user-name"
    USER_EMAIL = "#user-email"
    LOGOUT_BTN = "#logout-btn"
    ERROR = "#dashboard-error"  # BLOCKER 7: Dashboard error element
    METRICS_GRID = "[data-testid='metrics-grid']"  # Prefer data-testid where possible
    HISTORY_GRID = "#history-grid"
    POST_ROW = ".post-row"
    STYLE_FILTER = "#style-filter"
    SEARCH_INPUT = "#search-input"
    
    # Navigation
    NAV_DASHBOARD = "#nav-dashboard"
    NAV_GENERATE = "#nav-generate"
    NAV_HISTORY = "#nav-history"
    NAV_SETTINGS = "#nav-settings"
    
    # Sections
    SECTION_DASHBOARD = "#section-dashboard"
    SECTION_GENERATE = "#section-generate"
    SECTION_HISTORY = "#section-history"
    SECTION_SETTINGS = "#section-settings"


class GenerateSelectors:
    """Content generation section selectors."""
    SECTION = "#section-generate"
    TOPIC_INPUT = "#topic-input"
    STYLE_SELECT = "#style-select"
    BUTTON = "#generate-btn"
    LOADING_SPINNER = "#generate-spinner"  # Actual ID in HTML
    RESULT_CONTENT = "#result-content"
    RESULT_EMPTY = "#result-empty"
    VIRALITY_SCORE = "#result-score"  # Actual ID in HTML
    ERROR_MESSAGE = "#generate-error"
    STATUS_MESSAGE = "#generate-status"
    AGENT_PROGRESS = "#agent-progress"


class PersonaSelectors:
    """Admin persona/RBAC element selectors."""
    ADMIN_SECTION = "#admin-persona-section"
    TOGGLE = "#persona-toggle"
    MODE_LABEL = "#persona-mode-label"
    DETAILS = "#persona-details"
    LINKEDIN_ACTIONS = "#admin-linkedin-actions"
    REGULAR_SECTION = "#regular-persona-section"
    SETTINGS_SECTION = "#admin-settings-section"


class SettingsSelectors:
    """Settings page element selectors."""
    SECTION = "#section-settings"
    DEFAULT_PERSONA = "#default-persona"
    SAVE_BTN = "#save-settings"
    THEME_SELECT = "#theme-select"
