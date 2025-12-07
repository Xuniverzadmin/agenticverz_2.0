# Secrets Directory

**WARNING: This directory contains sensitive credentials. Never commit to git.**

---

## External Service Credentials (M8+)

| File | Service | Purpose | Milestone |
|------|---------|---------|-----------|
| `neon.env` | Neon PostgreSQL | Database (replaces local PgBouncer) | M8 |
| `clerk.env` | Clerk Auth | Authentication (replaces stub) | M8 |
| `clerk_public_key.pem` | Clerk Auth | JWT verification public key | M8 |
| `openai.env` | OpenAI | Memory embeddings (pgvector), LLM fallback | M8 |
| `resend.env` | Resend | Email sending (`email_send` skill) | M11 |
| `posthog.env` | PostHog | SDK analytics & beta tracking | M12 |
| `trigger.env` | Trigger.dev | Background jobs (aggregation) | M9 |
| `cloudflare.env` | Cloudflare | Workers for edge compute | M9/M10 |

---

## Usage

### Load all credentials

```bash
source /root/agenticverz2.0/secrets/load_all.sh
```

### Load specific service

```bash
source /root/agenticverz2.0/secrets/neon.env
```

### Verify loaded

```bash
env | grep -E 'NEON|CLERK|RESEND|POSTHOG|TRIGGER|CLOUDFLARE|OPENAI|EMBEDDING'
```

---

## Alertmanager Secrets (Legacy)

Required files for Alertmanager secrets mode:

```bash
# Slack webhook URL
echo 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL' > alert_slack_webhook.txt

# SMTP relay host:port
echo 'smtp.your-relay.com:587' > alert_smtp_smarthost.txt

# SMTP username
echo 'your-smtp-user' > alert_smtp_user.txt

# SMTP password
echo 'your-smtp-password' > alert_smtp_pass.txt

# Secure the files
chmod 600 *.txt
```

### Enabling Secrets Mode

1. Create the secret files above
2. Edit `docker-compose.yml`:
   - Uncomment the `entrypoint` and `secrets` lines in the alertmanager service
   - Uncomment the `secrets:` section at the bottom
3. Restart: `docker compose up -d alertmanager`

---

## Security

- All `.env` files have `600` permissions (owner read/write only)
- Directory has `700` permissions
- **NEVER** commit this directory to git
- Rotate keys if exposed

---

## Related

- Memory PIN: `docs/memory-pins/PIN-036-EXTERNAL-SERVICES.md`
- Account reference: All accounts use `admin1@agenticverz.com` or GitHub `Xuniverz`
