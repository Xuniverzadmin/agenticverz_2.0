#!/bin/bash
# Load all service credentials into environment
# Usage: source /root/agenticverz2.0/secrets/load_all.sh

SECRETS_DIR="$(dirname "$0")"

for f in "$SECRETS_DIR"/*.env; do
    if [ -f "$f" ]; then
        echo "Loading: $(basename "$f")"
        set -a
        source "$f"
        set +a
    fi
done

echo ""
echo "Loaded credentials for:"
echo "  - Neon PostgreSQL"
echo "  - Clerk Auth"
echo "  - OpenAI (Embeddings)"
echo "  - Resend Email"
echo "  - PostHog Analytics"
echo "  - Trigger.dev Jobs"
echo "  - Cloudflare Workers"
echo ""
echo "Verify with: env | grep -E 'NEON|CLERK|RESEND|POSTHOG|TRIGGER|CLOUDFLARE|OPENAI|EMBEDDING'"
