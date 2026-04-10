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
        output = json.dumps(data, indent=2)
        if len(output) > 4000:
            print(output[:4000] + "\n... (truncated)")
        else:
            print(output)
        return data
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"ERROR {method} {path}: {e}")
        print('='*80)
        return None

# Step 1: Check current state
print("\n\n### STEP 1: Check current DB state ###")
state1 = call("GET", "/admin/db-state")

# Step 2: Seed MCA odd semesters (duplicates already fixed)
print("\n\n### STEP 2: Seed MCA odd semesters ###")
seed_result = call("POST", "/admin/seed-mca-odd")

# Step 3: Verify final state
print("\n\n### STEP 3: Verify final state ###")
state2 = call("GET", "/admin/db-state")

# Summary
print("\n\n" + "="*80)
print("SUMMARY")
print("="*80)
if seed_result:
    print(f"Status: {seed_result.get('status')}")
    print(f"Subjects created: {len(seed_result.get('subjects_created', []))}")
    print(f"Subjects existed: {len(seed_result.get('subjects_existed', []))}")
    print(f"Offerings created: {seed_result.get('offerings_created', 0)}")
    print(f"Offerings existed: {seed_result.get('offerings_existed', 0)}")
    if seed_result.get('errors'):
        print(f"Errors: {seed_result['errors']}")
