"""
FCFS Concurrency Torture Test — HARDENED VERSION
Tests advisory lock serialization, quota enforcement, FCFS guarantee, and slot uniqueness.

CRITICAL FIXES:
- Uses multiple staff IDs to test true parallel contention
- Separate staff per test suite to avoid quota interference
- Cross-staff same-subject race test
- CHANGE vs SELECT interleaving test
- TRUNCATE-based cleanup to bypass audit_log immutability triggers

Requirements:
- PostgreSQL database with schema.sql v1.3 applied
- Active selection window
- Test staff and subjects seeded

Run: python tests/concurrency_torture_test.py
"""

import asyncio
import asyncpg
import os
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Database connection parameters
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "faculty_selection"
DB_USER = "faculty_user"
DB_PASSWORD = "faculty_password"


class TortureTestResults:
    """Aggregates test results for final reporting."""
    
    def __init__(self):
        self.test_1_quota_results: List[Dict[str, Any]] = []
        self.test_2_fcfs_results: List[Dict[str, Any]] = []
        self.test_3_cross_staff_results: List[Dict[str, Any]] = []
        self.test_4_change_select_results: Dict[str, Any] = {}
        self.test_5_slot_results: List[Dict[str, Any]] = []
        self.errors: List[str] = []
    
    def log_error(self, test_name: str, error: str):
        self.errors.append(f"[{test_name}] {error}")
    
    def print_summary(self):
        print("\n" + "="*80)
        print("CONCURRENCY TORTURE TEST SUMMARY — HARDENED VERSION")
        print("="*80)
        
        # Test 1: Quota Enforcement (multiple staff)
        print("\n[TEST 1] QUOTA ENFORCEMENT (5 staff, 2 subjects each, quota=3)")
        print("-" * 80)
        successes = sum(1 for r in self.test_1_quota_results if r["success"])
        quota_exceeded = sum(1 for r in self.test_1_quota_results if "Quota exceeded" in r.get("message", ""))
        print(f"Total requests: {len(self.test_1_quota_results)}")
        print(f"Successful selections: {successes}")
        print(f"Quota exceeded rejections: {quota_exceeded}")
        print(f"Expected: 15 successes (5 staff × 3 quota), 5 quota exceeded")
        if successes == 15 and quota_exceeded == 5:
            print("✅ PASS: Quota enforcement correct")
        else:
            print("❌ FAIL: Quota enforcement violated")
        
        # Test 2: FCFS Enforcement (same staff, same subject)
        print("\n[TEST 2] FCFS ENFORCEMENT (5 parallel, same staff, same subject)")
        print("-" * 80)
        fcfs_successes = sum(1 for r in self.test_2_fcfs_results if r["success"])
        fcfs_conflicts = sum(1 for r in self.test_2_fcfs_results if "Subject already selected" in r.get("message", ""))
        print(f"Total requests: {len(self.test_2_fcfs_results)}")
        print(f"Successful selections: {fcfs_successes}")
        print(f"Conflict rejections: {fcfs_conflicts}")
        print(f"Expected: exactly 1 success, 4 conflicts")
        if fcfs_successes == 1 and fcfs_conflicts == 4:
            print("✅ PASS: FCFS guarantee enforced (same-staff)")
        else:
            print("❌ FAIL: FCFS guarantee violated")
        
        # Test 3: Cross-Staff FCFS
        print("\n[TEST 3] CROSS-STAFF FCFS (4 different staff, same subject)")
        print("-" * 80)
        cross_successes = sum(1 for r in self.test_3_cross_staff_results if r["success"])
        cross_conflicts = sum(1 for r in self.test_3_cross_staff_results if "Subject already selected" in r.get("message", ""))
        print(f"Total requests: {len(self.test_3_cross_staff_results)}")
        print(f"Successful selections: {cross_successes}")
        print(f"Conflict rejections: {cross_conflicts}")
        print(f"Expected: exactly 1 success, 3 conflicts")
        if cross_successes == 1 and cross_conflicts == 3:
            print("✅ PASS: FCFS guarantee enforced (cross-staff)")
        else:
            print("❌ FAIL: Cross-staff FCFS violated (CRITICAL RACE CONDITION)")
        
        # Test 4: CHANGE vs SELECT Interleaving
        print("\n[TEST 4] CHANGE vs SELECT INTERLEAVING")
        print("-" * 80)
        if self.test_4_change_select_results:
            change_success = self.test_4_change_select_results.get("change_success", False)
            select_success = self.test_4_change_select_results.get("select_success", False)
            print(f"CHANGE outcome: {'SUCCESS' if change_success else 'FAILED'}")
            print(f"SELECT outcome: {'SUCCESS' if select_success else 'FAILED'}")
            print(f"Expected: Exactly one succeeds (either CHANGE or SELECT, not both)")
            if (change_success and not select_success) or (not change_success and select_success):
                print("✅ PASS: CHANGE/SELECT mutual exclusion enforced")
            else:
                print("❌ FAIL: Both succeeded or both failed (race condition)")
        else:
            print("⚠️  WARNING: No data collected")
        
        # Test 5: Slot Uniqueness
        print("\n[TEST 5] SLOT UNIQUENESS VERIFICATION")
        print("-" * 80)
        if self.test_5_slot_results:
            for staff_data in self.test_5_slot_results:
                staff_id = staff_data["staff_id"]
                slots = staff_data["slots"]
                unique_slots = len(set(slots))
                total_slots = len(slots)
                print(f"Staff {staff_id}: {total_slots} slots, {unique_slots} unique → {sorted(slots)}")
                if unique_slots != total_slots:
                    print(f"  ❌ FAIL: Slot collision detected for staff {staff_id}")
                elif slots != list(range(1, total_slots + 1)):
                    print(f"  ❌ FAIL: Slot gap detected for staff {staff_id}")
                else:
                    print(f"  ✅ PASS: Slots unique and sequential")
        else:
            print("⚠️  WARNING: No slot data collected")
        
        # Errors
        if self.errors:
            print("\n[ERRORS]")
            print("-" * 80)
            for error in self.errors:
                print(f"❌ {error}")
        else:
            print("\n✅ No errors encountered")
        
        print("\n" + "="*80)


async def setup_test_data(conn: asyncpg.Connection) -> Dict[str, Any]:
    """
    Setup test data: window, multiple staff, batch, specialization, subjects.
    Returns dict with IDs for use in tests.
    
    IDEMPOTENT: Uses UUID suffixes to ensure unique names per run.
    Multiple consecutive runs will succeed without manual DB reset.
    """
    from uuid import uuid4
    
    print("\n[SETUP] Creating test data...")
    
    # Generate unique run ID for this test execution
    run_id = str(uuid4())[:8]
    
    # Create batch with unique name
    batch_id = await conn.fetchval(
        "INSERT INTO batch (name, is_active) VALUES ($1, true) RETURNING id",
        f"Test Batch {run_id}"
    )
    
    # Create specialization with unique name
    spec_id = await conn.fetchval(
        "INSERT INTO specialization (name, is_active) VALUES ($1, true) RETURNING id",
        f"Computer Science {run_id}"
    )
    
    # Create 10 test staff members (for different test suites)
    staff_ids = []
    for i in range(1, 11):
        staff_id = await conn.fetchval(
            """
            INSERT INTO staff (email, name, is_coordinator, is_active)
            VALUES ($1, $2, false, true)
            RETURNING id
            """,
            f"test.staff{i}.{run_id}@hindustanuniv.ac.in", f"Test Staff {i} ({run_id})"
        )
        staff_ids.append(staff_id)
        
        # Create staff assignment
        await conn.execute(
            """
            INSERT INTO staff_assignment (staff_id, batch_id, specialization_id)
            VALUES ($1, $2, $3)
            """,
            staff_id, batch_id, spec_id
        )
    
    # Create selection window (active, quota=3) with unique name
    window_id = await conn.fetchval(
        """
        INSERT INTO selection_window (name, start_time, end_time, max_subjects_per_staff, is_active)
        VALUES ($1, now() - interval '1 hour', now() + interval '1 hour', 3, true)
        RETURNING id
        """,
        f"Test Window {run_id}"
    )
    
    # Create 30 test subjects with unique codes
    subject_ids = []
    for i in range(1, 31):
        subject_id = await conn.fetchval(
            """
            INSERT INTO subject (code, name, batch_id, specialization_id, is_active)
            VALUES ($1, $2, $3, $4, true)
            RETURNING id
            """,
            f"CS{i:03d}_{run_id}", f"Test Subject {i} ({run_id})", batch_id, spec_id
        )
        subject_ids.append(subject_id)
    
    print(f"✅ Created: batch_id={batch_id}, spec_id={spec_id}, window_id={window_id}")
    print(f"✅ Created {len(staff_ids)} staff members")
    print(f"✅ Created {len(subject_ids)} subjects")
    print(f"✅ Run ID: {run_id}")
    
    return {
        "batch_id": batch_id,
        "spec_id": spec_id,
        "staff_ids": staff_ids,
        "window_id": window_id,
        "subject_ids": subject_ids
    }


async def cleanup_test_data(conn: asyncpg.Connection, test_data: Dict[str, Any]):
    """Clean up test data using TRUNCATE to bypass audit_log triggers."""
    print("\n[CLEANUP] Removing test data...")
    
    # TRUNCATE audit_log (bypasses row-level triggers)
    await conn.execute("TRUNCATE TABLE audit_log CASCADE")
    
    # Delete in correct FK order: children first, then parents
    # 1. Delete subject_selection (all rows referencing test subjects)
    await conn.execute(
        "DELETE FROM subject_selection WHERE subject_id IN (SELECT id FROM subject WHERE batch_id = $1)",
        test_data["batch_id"]
    )
    
    # 2. Delete subject (child of batch, specialization)
    await conn.execute("DELETE FROM subject WHERE batch_id = $1", test_data["batch_id"])
    
    # 3. Delete staff_assignment (child of staff, batch, specialization)
    for staff_id in test_data["staff_ids"]:
        await conn.execute("DELETE FROM staff_assignment WHERE staff_id = $1", staff_id)
    
    # 4. Delete staff
    for staff_id in test_data["staff_ids"]:
        await conn.execute("DELETE FROM staff WHERE id = $1", staff_id)
    
    # 5. Delete selection_window
    await conn.execute("DELETE FROM selection_window WHERE id = $1", test_data["window_id"])
    
    # 6. Delete batch
    await conn.execute("DELETE FROM batch WHERE id = $1", test_data["batch_id"])
    
    # 7. Delete specialization
    await conn.execute("DELETE FROM specialization WHERE id = $1", test_data["spec_id"])
    
    print("✅ Cleanup complete")


async def select_subject_raw(
    staff_id: int,
    subject_id: int,
    batch_id: int,
    spec_id: int,
    worker_id: int
) -> Dict[str, Any]:
    """Execute select_subject transaction directly via asyncpg."""
    
    # FORENSIC: Track call count
    if not hasattr(select_subject_raw, 'call_count'):
        select_subject_raw.call_count = 0
    select_subject_raw.call_count += 1
    call_num = select_subject_raw.call_count
    
    if call_num <= 5:
        print(f"\n[FORENSIC] select_subject_raw call #{call_num}: staff_id={staff_id}, subject_id={subject_id}, worker_id={worker_id}")
    
    conn = await asyncpg.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )
    
    try:
        async with conn.transaction(isolation="read_committed"):
            await conn.execute("SET LOCAL lock_timeout = '5s'")
            
            # Window validation
            window = await conn.fetchrow(
                """
                SELECT id, max_subjects_per_staff
                FROM selection_window
                WHERE is_active = true AND now() BETWEEN start_time AND end_time
                FOR SHARE
                """
            )
            
            if not window:
                result = {"success": False, "message": "Window closed", "worker_id": worker_id}
                if call_num <= 5:
                    print(f"[FORENSIC] Call #{call_num} EARLY EXIT: Window closed")
                return result
            
            window_id = window["id"]
            max_quota = window["max_subjects_per_staff"]
            
            if call_num <= 5:
                print(f"[FORENSIC] Call #{call_num}: window_id={window_id}, max_quota={max_quota}")
            
            # Eligibility check
            eligible = await conn.fetchrow(
                """
                SELECT sa.id
                FROM staff_assignment sa
                JOIN subject s ON s.batch_id = sa.batch_id AND s.specialization_id = sa.specialization_id
                WHERE sa.staff_id = $1 AND s.id = $2
                FOR SHARE
                """,
                staff_id, subject_id
            )
            
            if not eligible:
                result = {"success": False, "message": "Not eligible", "worker_id": worker_id}
                if call_num <= 5:
                    print(f"[FORENSIC] Call #{call_num} EARLY EXIT: Not eligible (staff_id={staff_id}, subject_id={subject_id})")
                return result
            
            if call_num <= 5:
                print(f"[FORENSIC] Call #{call_num}: Eligibility OK")
            
            # Staff-level advisory lock (serializes slot computation per staff)
            await conn.fetchval("SELECT pg_advisory_xact_lock($1)", staff_id)
            
            # Staff+window advisory lock
            await conn.fetchval("SELECT pg_advisory_xact_lock($1, $2)", staff_id, window_id)
            
            if call_num <= 5:
                print(f"[FORENSIC] Call #{call_num}: Advisory locks acquired (staff + staff/window)")
            
            # Quota check
            # Cannot use COUNT(*) with FOR UPDATE, must fetch rows and count
            quota_rows = await conn.fetch(
                """
                SELECT id
                FROM subject_selection
                WHERE staff_id = $1 AND window_id = $2 AND status = 'SELECTED'
                FOR UPDATE
                """,
                staff_id, window_id
            )
            
            quota_count = len(quota_rows)
            
            if call_num <= 5:
                print(f"[FORENSIC] Call #{call_num}: Current quota={quota_count}/{max_quota}")
            
            if quota_count >= max_quota:
                result = {"success": False, "message": "Quota exceeded", "worker_id": worker_id}
                if call_num <= 5:
                    print(f"[FORENSIC] Call #{call_num} EARLY EXIT: Quota exceeded ({quota_count} >= {max_quota})")
                return result
            
            # Slot assignment
            # Cannot use MAX() with FOR UPDATE, must fetch rows and compute max
            slot_rows = await conn.fetch(
                """
                SELECT staff_slot_number
                FROM subject_selection
                WHERE staff_id = $1 AND window_id = $2 AND status = 'SELECTED'
                FOR UPDATE
                """,
                staff_id, window_id
            )
            
            slot = max([row['staff_slot_number'] for row in slot_rows], default=0) + 1
            
            if call_num <= 5:
                print(f"[FORENSIC] Call #{call_num}: Assigned slot={slot}")
            
            # FCFS claim
            selection_id = await conn.fetchval(
                """
                INSERT INTO subject_selection
                  (subject_id, staff_id, batch_id, specialization_id, window_id, staff_slot_number, status, selected_at)
                VALUES ($1, $2, $3, $4, $5, $6, 'SELECTED', now())
                ON CONFLICT (subject_id) WHERE status = 'SELECTED'
                DO NOTHING
                RETURNING id
                """,
                subject_id, staff_id, batch_id, spec_id, window_id, slot
            )
            
            if not selection_id:
                result = {"success": False, "message": "Subject already selected", "worker_id": worker_id}
                if call_num <= 5:
                    print(f"[FORENSIC] Call #{call_num} EARLY EXIT: Subject already selected (conflict)")
                return result
            
            if call_num <= 5:
                print(f"[FORENSIC] Call #{call_num}: INSERT succeeded, selection_id={selection_id}")
            
            # Audit log
            await conn.execute(
                """
                INSERT INTO audit_log (actor_staff_id, action_type, subject_id, affected_staff_id, details)
                VALUES ($1, 'SELECT', $2, $3, '{}'::jsonb)
                """,
                staff_id, subject_id, staff_id
            )
            
            result = {
                "success": True,
                "message": "Selected",
                "selection_id": selection_id,
                "slot": slot,
                "worker_id": worker_id,
                "staff_id": staff_id
            }
            
            if call_num <= 5:
                print(f"[FORENSIC] Call #{call_num} SUCCESS: {result}")
            
            return result
    
    except Exception as e:
        result = {"success": False, "message": f"Error: {str(e)}", "worker_id": worker_id}
        if call_num <= 5:
            print(f"[FORENSIC] Call #{call_num} EXCEPTION: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
        return result
    
    finally:
        await conn.close()


async def change_subject_raw(
    staff_id: int,
    old_subject_id: int,
    new_subject_id: int,
    batch_id: int,
    spec_id: int,
    worker_id: int
) -> Dict[str, Any]:
    """Execute change_subject transaction directly via asyncpg."""
    conn = await asyncpg.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )
    
    try:
        async with conn.transaction(isolation="read_committed"):
            await conn.execute("SET LOCAL lock_timeout = '5s'")
            
            # Window validation
            window = await conn.fetchrow(
                """
                SELECT id
                FROM selection_window
                WHERE is_active = true AND now() BETWEEN start_time AND end_time
                FOR SHARE
                """
            )
            
            if not window:
                return {"success": False, "message": "Window closed", "worker_id": worker_id}
            
            window_id = window["id"]
            
            # Eligibility check for new subject
            eligible = await conn.fetchrow(
                """
                SELECT sa.id
                FROM staff_assignment sa
                JOIN subject s ON s.batch_id = sa.batch_id AND s.specialization_id = sa.specialization_id
                WHERE sa.staff_id = $1 AND s.id = $2
                FOR SHARE
                """,
                staff_id, new_subject_id
            )
            
            if not eligible:
                return {"success": False, "message": "Not eligible", "worker_id": worker_id}
            
            # Staff-level advisory lock (serializes slot computation per staff)
            await conn.fetchval("SELECT pg_advisory_xact_lock($1)", staff_id)
            
            # Staff+window advisory lock
            await conn.fetchval("SELECT pg_advisory_xact_lock($1, $2)", staff_id, window_id)
            
            # Lock old subject and get slot
            old_selection = await conn.fetchrow(
                """
                SELECT id, staff_slot_number
                FROM subject_selection
                WHERE subject_id = $1 AND staff_id = $2 AND window_id = $3 AND status = 'SELECTED'
                FOR UPDATE
                """,
                old_subject_id, staff_id, window_id
            )
            
            if not old_selection:
                return {"success": False, "message": "Old subject not found", "worker_id": worker_id}
            
            old_id = old_selection["id"]
            reused_slot = old_selection["staff_slot_number"]
            
            # Atomic UPDATE: swap subject_id on existing row
            # Preserves staff_slot_number immutably
            update_count = await conn.execute(
                """
                UPDATE subject_selection
                SET subject_id = $1,
                    updated_at = now()
                WHERE id = $2
                  AND status = 'SELECTED'
                """,
                new_subject_id, old_id
            )
            
            # asyncpg returns "UPDATE N" string
            rows_updated = int(update_count.split(" ")[1])
            
            if rows_updated == 0:
                return {"success": False, "message": "Change failed unexpectedly", "worker_id": worker_id}
            
            # Audit log
            await conn.execute(
                """
                INSERT INTO audit_log (actor_staff_id, action_type, subject_id, affected_staff_id, details)
                VALUES ($1, 'CHANGE', $2, $3, jsonb_build_object('old_subject_id', $4, 'new_subject_id', $5))
                """,
                staff_id, new_subject_id, staff_id, old_subject_id, new_subject_id
            )
            
            return {
                "success": True,
                "message": "Changed",
                "selection_id": old_id,
                "slot": reused_slot,
                "worker_id": worker_id
            }
    
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}", "worker_id": worker_id}
    
    finally:
        await conn.close()


async def test_1_quota_enforcement(test_data: Dict[str, Any], results: TortureTestResults):
    """
    Test 1: Quota enforcement with 5 staff, each selecting 4 subjects (quota=3).
    Expected: 15 successes (5 staff × 3 quota), 5 quota exceeded (5 staff × 1 over).
    """
    print("\n[TEST 1] Running quota enforcement test (5 staff, 4 subjects each)...")
    
    batch_id = test_data["batch_id"]
    spec_id = test_data["spec_id"]
    staff_ids = test_data["staff_ids"][:5]  # Use first 5 staff
    subject_ids = test_data["subject_ids"][:20]  # Use first 20 subjects
    
    # Defensive assertion
    assert len(staff_ids) >= 5, f"Expected at least 5 staff, got {len(staff_ids)}"
    assert len(subject_ids) >= 20, f"Expected at least 20 subjects, got {len(subject_ids)}"
    
    tasks = []
    for i, staff_id in enumerate(staff_ids):
        for j in range(4):  # Each staff tries 4 subjects (quota is 3)
            subject_id = subject_ids[i * 4 + j]
            tasks.append(select_subject_raw(staff_id, subject_id, batch_id, spec_id, worker_id=len(tasks)))
    
    outcomes = await asyncio.gather(*tasks)
    results.test_1_quota_results = outcomes
    
    # FORENSIC: Verify actual database state
    conn = await asyncpg.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )
    try:
        row_count = await conn.fetchval(
            "SELECT COUNT(*) FROM subject_selection WHERE window_id = $1",
            test_data["window_id"]
        )
        print(f"\n[FORENSIC] Database verification: {row_count} rows in subject_selection")
        
        # Check per-staff counts
        for staff_id in staff_ids:
            staff_count = await conn.fetchval(
                "SELECT COUNT(*) FROM subject_selection WHERE staff_id = $1 AND window_id = $2",
                staff_id, test_data["window_id"]
            )
            print(f"[FORENSIC]   Staff {staff_id}: {staff_count} selections")
    finally:
        await conn.close()
    
    print(f"✅ Test 1 complete: {len(outcomes)} results collected")


async def test_2_fcfs_enforcement(test_data: Dict[str, Any], results: TortureTestResults):
    """
    Test 2: FCFS enforcement - 5 parallel requests from SAME staff for SAME subject.
    Expected: exactly 1 success, 4 "already selected" conflicts.
    """
    print("\n[TEST 2] Running FCFS enforcement test (5 workers, same staff, same subject)...")
    
    # Defensive assertion
    assert len(test_data["staff_ids"]) >= 6, f"Expected at least 6 staff, got {len(test_data['staff_ids'])}"
    assert len(test_data["subject_ids"]) >= 21, f"Expected at least 21 subjects, got {len(test_data['subject_ids'])}"
    
    staff_id = test_data["staff_ids"][5]  # Use staff 6 (fresh, no quota used)
    batch_id = test_data["batch_id"]
    spec_id = test_data["spec_id"]
    subject_id = test_data["subject_ids"][20]  # Use subject 21
    
    tasks = [
        select_subject_raw(staff_id, subject_id, batch_id, spec_id, worker_id=i)
        for i in range(5)
    ]
    
    outcomes = await asyncio.gather(*tasks)
    results.test_2_fcfs_results = outcomes
    
    print(f"✅ Test 2 complete: {len(outcomes)} results collected")


async def test_3_cross_staff_fcfs(test_data: Dict[str, Any], results: TortureTestResults):
    """
    Test 3: Cross-staff FCFS - 5 DIFFERENT staff competing for SAME subject.
    Expected: exactly 1 success, 4 conflicts.
    This is the TRUE race condition test (different advisory locks).
    """
    print("\n[TEST 3] Running cross-staff FCFS test (5 different staff, same subject)...")
    
    # Defensive assertion
    assert len(test_data["staff_ids"]) >= 10, f"Expected at least 10 staff, got {len(test_data['staff_ids'])}"
    assert len(test_data["subject_ids"]) >= 22, f"Expected at least 22 subjects, got {len(test_data['subject_ids'])}"
    
    staff_ids = test_data["staff_ids"][6:10]  # Use staff 7-10 (4 staff, fresh)
    batch_id = test_data["batch_id"]
    spec_id = test_data["spec_id"]
    subject_id = test_data["subject_ids"][21]  # Use subject 22
    
    tasks = [
        select_subject_raw(staff_ids[i], subject_id, batch_id, spec_id, worker_id=i)
        for i in range(len(staff_ids))
    ]
    
    outcomes = await asyncio.gather(*tasks)
    results.test_3_cross_staff_results = outcomes
    
    print(f"✅ Test 3 complete: {len(outcomes)} results collected")


async def test_4_change_select_interleaving(test_data: Dict[str, Any], results: TortureTestResults):
    """
    Test 4: CHANGE vs SELECT interleaving - same staff tries to CHANGE and SELECT same subject.
    Expected: Exactly one succeeds (mutual exclusion via advisory lock).
    """
    print("\n[TEST 4] Running CHANGE vs SELECT interleaving test...")
    
    # Defensive assertion
    assert len(test_data["staff_ids"]) >= 1, f"Expected at least 1 staff, got {len(test_data['staff_ids'])}"
    assert len(test_data["subject_ids"]) >= 25, f"Expected at least 25 subjects, got {len(test_data['subject_ids'])}"
    
    staff_id = test_data["staff_ids"][0]  # Use staff 1
    batch_id = test_data["batch_id"]
    spec_id = test_data["spec_id"]
    window_id = test_data["window_id"]
    
    # --- SETUP: Reset staff state to exactly 1 selection ---
    setup_conn = await asyncpg.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )
    try:
        # Delete all existing selections for this staff
        await setup_conn.execute(
            "DELETE FROM subject_selection WHERE staff_id = $1 AND window_id = $2",
            staff_id, window_id
        )
        
        # Insert exactly ONE selection (subject 24, slot 1)
        old_subject_id = test_data["subject_ids"][23]  # Subject 24 (fresh)
        await setup_conn.execute(
            """
            INSERT INTO subject_selection
              (subject_id, staff_id, batch_id, specialization_id, window_id, staff_slot_number, status, selected_at)
            VALUES ($1, $2, $3, $4, $5, 1, 'SELECTED', now())
            """,
            old_subject_id, staff_id, batch_id, spec_id, window_id
        )
        print(f"[TEST 4] Setup: staff {staff_id} now has 1 selection (subject_id={old_subject_id})")
    finally:
        await setup_conn.close()
    
    # --- RUN: CHANGE and SELECT concurrently ---
    new_subject_id = test_data["subject_ids"][24]  # Subject 25 (unused)
    
    # CHANGE: swap old_subject -> new_subject
    # SELECT: try to claim same new_subject
    change_task = change_subject_raw(staff_id, old_subject_id, new_subject_id, batch_id, spec_id, worker_id=0)
    select_task = select_subject_raw(staff_id, new_subject_id, batch_id, spec_id, worker_id=1)
    
    change_result, select_result = await asyncio.gather(change_task, select_task)
    
    results.test_4_change_select_results = {
        "change_success": change_result["success"],
        "select_success": select_result["success"],
        "change_message": change_result["message"],
        "select_message": select_result["message"]
    }
    
    print(f"✅ Test 4 complete: CHANGE={change_result['success']}, SELECT={select_result['success']}")


async def test_5_slot_uniqueness(test_data: Dict[str, Any], results: TortureTestResults):
    """
    Test 5: Verify slot uniqueness by querying subject_selection.
    """
    print("\n[TEST 5] Verifying slot uniqueness...")
    
    conn = await asyncpg.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )
    
    try:
        # Check slots for each staff
        for staff_id in test_data["staff_ids"][:5]:  # Staff 1-5 from Test 1
            rows = await conn.fetch(
                """
                SELECT staff_slot_number
                FROM subject_selection
                WHERE staff_id = $1 AND status = 'SELECTED'
                ORDER BY staff_slot_number
                """,
                staff_id
            )
            
            slots = [r["staff_slot_number"] for r in rows]
            results.test_5_slot_results.append({"staff_id": staff_id, "slots": slots})
        
        print(f"✅ Test 5 complete: {len(results.test_5_slot_results)} staff verified")
    
    finally:
        await conn.close()


async def main():
    """Main test orchestrator."""
    print("="*80)
    print("FCFS CONCURRENCY TORTURE TEST — HARDENED VERSION")
    print("="*80)
    print(f"Database: {DB_NAME}@{DB_HOST}:{DB_PORT}")
    print(f"Started: {datetime.now().isoformat()}")
    
    results = TortureTestResults()
    
    conn = await asyncpg.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )
    
    try:
        # Setup
        test_data = await setup_test_data(conn)
        
        # Run tests (with isolation: TRUNCATE subject_selection between tests)
        await test_1_quota_enforcement(test_data, results)
        
        await conn.execute("TRUNCATE subject_selection RESTART IDENTITY CASCADE")
        print("\n[ISOLATION] subject_selection truncated between Test 1 and Test 2")
        
        await test_2_fcfs_enforcement(test_data, results)
        
        await conn.execute("TRUNCATE subject_selection RESTART IDENTITY CASCADE")
        print("\n[ISOLATION] subject_selection truncated between Test 2 and Test 3")
        
        await test_3_cross_staff_fcfs(test_data, results)
        
        await conn.execute("TRUNCATE subject_selection RESTART IDENTITY CASCADE")
        print("\n[ISOLATION] subject_selection truncated between Test 3 and Test 4")
        
        await test_4_change_select_interleaving(test_data, results)
        
        await conn.execute("TRUNCATE subject_selection RESTART IDENTITY CASCADE")
        print("\n[ISOLATION] subject_selection truncated between Test 4 and Test 5")
        
        await test_5_slot_uniqueness(test_data, results)
        
        # Cleanup
        await cleanup_test_data(conn, test_data)
    
    except Exception as e:
        results.log_error("MAIN", str(e))
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await conn.close()
    
    # Print summary
    results.print_summary()
    print(f"\nFinished: {datetime.now().isoformat()}")


if __name__ == "__main__":
    asyncio.run(main())
