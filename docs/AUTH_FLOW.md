# AOS Authentication Flow Documentation

## Overview

AOS uses JWT/OIDC authentication with Keycloak as the identity provider. This document covers the complete auth flow from token acquisition to API access.

---

## Authentication Methods

### 1. JWT Bearer Token (Recommended)

```bash
curl -H "Authorization: Bearer $JWT_TOKEN" \
  https://api.agenticverz.com/api/v1/traces
```

### 2. X-API-Key Header (Legacy/Development)

```bash
curl -H "X-API-Key: $AOS_API_KEY" \
  https://api.agenticverz.com/api/v1/traces
```

### 3. Development Token (Testing Only)

```bash
curl -H "Authorization: Bearer dev:$DEV_TOKEN" \
  https://api.agenticverz.com/api/v1/traces
```

---

## Token Acquisition

### Keycloak Password Grant

```bash
export AUTH_URL="https://auth-dev.xuniverz.com"
export REALM="agentiverz-dev"
export CLIENT_ID="aos-backend"

TOKEN=$(curl -s -X POST \
  "$AUTH_URL/realms/$REALM/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=$CLIENT_ID" \
  -d "grant_type=password" \
  -d "username=$USERNAME" \
  -d "password=$PASSWORD" \
  | jq -r '.access_token')
```

### Keycloak Client Credentials (Service Accounts)

```bash
TOKEN=$(curl -s -X POST \
  "$AUTH_URL/realms/$REALM/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET" \
  -d "grant_type=client_credentials" \
  | jq -r '.access_token')
```

---

## JWT Token Structure

### Required Claims

| Claim | Description | Example |
|-------|-------------|---------|
| `sub` | User ID | `user-123` |
| `tenant_id` | Tenant identifier | `acme-corp` |
| `roles` | User roles array | `["developer", "traces:read"]` |
| `exp` | Expiration timestamp | `1735000000` |
| `iat` | Issued at timestamp | `1734900000` |
| `iss` | Token issuer | `https://auth.xuniverz.com/realms/aos` |
| `aud` | Audience | `aos-api` |

### Optional Claims

| Claim | Description | Default |
|-------|-------------|---------|
| `rate_limit_tier` | Rate limit tier | `standard` |

### Example Decoded Token

```json
{
  "sub": "user-123",
  "tenant_id": "acme-corp",
  "roles": ["developer", "traces:read", "traces:write"],
  "rate_limit_tier": "premium",
  "exp": 1735000000,
  "iat": 1734900000,
  "iss": "https://auth-dev.xuniverz.com/realms/agentiverz-dev",
  "aud": "aos-api"
}
```

---

## RBAC Roles

### Trace API Roles

| Role | Permissions |
|------|-------------|
| `traces:read` | List and view traces |
| `traces:write` | Store new traces |
| `admin` | All permissions + cross-tenant access |
| `operator` | Delete traces, run cleanup |

### Default Role Mapping

| Keycloak Role | AOS Roles |
|---------------|-----------|
| `aos-developer` | `developer`, `traces:read`, `traces:write` |
| `aos-operator` | `operator`, `traces:read`, `traces:write` |
| `aos-admin` | `admin` |

---

## Tenant Isolation

All trace operations enforce tenant isolation:

1. **List Traces**: Users see only their tenant's traces (unless admin)
2. **Get Trace**: 403 if trace belongs to different tenant
3. **Store Trace**: Automatically tagged with user's tenant_id
4. **Delete Trace**: Requires admin/operator + tenant match

### Cross-Tenant Access (Admin Only)

```bash
# Admin can query any tenant
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://api.agenticverz.com/api/v1/traces?tenant_id=other-tenant"
```

---

## Environment Configuration

### Backend Configuration

```bash
# OIDC Provider Settings
OIDC_ISSUER_URL=https://auth-dev.xuniverz.com/realms/agentiverz-dev
OIDC_JWKS_URI=https://auth-dev.xuniverz.com/realms/agentiverz-dev/protocol/openid-connect/certs
OIDC_AUDIENCE=aos-api
OIDC_CLIENT_ID=aos-backend

# JWT Verification
JWT_ALGORITHMS=RS256,ES256
JWT_VERIFY_EXP=true
JWT_VERIFY_AUD=true
JWT_VERIFY_ISS=true

# Development Mode (NOT for production)
JWT_ALLOW_DEV_TOKEN=false
JWT_DEV_SECRET=dev-secret-not-for-production

# Legacy API Key (backwards compatibility)
AOS_API_KEY=your-api-key-here
```

### SDK Configuration

```python
# Python SDK
from aos_sdk import AOSClient

client = AOSClient(
    api_url="https://api.agenticverz.com",
    token=os.getenv("AOS_TOKEN"),  # JWT token
    # OR
    api_key=os.getenv("AOS_API_KEY"),  # Legacy API key
)
```

```typescript
// JS SDK
const client = new AOSClient({
  apiUrl: "https://api.agenticverz.com",
  token: process.env.AOS_TOKEN,  // JWT token
  // OR
  apiKey: process.env.AOS_API_KEY,  // Legacy API key
});
```

---

## Token Refresh

JWT tokens expire. Handle refresh in your application:

### Python Example

```python
import time
import requests

class TokenManager:
    def __init__(self, auth_url, realm, client_id, username, password):
        self.auth_url = auth_url
        self.realm = realm
        self.client_id = client_id
        self.username = username
        self.password = password
        self._token = None
        self._expires_at = 0

    def get_token(self):
        if time.time() < self._expires_at - 60:  # 60s buffer
            return self._token
        return self._refresh()

    def _refresh(self):
        resp = requests.post(
            f"{self.auth_url}/realms/{self.realm}/protocol/openid-connect/token",
            data={
                "client_id": self.client_id,
                "grant_type": "password",
                "username": self.username,
                "password": self.password,
            }
        )
        data = resp.json()
        self._token = data["access_token"]
        self._expires_at = time.time() + data["expires_in"]
        return self._token
```

---

## Error Responses

### 401 Unauthorized

```json
{
  "detail": "Missing authentication token"
}
```

**Causes:**
- No Authorization header
- No X-API-Key header
- Empty token

### 401 Token Expired

```json
{
  "detail": "Token expired"
}
```

**Fix:** Refresh your token

### 401 Invalid Token

```json
{
  "detail": "Invalid token"
}
```

**Causes:**
- Malformed JWT
- Wrong signing key
- Invalid audience/issuer

### 403 Forbidden

```json
{
  "detail": "Cannot access other tenant's traces"
}
```

**Causes:**
- Trying to access another tenant's data without admin role
- Missing required role for operation

---

## Development Tokens

For local development and testing, you can use development tokens:

### Generate Development Token

```python
from app.auth.jwt_auth import create_dev_token

token = create_dev_token(
    sub="dev-user",
    tenant_id="dev-tenant",
    roles=["developer", "traces:read", "traces:write"],
    expires_in=3600  # 1 hour
)
print(token)  # dev:eyJhbGci...
```

### Use Development Token

```bash
# Set JWT_ALLOW_DEV_TOKEN=true in backend config
curl -H "Authorization: Bearer dev:eyJhbGci..." \
  http://localhost:8000/api/v1/traces
```

**Warning:** Never use development tokens in production!

---

## Security Best Practices

1. **Never expose tokens in logs** - Redact Authorization headers
2. **Use short-lived tokens** - Default 5 minutes, max 1 hour
3. **Implement token refresh** - Don't hardcode tokens
4. **Use HTTPS** - Never send tokens over HTTP
5. **Validate audience** - Reject tokens meant for other services
6. **Monitor failed auth** - Alert on unusual 401 patterns
