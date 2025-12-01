# Secrets Directory

This directory contains sensitive credentials for the NOVA Agent Manager.

**NEVER commit actual secrets to git.**

## Required Files for Alertmanager Secrets Mode

Create these files with your actual credentials:

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

## Enabling Secrets Mode

1. Create the secret files above
2. Edit `docker-compose.yml`:
   - Uncomment the `entrypoint` and `secrets` lines in the alertmanager service
   - Uncomment the `secrets:` section at the bottom
3. Restart: `docker compose up -d alertmanager`
