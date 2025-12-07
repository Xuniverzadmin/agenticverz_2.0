# AOS Authentication Setup

How to authenticate with AOS using Keycloak OIDC tokens.

## Overview

AOS supports two authentication methods:

| Method | Use Case | Header |
|--------|----------|--------|
| API Key | Simple scripts, CLI | `X-AOS-Key: <key>` |
| OIDC Token | Production, RBAC | `Authorization: Bearer <token>` |

## Quick Start (API Key)

For demos and development, use the API key:

```bash
export AOS_API_KEY=your-api-key

# SDK uses this automatically
aos health
```

## Production (OIDC Token)

For production with RBAC, use Keycloak tokens.

### 1. Get Token from Keycloak

```bash
# Configuration
KC_URL="https://auth-dev.xuniverz.com"
REALM="agentiverz-dev"
CLIENT_ID="aos-backend"
CLIENT_SECRET="your-client-secret"

# Get access token
TOKEN=$(curl -sk -X POST "$KC_URL/realms/$REALM/protocol/openid-connect/token" \
  -d "grant_type=client_credentials" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET" | jq -r '.access_token')

echo "Token: ${TOKEN:0:50}..."
```

### 2. Use Token with API

```bash
# Health check
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/health

# Get capabilities
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/runtime/capabilities
```

### 3. Use Token with SDK

```python
from aos_sdk import AOSClient
import os

# Client will use Bearer token from env if set
os.environ["AOS_TOKEN"] = "your-access-token"

client = AOSClient()
# Or pass explicitly
client = AOSClient(token="your-access-token")
```

## User Authentication

For end-user authentication (password grant):

```bash
# Get token for a user
TOKEN=$(curl -sk -X POST "$KC_URL/realms/$REALM/protocol/openid-connect/token" \
  -d "grant_type=password" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET" \
  -d "username=devuser" \
  -d "password=devuser123" | jq -r '.access_token')
```

## RBAC Roles

Tokens include roles that determine permissions:

| Role | Permissions |
|------|-------------|
| `viewer` | Read runs, list skills |
| `developer` | Create runs, execute plans |
| `operator` | Approve recovery, manage workflows |
| `admin` | Full access, manage users |

Example token payload:

```json
{
  "realm_access": {
    "roles": ["developer", "default-roles-agentiverz-dev"]
  },
  "resource_access": {
    "aos-backend": {
      "roles": ["aos_developer"]
    }
  }
}
```

## Token Inspection

Decode your token to see claims:

```bash
# Split token and decode payload (middle section)
echo $TOKEN | cut -d. -f2 | base64 -d 2>/dev/null | jq .

# Expected output:
# {
#   "exp": 1733500000,
#   "iat": 1733496400,
#   "sub": "user-uuid",
#   "realm_access": {
#     "roles": ["developer"]
#   }
# }
```

## Token Refresh

Access tokens expire (default: 5 minutes). Refresh before expiry:

```bash
REFRESH_TOKEN="your-refresh-token"

NEW_TOKEN=$(curl -sk -X POST "$KC_URL/realms/$REALM/protocol/openid-connect/token" \
  -d "grant_type=refresh_token" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET" \
  -d "refresh_token=$REFRESH_TOKEN" | jq -r '.access_token')
```

## Keycloak Admin

### Access Admin Console

- URL: https://auth-dev.xuniverz.com
- Realm: `agentiverz-dev`
- Admin user: See internal credentials

### Create New User

1. Login to admin console
2. Navigate to Users → Add user
3. Set username, email
4. Credentials tab → Set password
5. Role Mappings → Assign roles

### Create New Client

1. Navigate to Clients → Create
2. Set Client ID (e.g., `my-app`)
3. Set Valid Redirect URIs
4. Enable Client Authentication if needed
5. Copy Client Secret for your app

## Troubleshooting

### `401 Unauthorized`

- Token expired → Refresh or get new token
- Wrong audience → Check `client_id`
- Invalid signature → Keycloak key rotated

### `403 Forbidden`

- Missing role → Check token's `realm_access.roles`
- RBAC policy denied → Check permission matrix

### Token Not Accepted

```bash
# Verify JWKS is reachable
curl -s "$KC_URL/realms/$REALM/.well-known/openid-configuration" | jq .jwks_uri

# Verify signature
curl -s $(curl -s "$KC_URL/realms/$REALM/.well-known/openid-configuration" | jq -r .jwks_uri)
```

### Can't Connect to Keycloak

```bash
# Check Keycloak is running
curl -s https://auth-dev.xuniverz.com/health

# Check DNS
nslookup auth-dev.xuniverz.com
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AOS_API_KEY` | Simple API key auth | `abc123...` |
| `AOS_TOKEN` | Bearer token (OIDC) | `eyJhbG...` |
| `AOS_BASE_URL` | Server URL | `http://localhost:8000` |
| `OIDC_ISSUER_URL` | Keycloak realm URL | `https://auth.../realms/...` |

## Summary

| Scenario | Auth Method | Setup Time |
|----------|-------------|------------|
| Local dev | API Key | 30 seconds |
| Demo scripts | API Key | 30 seconds |
| Production | OIDC Token | 5 minutes |
| Multi-tenant | OIDC + RBAC | 10 minutes |

For most demos, API key authentication is sufficient. Switch to OIDC for production deployments with RBAC.
