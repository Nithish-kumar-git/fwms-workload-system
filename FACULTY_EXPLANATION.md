# Faculty Subject Selection System — Explained

> **For:** Faculty, Deans, Administrative Staff
> **Reading time:** 5 minutes

---

## What This System Does

This system lets faculty **choose which subjects they will teach** for the upcoming semester. It replaces the manual process of paper forms and email requests with a fair, transparent, and automated system.

### How It Works

1. **The Coordinator creates a "Selection Window"** — a specific time period (e.g., Monday 10 AM to Friday 5 PM) during which faculty can make their selections.

2. **Faculty log in with their university Google account** (`@hindustanuniv.ac.in`) and select the subjects they want to teach.

3. **Selections are first-come, first-served (FCFS)** — if two faculty want the same subject, the one who selects first gets it.

4. **The window closes** — after the deadline, no more changes are allowed.

5. **The results are final and auditable** — every action is permanently logged.

---

## What This System Does NOT Do

| ❌ Not Included | Why |
|-----------------|-----|
| Timetable generation | Timetable scheduling is a separate system. This system only decides *who teaches what*, not *when*. |
| Classroom allocation | Rooms are assigned separately by the timetable coordinator. |
| Student enrollment | Student registrations are handled by the academic registrar. |
| Workload calculation | Teaching hours/load balancing is not automated. |
| Preference ranking | Faculty either select a subject or they don't — there is no waiting list. |

---

## How Fairness Is Protected

### Problem: What if two faculty click "Select" at the same time?

**Answer:** The system uses **database-level locking** to guarantee that only one person can hold a subject at a time. Even if two people click simultaneously:

- One will succeed ✅
- The other will see "Subject already selected" ❌

This is not a software check that can fail — it is enforced by the database engine itself, the same technology used by banks and airlines.

### Problem: What if someone tries to bypass the system?

**Answer:** Every protection is enforced at the **database level**, not just in the application:

| Protection | How It's Enforced |
|-----------|-------------------|
| One faculty per subject | Database unique constraint |
| Maximum subjects per faculty | Quota check inside a transaction |
| Only eligible faculty | Database foreign key constraint |
| Window must be open | Checked inside a locked transaction |
| Audit log cannot be modified | Database triggers block UPDATE/DELETE |

Even if someone found a way to bypass the website, the database would reject the invalid operation.

---

## Who Can Do What

| Role | Can Do |
|------|--------|
| **Faculty** | Log in, view available subjects, select subjects (during open window) |
| **Coordinator** | Everything faculty can do + create/schedule/open/close windows, override selections |

---

## Important Guarantees

✅ **Fair:** First-come, first-served — no favoritism possible
✅ **Transparent:** Every action is logged permanently
✅ **Secure:** University Google accounts only
✅ **Tamper-proof:** Audit log cannot be edited or deleted
✅ **Time-bound:** Selections only allowed during the open window

---

## Frequently Asked Questions

**Q: Can the coordinator change my selection?**
A: Yes, a coordinator can override a selection if necessary (e.g., for workload balancing). This action is permanently logged in the audit trail.

**Q: What if I selected the wrong subject?**
A: Contact your coordinator to override the selection during the open window period.

**Q: What happens if the system goes down during the window?**
A: All selections already made are safe (stored in the database). The window can be extended by the coordinator if needed.

**Q: Who can see my selections?**
A: Coordinators can see all selections. Individual faculty can see their own selections.

**Q: Is my data safe?**
A: Yes. The system uses encrypted HTTPS connections, secure session management, and all data is stored in a PostgreSQL database with automated backups.
