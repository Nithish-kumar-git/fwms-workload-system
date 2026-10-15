"""Server-selected synthetic identities; never accept a client staff ID."""

ACCOUNTS = {
    "hod": ("demo@fwms-demo.com", "Demo HOD", "DEMO001"),
    "tt_coordinator": ("coordinator@demo.example.com", "Demo Coordinator", "DEMO002"),
    "faculty": ("teacher@demo.example.com", "Demo Teacher", "DEMO003"),
}


def ensure_demo_account(execute, role):
    if role not in ACCOUNTS:
        raise ValueError("Unsupported demo role")
    email, name, code = ACCOUNTS[role]
    params = {"email": email, "name": name, "role": role, "code": code,
              "coordinator": role in ("hod", "tt_coordinator")}
    select = "SELECT id, email, name, role, emp_code, is_active FROM staff WHERE email = :email"
    row = execute(select, {"email": email}).fetchone()
    if row is None:
        # No explicit IDs, deletion, sequence repair or privilege-changing upsert.
        # Concurrent logins resolve through PostgreSQL's email unique constraint.
        execute("""
            INSERT INTO staff (email, name, role, emp_code, is_active, is_coordinator,
                               designation, shift, tch_norm, total_workload_norm, is_class_teacher)
            VALUES (:email, :name, :role, :code, true, :coordinator,
                    'Assistant Professor', 'SHIFT1', 16, 16, false)
            ON CONFLICT (email) DO NOTHING
        """, params)
        row = execute(select, {"email": email}).fetchone()
    if not row or row[3] != role or row[4] != code or not row[5]:
        raise RuntimeError("Synthetic demo account configuration mismatch")
    return row[:4]
