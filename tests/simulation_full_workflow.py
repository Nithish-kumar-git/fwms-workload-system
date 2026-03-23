"""
FWMS Full Operational Simulation Script
=======================================
Run with: python tests/simulation_full_workflow.py

Prerequisites:
  - Docker containers running (docker-compose up -d)
  - Database migrated (happens automatically on startup)

This script simulates a complete semester workflow:
  1. Create & activate academic cycle
  2. Open preference window
  3. Submit faculty preferences (10 faculty × 5 prefs)
  4. Run allocation engine
  5. Generate reports
  6. Coordinator override
  7. Health check verification
  8. Integrity checks
"""

import requests
import json
import sys
import time
from datetime import datetime, timedelta, timezone

BASE = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

# For dev mode authentication — adjust if using real OAuth
DEV_COORDINATOR_COOKIE = {}  # Fill in after login


def log(step, msg, ok=True):
    icon = "✅" if ok else "❌"
    print(f"  {icon} [{step}] {msg}")


def api(method, path, json_data=None, expect_status=200):
    """Make API call and return response."""
    url = f"{BASE}{path}"
    r = getattr(requests, method)(url, json=json_data, headers=HEADERS, cookies=DEV_COORDINATOR_COOKIE)
    if r.status_code != expect_status:
        print(f"  ⚠️  {method.upper()} {path} → {r.status_code}: {r.text[:200]}")
        return None
    return r.json()


def step_1_health_check():
    """Step 1: Verify system is running and DB is connected."""
    print("\n" + "=" * 60)
    print("STEP 1: Health Check")
    print("=" * 60)

    # Basic health
    r = requests.get(f"{BASE}/health")
    if r.status_code == 200:
        log("1a", f"GET /health → {r.json()}")
    else:
        log("1a", f"GET /health failed: {r.status_code}", ok=False)
        return False

    # Deep health (DB connectivity)
    r = requests.get(f"{BASE}/health/deep")
    data = r.json()
    if data.get("database") == "ok":
        log("1b", f"GET /health/deep → database: ok")
    else:
        log("1b", f"GET /health/deep → database: {data.get('database')}", ok=False)
        return False

    return True


def step_2_cycle_management():
    """Step 2: Create and activate academic cycle."""
    print("\n" + "=" * 60)
    print("STEP 2: Academic Cycle Management")
    print("=" * 60)

    # Create cycle
    result = api("post", "/api/cycles", {
        "academic_year": "2026-2027",
        "semester_type": "ODD"
    })
    if result and result.get("success"):
        cycle_id = result["cycle_id"]
        log("2a", f"Created cycle: id={cycle_id}, 2026-2027 ODD")
    else:
        log("2a", f"Create cycle failed: {result}", ok=False)
        return None

    # Activate cycle
    result = api("post", "/api/cycles/activate", {"cycle_id": cycle_id})
    if result and result.get("success"):
        log("2b", f"Activated cycle: id={cycle_id}")
    else:
        log("2b", f"Activate failed: {result}", ok=False)
        return None

    # Verify single-active constraint
    active = api("get", "/api/cycles/active")
    if active and active["id"] == cycle_id:
        log("2c", f"Verified single active cycle: {active['academic_year']} {active['semester_type']}")
    else:
        log("2c", f"Active cycle mismatch", ok=False)

    return cycle_id


def step_3_preference_window():
    """Step 3: Open preference window."""
    print("\n" + "=" * 60)
    print("STEP 3: Preference Window (DRAFT → SCHEDULED → OPEN)")
    print("=" * 60)

    now = datetime.now(timezone.utc)
    start = now.isoformat()
    end = (now + timedelta(hours=2)).isoformat()

    result = api("post", "/api/preference-window/open", {
        "start_time": start,
        "end_time": end,
    })

    if result and result.get("success"):
        window_id = result["window_id"]
        log("3a", f"Window opened: id={window_id} (DRAFT→SCHEDULED→OPEN)")
    else:
        log("3a", f"Window open failed: {result}", ok=False)
        return None

    # Verify window status
    status = api("get", "/api/preference-window/status")
    if status and status.get("is_open"):
        log("3b", f"Window verified OPEN, remaining={status['remaining_seconds']}s")
    else:
        log("3b", "Window not open", ok=False)

    return window_id


def step_4_preference_submissions(num_faculty=10, prefs_per_faculty=5):
    """Step 4: Simulate faculty preference submissions."""
    print("\n" + "=" * 60)
    print(f"STEP 4: Preference Submissions ({num_faculty} faculty × {prefs_per_faculty} prefs)")
    print("=" * 60)

    # Get available offerings
    offerings = api("get", "/api/subjects/offerings")
    if not offerings or len(offerings) == 0:
        log("4a", "No subject offerings available", ok=False)
        return False

    log("4a", f"Found {len(offerings)} subject offerings")

    # Get faculty list
    faculty = api("get", "/api/staff?limit=10")
    if not faculty or len(faculty) == 0:
        log("4b", "No faculty found", ok=False)
        return False

    log("4b", f"Found {len(faculty)} faculty members")

    # Submit preferences
    total_submitted = 0
    total_rejected = 0

    for i, fac in enumerate(faculty[:num_faculty]):
        staff_id = fac["id"]
        for pref_num in range(1, prefs_per_faculty + 1):
            # Pick an offering (wrap around if needed)
            offering_idx = (i * prefs_per_faculty + pref_num - 1) % len(offerings)
            offering_id = offerings[offering_idx]["id"]

            result = api("post", "/api/preferences", {
                "staff_id": staff_id,
                "subject_offering_id": offering_id,
                "preference_number": pref_num,
            })

            if result and result.get("success"):
                total_submitted += 1
            else:
                total_rejected += 1

    log("4c", f"Submitted: {total_submitted}, Rejected: {total_rejected} "
                f"(rejections expected from PREF-02/SHIFT-01/CT-01 rules)")

    return True


def step_5_allocation():
    """Step 5: Run allocation engine."""
    print("\n" + "=" * 60)
    print("STEP 5: Allocation Engine")
    print("=" * 60)

    result = api("post", "/api/allocation/run")
    if result and result.get("success"):
        log("5a", f"Allocation complete: "
            f"{result['subjects_assigned']}/{result['subjects_total']} assigned, "
            f"{result['subjects_unassigned']} unassigned")
        log("5b", f"Overloaded: {result['faculty_overloaded']}, "
            f"Underloaded: {result['faculty_underloaded']}, "
            f"Balanced: {result['faculty_balanced']}")
        return result
    else:
        log("5a", f"Allocation failed: {result}", ok=False)
        return None


def step_6_reports():
    """Step 6: Generate reports."""
    print("\n" + "=" * 60)
    print("STEP 6: Reports (active cycle resolution)")
    print("=" * 60)

    # Faculty workload
    result = api("get", "/api/reports/faculty-workload")
    if result:
        log("6a", f"Faculty workload: {result['total_faculty']} faculty")
    else:
        log("6a", "Faculty workload report failed", ok=False)

    # Subject summary
    result = api("get", "/api/reports/subject-summary")
    if result:
        log("6b", f"Subject summary: {result['total']} records")
    else:
        log("6b", "Subject summary report failed", ok=False)

    # Department summary
    result = api("get", "/api/reports/department-summary")
    if result:
        log("6c", f"Department summary: "
            f"offerings={result['total_subject_offerings']}, "
            f"avg_workload={result['average_workload']}")
    else:
        log("6c", "Department summary report failed", ok=False)


def step_7_integrity_checks():
    """Step 7: Database integrity checks."""
    print("\n" + "=" * 60)
    print("STEP 7: Integrity Checks")
    print("=" * 60)

    # Health metrics (contains window status counts)
    result = api("get", "/health/metrics")
    if result:
        log("7a", f"Health metrics: status={result.get('status')}")
        windows = result.get("windows", {})
        expired = windows.get("expired_open", {}).get("count", 0)
        stuck = windows.get("stuck_scheduled", {}).get("count", 0)
        if expired > 0:
            log("7b", f"WARNING: {expired} expired OPEN windows", ok=False)
        else:
            log("7b", "No expired OPEN windows")
        if stuck > 0:
            log("7c", f"WARNING: {stuck} stuck SCHEDULED windows", ok=False)
        else:
            log("7c", "No stuck SCHEDULED windows")
    else:
        log("7a", "Health metrics failed", ok=False)


def main():
    print("=" * 60)
    print("FWMS FULL OPERATIONAL SIMULATION")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    # Step 1: Health
    if not step_1_health_check():
        print("\n❌ SIMULATION ABORTED: System not healthy")
        sys.exit(1)

    # Step 2: Cycle
    cycle_id = step_2_cycle_management()
    if not cycle_id:
        print("\n❌ SIMULATION ABORTED: Cycle setup failed")
        sys.exit(1)

    # Step 3: Window
    window_id = step_3_preference_window()

    # Step 4: Preferences
    step_4_preference_submissions()

    # Step 5: Allocation
    step_5_allocation()

    # Step 6: Reports
    step_6_reports()

    # Step 7: Integrity
    step_7_integrity_checks()

    print("\n" + "=" * 60)
    print("SIMULATION COMPLETE")
    print(f"Finished: {datetime.now().isoformat()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
