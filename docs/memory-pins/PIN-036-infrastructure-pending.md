# PIN-036: Infrastructure Pending Items

**Serial:** PIN-036
**Created:** 2025-12-06
**Status:** ACTIVE
**Category:** Infrastructure / Planning

---

## Summary

Tracking infrastructure items that are NOT blocking M8 but will be needed for later milestones. These were identified during the Priority A-C review session.

---

## Status Overview

### ✅ Completed (Priority A - Hard Blockers)

| Item | Status | Milestone | Evidence |
|------|--------|-----------|----------|
| Identity Provider (Keycloak) | ✅ COMPLETE | M8 | auth-dev.xuniverz.com, OIDC wired |
| Secrets Manager (Vault) | ✅ COMPLETE | M8 | 127.0.0.1:8200, 4 secret paths |
| npm + PyPI Publisher | ✅ COMPLETE | M8 | aos-sdk v0.1.0 on both registries |
| Slack App | ✅ COMPLETE | M8 | App ID: A0A1YTBENAE, webhook working |

### ⏳ Pending (Will Need Before Milestone)

| Item | Status | Needed By | Blocking? |
|------|--------|-----------|-----------|
| Email Provider | ❌ NOT DONE | M11 | No |
| S3/Object Storage | ❌ NOT DONE | M9 | No |
| Demo Screencast | ❌ NOT DONE | M8 | No (nice-to-have) |

---

## Pending Item Details

### 1. Email Provider (Needed: M11)

**Purpose:** `/notify/email` skill for agent notifications

**Setup Steps:**
1. Sign up for transactional email service (SendGrid/Mailgun/SES)
2. Verify domain: `agenticverz.com` or `xuniverz.com`
3. Store API key in Vault: `agenticverz/email-provider`
4. Create `/notify/email` skill in `backend/app/skills/`
5. Add integration test

**Effort:** ~0.5-1 day

**Acceptance Criteria:**
- [ ] Email service account created
- [ ] Domain/sender verified
- [ ] API key in Vault
- [ ] Skill sends test email to real inbox
- [ ] No email secrets in code

---

### 2. S3/Object Storage (Needed: M9)

**Purpose:** Persist JSONL exports, failure catalog, provenance dumps

**Setup Steps:**
1. Create S3 bucket (or MinIO/DO Spaces)
2. Create least-privilege IAM user/role
3. Store credentials in Vault: `agenticverz/object-storage`
4. Create utility for write/read operations
5. Wire into failure catalog export

**Effort:** ~0.5-1 day

**Acceptance Criteria:**
- [ ] Bucket created with restricted access
- [ ] Credentials in Vault
- [ ] Write/read utility works
- [ ] One endpoint uses it for export

---

### 3. Demo Screencast (Needed: M8 Nice-to-Have)

**Purpose:** Show system in action for onboarding/investor demos

**Setup Steps:**
1. Record 5-10 min walkthrough
   - What is AOS
   - Create agent → run skill → see logs
   - Grafana monitoring
2. Upload to YouTube (@AgenticverzAdmin)
3. Add link to README and landing page

**Effort:** ~4-6 hours

**Acceptance Criteria:**
- [ ] Video uploaded and accessible
- [ ] Link in README.md
- [ ] Link on agenticverz.com landing page

---

## External Integrations Completed (2025-12-06)

These were set up on agenticverz.com domain:

| Integration | Status | Details |
|-------------|--------|---------|
| YouTube | ✅ | @AgenticverzAdmin, Channel ID: UC9cR-k7YieBdlN82GYiW7aA |
| Loom | ✅ | https://www.loom.com/spaces/Agenticverz-AOS-41973046 |
| Slack Workspace | ✅ | agenticverzworkspace, invite link active |
| Slack Webhook | ✅ | #test-1-aos channel, webhook verified |
| Grafana Cloud | ✅ | agenticverz.grafana.net, dashboard + Slack alerts |
| Landing Page | ✅ | https://agenticverz.com |
| DNS/SSL | ✅ | Cloudflare Full Strict, Origin certs |
| Email (SMTP) | ✅ | mail.xuniverz.com, DKIM signed |

**See:** `/var/www/agenticverz.com/memory-pins/` for detailed documentation.

---

## Milestone Dependencies

```
M8 (Demo + SDK + Auth)
├── Auth Integration ✅
├── SDK Packaging ✅
└── Demo Screencast ⏳ (nice-to-have)

M9 (Failure Catalog v2 + Persistence)
├── S3/Object Storage ⏳ (BLOCKING)
└── Failure schema persistence

M11 (Skill Expansion)
├── Email Provider ⏳ (BLOCKING for /notify/email)
├── postgres_query production
└── calendar_write production
```

---

## Quick Setup Commands

### Email (when ready)

```bash
# Example: SendGrid
vault kv put agenticverz/email-provider \
  SENDGRID_API_KEY="SG.xxx" \
  FROM_EMAIL="notifications@agenticverz.com"
```

### S3 (when ready)

```bash
# Example: AWS S3
vault kv put agenticverz/object-storage \
  AWS_ACCESS_KEY_ID="AKIA..." \
  AWS_SECRET_ACCESS_KEY="..." \
  S3_BUCKET="agenticverz-exports" \
  S3_REGION="us-east-1"
```

---

## Related PINs

- PIN-033: M8-M14 Machine-Native Realignment Roadmap
- PIN-034: HashiCorp Vault Secrets Management
- PIN-035: SDK Package Registry

---

## Related agenticverz.com PINs

Location: `/var/www/agenticverz.com/memory-pins/`

| PIN | Title |
|-----|-------|
| PIN-001 | DNS Setup |
| PIN-002 | Email Setup |
| PIN-003 | Landing Page |
| PIN-004 | Slack Integration |
| PIN-005 | Grafana Status Page |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-06 | Created PIN-036 tracking pending infrastructure |
| 2025-12-06 | Documented M9/M11 dependencies |
| 2025-12-06 | Added agenticverz.com integration summary |
