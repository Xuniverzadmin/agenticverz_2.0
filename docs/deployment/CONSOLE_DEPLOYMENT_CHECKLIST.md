# Console Deployment Checklist

**Target:** console.agenticverz.com
**Status:** DRAFT
**Date:** 2026-01-07

---

## Pre-Deployment

### 1. Database Setup

- [ ] Verify DATABASE_URL is set and accessible
- [ ] Run migrations: `alembic upgrade head`
- [ ] Verify tables exist: `tenants`, `users`, `tenant_memberships`, `api_keys`, `audit_log`

### 2. Admin User Setup

```bash
# Dry run first
cd /root/agenticverz2.0
DATABASE_URL=$DATABASE_URL python3 backend/scripts/seed_admin.py --dry-run

# Create admin user
DATABASE_URL=$DATABASE_URL python3 backend/scripts/seed_admin.py

# If Clerk user ID is known
DATABASE_URL=$DATABASE_URL python3 backend/scripts/seed_admin.py --clerk-user-id user_xxx
```

- [ ] Tenant created: `agenticverz-internal`
- [ ] User created: `admin1@agenticverz.com`
- [ ] Membership created: `owner` role
- [ ] API key generated (saved securely)
- [ ] Audit log entry recorded

### 3. Clerk Setup (Optional for Initial Deploy)

- [ ] Create user in Clerk: `admin1@agenticverz.com`
- [ ] Add metadata: `is_operator: true`
- [ ] Update clerk_user_id in database (if seeded before Clerk setup)
- [ ] Set `CLERK_SECRET_KEY` in environment

### 4. Environment Variables

```bash
# Required
export DATABASE_URL=postgresql://...

# Safety switches (MANDATORY for initial deploy)
export CONSOLE_MODE=DRAFT
export DATA_MODE=REAL      # or SYNTHETIC for testing
export ACTION_MODE=NOOP    # CRITICAL: Prevents mutations

# Auth (optional if using DevIdentityAdapter)
export DEV_AUTH_ENABLED=true
export DEV_DEFAULT_ROLE=founder

# Or Clerk (production)
export CLERK_SECRET_KEY=sk_xxx
```

- [ ] `CONSOLE_MODE=DRAFT` set
- [ ] `DATA_MODE` set (REAL or SYNTHETIC)
- [ ] `ACTION_MODE=NOOP` set (CRITICAL)
- [ ] Auth configuration set (DEV or Clerk)

### 5. Frontend Build

```bash
cd website/app-shell
npm install
npm run build
```

- [ ] Build succeeds
- [ ] `ui_contract.v1.json` accessible at `/contracts/ui_contract.v1.json`

---

## Deployment

### 6. Backend Deployment

```bash
# Docker
docker compose up -d backend

# Or direct
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- [ ] Backend starts without errors
- [ ] Health check passes: `curl http://localhost:8000/health`
- [ ] Console status logged at startup

### 7. Frontend Deployment

- [ ] Static files deployed to console.agenticverz.com
- [ ] HTTPS configured
- [ ] CORS configured for API calls

---

## Post-Deployment Verification

### 8. Login Verification (10 minutes)

Log in as `admin1@agenticverz.com` and verify:

| Check | Expected | Status |
|-------|----------|--------|
| Login page loads | No errors | [ ] |
| Authentication succeeds | Session created | [ ] |
| Overview domain loads | 3 panels visible | [ ] |
| Activity domain loads | 10 panels visible | [ ] |
| Incidents domain loads | 11 panels visible | [ ] |
| Policies domain loads | 15 panels visible | [ ] |
| Logs domain loads | 13 panels visible | [ ] |
| **Total panels** | **52 panels** | [ ] |

### 9. Control Verification

| Check | Expected | Status |
|-------|----------|--------|
| SAFE panels show enabled controls | Buttons clickable | [ ] |
| QUESTIONABLE panels show disabled controls | Buttons grayed + reason | [ ] |
| Clicking WRITE/ACTIVATE logs NOOP | Action logged, no mutation | [ ] |
| Navigation between panels works | URL updates | [ ] |
| Panel order follows O1-O5 | Summary → List → Detail → Context → Proof | [ ] |

### 10. Backend Logs Verification

```bash
docker compose logs backend --tail 100 | grep -E "(NOOP|Console Status|admin1)"
```

- [ ] No RBAC errors in logs
- [ ] NOOP actions logged for WRITE/ACTIVATE
- [ ] Console status shows `ACTION_MODE=NOOP`

### 11. Contract Sync Verification

```bash
python3 scripts/tools/l2_pipeline.py status
```

- [ ] UI contract shows `IN SYNC`
- [ ] Approved version matches deployed contract

---

## Safety Matrix

| Configuration | CONSOLE_MODE | DATA_MODE | ACTION_MODE | Risk Level |
|---------------|--------------|-----------|-------------|------------|
| **Initial Deploy** | DRAFT | REAL | **NOOP** | LOW |
| Staging | DRAFT | SYNTHETIC | NOOP | LOW |
| Pre-Prod | LIVE | REAL | NOOP | MEDIUM |
| Production | LIVE | REAL | LIVE | HIGH |

**CRITICAL:** Never deploy with `ACTION_MODE=LIVE` until:
1. All panels verified
2. All controls mapped correctly
3. Backend mutation handlers tested
4. Explicit approval obtained

---

## Rollback Procedure

If issues are found:

```bash
# 1. Set to maintenance mode
export CONSOLE_MODE=MAINTENANCE

# 2. Restart backend
docker compose restart backend

# 3. Investigate logs
docker compose logs backend --tail 500

# 4. If needed, demote contract version
python3 scripts/tools/l2_pipeline.py demote
```

---

## Contacts

| Role | Email |
|------|-------|
| Admin | admin1@agenticverz.com |
| Alerts | admin1@agenticverz.com |

---

## Attestation

```
Deploy Date: _______________
Deployed By: _______________

[ ] Pre-deployment checklist complete
[ ] Admin user verified
[ ] Safety switches confirmed (ACTION_MODE=NOOP)
[ ] Post-deployment verification complete
[ ] No blocking issues found
```
