import sys
import os

# Fix encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

import requests
import time
import json
from datetime import datetime

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword"

# Test JWT token (for development only)
TEST_JWT = "dev_jwt_for_testing"

# Test results
results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "tests": []
}

# Global variables for test data
test_post_id = None

def run_test(name, test_func):
    """Run a test and record results"""
    global results
    results["total"] += 1
    
    print(f"\n🧪 Running test: {name}")
    start_time = time.time()
    
    try:
        test_func()
        results["passed"] += 1
        status = "PASSED"
        error = None
        print(f"✓ Test passed in {time.time() - start_time:.2f}s")
    except Exception as e:
        results["failed"] += 1
        status = "FAILED"
        error = str(e)
        print(f"✗ Test failed: {e}")
        print(f"✗ Test failed in {time.time() - start_time:.2f}s")
    
    duration = time.time() - start_time
    
    results["tests"].append({
        "name": name,
        "status": status,
        "duration": duration,
        "error": error,
        "timestamp": datetime.now().isoformat()
    })

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{API_BASE_URL}/health", timeout=5)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert "status" in data, "Missing 'status' in response"
    assert "api" in data, "Missing 'api' in response"
    assert "clerk" in data, "Missing 'clerk' in response"
    assert "supabase" in data, "Missing 'supabase' in response"
    
    print(f"Health status: {data['status']}")
    print(f"API: {data['api']}")
    print(f"Clerk: {data['clerk']}")
    print(f"Supabase: {data['supabase']}")

def test_auth():
    """Test authentication"""
    headers = {"Authorization": f"Bearer {TEST_JWT}"}
    response = requests.get(f"{API_BASE_URL}/auth/verify", headers=headers, timeout=5)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert "status" in data, "Missing 'status' in response"
    assert data["status"] == "authenticated", f"Expected 'authenticated', got {data['status']}"
    assert "user" in data, "Missing 'user' in response"
    
    user = data["user"]
    assert "clerk_id" in user, "Missing 'clerk_id' in user"
    assert "email" in user, "Missing 'email' in user"
    
    print(f"Authenticated as: {user['email']}")

def test_user_profile():
    """Test user profile endpoint"""
    headers = {"Authorization": f"Bearer {TEST_JWT}"}
    response = requests.get(f"{API_BASE_URL}/user/profile", headers=headers, timeout=5)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert "status" in data, "Missing 'status' in response"
    
    if data["status"] == "success":
        assert "id" in data, "Missing 'id' in response"
        print(f"User profile found: {data.get('id')}")
    else:
        print(f"User profile status: {data['status']}")

def test_onboarding():
    """Test onboarding questionnaire"""
    headers = {
        "Authorization": f"Bearer {TEST_JWT}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "writing_tone": "Professional & Formal",
        "audience": "Technology Leaders",
        "values": ["Innovation", "Leadership", "Growth"],
        "personality": "Thought leader in technology",
        "frequency": 3,
        "focus": "AI and Machine Learning"
    }
    
    response = requests.post(
        f"{API_BASE_URL}/onboarding/questionnaire",
        headers=headers,
        json=payload,
        timeout=10
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert "status" in data, "Missing 'status' in response"
    
    print(f"Onboarding status: {data['status']}")

def test_post_generation():
    """Test post generation"""
    global test_post_id
    
    headers = {
        "Authorization": f"Bearer {TEST_JWT}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "topic": "AI in Healthcare",
        "style": "Professional"
    }
    
    response = requests.post(
        f"{API_BASE_URL}/posts/generate",
        headers=headers,
        json=payload,
        timeout=30
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert "status" in data, "Missing 'status' in response"
    assert "content" in data, "Missing 'content' in response"
    assert "post_id" in data, "Missing 'post_id' in response"
    
    # Store post_id for later tests
    test_post_id = data.get("post_id")
    
    print(f"Generated post ID: {test_post_id}")
    print(f"Content preview: {data['content'][:100]}...")

def test_pending_posts():
    """Test pending posts endpoint"""
    headers = {"Authorization": f"Bearer {TEST_JWT}"}
    response = requests.get(f"{API_BASE_URL}/posts/pending", headers=headers, timeout=5)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert "status" in data, "Missing 'status' in response"
    assert "posts" in data, "Missing 'posts' in response"
    
    print(f"Pending posts count: {len(data['posts'])}")

def test_published_posts():
    """Test published posts endpoint"""
    headers = {"Authorization": f"Bearer {TEST_JWT}"}
    response = requests.get(f"{API_BASE_URL}/posts/published", headers=headers, timeout=5)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert "status" in data, "Missing 'status' in response"
    assert "posts" in data, "Missing 'posts' in response"
    
    print(f"Published posts count: {len(data['posts'])}")

def test_post_update():
    """Test post update"""
    global test_post_id
    
    if not test_post_id:
        print("Skipping post update test - no post ID available")
        return
    
    headers = {
        "Authorization": f"Bearer {TEST_JWT}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "content": "This is an updated test post content.",
        "topic": "Updated AI in Healthcare"
    }
    
    response = requests.put(
        f"{API_BASE_URL}/posts/{test_post_id}",
        headers=headers,
        json=payload,
        timeout=10
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert "status" in data, "Missing 'status' in response"
    assert data["status"] == "success", f"Expected 'success', got {data['status']}"
    
    print(f"Post updated successfully: {test_post_id}")

def test_post_publish():
    """Test post publishing"""
    global test_post_id
    
    if not test_post_id:
        print("Skipping post publish test - no post ID available")
        return
    
    headers = {"Authorization": f"Bearer {TEST_JWT}"}
    
    response = requests.post(
        f"{API_BASE_URL}/posts/publish/{test_post_id}",
        headers=headers,
        timeout=10
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert "status" in data, "Missing 'status' in response"
    
    print(f"Post publishing status: {data['status']}")

def test_linkedin_status():
    """Test LinkedIn status endpoint"""
    headers = {"Authorization": f"Bearer {TEST_JWT}"}
    response = requests.get(f"{API_BASE_URL}/auth/linkedin/status", headers=headers, timeout=5)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    print(f"LinkedIn status: {data}")

def test_linkedin_authorize():
    """Test LinkedIn authorization URL generation"""
    headers = {"Authorization": f"Bearer {TEST_JWT}"}
    response = requests.get(f"{API_BASE_URL}/auth/linkedin/authorize", headers=headers, timeout=5)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert "auth_url" in data, "Missing 'auth_url' in response"
    
    print(f"LinkedIn auth URL generated: {data['auth_url'][:50]}...")

def generate_report():
    """Generate test report"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": results["total"],
            "passed": results["passed"],
            "failed": results["failed"],
            "pass_rate": f"{(results['passed'] / results['total']) * 100:.2f}%" if results["total"] > 0 else "N/A"
        },
        "tests": results["tests"]
    }
    
    # Save report to file
    with open("integration_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    
    # Generate markdown report
    with open("integration_test_report.md", "w", encoding="utf-8") as f:
        f.write("# CIS Integration Test Report\n\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        
        f.write("## Summary\n\n")
        f.write(f"- Total Tests: {report['summary']['total']}\n")
        f.write(f"- Passed: {report['summary']['passed']}\n")
        f.write(f"- Failed: {report['summary']['failed']}\n")
        f.write(f"- Pass Rate: {report['summary']['pass_rate']}\n\n")
        
        f.write("## Test Results\n\n")
        f.write("| Test | Status | Duration (s) |\n")
        f.write("|------|--------|-------------|\n")
        
        for test in report["tests"]:
            status_icon = "✓" if test["status"] == "PASSED" else "✗"
            f.write(f"| {test['name']} | {status_icon} {test['status']} | {test['duration']:.2f} |\n")
        
        f.write("\n## Failed Tests\n\n")
        failed_tests = [t for t in report["tests"] if t["status"] == "FAILED"]
        
        if failed_tests:
            for test in failed_tests:
                f.write(f"### {test['name']}\n\n")
                f.write(f"Error: {test['error']}\n\n")
        else:
            f.write("No failed tests! 🎉\n")
    
    print(f"\n📊 Test Report Summary:")
    print(f"Total Tests: {report['summary']['total']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Pass Rate: {report['summary']['pass_rate']}")
    print(f"\nDetailed reports saved to:")
    print("- integration_test_report.json")
    print("- integration_test_report.md")

if __name__ == "__main__":
    # Initialize test post ID
    test_post_id = None
    
    # Run tests
    run_test("Health Check", test_health)
    run_test("Authentication", test_auth)
    run_test("User Profile", test_user_profile)
    run_test("Onboarding", test_onboarding)
    run_test("Post Generation", test_post_generation)
    run_test("Pending Posts", test_pending_posts)
    run_test("Published Posts", test_published_posts)
    run_test("Post Update", test_post_update)
    run_test("Post Publish", test_post_publish)
    run_test("LinkedIn Status", test_linkedin_status)
    run_test("LinkedIn Authorization", test_linkedin_authorize)
    
    # Generate report
    generate_report()