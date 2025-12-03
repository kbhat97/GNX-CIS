import requests
import json

API_BASE_URL = "http://localhost:8080"
TEST_JWT = "dev_jwt_for_testing"

def test_endpoint(name, method, url, headers=None, json_data=None):
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=json_data, timeout=5)
        
        print(f"Status: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        except:
            print(f"Response (text): {response.text[:500]}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"ERROR: {e}")
        return False

# Test endpoints
headers = {"Authorization": f"Bearer {TEST_JWT}"}

print("\n" + "="*60)
print("CIS API VALIDATION TEST")
print("="*60)

# 1. Health Check
test_endpoint("Health Check", "GET", f"{API_BASE_URL}/health")

# 2. Authentication
test_endpoint("Authentication", "GET", f"{API_BASE_URL}/auth/verify", headers=headers)

# 3. User Profile
test_endpoint("User Profile", "GET", f"{API_BASE_URL}/user/profile", headers=headers)

# 4. Onboarding
onboarding_data = {
    "writing_tone": "Professional & Formal",
    "audience": "Technology Leaders",
    "values": ["Innovation", "Leadership"],
    "personality": "Thought leader",
    "frequency": 3,
    "focus": "AI and ML"
}
test_endpoint("Onboarding", "POST", f"{API_BASE_URL}/onboarding/questionnaire", 
              headers=headers, json_data=onboarding_data)

# 5. Post Generation
post_data = {
    "topic": "AI in Healthcare",
    "style": "Professional"
}
test_endpoint("Post Generation", "POST", f"{API_BASE_URL}/posts/generate", 
              headers=headers, json_data=post_data)

# 6. Pending Posts
test_endpoint("Pending Posts", "GET", f"{API_BASE_URL}/posts/pending", headers=headers)

# 7. LinkedIn Status
test_endpoint("LinkedIn Status", "GET", f"{API_BASE_URL}/auth/linkedin/status", headers=headers)

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
