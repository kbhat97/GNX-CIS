"""
Test CIS workflow by calling the API directly
"""
import requests
import json

API_BASE_URL = "http://localhost:8080"

# Use DEV_MODE token to bypass auth
headers = {
    "Authorization": "Bearer dev_jwt_for_testing"
}

# Topic based on the SAP image
topic = "The journey from SAP ECC to S/4HANA (2015-2020): Early challenges like data migration complexity, custom code remediation, and talent gaps - and how we achieved major milestones including cloud adoption and industry solutions."

print("🚀 Testing CIS Post Generation...")
print(f"📝 Topic: {topic}\n")

# Call the generate endpoint
response = requests.post(
    f"{API_BASE_URL}/posts/generate",
    json={"topic": topic, "style": "Thought Leadership"},
    headers=headers,
    timeout=60
)

print(f"Status Code: {response.status_code}")
print("\n📊 Response:")
print(json.dumps(response.json(), indent=2))
