# Agenticverz Testing Guide

**Status:** RATIFIED (Canonical Testing Contract)
**Version:** 1.0.0
**Created:** 2026-01-18
**Authority:** Engineering / QA / Security

---

## Purpose

This document is the **single source of truth** for how testing is performed across all Agenticverz environments. It defines:

- Which environment modes exist
- What each mode permits
- How to configure and use each mode
- What is explicitly forbidden

**This is an enforceable contract, not a guideline.**

---

## Environment Modes

### The Three Modes

| Mode | Purpose | Database | Sandbox Auth | Production Auth | Cost |
|------|---------|----------|--------------|-----------------|------|
| **LOCAL** | Isolated development | Local PostgreSQL | ✅ | ✅ | None |
| **TEST** | Integration testing | Neon (test data) | ✅ | ✅ | Neon costs |
| **PROD** | Production traffic | Neon (live data) | ❌ | ✅ | Full billing |

---

## LOCAL Mode

### Purpose
- Unit testing
- Feature development
- Isolated debugging
- SDK development

### Configuration
```env
AOS_MODE=local
DB_AUTHORITY=local
CUSTOMER_SANDBOX_ENABLED=true
DATABASE_URL=postgresql://nova:novapass@localhost:5433/nova_aos
```

### What You Can Do
- [x] Use sandbox credentials (`X-AOS-Customer-Key`)
- [x] Use production-style credentials (if available)
- [x] Seed arbitrary test data
- [x] Run destructive tests
- [x] Modify database schema (local only)
- [x] Test without Neon connection

### What You Cannot Do
- [ ] Access Neon data
- [ ] Validate against production schema
- [ ] Test real integrations
- [ ] Generate production-grade test reports

### Example Commands
```bash
# Start in LOCAL mode
AOS_MODE=local DB_AUTHORITY=local CUSTOMER_SANDBOX_ENABLED=true \
  docker compose up -d backend

# Run tests with sandbox auth
curl -H "X-AOS-Customer-Key: cus_sandbox_demo" \
  http://localhost:8000/api/v1/cus/integrations

# Seed test data
python backend/scripts/seed_sandbox_data.py
```

---

## TEST Mode

### Purpose
- Integration testing against real infrastructure
- End-to-end validation
- Performance testing
- Pre-production verification
- CI/CD pipelines

### Configuration
```env
AOS_MODE=test
DB_AUTHORITY=neon
CUSTOMER_SANDBOX_ENABLED=true
DATABASE_URL=postgresql://...@...neon.tech/nova_aos_test
```

### What You Can Do
- [x] Use sandbox credentials for controlled testing
- [x] Use production-style credentials
- [x] Query real Neon data (test database)
- [x] Validate schema compatibility
- [x] Test real LLM integrations (test keys)
- [x] Generate authoritative test reports

### What You Cannot Do
- [ ] Access production Neon database
- [ ] Use production customer credentials
- [ ] Generate production billing events
- [ ] Modify production data

### Example Commands
```bash
# Start in TEST mode
AOS_MODE=test DB_AUTHORITY=neon CUSTOMER_SANDBOX_ENABLED=true \
  docker compose up -d backend

# Run integration tests with sandbox auth
curl -H "X-AOS-Customer-Key: cus_ci_test" \
  http://localhost:8000/api/v1/cus/integrations

# Run full test suite
pytest backend/tests/ -v --tb=short
```

### CI/CD Usage
```yaml
# GitHub Actions example
env:
  AOS_MODE: test
  DB_AUTHORITY: neon
  CUSTOMER_SANDBOX_ENABLED: true
  DATABASE_URL: ${{ secrets.NEON_TEST_DATABASE_URL }}

steps:
  - name: Run integration tests
    run: |
      curl -H "X-AOS-Customer-Key: cus_ci_test" \
        http://localhost:8000/api/v1/cus/integrations
```

---

## PROD Mode

### Purpose
- Live production traffic
- Real customer interactions
- Billing-active operations

### Configuration
```env
AOS_MODE=prod
DB_AUTHORITY=neon
CUSTOMER_SANDBOX_ENABLED=false  # Ignored, PROD blocks sandbox regardless
DATABASE_URL=postgresql://...@...neon.tech/nova_aos
```

### What You Can Do
- [x] Serve real customer traffic
- [x] Process production credentials (Clerk JWT, API keys)
- [x] Bill for LLM usage
- [x] Store authoritative data

### What You Cannot Do
- [ ] Use sandbox credentials
- [ ] Bypass authentication
- [ ] Run destructive tests
- [ ] Use test data

### Security Properties
- Sandbox auth is **hard blocked** regardless of `CUSTOMER_SANDBOX_ENABLED`
- Only Clerk JWT or production API keys are accepted
- All requests are audited
- Tenant isolation is enforced

---

## Authentication Methods by Mode

| Auth Method | LOCAL | TEST | PROD |
|-------------|-------|------|------|
| `X-AOS-Customer-Key: cus_sandbox_*` | ✅ | ✅ | ❌ |
| `Authorization: Bearer <clerk_jwt>` | ✅ | ✅ | ✅ |
| `X-AOS-Key: <api_key>` | ✅ | ✅ | ✅ |
| No authentication | ❌ | ❌ | ❌ |

---

## Sandbox Credentials

### Available Sandbox Keys

| Key | Tenant | Role | Use Case |
|-----|--------|------|----------|
| `cus_sandbox_demo` | `demo-tenant` | `customer_admin` | General testing |
| `cus_sandbox_readonly` | `demo-tenant` | `customer_viewer` | Read-only testing |
| `cus_sandbox_tenant2` | `tenant-2` | `customer_admin` | Multi-tenant testing |
| `cus_ci_test` | `ci-tenant` | `customer_admin` | CI/CD pipelines |

### Usage
```bash
# Header format
X-AOS-Customer-Key: cus_sandbox_demo

# Full curl example
curl -H "X-AOS-Customer-Key: cus_sandbox_demo" \
  -H "Content-Type: application/json" \
  http://localhost:8000/api/v1/cus/integrations
```

---

## Testing Customer Integration APIs

### Endpoints Covered

| Endpoint | Methods | Required Permission |
|----------|---------|---------------------|
| `/api/v1/cus/integrations` | GET | `customer:integrations:read` |
| `/api/v1/cus/integrations` | POST, PUT, DELETE | `customer:integrations:write` |
| `/api/v1/cus/enforcement` | GET | `customer:enforcement:read` |
| `/api/v1/cus/enforcement` | POST, PUT, DELETE | `customer:enforcement:write` |
| `/api/v1/cus/telemetry` | GET | `customer:telemetry:read` |
| `/api/v1/cus/visibility` | GET | `customer:visibility:read` |

### Test Matrix

| Test Type | Mode | Auth | Expected Result |
|-----------|------|------|-----------------|
| Unit tests | LOCAL | Sandbox | Isolated, fast |
| Integration tests | TEST | Sandbox | Real data, controlled |
| E2E tests | TEST | Sandbox or Prod | Full validation |
| Security tests | TEST | Both | Verify boundaries |
| Production smoke | PROD | Prod only | Health check |

---

## SDK Testing

### Python SDK
```python
from aos_sdk import AOSClient

# LOCAL/TEST mode - use sandbox credentials
client = AOSClient(
    base_url="http://localhost:8000",
    customer_key="cus_sandbox_demo"  # Only in LOCAL/TEST
)

# PROD mode - use production credentials
client = AOSClient(
    base_url="https://api.agenticverz.com",
    api_key=os.environ["AOS_API_KEY"]  # Production API key
)
```

### JavaScript SDK
```javascript
import { AOSClient } from '@agenticverz/aos-sdk';

// LOCAL/TEST mode
const client = new AOSClient({
  baseUrl: 'http://localhost:8000',
  customerKey: 'cus_sandbox_demo'  // Only in LOCAL/TEST
});

// PROD mode
const client = new AOSClient({
  baseUrl: 'https://api.agenticverz.com',
  apiKey: process.env.AOS_API_KEY  // Production API key
});
```

---

## Forbidden Actions

### NEVER Do These

| Action | Why | Risk Level |
|--------|-----|------------|
| Use sandbox credentials in PROD | Security bypass | **CRITICAL** |
| Disable auth middleware for testing | Creates untested code paths | **HIGH** |
| Skip RBAC in "test mode" | Production will behave differently | **HIGH** |
| Hardcode tenant IDs in routes | Breaks multi-tenancy | **MEDIUM** |
| Use production Neon in LOCAL | Data corruption risk | **HIGH** |
| Share sandbox keys externally | Credential leak | **MEDIUM** |

### Always Do These

| Action | Why |
|--------|-----|
| Set `AOS_MODE` explicitly | Prevents accidental production exposure |
| Use sandbox for development | Isolates test activity |
| Test both auth paths | Ensures production readiness |
| Verify mode before deploying | Catches misconfiguration |
| Log sandbox usage | Audit trail |

---

## Troubleshooting

### "Sandbox auth not working"

1. Check `AOS_MODE` is `local` or `test`
2. Check `CUSTOMER_SANDBOX_ENABLED=true`
3. Verify using `X-AOS-Customer-Key` header (not `X-AOS-Key`)
4. Check backend logs: `docker logs nova_agent_manager | grep sandbox`

### "401 in TEST mode with sandbox key"

1. Verify environment variables are passed to container
2. Check: `docker exec nova_agent_manager env | grep AOS_MODE`
3. Restart container after env changes

### "403 from RBAC"

1. Verify RBAC rules exist for path in `RBAC_RULES.yaml`
2. Check role has required permission
3. Verify RBAC middleware recognizes principal type

### "Production accepting sandbox auth" (SECURITY INCIDENT)

1. **Stop immediately**
2. Verify `AOS_MODE=prod`
3. Check deployment configuration
4. Escalate to security team
5. Audit logs for unauthorized access

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                 TESTING MODE QUICK REFERENCE                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  LOCAL MODE                                                  │
│  ─────────                                                  │
│  AOS_MODE=local DB_AUTHORITY=local CUSTOMER_SANDBOX_ENABLED=true
│  → Sandbox: ✅  |  Database: local  |  Cost: none           │
│                                                              │
│  TEST MODE                                                   │
│  ─────────                                                  │
│  AOS_MODE=test DB_AUTHORITY=neon CUSTOMER_SANDBOX_ENABLED=true
│  → Sandbox: ✅  |  Database: Neon  |  Cost: Neon only        │
│                                                              │
│  PROD MODE                                                   │
│  ─────────                                                  │
│  AOS_MODE=prod DB_AUTHORITY=neon                            │
│  → Sandbox: ❌  |  Database: Neon  |  Cost: full            │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  SANDBOX KEYS (LOCAL/TEST only)                             │
│  ─────────────────────────────────                          │
│  cus_sandbox_demo     → demo-tenant, admin                  │
│  cus_sandbox_readonly → demo-tenant, viewer                 │
│  cus_sandbox_tenant2  → tenant-2, admin                     │
│  cus_ci_test          → ci-tenant, admin (CI/CD)            │
└─────────────────────────────────────────────────────────────┘
```

---

## Related Documents

- `docs/architecture/auth/THREE_MODE_AUTHORITY_SYSTEM.md` - Full architecture
- `docs/memory-pins/PIN-440-customer-sandbox-auth-mode.md` - Implementation PIN
- `design/auth/RBAC_RULES.yaml` - RBAC rule definitions
- `docs/governance/AUTHORIZATION_CONSTITUTION.md` - Auth governance

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-01-18 | 1.0.0 | Initial release |
