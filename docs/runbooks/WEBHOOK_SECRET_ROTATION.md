# Webhook Secret Rotation Procedure

**Service:** AOS Policy API Webhooks
**Owner:** Security Team
**Last Updated:** 2025-12-03

---

## Overview

Webhook secrets are used to sign outgoing webhook payloads using HMAC-SHA256. Receivers verify the signature using the `X-Webhook-Signature` header to ensure authenticity.

**Security Properties:**
- Secrets are stored as SHA-256 hashes (not plaintext)
- Signatures use HMAC-SHA256: `sha256=<signature>`
- Receiver must verify signature before processing

---

## Current Implementation

```python
# Signature computation (sender side)
def _compute_webhook_signature(payload: str, secret: str) -> str:
    import hmac
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

# Header format
headers["X-Webhook-Signature"] = f"sha256={signature}"
```

---

## Rotation Schedule

| Environment | Rotation Frequency | Notification Lead Time |
|-------------|-------------------|----------------------|
| Production | Every 90 days | 7 days |
| Staging | Every 30 days | 3 days |
| Development | On-demand | None |

---

## Pre-Rotation Checklist

1. [ ] Notify all webhook consumers (via email/Slack)
2. [ ] Confirm receivers support dual-secret validation
3. [ ] Schedule rotation window (low-traffic period)
4. [ ] Prepare rollback plan
5. [ ] Test new secret generation

---

## Rotation Procedure

### Step 1: Generate New Secret

```bash
# Generate cryptographically secure secret
NEW_SECRET=$(openssl rand -hex 32)
echo "New secret: $NEW_SECRET"

# Store securely (don't log in production)
```

### Step 2: Update Database (Per-Request)

For individual request rotation:

```bash
# Hash the new secret
NEW_HASH=$(echo -n "$NEW_SECRET" | sha256sum | cut -d' ' -f1)

# Update specific request
PGPASSWORD=novapass psql -h 127.0.0.1 -p 5433 -U nova -d nova_aos \
  -c "UPDATE approval_requests SET webhook_secret_hash = '$NEW_HASH' WHERE id = '<request_id>';"
```

### Step 3: Notify Receivers

Send to webhook consumers:

```
Subject: [Action Required] Webhook Secret Rotation - <date>

The webhook signing secret for AOS Policy API will be rotated on <date>.

New secret: <provide securely>

Please update your webhook verification code by <deadline>.

During the transition period, we recommend accepting signatures from both
the old and new secrets.
```

### Step 4: Verify Receiver Updates

```bash
# Test webhook delivery with new secret
curl -X POST http://127.0.0.1:8000/api/v1/policy/requests \
  -H "Content-Type: application/json" \
  -d '{
    "policy_type": "cost",
    "skill_id": "test_rotation",
    "tenant_id": "t1",
    "requested_by": "rotation_test",
    "webhook_url": "https://your-receiver/webhook",
    "webhook_secret": "<NEW_SECRET>"
  }'

# Check receiver logs for successful verification
```

### Step 5: Complete Rotation

After confirming receivers work with new secret:

```bash
# Mark rotation complete in audit log
logger -t aos-webhook "Webhook secret rotation completed for tenant <tenant_id>"
```

---

## Receiver-Side Verification

Receivers should implement dual-secret validation during rotation:

```python
import hmac
import hashlib

def verify_webhook(payload: bytes, signature: str, secrets: list[str]) -> bool:
    """
    Verify webhook signature against one or more secrets.

    Args:
        payload: Raw request body
        signature: X-Webhook-Signature header value
        secrets: List of valid secrets (current + old during rotation)

    Returns:
        True if signature matches any secret
    """
    if not signature.startswith("sha256="):
        return False

    received_sig = signature[7:]  # Remove "sha256=" prefix

    for secret in secrets:
        expected = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        if hmac.compare_digest(expected, received_sig):
            return True

    return False

# Usage during rotation period
CURRENT_SECRET = "new_secret_here"
OLD_SECRET = "old_secret_here"  # Remove after rotation window

if verify_webhook(request.body, request.headers["X-Webhook-Signature"],
                   [CURRENT_SECRET, OLD_SECRET]):
    process_webhook(request)
else:
    return 401, "Invalid signature"
```

---

## Emergency Rotation (Compromise Response)

If secret is compromised:

### Immediate Actions

```bash
# 1. Disable all webhooks immediately
PGPASSWORD=novapass psql -h 127.0.0.1 -p 5433 -U nova -d nova_aos \
  -c "UPDATE approval_requests SET webhook_url = NULL WHERE webhook_url IS NOT NULL;"

# 2. Generate new secret
NEW_SECRET=$(openssl rand -hex 32)

# 3. Notify all consumers immediately
# (use out-of-band communication - phone, secure chat)

# 4. Re-enable webhooks with new secret after consumer confirmation
```

### Post-Incident

1. [ ] Investigate compromise source
2. [ ] Review access logs
3. [ ] Update rotation schedule if needed
4. [ ] Document incident in security log

---

## Audit Trail

All rotations should be logged:

```bash
# Query rotation history (via status_history_json)
PGPASSWORD=novapass psql -h 127.0.0.1 -p 5433 -U nova -d nova_aos \
  -c "SELECT id, updated_at, webhook_secret_hash
      FROM approval_requests
      WHERE webhook_secret_hash IS NOT NULL
      ORDER BY updated_at DESC LIMIT 20;"
```

---

## Contacts

| Role | Contact | When to Notify |
|------|---------|----------------|
| Security On-Call | #security-oncall | Compromise suspected |
| Platform Team | #platform | Scheduled rotation |
| Webhook Consumers | Consumer contact list | 7 days before rotation |

---

## Related Documentation

- [M5 Policy Runbook](./M5_POLICY_RUNBOOK.md)
- [Webhook API Documentation](../api/webhooks.md)
- [Security Incident Response](../security/incident-response.md)
