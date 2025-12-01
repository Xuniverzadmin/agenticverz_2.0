#!/usr/bin/env bash
set -euo pipefail

TEMPLATE=/etc/alertmanager/config.yml.tmpl
OUT=/etc/alertmanager/config.yml

# Docker secrets path fallback
read_secret() {
  name="$1"
  file="/run/secrets/$name"
  if [ -f "$file" ]; then
    cat "$file"
  else
    # fallback to env var uppercase
    varname="$(echo "$name" | tr '[:lower:]-' '[:upper:]_')"
    if [ -z "${!varname:-}" ]; then
      echo ""
    else
      echo "${!varname}"
    fi
  fi
}

# Required secrets
SLACK_WEBHOOK="$(read_secret alert_slack_webhook)"
SMTP_SMARTHOST="$(read_secret alert_smtp_smarthost)"
SMTP_USER="$(read_secret alert_smtp_user)"
SMTP_PASS="$(read_secret alert_smtp_pass)"

# Basic validation
if [ -z "$SLACK_WEBHOOK" ] || [ -z "$SMTP_SMARTHOST" ] || [ -z "$SMTP_USER" ] || [ -z "$SMTP_PASS" ]; then
  echo "WARNING: One or more Alertmanager secrets are empty. Falling back to template values if present."
fi

# Export for envsubst
export SLACK_WEBHOOK SMTP_SMARTHOST SMTP_USER SMTP_PASS

# Render template to config.yml using envsubst
if command -v envsubst >/dev/null 2>&1; then
  envsubst '${SLACK_WEBHOOK} ${SMTP_SMARTHOST} ${SMTP_USER} ${SMTP_PASS}' < "$TEMPLATE" > "$OUT"
else
  # minimal sed fallback (less safe for special chars)
  cp "$TEMPLATE" "$OUT"
  sed -i "s|REPLACE_SLACK_WEBHOOK|$SLACK_WEBHOOK|g" "$OUT" || true
  sed -i "s|REPLACE_SMTP_SMARTHOST|$SMTP_SMARTHOST|g" "$OUT" || true
  sed -i "s|REPLACE_SMTP_USER|$SMTP_USER|g" "$OUT" || true
  sed -i "s|REPLACE_SMTP_PASS|$SMTP_PASS|g" "$OUT" || true
fi

echo "Rendered Alertmanager config to $OUT (masked values omitted)."

# Start alertmanager (preserve args)
exec /bin/alertmanager --config.file="$OUT" "$@"
