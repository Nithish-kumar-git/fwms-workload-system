#!/usr/bin/env python3
import urllib.request
import json
import time

base = "https://fwms-workload-system-production.up.railway.app/api/reports"

def get(path):
    req = urllib.request.Request(base+path, headers={"Accept":"application/json"})
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read())

def post(path):
    req = urllib.request.Request(base+path, method="POST", data=b"{}", headers={"Content-Type":"application/json"})
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read())

print("Waiting 60 seconds for Railway deployment...")
time.sleep(60)

print("\n=== SHIFT STATE BEFORE ===")
before = get("/admin/shift-state")
print(json.dumps(before, indent=2))

print("\n\n=== FIX SHIFT 2 ===")
fix_result = post("/admin/fix-shift2-offerings")
print(json.dumps(fix_result, indent=2))

print("\n\n=== SHIFT STATE AFTER ===")
after = get("/admin/shift-state")
print(json.dumps(after, indent=2))
