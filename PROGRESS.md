## Latest Update - March 28, 2026

### Migration 026: Odd Semester Subjects Created

#### What Was Done
Created `migrations/026_odd_semester_subjects.sql` to populate odd semester subject offerings:

**MCA Odd Semesters**:
- Semester I: 7 core subjects (Statistics, Accounting, OOP, Networking, Software Engineering, Data Structures, Python)
- Semester III: 5 subjects (Testing, Cryptography, Communication Skills, Research Paper, Internship)
- 3 sections each (A, B, C)

**BCA Odd Semesters**:
- Semester I: 7 core subjects (Computer Fundamentals, Problem Solving, Data Structures, Math, Communication, Tamil, Environment)
- Semester III: 6 subjects (Computer Networks, Full Stack Web, Public Speaking, Indian Knowledge, CSR, Internship)
- Semester V: 6 Cyber Security subjects (Python for Cyber, Ethical Hacking, SIEM, Security Ethics, Lab, Threat Management)
- 6 sections each (A, B, C, D, E, F)

**Expected Totals**:
- Semester I: ~63 offerings (21 MCA + 42 BCA)
- Semester III: ~45 offerings (15 MCA + 30 BCA)
- Semester V: ~36 offerings (BCA Cyber only)
- Total odd semester offerings: ~144

#### Changes Made
- Created `migrations/026_odd_semester_subjects.sql`
- Added to `startup.sh` after migration 025
- Committed: d5aae8a "Add migration 026: odd semester subjects scaffold"
- Pushed to Railway

#### Next Step
Wait 3 minutes for Railway deployment, then run:
```
railway logs --tail 30
```
Look for NOTICE lines showing:
- "026: Semester I offerings=X"
- "026: Semester III offerings=X"
- "026: Semester V offerings=X"
- "026: Total odd semester offerings=X"

Paste the verification output to confirm data loaded correctly.
