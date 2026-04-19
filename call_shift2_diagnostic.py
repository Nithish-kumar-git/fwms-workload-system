#!/usr/bin/env python3
import urllib.request
import json

base = "https://fwms-workload-system-production.up.railway.app/api/reports"

def get(path):
    req = urllib.request.Request(base + path, headers={"Accept": "application/json"})
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read())

print("=== SHIFT2 CHECK ===")
result = get("/admin/shift2-check")
print(json.dumps(result, indent=2))
