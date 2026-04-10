import urllib.request, json, time

print("Waiting 60 seconds for Railway deployment...")
time.sleep(60)

base = "https://fwms-workload-system-production.up.railway.app/api/reports"

def call(method, path):
    url = base + path
    req = urllib.request.Request(url, method=method, headers={"Content-Type": "application/json"})
    if method == "POST":
        req.data = b"{}"
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        print(f"\n=== {method} {path} ===")
        print(json.dumps(data, indent=2)[:3000])
        return data
    except Exception as e:
        print(f"ERROR {method} {path}: {e}")
        return None

# Step 1: Check initial state
print("\n" + "="*80)
print("STEP 1: Check initial database state")
print("="*80)
call("GET", "/admin/db-state")

# Step 2: Fix duplicate programs
print("\n" + "="*80)
print("STEP 2: Fix duplicate programs")
print("="*80)
call("POST", "/admin/fix-duplicate-programs")

# Step 3: Seed MCA odd semesters
print("\n" + "="*80)
print("STEP 3: Seed MCA odd semester subjects and offerings")
print("="*80)
call("POST", "/admin/seed-mca-odd")

# Step 4: Verify final state
print("\n" + "="*80)
print("STEP 4: Verify final database state")
print("="*80)
call("GET", "/admin/db-state")

print("\n" + "="*80)
print("DONE - Check output above for results")
print("="*80)
