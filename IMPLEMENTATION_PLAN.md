# IMPLEMENTATION_PLAN.md
## Faculty Subject Selection System — 4-Week Execution Plan

**Version:** 1.0  
**Status:** Execution Roadmap (Architecture Locked)  
**Target:** Solo developer with AI assistance  
**Timeline:** 4 weeks (160 hours total)  
**Deployment:** University on-premises (primary)  
**Date:** 2026-02-07

---

## 0. PREREQUISITES & SETUP

### 0.1 Required Before Starting

**Infrastructure:**
- [ ] PostgreSQL 14+ accessible (on-prem or test instance)
- [ ] Python 3.12+ installed
- [ ] Git repository created
- [ ] Development machine meets requirements

**Credentials:**
- [ ] Google Cloud Console project created
- [ ] OAuth 2.0 credentials obtained (Client ID + Secret)
- [ ] University SMTP server access (hostname, port, credentials if needed)
- [ ] Database credentials (username, password, database name)

**Optional (but recommended):**
- [ ] Redis installed (or plan to use in-memory fallback)
- [ ] Staging/test server access
- [ ] SSL certificate for production domain

### 0.2 Development Environment Setup (Day 0 — 2 hours)
```bash
# 1. Clone repository
git clone <repository-url>
cd faculty-subject-selection

# 2. Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install minimal dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic pydantic-settings python-dotenv

# 4. Create .env from template
cp .env.example .env

# 5. Verify Python version
python --version  # Should be 3.12+
```

### 0.3 Database Initialization (Day 0 — 1 hour)
```bash
# 1. Create database
psql -U postgres -c "CREATE DATABASE faculty_selection;"
psql -U postgres -c "CREATE USER faculty_user WITH PASSWORD 'your-password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE faculty_selection TO faculty_user;"

# 2. Load schema (from Phase 1)
psql -U faculty_user -d faculty_selection -f migrations/schema.sql

# 3. Verify tables created
psql -U faculty_user -d faculty_selection -c "\dt"
```

---

## 1. WEEK 1 — FOUNDATION & AUTHENTICATION

**Goals:**
- ✅ Project structure finalized
- ✅ Database connection working
- ✅ Google OAuth login functional
- ✅ Session management implemented
- ✅ Health checks operational

**Estimated Hours:** 40 hours (5 days × 8 hours)

---

### DAY 1 — Project Structure & Database Layer (8 hours)

**Tasks:**

1. **Create Project Structure** (2 hours)
   - Create all directories per BACKEND_STRUCTURE.md
   - Create `__init__.py` files
   - Create placeholder files for all modules
   - Configure `.gitignore`

2. **Database Connection Pool** (3 hours) ⚠️ **HAND-WRITTEN**
   - Implement `app/db/pool.py`
   - Implement `app/db/session.py`
   - Configure conservative pool settings (10/20)
   - Test connection

3. **Configuration Management** (2 hours)
   - Implement `app/core/config.py`
   - Create `.env.example`
   - Configure `.env` with dev settings
   - Test settings loading

4. **Logging Setup** (1 hour)
   - Implement `app/core/logging_config.py`
   - Test logging to console and file

**Deliverables:**
- [ ] All directories created
- [ ] Database connection pool working
- [ ] Transaction context manager tested
- [ ] Configuration loading from `.env`
- [ ] Logging operational

---

### DAY 2 — Session Management & Health Checks (8 hours)

**Tasks:**

1. **Session Management** (3 hours) — AI-assisted
   - Implement `app/auth/session_manager.py`
   - MemorySessionBackend (default)
   - RedisSessionBackend (optional)
   - Session CRUD operations

2. **Health Check Endpoints** (2 hours) — AI-assisted
   - Implement `app/health/router.py`
   - Basic health check (`/health`)
   - Deep health check (`/health/deep`)

3. **FastAPI Bootstrap** (2 hours) — AI-assisted
   - Implement `app/main.py`
   - Include health router
   - Configure CORS
   - Add startup/shutdown events

4. **Testing & Validation** (1 hour)
   - Start application: `uvicorn app.main:app --reload`
   - Test `/health` endpoint
   - Test `/health/deep` endpoint

**Deliverables:**
- [ ] Session management working (memory backend)
- [ ] Health checks operational
- [ ] FastAPI app running

---

### DAY 3 — Google OAuth Integration (8 hours)

**Tasks:**

1. **Google OAuth Client** (3 hours) — AI-assisted, MANUAL REVIEW
   - Implement `app/auth/google_oauth.py`
   - OAuth flow: redirect → callback → token verification
   - Email domain validation (`endswith` check)

2. **Auth Router** (3 hours) — AI-assisted, MANUAL REVIEW
   - Implement `app/auth/router.py`
   - `/api/auth/login` — redirect to Google
   - `/api/auth/callback` — handle OAuth callback
   - `/api/auth/logout` — destroy session

3. **Auth Dependencies** (1 hour) — AI-assisted, MANUAL REVIEW
   - Implement `app/auth/dependencies.py`
   - `get_current_user()` dependency
   - `require_coordinator()` dependency

4. **Testing** (1 hour)
   - Configure OAuth credentials in `.env`
   - Test login flow (manual browser test)
   - Test session persistence
   - Test logout

**Deliverables:**
- [ ] Google OAuth login working
- [ ] Email domain validation enforced
- [ ] Session creation on successful login
- [ ] Role-based access control working

---

### DAY 4 — Read APIs (Subject Listing) (8 hours)

**Tasks:**

1. **Staff Schemas** (1 hour) — AI-assisted
   - Implement `app/staff/schemas.py`
   - Subject response models
   - Pydantic validation

2. **Staff Service Layer** (2 hours) — AI-assisted
   - Implement `app/staff/service.py`
   - Eligibility query logic (exact SQL from FSB)
   - Window status checks

3. **Staff Router** (2 hours) — AI-assisted
   - Implement `app/staff/router.py`
   - `GET /api/staff/subjects` endpoint
   - Authorization via `get_current_user`

4. **Integration & Testing** (3 hours)
   - Add staff router to `main.py`
   - Seed test data (staff, batches, subjects)
   - Test subject listing with authenticated user
   - Verify eligibility filtering

**Deliverables:**
- [ ] Subject listing endpoint working
- [ ] Eligibility filtering correct
- [ ] Availability hints shown
- [ ] Window status displayed

---

### DAY 5 — Week 1 Integration & Testing (8 hours)

**Tasks:**

1. **Code Review & Cleanup** (2 hours)
   - Review all code written this week
   - Check for security issues
   - Verify error handling
   - Add docstrings

2. **Integration Testing** (3 hours)
   - Test full authentication flow
   - Test subject listing with multiple users
   - Test session expiration
   - Test unauthorized access (401, 403)

3. **Documentation** (2 hours)
   - Update README.md with setup instructions
   - Document API endpoints
   - Document environment variables

4. **Week 1 Demo** (1 hour)
   - Prepare demo script
   - Test on clean database
   - Verify all endpoints working

**Deliverables:**
- [ ] Week 1 functionality complete
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Ready for Week 2 (FCFS implementation)

---

## 2. WEEK 2 — FCFS CORE TRANSACTIONS (CRITICAL)

**Goals:**
- ✅ SELECT subject transaction (HAND-WRITTEN, NO AI)
- ✅ CHANGE subject transaction (HAND-WRITTEN, NO AI)
- ✅ Quota enforcement (race-safe)
- ✅ Concurrency testing (50+ concurrent requests)

**Estimated Hours:** 40 hours (critical, detailed work)

---

### DAY 6 — SELECT Subject Transaction (10 hours)

**⚠️ CRITICAL: This code MUST be hand-written. NO AI generation.**

**Tasks:**

1. **Transaction Design Review** (2 hours)
   - Review FSB v1.1 Section 3.4 (SELECT SUBJECT flow)
   - Draw transaction flow diagram
   - Identify all lock points
   - Plan error handling

2. **Implement SELECT Transaction** (5 hours) ⚠️ **HAND-WRITTEN ONLY**
   - File: `app/selection/transactions.py`
   - Implement exact SQL from FSB
   - Use `READ COMMITTED` + explicit `FOR UPDATE`
   - Add comprehensive error handling
   - Follow FSB Section 3.4 exactly

3. **Error Handling Verification** (1 hour)
   - Test all error paths (403, 409)
   - Verify rollback on exception
   - Test lock timeout (55P03)

4. **Selection Router** (1 hour) — AI-assisted
   - Implement `app/selection/router.py`
   - POST `/api/selection/select` endpoint

5. **Unit Testing** (1 hour)
   - Test successful selection
   - Test quota enforcement
   - Test eligibility check
   - Test window closed scenario

**Deliverables:**
- [ ] SELECT transaction hand-written and tested
- [ ] Quota enforcement verified (race-safe)
- [ ] Error handling complete
- [ ] All tests passing

---

### DAY 7 — CHANGE Subject Transaction (8 hours)

**⚠️ CRITICAL: This code MUST be hand-written. NO AI generation.**

**Tasks:**

1. **Transaction Design** (2 hours)
   - Review atomic swap requirements
   - Design lock ordering (prevent deadlock)
   - Plan rollback scenarios

2. **Implement CHANGE Transaction** (4 hours) ⚠️ **HAND-WRITTEN ONLY**
   - Add to `app/selection/transactions.py`
   - Acquire NEW before releasing OLD
   - Deadlock handling (SQLSTATE 40P01)
   - Follow FSB Section 3.5 exactly

3. **Testing** (2 hours)
   - Test successful change
   - Test deadlock scenario
   - Test new subject taken
   - Verify atomic swap

**Deliverables:**
- [ ] CHANGE transaction implemented
- [ ] Atomic swap verified
- [ ] Deadlock handling tested
- [ ] All tests passing

---

### DAY 8 — Concurrency Testing (8 hours)

**Tasks:**

1. **Setup Test Infrastructure** (2 hours)
   - Install pytest, httpx
   - Create test fixtures
   - Setup test database

2. **Write Concurrency Tests** (4 hours)
   - File: `tests/test_selection_concurrency.py`
   - Test: Concurrent selection (same subject, 2 staff)
   - Test: Quota enforcement (concurrent, same staff)
   - Test: Circular swap deadlock (A→B, B→A)

3. **Load Testing** (2 hours)
   - Setup Locust or JMeter
   - Simulate 50 concurrent selections
   - Verify pool doesn't exhaust
   - Monitor database connections

**Deliverables:**
- [ ] Concurrency tests passing
- [ ] Load test completed (50 users)
- [ ] No double bookings detected
- [ ] Pool handling verified

---

### DAY 9 — Bug Fixes & Security Review (8 hours)

**Tasks:**

1. **Bug Fixes** (4 hours)
   - Fix any issues found during testing
   - Refine error messages
   - Optimize query performance

2. **Security Audit** (4 hours)
   - SQL injection review (all queries parameterized?)
   - Session security review
   - Rate limiting implementation (optional)

**Deliverables:**
- [ ] All bugs fixed
- [ ] Security audit complete
- [ ] Performance acceptable

---

### DAY 10 — Week 2 Documentation (8 hours)

**Tasks:**

1. **Documentation** (4 hours)
   - API documentation updated (OpenAPI/Swagger)
   - Transaction flow diagrams created
   - Concurrency test report written

2. **Week 2 Review** (4 hours)
   - Code review
   - Load test results documented
   - FCFS correctness proof documented

**Deliverables:**
- [ ] Week 2 complete
- [ ] FCFS transactions battle-tested
- [ ] Ready for Week 3

---

## 3. WEEK 3 — COORDINATOR & EMAIL

**Goals:**
- ✅ Coordinator override transaction
- ✅ Selection window management
- ✅ Email notification system (abstracted)
- ✅ Audit log endpoints

**Estimated Hours:** 40 hours

---

### DAY 11 — Coordinator Override (8 hours)

**Tasks:**

1. **Override Transaction** (4 hours) ⚠️ **HAND-WRITTEN**
   - File: `app/coordinator/transactions.py`
   - Implement override logic (FSB Section 4.2)
   - Row-level locking
   - Audit logging

2. **Coordinator Router** (2 hours) — AI-assisted
   - Implement `app/coordinator/router.py`
   - POST `/api/coordinator/override` endpoint
   - Background email notification

3. **Testing** (2 hours)
   - Test override success
   - Test override-during-change scenario
   - Verify audit logging

**Deliverables:**
- [ ] Override transaction implemented
- [ ] Coordinator-only access enforced
- [ ] Audit logging complete

---

### DAY 12 — Email Abstraction Layer (8 hours)

**Tasks:**

1. **Email Adapter Implementation** (4 hours) — AI-assisted
   - File: `app/notifications/email_adapter.py`
   - File: `app/notifications/smtp_backend.py`
   - File: `app/notifications/log_backend.py` (dev/testing)

2. **Email Queue Integration** (2 hours) — AI-assisted
   - File: `app/notifications/queue.py`
   - FastAPI BackgroundTasks integration

3. **Configuration & Testing** (2 hours)
   - Configure SMTP settings in `.env`
   - Test with LogEmailBackend (dev)
   - Test with SMTPBackend (if SMTP available)
   - Verify async execution

**Deliverables:**
- [ ] Email adapter pattern implemented
- [ ] SMTP backend working
- [ ] Log backend for development
- [ ] Email failures don't affect transactions

---

### DAY 13 — Selection Window Management (8 hours)

**Tasks:**

1. **Window Schemas** (1 hour) — AI-assisted
   - File: `app/coordinator/schemas.py`
   - CreateWindowRequest, WindowResponse

2. **Window Service** (3 hours) — AI-assisted
   - File: `app/coordinator/service.py`
   - create_window, activate_window, close_window

3. **Window Router** (2 hours) — AI-assisted
   - Add to `app/coordinator/router.py`
   - POST `/window`, POST `/activate`, POST `/close`

4. **Testing** (2 hours)
   - Test window creation
   - Test window activation
   - Test window closure
   - Verify only one active window

**Deliverables:**
- [ ] Window management endpoints working
- [ ] Window activation enforced
- [ ] Window closure prevents selections

---

### DAY 14 — Audit Log Endpoints (8 hours)

**Tasks:**

1. **Audit Service** (3 hours) — AI-assisted
   - File: `app/audit/service.py`
   - get_selection_audit with pagination

2. **Audit Router** (2 hours) — AI-assisted
   - File: `app/audit/router.py`
   - GET `/api/audit/selections`

3. **Testing** (3 hours)
   - Test audit log retrieval
   - Verify coordinator-only access
   - Test pagination
   - Verify audit completeness

**Deliverables:**
- [ ] Audit log endpoints working
- [ ] Coordinator-only access enforced
- [ ] Pagination working

---

### DAY 15 — Week 3 Integration (8 hours)

**Tasks:**

1. **Integration Testing** (4 hours)
   - Test full coordinator workflow
   - Test override + email notification
   - Test window management

2. **Documentation** (2 hours)
   - Coordinator user guide
   - API documentation updates

3. **Week 3 Review** (2 hours)
   - Code review
   - Security review

**Deliverables:**
- [ ] Week 3 complete
- [ ] All coordinator features working
- [ ] Email system operational
- [ ] Ready for Week 4

---

## 4. WEEK 4 — DEPLOYMENT & PRODUCTION READINESS

**Goals:**
- ✅ Production deployment configuration
- ✅ Security hardening
- ✅ Backup & recovery procedures
- ✅ Monitoring & alerts
- ✅ User acceptance testing

**Estimated Hours:** 40 hours

---

### DAY 16 — Production Configuration (8 hours)

**Tasks:**

1. **Environment Configuration** (3 hours)
   - Production `.env` template
   - Secret management guide
   - Database connection tuning
   - Pool size optimization (based on load tests)

2. **Security Hardening** (3 hours)
   - HTTPS enforcement
   - CORS configuration (production domains)
   - Rate limiting implementation
   - SQL injection audit (final pass)

3. **Nginx Configuration** (2 hours)
   - Create `nginx.conf`
   - Configure reverse proxy
   - SSL certificate setup

**Deliverables:**
- [ ] Production configuration complete
- [ ] Security hardened
- [ ] Nginx configured

---

### DAY 17 — Backup & Monitoring (8 hours)

**Tasks:**

1. **Database Backup** (3 hours)
   - Automated backup script (`backup.sh`)
   - Backup retention policy (30 days)
   - Restore procedure testing

2. **Monitoring Setup** (3 hours)
   - Application logging (production level)
   - Database query logging (slow queries)
   - Health check monitoring

3. **Alert Configuration** (2 hours)
   - Pool exhaustion alerts
   - Error rate alerts
   - Database connection failures

**Deliverables:**
- [ ] Backup automation working
- [ ] Monitoring configured
- [ ] Alerts tested

---

### DAY 18 — User Acceptance Testing (8 hours)

**Tasks:**

1. **Test User Setup** (2 hours)
   - Create test staff accounts
   - Assign to test batches
   - Configure test window

2. **UAT Scenarios** (4 hours)
   - Staff login and subject selection
   - Concurrent selection (5-10 test users)
   - Subject change workflow
   - Coordinator override
   - Email notification verification

3. **Bug Fixes** (2 hours)
   - Fix any issues found during UAT
   - Re-test critical paths

**Deliverables:**
- [ ] UAT completed
- [ ] All critical scenarios pass
- [ ] Bugs fixed

---

### DAY 19 — Documentation & Training (8 hours)

**Tasks:**

1. **User Documentation** (4 hours)
   - Staff user guide
   - Coordinator manual
   - FAQ document
   - Troubleshooting guide

2. **Deployment Guide** (2 hours)
   - Installation instructions
   - Configuration checklist
   - Rollback procedures

3. **Training Materials** (2 hours)
   - Screenshots for user guide
   - Training session preparation

**Deliverables:**
- [ ] All documentation complete
- [ ] Deployment guide finalized
- [ ] Training materials ready

---

### DAY 20 — Production Deployment & Go-Live (8 hours)

**Pre-Deployment Checklist:**
- [ ] Database schema created (production)
- [ ] OAuth credentials configured
- [ ] SMTP tested
- [ ] SSL certificate installed
- [ ] Nginx configured
- [ ] Backup script configured
- [ ] Monitoring active
- [ ] Test data cleared

**Deployment:**
- [ ] Deploy application
- [ ] Run health checks
- [ ] Test authentication
- [ ] Test one selection (dry run)
- [ ] Verify audit logging

**Post-Deployment:**
- [ ] Load test (10 concurrent users)
- [ ] Monitor logs
- [ ] Verify email delivery
- [ ] Verify backup creation

**Go-Live:**
- [ ] Announce to staff
- [ ] Monitor first selections
- [ ] Be available for support

**Deliverables:**
- [ ] Application deployed
- [ ] All checks passed
- [ ] System live in production

---

## 5. TIMELINE SUMMARY

| Week | Focus | Critical Deliverables | Risk Level |
|------|-------|----------------------|------------|
| Week 1 | Foundation & Auth | OAuth, Sessions, Health Checks | Low |
| Week 2 | FCFS Core | SELECT/CHANGE Transactions, Concurrency Tests | **High** |
| Week 3 | Coordinator & Email | Override, Window Management, Notifications | Medium |
| Week 4 | Production Ready | Deployment, UAT, Go-Live | Medium |

**Total:** 160 hours (4 weeks × 40 hours)

---

**END OF IMPLEMENTATION_PLAN.md**
