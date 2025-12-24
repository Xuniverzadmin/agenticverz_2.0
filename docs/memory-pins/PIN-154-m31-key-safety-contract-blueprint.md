# PIN-154: M31 Key Safety Contract Blueprint

**Status:** READY
**Category:** Security / Trust / Customer Experience
**Created:** 2025-12-24
**Related PINs:** PIN-128, PIN-133, PIN-134, PIN-148

---

## Executive Summary

M31 codifies the trust model for customers providing API keys to AOS's proxy service. The core principle:

> **"You don't have to trust us with a powerful key."**

This milestone delivers customer-facing security guarantees, internal hardening, and breach response playbooks.

---

## The Trust Model

### Fundamental Principle

Trust must be:
- **Minimized** - Accept only blast-radius-limited credentials
- **Scoped** - Per-tenant isolation, per-key limits
- **Reversible** - Instant revocation, visible confirmation
- **Provable** - Usage ledger, audit trail, forensic evidence

### What AOS Already Has (Infrastructure)

| Capability | Implementation | Status |
|-----------|---------------|--------|
| Hash-only key storage | `tenant.py:216-229` SHA-256 | ✅ COMPLETE |
| Key fingerprinting | `key_prefix` (aos_xxxxxxxx) | ✅ COMPLETE |
| Per-call usage ledger | `ProxyCall` model | ✅ COMPLETE |
| Instant revocation | `APIKey.status` + `revoked_at` | ✅ COMPLETE |
| Automatic containment | KillSwitch in request path | ✅ COMPLETE |
| Forensic evidence | `evidence_report.py` PDF generator | ✅ COMPLETE |
| Audit trail | `AuditLog` + `FounderAction` models | ✅ COMPLETE |

### What M31 Adds

| Deliverable | Description | Priority |
|-------------|-------------|----------|
| Key Safety Contract | Customer-facing security promise | P0 |
| Security UX Flows | What users see at each touchpoint | P0 |
| Breach Response Playbook | Mechanical incident response | P1 |
| `X-AOS-Key-Fingerprint` header | Transparency in responses | P0 |
| Key health warnings | Blast-radius guidance on onboarding | P1 |
| Envelope encryption | KMS-wrapped key hashes | P2 |

---

## Deliverable 1: Key Safety Contract (Customer-Facing)

### Document Structure

```
KEY SAFETY CONTRACT
═══════════════════

1. WHAT WE STORE
   ✓ SHA-256 hash of your key (irreversible)
   ✓ First 12 characters for display (aos_xxxxxxxx)
   ✗ We NEVER store your full API key
   ✗ We NEVER log your key in plaintext

2. HOW WE USE IT
   ✓ Decrypt in-memory only during request processing
   ✓ Forward to upstream provider (OpenAI/Anthropic)
   ✓ Log usage metadata (tokens, cost, model, timestamp)
   ✗ We NEVER use your key outside the request path
   ✗ We NEVER cache decrypted keys

3. WHAT YOU CAN DO
   ✓ View usage ledger (every call with your key)
   ✓ Revoke instantly (takes effect in <1 second)
   ✓ Set spend limits (automatic freeze on breach)
   ✓ Export audit logs (machine-readable JSON)

4. WHAT HAPPENS IF SOMETHING GOES WRONG
   ✓ Automatic containment (no human approval needed)
   ✓ Immediate notification (webhook + email)
   ✓ Forensic evidence pack (PDF with hash verification)
   ✓ Key rotation guidance

5. RECOMMENDED KEY HYGIENE
   ⚠️ Use a SEPARATE key for AOS (not your master key)
   ⚠️ Set a LOW spend limit on the provider side
   ⚠️ Enable key rotation on your provider
   ⚠️ Monitor usage through our dashboard
```

### Implementation

- **Location:** `/docs/KEY_SAFETY_CONTRACT.md`
- **API Endpoint:** `GET /v1/security/contract` (returns JSON version)
- **Console Page:** `/settings/security` displays contract summary

---

## Deliverable 2: Security UX Flows

### Flow 1: Key Onboarding

```
┌─────────────────────────────────────────────────────────────────┐
│  ADD API KEY                                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Provider: [OpenAI ▼]                                          │
│                                                                 │
│  API Key: [sk-••••••••••••••••••••••••••••••••••••••]          │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ⚠️ KEY HYGIENE RECOMMENDATIONS                          │   │
│  │                                                         │   │
│  │ • Use a dedicated key for AOS (not your master key)    │   │
│  │ • Set a spend limit on your OpenAI dashboard           │   │
│  │ • Enable usage alerts on your provider                 │   │
│  │                                                         │   │
│  │ We store only a hash of your key. You can revoke       │   │
│  │ access instantly at any time.                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  [Cancel]                              [Add Key & Verify]       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Flow 2: Key Revocation

```
┌─────────────────────────────────────────────────────────────────┐
│  REVOKE API KEY                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Key: aos_7x9k2m... (OpenAI)                                   │
│  Created: 2025-12-15                                           │
│  Last Used: 2025-12-24 14:32:01 UTC                            │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ⚠️ This action takes effect IMMEDIATELY                 │   │
│  │                                                         │   │
│  │ • All pending requests will be rejected                │   │
│  │ • No new requests can use this key                     │   │
│  │ • Usage history will be preserved                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Reason: [Security concern ▼]                                  │
│                                                                 │
│  [Cancel]                              [Revoke Permanently]     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Flow 3: Post-Revocation Confirmation

```
┌─────────────────────────────────────────────────────────────────┐
│  ✅ KEY REVOKED                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Key: aos_7x9k2m... has been permanently revoked.              │
│                                                                 │
│  Revoked at: 2025-12-24 14:35:22 UTC                           │
│  Revoked by: you@example.com                                   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ VERIFICATION                                            │   │
│  │                                                         │   │
│  │ • 0 requests accepted since revocation                 │   │
│  │ • 3 requests rejected (attempted after revocation)     │   │
│  │ • Audit log entry created                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  [Download Audit Log]              [Return to Settings]         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Deliverable 3: Breach Response Playbook

### Phase 1: Detection (Automatic)

| Trigger | Source | Action |
|---------|--------|--------|
| Sudden cost spike | M26 Cost Intelligence | Flag anomaly |
| Unusual model usage | ProxyCall analysis | Flag anomaly |
| Geographic anomaly | Request metadata | Flag anomaly |
| Rate limit breach | Rate limiter | Log + alert |

### Phase 2: Containment (Automatic, <1 second)

```python
# Triggered automatically when anomaly score > threshold
async def auto_contain(tenant_id: str, reason: str):
    # 1. Freeze traffic immediately
    await killswitch_freeze(
        entity_type="tenant",
        entity_id=tenant_id,
        reason=f"AUTO: {reason}",
        freeze_source="anomaly_detection"
    )

    # 2. Log founder action (even though automatic)
    await create_founder_action(
        action_type="FREEZE_TENANT",
        target_type="TENANT",
        target_id=tenant_id,
        reason_code="ANOMALY_DETECTED",
        reason_note=reason,
        founder_id="SYSTEM",
        founder_email="system@aos.internal",
        mfa_verified=False  # N/A for automatic actions
    )

    # 3. Notify customer
    await send_notification(
        tenant_id=tenant_id,
        type="TRAFFIC_STOPPED",
        message=f"Traffic stopped: {reason}",
        channels=["webhook", "email"]
    )
```

### Phase 3: Forensics (Automatic, <5 minutes)

```python
async def generate_forensic_pack(tenant_id: str, incident_id: str):
    # 1. Gather evidence
    calls = await get_proxy_calls(
        tenant_id=tenant_id,
        since=incident_start - timedelta(hours=1),
        until=incident_end + timedelta(minutes=5)
    )

    # 2. Build timeline
    timeline = build_decision_timeline(calls)

    # 3. Calculate impact
    impact = {
        "total_calls": len(calls),
        "total_cost_cents": sum(c.cost_cents for c in calls),
        "models_used": list(set(c.model for c in calls)),
        "suspicious_calls": [c for c in calls if c.anomaly_score > 0.7]
    }

    # 4. Generate PDF evidence pack
    pdf = generate_evidence_report(
        incident_id=incident_id,
        tenant_id=tenant_id,
        timeline_events=timeline,
        impact_assessment=impact,
        severity="HIGH"
    )

    return pdf
```

### Phase 4: Customer Communication (Template)

```
Subject: [AOS Security] Traffic Stopped - Action Required

Your AOS traffic has been automatically stopped.

WHAT HAPPENED
─────────────
• Anomaly detected: {reason}
• Time: {timestamp}
• Affected key: aos_{prefix}...

WHAT WE DID
───────────
• Blocked all traffic using this key
• Preserved all usage logs
• Generated forensic evidence pack

WHAT YOU SHOULD DO
──────────────────
1. Review the attached evidence pack
2. Check your provider dashboard for unauthorized usage
3. Rotate your API key on the provider side
4. Contact us to restore access after review

EVIDENCE PACK
─────────────
[Download PDF] (expires in 7 days)

If you believe this was a false positive, reply to this email
with "RESTORE" and we will review within 4 hours.
```

### Phase 5: Post-Incident (Manual Review)

| Step | Owner | SLA |
|------|-------|-----|
| Review forensic pack | Security team | 4 hours |
| Customer communication | Support team | 1 hour |
| Root cause analysis | Engineering | 24 hours |
| Control enhancement | Engineering | 72 hours |
| Incident closure | Security team | 7 days |

---

## Deliverable 4: `X-AOS-Key-Fingerprint` Header

### Specification

Every proxy response includes:

```http
HTTP/1.1 200 OK
X-AOS-Key-Fingerprint: aos_7x9k2m
X-AOS-Request-ID: req_abc123
X-AOS-Cost-Cents: 0.42
```

### Implementation

```python
# v1_proxy.py - Add to response headers
@router.post("/chat/completions")
async def chat_completions(...):
    # ... existing code ...

    response.headers["X-AOS-Key-Fingerprint"] = auth["api_key"].key_prefix
    response.headers["X-AOS-Request-ID"] = call.id
    response.headers["X-AOS-Cost-Cents"] = str(call.cost_cents)

    return response
```

### Customer Benefit

Customers can verify in their logs:
- Which key was used (fingerprint matches their records)
- Request traceability (request ID for support)
- Cost per request (budget tracking)

---

## Deliverable 5: Key Health Warnings

### Onboarding-Time Checks

```python
async def check_key_health(provider: str, key: str) -> List[Warning]:
    warnings = []

    # 1. Check if key has unrestricted permissions
    if await key_has_full_permissions(provider, key):
        warnings.append(Warning(
            level="HIGH",
            message="This key has unrestricted permissions. "
                    "Consider creating a scoped key for AOS."
        ))

    # 2. Check if key has no spend limit
    if await key_has_no_spend_limit(provider, key):
        warnings.append(Warning(
            level="MEDIUM",
            message="This key has no spend limit. "
                    "Set a limit on your provider dashboard."
        ))

    # 3. Check if key is a production/master key
    if await key_appears_to_be_master(provider, key):
        warnings.append(Warning(
            level="HIGH",
            message="This appears to be a master key. "
                    "We strongly recommend using a dedicated key for AOS."
        ))

    return warnings
```

---

## Deliverable 6: Envelope Encryption (P2)

### Current State

```
Key → SHA-256 → key_hash (stored in DB)
```

### M31 Enhancement

```
Key → SHA-256 → DEK encrypt → encrypted_key_hash (stored in DB)
                    ↑
               KEK from KMS
```

### Implementation

```python
from cryptography.fernet import Fernet
from app.secrets.vault_client import get_kms_key

class KeyEncryption:
    def __init__(self):
        self.kek = get_kms_key("aos/key-encryption-key")
        self.cipher = Fernet(self.kek)

    def encrypt_hash(self, key_hash: str) -> str:
        """Encrypt key hash with KMS-managed KEK."""
        return self.cipher.encrypt(key_hash.encode()).decode()

    def decrypt_hash(self, encrypted: str) -> str:
        """Decrypt key hash for comparison."""
        return self.cipher.decrypt(encrypted.encode()).decode()
```

### Migration Path

1. Add `encrypted_key_hash` column
2. Backfill existing keys
3. Update lookup to use decryption
4. Remove plaintext `key_hash` column

---

## Implementation Plan

### Phase 1: Customer-Facing (Days 1-3)

| Task | Effort | Owner |
|------|--------|-------|
| Create `KEY_SAFETY_CONTRACT.md` | 2 hours | Docs |
| Add `GET /v1/security/contract` endpoint | 2 hours | Backend |
| Add `X-AOS-Key-Fingerprint` header | 1 hour | Backend |
| Add key health warnings to onboarding UI | 4 hours | Frontend |

### Phase 2: Breach Response (Days 4-7)

| Task | Effort | Owner |
|------|--------|-------|
| Document breach response playbook | 4 hours | Security |
| Implement auto-containment triggers | 8 hours | Backend |
| Create forensic pack generator integration | 4 hours | Backend |
| Create customer notification templates | 2 hours | Ops |

### Phase 3: Hardening (Days 8-14)

| Task | Effort | Owner |
|------|--------|-------|
| Implement envelope encryption | 16 hours | Backend |
| Migration script for existing keys | 4 hours | Backend |
| Security UX flows in console | 8 hours | Frontend |
| End-to-end security audit | 8 hours | Security |

---

## Success Criteria

### P0 (Must Have)

- [ ] `KEY_SAFETY_CONTRACT.md` published and linked from dashboard
- [ ] `X-AOS-Key-Fingerprint` header on all proxy responses
- [ ] Key health warnings displayed during onboarding
- [ ] Instant revocation with confirmation UI

### P1 (Should Have)

- [ ] Breach response playbook documented
- [ ] Auto-containment triggers active
- [ ] Forensic pack generation automated
- [ ] Customer notification templates ready

### P2 (Nice to Have)

- [ ] Envelope encryption for key hashes
- [ ] Per-tenant container isolation option
- [ ] Provider-side spend limit validation

---

## Dependencies

| Dependency | Source | Required By |
|------------|--------|-------------|
| KillSwitch | M22 | Auto-containment |
| Evidence Report | M22 | Forensic pack |
| Cost Intelligence | M26/M27 | Anomaly detection |
| Founder Actions | M29 | Audit trail |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Customer distrust despite measures | Medium | High | Transparent UX, proactive communication |
| False positive freezes | Low | Medium | Tunable thresholds, quick restore process |
| Breach despite controls | Low | Critical | Blast-radius limits, forensic evidence |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-24 | Created PIN-154 M31 Key Safety Contract Blueprint |
