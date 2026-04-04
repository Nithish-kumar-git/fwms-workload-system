"""
FWMS Demo Preparation Script
Usage: python scripts/demo_prep.py
"""

import subprocess
import sys
import os
import json
import time
from datetime import datetime, timedelta, timezone

# Fix Windows encoding
os.environ["PYTHONIOENCODING"] = "utf-8"
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

BASE_URL = "http://localhost:8000"
DB_CONTAINER = "faculty_selection_db"


def psql(sql):
    r = subprocess.run(
        ["docker", "exec", DB_CONTAINER, "psql", "-U", "postgres", "-d", "faculty_selection",
         "-t", "-A", "-c", sql],
        capture_output=True, text=True
    )
    return r.stdout.strip()


def psql_exec(sql):
    subprocess.run(
        ["docker", "exec", DB_CONTAINER, "psql", "-U", "postgres", "-d", "faculty_selection",
         "-c", sql],
        capture_output=True, text=True
    )


def main():
    print()
    print("=" * 60)
    print("   FWMS DEMO PREPARATION")
    print("=" * 60)
    print()

    # Step 1: Dev Login
    print("[1/6] Dev login...")
    try:
        r = requests.post(f"{BASE_URL}/api/auth/dev-login", timeout=5)
    except requests.ConnectionError:
        print("  [FAIL] Cannot connect to backend at", BASE_URL)
        sys.exit(1)

    if r.status_code != 200:
        print(f"  [FAIL] Dev login failed ({r.status_code}): {r.text}")
        sys.exit(1)

    login_data = r.json()
    token = login_data["token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print(f"  [OK] Logged in as: {login_data['name']} (role={login_data['role']})")

    # Step 2: Ensure active cycle
    print("\n[2/6] Academic cycle...")
    cycle_id = psql("SELECT id FROM cycle WHERE status = 'OPEN' LIMIT 1")
    if not cycle_id:
        # Get or create academic year
        ay_id = psql("SELECT id FROM academic_year WHERE label = '2025-2026' LIMIT 1")
        if not ay_id:
            psql_exec("INSERT INTO academic_year (label) VALUES ('2025-2026')")
            ay_id = psql("SELECT id FROM academic_year WHERE label = '2025-2026' LIMIT 1")
        
        # Get semester (assuming EVEN semester exists)
        sem_id = psql("SELECT id FROM semester WHERE label = 'EVEN' LIMIT 1")
        if not sem_id:
            print("  [FAIL] EVEN semester not found in database!")
            sys.exit(1)
        
        # Create cycle
        psql_exec(
            f"INSERT INTO cycle (academic_year_id, semester_id, status) "
            f"VALUES ({ay_id}, {sem_id}, 'OPEN')"
        )
        cycle_id = psql("SELECT id FROM cycle WHERE status = 'OPEN' LIMIT 1")
        print(f"  [OK] Created cycle id={cycle_id}")
    else:
        print(f"  [OK] Active cycle id={cycle_id}")

    # Step 3: Open preference window
    print("\n[3/6] Preference window...")
    r = requests.get(f"{BASE_URL}/api/pref-window/status", headers=headers, timeout=5)
    if r.status_code == 200 and r.json().get("is_open"):
        print(f"  [OK] Already open (id={r.json().get('window_id')})")
    else:
        # The original code used datetime.utcnow() and timedelta.
        # The instruction is to replace datetime.UTC with timezone.utc.
        # The provided code edit block changes the logic for start_time and end_time.
        # I will apply the logic from the provided code edit block,
        # ensuring the dictionary syntax is correct.
        r = requests.post(f"{BASE_URL}/api/pref-window/open", headers=headers, timeout=5, json={
            "academic_year": "2025-2026",
            "semester_type": "EVEN",
            "start_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00Z"),
            "end_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT23:59:59Z"),
        })
        if r.status_code == 200:
            result = r.json()
            if result.get("success"):
                print(f"  [OK] Opened (id={result.get('window_id')})")
            else:
                print(f"  [WARN] {result.get('message', 'Unknown')}")
        else:
            print(f"  [WARN] {r.status_code}: {r.text[:200]}")

    # Step 4: Clear old data
    print("\n[4/6] Clearing old data...")
    psql_exec(f"DELETE FROM allocation WHERE cycle_id = {cycle_id}")
    psql_exec(f"DELETE FROM workload_summary WHERE cycle_id = {cycle_id}")
    psql_exec(f"DELETE FROM faculty_preference WHERE cycle_id = {cycle_id}")
    print("  [OK] Cleared allocations, workload summaries, and preferences")

    # Step 5: Seed preferences
    print("\n[5/6] Seeding preferences (5 per faculty, shift-compatible)...")

    staff_raw = psql("SELECT id, shift FROM staff WHERE is_active = true ORDER BY id")
    if not staff_raw:
        print("  [FAIL] No active staff found!")
        sys.exit(1)

    staff_list = []
    for line in staff_raw.split("\n"):
        parts = line.strip().split("|")
        if len(parts) == 2:
            sid = int(parts[0].strip())
            shift = parts[1].strip() or None
            staff_list.append((sid, shift))

    total_prefs = 0
    for i, (staff_id, shift) in enumerate(staff_list):
        if shift == "SHIFT1":
            shift_sql = "AND so.shift = 1"
        elif shift == "SHIFT2":
            shift_sql = "AND so.shift = 2"
        else:
            shift_sql = ""

        offerings_raw = psql(
            f"SELECT so.id FROM subject_offering so "
            f"JOIN cycle c ON c.academic_year_id = so.academic_year_id "
            f"             AND c.semester_id = so.semester_id "
            f"WHERE c.id = {cycle_id} AND so.is_active = true "
            f"{shift_sql} ORDER BY RANDOM() LIMIT 5"
        )

        if not offerings_raw:
            continue

        for pref_num, line in enumerate(offerings_raw.split("\n"), 1):
            off_id = line.strip()
            if off_id:
                psql_exec(
                    f"INSERT INTO faculty_preference "
                    f"(staff_id, subject_offering_id, preference_number, cycle_id) "
                    f"VALUES ({staff_id}, {off_id}, {pref_num}, {cycle_id})"
                )
                total_prefs += 1

        # Progress indicator
        if (i + 1) % 5 == 0 or i == len(staff_list) - 1:
            print(f"  ... {i + 1}/{len(staff_list)} faculty processed")

    print(f"  [OK] Seeded {total_prefs} preferences for {len(staff_list)} faculty")

    # Step 6: Run allocation
    print("\n[6/6] Running allocation engine...")
    r = requests.post(f"{BASE_URL}/api/allocation/run", headers=headers, timeout=60)
    if r.status_code == 200:
        result = r.json()
        print(f"  [OK] Allocation complete!")
        print()
        print("  +-------------------------------------+")
        print(f"  | Total offerings:    {str(result.get('subjects_total', '?')):>13s} |")
        print(f"  | Allocated:          {str(result.get('subjects_assigned', '?')):>13s} |")
        print(f"  | Unallocated:        {str(result.get('subjects_unassigned', '?')):>13s} |")
        print(f"  | Faculty balanced:   {str(result.get('faculty_balanced', '?')):>13s} |")
        print(f"  | Faculty overloaded: {str(result.get('faculty_overloaded', '?')):>13s} |")
        print(f"  | Faculty underloaded:{str(result.get('faculty_underloaded', '?')):>13s} |")
        print("  +-------------------------------------+")
    else:
        print(f"  [WARN] Allocation returned {r.status_code}")
        print(f"  You can run allocation from the UI: /admin/allocation")

    # Final summary
    pref_count = psql(f"SELECT count(*) FROM faculty_preference WHERE cycle_id = {cycle_id}")
    alloc_count = psql(f"SELECT count(*) FROM allocation WHERE cycle_id = {cycle_id}")

    print()
    print("=" * 60)
    print("   DEMO SEED COMPLETE")
    print(f"   Preferences: {pref_count}")
    print(f"   Allocations: {alloc_count}")
    print(f"   Dashboard: http://localhost:5173/dashboard")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
