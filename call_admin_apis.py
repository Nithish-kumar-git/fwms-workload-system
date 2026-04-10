#!/usr/bin/env python3
import urllib.request
import json
import time

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

print("Waiting 60 seconds for Railway deployment...")
time.sleep(60)

print("\n\nSTEP 1: Check database state")
call("GET", "/admin/db-state")

print("\n\nSTEP 2: Fix duplicate programs")
call("POST", "/admin/fix-duplicate-programs")

print("\n\nSTEP 3: Seed MCA odd semesters")
call("POST", "/admin/seed-mca-odd")

print("\n\nSTEP 4: Verify database state after seeding")
call("GET", "/admin/db-state")
