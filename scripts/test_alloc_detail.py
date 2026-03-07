"""Run allocation via API and capture full error detail."""
import requests
import sys
import json

BASE = "http://localhost:8000"

# Step 1: Login
r = requests.post(f"{BASE}/api/auth/dev-login")
if r.status_code != 200:
    print(f"Login failed: {r.status_code} {r.text}")
    sys.exit(1)

token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Step 2: Run allocation
r2 = requests.post(f"{BASE}/api/allocation/run", headers=headers, json={})
print(f"Status: {r2.status_code}")
print(f"Full response body:")
try:
    body = r2.json()
    print(json.dumps(body, indent=2))
except:
    print(r2.text)
