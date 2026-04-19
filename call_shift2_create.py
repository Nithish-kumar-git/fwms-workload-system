#!/usr/bin/env python3
import urllib.request
import json

base = "https://fwms-workload-system-production.up.railway.app/api/reports"

def post(path):
    req = urllib.request.Request(
        base + path,
        method="POST",
        data=b"{}",
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read())

def get(path):
    req = urllib.request.Request(
        base + path,
        headers={"Accept": "application/json"}
    )
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read())

print("=== CREATE SHIFT 2 OFFERINGS ===")
result = post("/admin/create-shift2-offerings")
print(json.dumps(result, indent=2))

print("\n=== VERIFY SHIFT STATE ===")
shift_state = get("/admin/shift-state")
print(json.dumps(shift_state, indent=2))
