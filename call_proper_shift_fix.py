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

print("\n=== PROGRAM SHIFTS (before fix) ===")
prog_shifts = get("/admin/program-shifts")
print(json.dumps(prog_shifts, indent=2))

print("\n\n=== FIX SHIFT FROM PROGRAM ===")
fix_result = post("/admin/fix-shift-from-program")
print(json.dumps(fix_result, indent=2)[:3000])

print("\n\n=== SHIFT DISTRIBUTION AFTER ===")
shift_state = get("/admin/shift-state")
print(json.dumps(shift_state, indent=2)[:2000])
