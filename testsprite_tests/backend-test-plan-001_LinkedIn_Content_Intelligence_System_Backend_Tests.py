import requests

BASE_URL = "http://localhost:8080"
TIMEOUT = 30

# For testing, use a placeholder valid and invalid JWT token
VALID_JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.validpayload.validsignature"
INVALID_JWT_TOKEN = "invalid.token.value"

def test_linkedin_content_intelligence_system_backend():
    # 1. Health Check Endpoint
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        resp.raise_for_status()
        health_data = resp.json()
        assert "api" in health_data, "Missing 'api' status in health check response"
        assert "clerk" in health_data, "Missing 'clerk' status in health check response"
        assert "supabase" in health_data, "Missing 'supabase' status in health check response"
    except Exception as e:
        assert False, f"Health check failed: {e}"

    # 2. Authentication - valid token
    headers = {"Authorization": f"Bearer {VALID_JWT_TOKEN}"}
    try:
        resp = requests.get(f"{BASE_URL}/user/profile", headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        profile = resp.json()
        assert "id" in profile, "User profile should have 'id'"
    except Exception as e:
        assert False, f"Authenticated user profile fetch failed: {e}"

    # 3. Authentication - invalid token
    headers_invalid = {"Authorization": f"Bearer {INVALID_JWT_TOKEN}"}
    resp = requests.get(f"{BASE_URL}/user/profile", headers=headers_invalid, timeout=TIMEOUT)
    assert resp.status_code == 401, "Invalid token must return 401 Unauthorized"

    # 4. User Onboarding - submit questionnaire, create profile, check status
    onboarding_payload = {
        "responses": {
            "experience": "5 years in marketing",
            "industry": "Technology",
            "goals": "Increase engagement on LinkedIn"
        }
    }
    try:
        # Submit onboarding questionnaire
        resp = requests.post(f"{BASE_URL}/user/onboarding", json=onboarding_payload, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        onboarding_resp = resp.json()
        user_id = onboarding_resp.get("user_id")
        assert user_id is not None, "Onboarding response must contain user_id"

        # Get user profile to verify creation and onboarding status
        resp = requests.get(f"{BASE_URL}/user/profile", headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        profile = resp.json()
        assert profile.get("onboarding_completed") is True, "User onboarding_completed should be True"

    except Exception as e:
        assert False, f"User onboarding flow failed: {e}"

    # 5. Content Generation - generate post draft and retrieve by status
    post_payload = {
        "topic": "AI in Marketing",
        "profile_id": user_id
    }
    try:
        # Generate post draft
        resp = requests.post(f"{BASE_URL}/posts/generate", json=post_payload, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        post_resp = resp.json()
        post_id = post_resp.get("post_id")
        assert post_id is not None, "Generated post response must contain post_id"
        assert post_resp.get("status") == "draft", "Generated post must have status 'draft'"

        # Retrieve posts by status=draft
        resp = requests.get(f"{BASE_URL}/posts?status=draft", headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        posts_list = resp.json()
        assert any(p.get("post_id") == post_id for p in posts_list), "Draft posts should include the generated post"

    except Exception as e:
        assert False, f"Content generation flow failed: {e}"

    # 6. LinkedIn Integration - store OAuth token, check connection status
    linked_in_oauth_payload = {
        "access_token": "linkedin_oauth_dummy_token",
        "expires_in": 3600
    }
    try:
        # Store LinkedIn OAuth token
        resp = requests.post(f"{BASE_URL}/linkedin/token", json=linked_in_oauth_payload, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        token_resp = resp.json()
        assert token_resp.get("success") is True, "Storing LinkedIn OAuth token should be successful"

        # Check LinkedIn connection status
        resp = requests.get(f"{BASE_URL}/linkedin/status", headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        status_resp = resp.json()
        assert "connected" in status_resp, "LinkedIn status response must include 'connected'"
        assert isinstance(status_resp["connected"], bool), "'connected' must be a boolean"

    except Exception as e:
        assert False, f"LinkedIn integration tests failed: {e}"

test_linkedin_content_intelligence_system_backend()