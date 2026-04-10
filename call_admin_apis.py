import urllib.request, json, time

print("Waiting 60 seconds for Railway deployment...")
time.sleep(60)

base = "https://fwms-workload-system-production.up.railway.app/api/reports"

def call(method, path):
    url = base + path
    req = urllib.request.Request(
        url,
        method=method,
        headers={"Content-Type": "application/json"}
    )
    if method == "POST":
        req.data = b"{}"
    
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        print(f"\n{'='*80}")
        print(f"{method} {path}")
        print('='*80)
        print(json.dumps(data, indent=2)[:3000])
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"ERROR {method} {path}: {e}")
        print('='*80)

# Step 1: Check current state
call("GET", "/admin/db-state")

# Step 2: Fix duplicate programs
call("POST", "/admin/fix-duplicate-programs")

# Step 3: Seed MCA odd semesters
call("POST", "/admin/seed-mca-odd")

# Step 4: Verify final state
call("GET", "/admin/db-state")
