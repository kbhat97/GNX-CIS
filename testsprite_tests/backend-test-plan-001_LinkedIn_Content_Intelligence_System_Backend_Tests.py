"""
LinkedIn Content Intelligence System – Backend End‑to‑End Tests (TEST_MODE=1)

Validates the FastAPI endpoints for the CIS backend when running locally at:
    http://localhost:8080
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8080"
TIMEOUT = 30

VALID_JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.validpayload.validsignature"
INVALID_JWT_TOKEN = "invalid.token.value"

def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def raise_if(condition: bool, message: str):
    if condition:
        raise AssertionError(message)

def write_report(summary: str):
    path = "testsprite_tests/testsprite-mcp-test-report.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write("# TestSprite End‑to‑End Backend Report\n\n")
        f.write(f"Generated: {datetime.utcnow().isoformat()} UTC\n\n")
        f.write(summary)
    log(f"✅ Report written to {path}")

def test_backend():
    passed = 0
    total = 6

    headers = {"Authorization": f"Bearer {VALID_JWT_TOKEN}"}
    log("1️⃣  Testing /health ...")
    resp = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    raise_if("api" not in data or "clerk" not in data or "supabase" not in data,
             "Missing required fields in health response.")
    passed += 1
    log("✓ Health check passed.")

    log("2️⃣  Testing /user/profile with valid token ...")
    resp = requests.get(f"{BASE_URL}/user/profile", headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    profile = resp.json()
    raise_if("id" not in profile, "User profile should have 'id'")
    passed += 1
    log("✓ Authenticated profile passed.")

    log("3️⃣  Testing /user/profile with invalid token ...")
    bad = {"Authorization": f"Bearer {INVALID_JWT_TOKEN}"}
    resp = requests.get(f"{BASE_URL}/user/profile", headers=bad, timeout=TIMEOUT)
    raise_if(resp.status_code != 401, f"Expected 401, got {resp.status_code}")
    passed += 1
    log("✓ Invalid‑token rejection passed.")

    log("4️⃣  Testing /user/onboarding ...")
    onboarding_body = {
        "responses": {
            "experience": "5 years in marketing",
            "industry": "Technology",
            "goals": "Increase engagement on LinkedIn"
        }
    }
    resp = requests.post(f"{BASE_URL}/user/onboarding",
                         json=onboarding_body, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    onboarding = resp.json()
    user_id = onboarding.get("user_id")
    raise_if(user_id is None, "Onboarding response missing user_id")
    resp = requests.get(f"{BASE_URL}/user/profile", headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    prof = resp.json()
    raise_if(prof.get("onboarding_completed") is not True,
             "onboarding_completed should be True")
    passed += 1
    log("✓ User onboarding flow passed.")

    log("5️⃣  Testing content generation and listing ...")
    post_body = {"topic": "AI in Marketing", "profile_id": user_id}
    resp = requests.post(f"{BASE_URL}/posts/generate",
                         json=post_body, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    post = resp.json()
    post_id = post.get("post_id")
    raise_if(not post_id, "Post generation missing post_id")
    raise_if(post.get("status") != "draft", "Post status should be 'draft'")

    resp = requests.get(f"{BASE_URL}/posts?status=draft",
                        headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    drafts = resp.json()
    found = any((p.get("post_id") == post_id) for p in drafts)
    raise_if(not found, "Generated draft not found in draft list")
    passed += 1
    log("✓ Content generation passed.")

    log("6️⃣  Testing LinkedIn token and status ...")
    token_data = {"access_token": "linkedin_oauth_dummy_token", "expires_in": 3600}
    resp = requests.post(f"{BASE_URL}/linkedin/token",
                         json=token_data, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    token_resp = resp.json()
    raise_if(token_resp.get("success") is not True,
             "Expected success=True in LinkedIn token response")
    resp = requests.get(f"{BASE_URL}/linkedin/status", headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    status_resp = resp.json()
    raise_if("connected" not in status_resp, "Missing 'connected' field")
    raise_if(not isinstance(status_resp["connected"], bool),
             "'connected' should be boolean")
    passed += 1
    log("✓ LinkedIn integration passed.")

    summary = (
        f"## Summary\n"
        f"- Total Cases: {total}\n"
        f"- Passed: {passed}\n"
        f"- Failed: {total - passed}\n"
        f"- Mode: TEST_MODE=1 (bypass active)\n\n"
        f"✅ All {passed}/{total} backend tests passed successfully.\n"
    )
    log("=" * 60)
    log("🎉  All backend tests completed successfully.")
    log("=" * 60)
    write_report(summary)


if __name__ == "__main__":
    try:
        test_backend()
    except Exception as e:
        print(f"❌ Test run failed: {e}")
        exit(1)