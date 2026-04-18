#!/usr/bin/env python3
import urllib.request
import json

base = "https://fwms-workload-system-production.up.railway.app/api/reports"

def get(path):
    req = urllib.request.Request(base+path, headers={"Accept":"application/json"})
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read())

print("=== Offerings by Semester ===")
data = get("/admin/db-state")
print("\nMCA offerings by semester:")
for item in data.get("mca_offerings_by_sem", []):
    print(f"  {item['prog']:<30} Sem {item['sem_label']:<3} = {item['cnt']} offerings")

print("\n=== Open Cycles ===")
for cycle in data.get("open_cycles", []):
    print(f"  Cycle {cycle['id']}: Semester {cycle['semester_id']} ({cycle['status']})")

print("\n=== Summary ===")
print(f"Total MCA offerings: {sum(item['cnt'] for item in data.get('mca_offerings_by_sem', []))}")
print(f"Open semesters: {[c['semester_id'] for c in data.get('open_cycles', [])]}")
