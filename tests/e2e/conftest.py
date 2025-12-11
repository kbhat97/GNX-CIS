"""
E2E Test Infrastructure for GNX CIS Dashboard
Target: dashboard/app.html
Environment: veve (default), local
"""
import pytest
from typing import Generator
from playwright.sync_api import Page, BrowserContext, Playwright
from tests.e2e.selectors import LoginSelectors as Login, DashboardSelectors as Dashboard

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

# Environment configuration
import os
DASHBOARD_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dashboard", "app.html"))

ENV_CONFIG = {
    "veve": {
        "base_url": f"file:///{DASHBOARD_PATH.replace(os.sep, '/')}",  # Local HTML file
        "api_base": "http://localhost:8080",  # Backend API
        "mock_by_default": False,
    },
    "local": {
        "base_url": f"file:///{DASHBOARD_PATH.replace(os.sep, '/')}",  # Same file
        "api_base": "http://localhost:8080",
        "mock_by_default": True,
    },
}

# Test credentials
# Note: Dashboard is in DEMO MODE - accepts any password for login
# Kunal (admin) is identified by email for persona detection
TEST_CREDENTIALS = {
    "admin": {
        "email": "kunalsbhatt@gmail.com",
        "password": "test123",  # Demo mode: any password works
    },
    "user": {
        "email": "testuser@example.com",
        "password": "test123",  # Demo mode: any password works
    },
}

# ═══════════════════════════════════════════════════════════════════
# PYTEST OPTIONS
# ═══════════════════════════════════════════════════════════════════

def pytest_addoption(parser):
    """Register --env option for environment selection."""
    parser.addoption(
        "--env",
        action="store",
        default="veve",
        choices=["veve", "local"],
        help="Target environment: veve (default) or local",
    )


@pytest.fixture(scope="session")
def env(request) -> str:
    """Get the target environment from CLI option."""
    return request.config.getoption("--env")


@pytest.fixture(scope="session")
def base_url(env: str) -> str:
    """Get base URL for the target environment."""
    if env not in ENV_CONFIG:
        pytest.fail(f"Unknown environment: {env}. Allowed: {list(ENV_CONFIG.keys())}")
    return ENV_CONFIG[env]["base_url"]


# ═══════════════════════════════════════════════════════════════════
# ACCESSIBILITY HELPER
# ═══════════════════════════════════════════════════════════════════

def run_axe(page: Page, context: str = "page") -> dict:
    """
    Run axe-core accessibility scan on the current page.
    
    Args:
        page: Playwright page object
        context: Description of the page being scanned (for reporting)
    
    Returns:
        dict with violations and passes
    
    Raises:
        AssertionError if critical/serious violations found
    """
    from axe_playwright_python.sync_playwright import Axe
    
    axe = Axe()
    results = axe.run(page)
    
    # Filter for critical and serious violations
    critical_violations = [
        v for v in results.response.get("violations", [])
        if v.get("impact") in ["critical", "serious"]
    ]
    
    if critical_violations:
        violation_summary = "\n".join([
            f"- {v['id']}: {v['description']} (impact: {v['impact']})"
            for v in critical_violations
        ])
        pytest.fail(
            f"Accessibility violations found on {context}:\n{violation_summary}"
        )
    
    return results.response


# ═══════════════════════════════════════════════════════════════════
# AUTHENTICATION FIXTURES
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def authenticated_admin(page: Page, base_url: str) -> Generator[Page, None, None]:
    """
    Returns a page logged in as admin (Kunal).
    Uses test_admin=1 hook for reliable admin detection in E2E tests.
    """
    # Use test hook for reliable admin mode
    admin_url = base_url + ("?" if "?" not in base_url else "&") + "test_admin=1"
    page.goto(admin_url)
    
    # Wait for dashboard to load (test hook auto-logs in as admin)
    page.wait_for_selector(f"{Dashboard.PAGE}:not(.hidden)", timeout=15000)
    
    yield page


@pytest.fixture
def authenticated_user(page: Page, base_url: str) -> Generator[Page, None, None]:
    """
    Returns a page logged in as standard user.
    Uses test_user=1 hook for reliable user mode in E2E tests.
    """
    # Use test hook for reliable user mode
    user_url = base_url + ("?" if "?" not in base_url else "&") + "test_user=1"
    page.goto(user_url)
    
    # Wait for dashboard to load (test hook auto-logs in as user)
    page.wait_for_selector(f"{Dashboard.PAGE}:not(.hidden)", timeout=15000)
    
    yield page


# ═══════════════════════════════════════════════════════════════════
# MOCKING HELPERS
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_login_401(page: Page):
    """Mock /api/auth/login to return 401 Unauthorized."""
    def handle_route(route):
        route.fulfill(
            status=401,
            content_type="application/json",
            body='{"error": "Invalid credentials"}'
        )
    
    page.route("**/api/auth/login", handle_route)
    yield
    page.unroute("**/api/auth/login")


@pytest.fixture
def mock_login_500(page: Page):
    """Mock /api/auth/login to return 500 Server Error."""
    def handle_route(route):
        route.fulfill(
            status=500,
            content_type="application/json",
            body='{"error": "Internal server error"}'
        )
    
    page.route("**/api/auth/login", handle_route)
    yield
    page.unroute("**/api/auth/login")


@pytest.fixture
def mock_generate_500(page: Page):
    """Mock /api/generate to return 500 Server Error."""
    def handle_route(route):
        route.fulfill(
            status=500,
            content_type="application/json",
            body='{"error": "Generation failed"}'
        )
    
    page.route("**/api/generate", handle_route)
    yield
    page.unroute("**/api/generate")


@pytest.fixture
def mock_generate_429(page: Page):
    """Mock /api/generate to return 429 Rate Limited."""
    def handle_route(route):
        route.fulfill(
            status=429,
            content_type="application/json",
            body='{"error": "Rate limit exceeded", "retry_after": 60}'
        )
    
    page.route("**/api/generate", handle_route)
    yield
    page.unroute("**/api/generate")


@pytest.fixture
def mock_generate_success(page: Page):
    """
    Mock /api/generate to return a successful response.
    This provides CI-deterministic results for generate tests.
    BLOCKER 2: Must match real backend response structure exactly.
    """
    import json
    from datetime import datetime
    
    def handle_route(route):
        body = {
            "virality_score": 85,
            "content": "This is a test generated post about SAP S/4HANA migration.\n\nKey insights:\n• Cloud-first approach recommended\n• Change management is critical\n• Expect 6-18 month timeline",
            "suggestions": [
                "Add more specific metrics",
                "Include a call-to-action",
                "Consider adding relevant hashtags"
            ],
            "hook": "Did you know that 70% of SAP migrations face unexpected delays?",
            "style": "professional",
            "topic": "SAP S/4HANA migration best practices",
            "timestamp": datetime.now().isoformat(),
            "image_url": None  # No image in mock
        }
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(body)
        )
    
    page.route("**/api/generate**", handle_route)
    yield
    page.unroute("**/api/generate**")


@pytest.fixture
def mock_dashboard_data_500(page: Page):
    """Mock dashboard data endpoint to return 500."""
    def handle_route(route):
        route.fulfill(
            status=500,
            content_type="application/json",
            body='{"error": "Failed to load data"}'
        )
    
    # Mock common dashboard data endpoints
    page.route("**/api/posts*", handle_route)
    page.route("**/api/dashboard*", handle_route)
    yield
    page.unroute("**/api/posts*")
    page.unroute("**/api/dashboard*")


# ═══════════════════════════════════════════════════════════════════
# VIEWPORT FIXTURES (for responsive tests)
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def desktop_viewport(page: Page) -> Page:
    """Set viewport to desktop size (1440x900)."""
    page.set_viewport_size({"width": 1440, "height": 900})
    return page


@pytest.fixture
def tablet_viewport(page: Page) -> Page:
    """Set viewport to tablet size (1024x768)."""
    page.set_viewport_size({"width": 1024, "height": 768})
    return page


@pytest.fixture
def mobile_viewport(page: Page) -> Page:
    """Set viewport to mobile size (375x812)."""
    page.set_viewport_size({"width": 375, "height": 812})
    return page
