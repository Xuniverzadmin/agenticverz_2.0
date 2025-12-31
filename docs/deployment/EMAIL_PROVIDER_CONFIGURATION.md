# Email Transactional Provider Configuration

**Date:** 2025-12-30
**Provider:** Resend
**Reference:** PIN-052, M11

---

## Overview

AOS uses [Resend](https://resend.com) for transactional email delivery.

### Email Features

| Feature | Service | Description |
|---------|---------|-------------|
| Workflow Notifications | `email_send` skill | Workflow completion, alerts |
| Email OTP Verification | `email_verification` service | Onboarding OTP codes |

---

## Environment Variables

Add these to your `.env` file:

```bash
# Required: Resend API Key
RESEND_API_KEY=re_xxxxxxxxxxxx

# Default sender address (must be verified in Resend)
RESEND_FROM_ADDRESS=notifications@agenticverz.com

# For onboarding emails
EMAIL_FROM=Agenticverz <noreply@agenticverz.com>

# OTP configuration
EMAIL_VERIFICATION_TTL=600  # 10 minutes
```

---

## Resend Setup Steps

### 1. Create Resend Account

1. Sign up at https://resend.com
2. Verify your email domain (DNS records)

### 2. Add DNS Records

In your DNS provider, add these records:

**For `agenticverz.com`:**

| Type | Name | Value | Purpose |
|------|------|-------|---------|
| TXT | resend._domainkey | (from Resend dashboard) | DKIM signing |
| TXT | @ or subdomain | (from Resend dashboard) | Domain verification |

### 3. Generate API Key

1. Go to Resend Dashboard → API Keys
2. Create a new API key with `Full access` or `Sending access`
3. Copy the key (starts with `re_`)

### 4. Configure Environment

```bash
# Add to .env
echo 'RESEND_API_KEY=re_your_api_key_here' >> /root/agenticverz2.0/.env
echo 'RESEND_FROM_ADDRESS=notifications@agenticverz.com' >> /root/agenticverz2.0/.env

# Restart services
docker compose restart backend worker
```

---

## Verification

### Test Email Sending

```bash
# Test via CLI
cd /root/agenticverz2.0/backend
PYTHONPATH=. python3 -c "
import asyncio
from app.skills.email_send import EmailSendSkill

async def test():
    skill = EmailSendSkill(allow_external=True)
    result = await skill.execute({
        'to': 'test@example.com',
        'subject': 'AOS Test Email',
        'body': 'This is a test email from AOS.',
    })
    print(result)

asyncio.run(test())
"
```

### Test OTP Flow

```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. python3 -c "
import asyncio
from app.services.email_verification import get_email_verification_service

async def test():
    svc = get_email_verification_service()
    result = await svc.send_otp('test@example.com', 'Test User')
    print(result)

asyncio.run(test())
"
```

### Check Logs

```bash
# Check for email-related logs
docker compose logs backend 2>&1 | grep -E "(email|resend|OTP)" | tail -20
```

---

## Email Templates

### Workflow Notification

The `email_send` skill supports both plain text and HTML:

```python
# Plain text
{
    "to": "user@example.com",
    "subject": "Workflow Complete",
    "body": "Your workflow has finished.",
}

# HTML
{
    "to": "user@example.com",
    "subject": "Workflow Complete",
    "body": "<h1>Success!</h1><p>Your workflow completed.</p>",
    "html": True,
}
```

### OTP Email

The OTP email template is built-in to `email_verification.py`:

- Professional HTML template with code display
- Plain text fallback
- Expiration time displayed
- Branded as Agenticverz

---

## Rate Limits

Resend has the following limits:

| Plan | Daily Limit | Burst Rate |
|------|-------------|------------|
| Free | 100 emails | 10/second |
| Pro | 50,000 emails | 100/second |
| Enterprise | Unlimited | Custom |

### Handling Rate Limits

The `email_send` skill handles rate limits gracefully:

```json
{
  "result": {
    "status": "error",
    "error": "api_error",
    "message": "Resend API error (429): Rate limit exceeded"
  }
}
```

---

## Monitoring

### Prometheus Metrics

```promql
# Email send attempts
email_send_total{status="ok"}
email_send_total{status="error"}

# OTP verification
email_otp_sent_total
email_otp_verified_total
email_otp_failed_total
```

### Resend Dashboard

Check delivery stats at: https://resend.com/emails

---

## Troubleshooting

### Issue: API Key Not Configured

```
Error: RESEND_API_KEY not configured
```

**Fix:** Ensure `RESEND_API_KEY` is set in `.env` and services are restarted.

### Issue: Domain Not Verified

```
Error: Resend API error (403): Domain not verified
```

**Fix:** Complete DNS verification in Resend dashboard.

### Issue: Invalid From Address

```
Error: Resend API error (400): Invalid from address
```

**Fix:** Use an address from a verified domain.

### Issue: OTP Cooldown

```
Error: Please wait X seconds before requesting another code
```

**Expected behavior:** Users must wait 60 seconds between OTP requests.

---

## Security Considerations

1. **API Key Security:** Never commit `RESEND_API_KEY` to version control
2. **Rate Limiting:** Built-in cooldown prevents OTP abuse
3. **OTP Expiration:** Codes expire after 10 minutes (configurable)
4. **Attempt Limiting:** Max 3 OTP attempts before requiring new code

---

## Production Checklist

- [ ] DNS records configured and verified
- [ ] API key generated and stored securely
- [ ] `RESEND_API_KEY` added to production `.env`
- [ ] `RESEND_FROM_ADDRESS` configured
- [ ] Test email sent successfully
- [ ] OTP flow tested
- [ ] Monitoring dashboards configured
- [ ] Alerting for email failures configured

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-30 | Initial configuration guide |
