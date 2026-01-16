# Auth Integration Checklist (M8)

**Goal:** RBAC uses REAL auth provider (no stub)
**Status:** ✅ **COMPLETE (2025-12-05)**
**Source:** PIN-009

---

## Summary

Auth integration is complete. Keycloak is deployed and working.

| Component | Status | Details |
|-----------|--------|---------|
| Auth Provider | ✅ Keycloak | auth-dev.xuniverz.com |
| OIDC Integration | ✅ Complete | JWKS-based JWT validation |
| RBAC Wiring | ✅ Complete | Keycloak roles → AOS RBAC |
| Test User | ✅ Created | devuser with admin role |
| API Verified | ✅ Working | Memory pins API tested |

---

## What Was Deployed

### Keycloak

- **URL:** https://auth-dev.xuniverz.com
- **Realm:** agentiverz-dev
- **Client:** aos-backend (confidential, OIDC)
- **Client Secret:** Stored in `/root/agenticverz2.0/secrets/keycloak_oidc.env`

### Backend Integration

- **OIDC Provider:** `backend/app/auth/oidc_provider.py`
  - JWKS-based JWT signature verification (RS256)
  - Role extraction from `realm_access.roles`
  - Keycloak role → AOS role mapping

- **RBAC Middleware:** `backend/app/auth/rbac_middleware.py`
  - Updated to use OIDC provider when `OIDC_ENABLED=true`
  - Falls back to machine token or API key auth

### Environment Variables

```bash
# In /root/agenticverz2.0/.env
OIDC_ISSUER_URL=https://auth-dev.xuniverz.com/realms/agentiverz-dev
OIDC_CLIENT_ID=aos-backend
OIDC_CLIENT_SECRET=<redacted - see secrets/keycloak_oidc.env>
OIDC_VERIFY_SSL=true
```

### Apache Reverse Proxy

- **Config:** `/etc/apache2/sites-available/auth-dev.conf`
- **TLS:** Cloudflare Origin certificates (Full Strict mode)
- **Proxy:** Apache → localhost:8080 (Keycloak)

---

## Test User

| Field | Value |
|-------|-------|
| Username | devuser |
| Password | devuser123 |
| Realm | agentiverz-dev |
| Roles | admin |

---

## How to Get a Token

```bash
KC_URL="https://auth-dev.xuniverz.com"
REALM="agentiverz-dev"
CLIENT_ID="aos-backend"
CLIENT_SECRET="<from secrets/keycloak_oidc.env>"

# Get token
TOKEN=$(curl -sk -X POST "$KC_URL/realms/$REALM/protocol/openid-connect/token" \
  -d "username=devuser" \
  -d "password=devuser123" \
  -d "grant_type=password" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET" | jq -r '.access_token')

# Use with API
curl -s http://localhost:8000/api/v1/memory/pins \
  -H "Authorization: Bearer $TOKEN"
```

---

## Verification Done

| Test | Result |
|------|--------|
| Keycloak health | ✅ 200 OK |
| Token acquisition | ✅ Working |
| API with token | ✅ 200, returns data |
| Cloudflare proxy | ✅ cf-ray header present |
| OIDC JWKS fetch | ✅ Working |
| Role extraction | ✅ admin role extracted |

---

## Files Created/Modified

| File | Change |
|------|--------|
| `/opt/keycloak/docker-compose.yml` | Created - Keycloak container |
| `/etc/apache2/sites-available/auth-dev.conf` | Created - Apache vhost |
| `backend/app/auth/oidc_provider.py` | **NEW** - OIDC JWT validation |
| `backend/app/auth/rbac_middleware.py` | Modified - Use OIDC provider |
| `backend/app/auth/__init__.py` | Modified - Export OIDC symbols |
| `backend/requirements.txt` | Added cryptography>=41.0.0 |
| `.env` | Added OIDC_* variables |
| `docker-compose.yml` | Added OIDC env vars, auth volume mount |
| `secrets/keycloak_oidc.env` | Created - Credentials (600 perms) |

---

## Next Steps (Remaining M8 Tasks)

1. **SDK Packaging** - `sdk_packaging_checklist.md`
2. **Demo Productionization** - `demo_checklist.md`
3. Create additional Keycloak users/roles as needed
4. Write AUTH_SETUP.md documentation

---

## Rollback (If Needed)

```bash
# Disable OIDC (revert to machine token only)
# In .env, comment out:
# OIDC_ISSUER_URL=...

# Restart backend
docker compose restart backend
```

The system will fall back to machine token (`X-Machine-Token`) authentication.
