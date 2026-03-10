import requests
import sys
import json

BASE_URL = "http://localhost:8000/api"

# 1. Register User
print("--- Registration ---")
reg_data = {
    "full_name": "Test Farmer",
    "email": "test@farmxpert.com",
    "phone": "9876543210",
    "password": "TestPass123!",
    "username": "testfarmer"
}
try:
    resp = requests.post(f"{BASE_URL}/auth/register", json=reg_data)
    print(f"Status: {resp.status_code}")
    print(json.dumps(resp.json(), indent=2))
except Exception as e:
    print(f"Request failed: {e}")

# Try to get the token for next steps (login might be needed if register doesn't return it)
token = None
if resp.status_code == 200 or resp.status_code == 201:
    data = resp.json()
    token = data.get("access_token")

# 2. Login to get token
print("\n--- Login ---")
login_data = {
    "username": "testfarmer",
    "password": "TestPass123!"
}
resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
print(f"Status: {resp.status_code}")
try:
    data = resp.json()
    token = data.get("access_token")
    if token:
        print("Successfully obtained access token")
    else:
        print(f"Token not found in response: {json.dumps(data, indent=2)}")
except Exception as e:
    print(f"Failed to parse login response: {e}")

if not token:
    print("Could not get auth token. Stopping tests.")
    sys.exit(1)

# 3. Create a profile / farm endpoint? Let's check status first.
headers = {"Authorization": f"Bearer {token}"}

print("\n--- Active Agents Status ---")
resp = requests.get(f"{BASE_URL}/agents/status/active", headers=headers)
print(f"Status: {resp.status_code}")
print(json.dumps(resp.json(), indent=2))

print("\n--- Current User Info ---")
resp = requests.get(f"{BASE_URL}/auth/me", headers=headers)
print(f"Status: {resp.status_code}")
print(json.dumps(resp.json(), indent=2))

print("\n--- Create Farm ---")
farm_data = {
    "name": "Kavya Joshi's Farm",
    "location": "Pune",
    "size_acres": 5.5,
    "farmer_name": "Kavya Joshi",
    "farmer_phone": "9316130106",
    "farmer_email": "kavyajoshi4290@gmail.com"
}
resp = requests.post(f"{BASE_URL}/farms/", headers=headers, json=farm_data)
print(f"Status: {resp.status_code}")
print(json.dumps(resp.json(), indent=2))
