#!/usr/bin/env bash
# Run NOVA worker pool locally (for development)
set -euo pipefail

export DATABASE_URL=${DATABASE_URL:-postgresql://nova:novapass@localhost:5433/nova_aos}
export WORKER_CONCURRENCY=${WORKER_CONCURRENCY:-2}
export WORKER_POLL_INTERVAL=${WORKER_POLL_INTERVAL:-2.0}
export RUN_MAX_ATTEMPTS=${RUN_MAX_ATTEMPTS:-5}
export EVENT_PUBLISHER=${EVENT_PUBLISHER:-logging}

echo "Starting NOVA Worker Pool..."
echo "  DATABASE_URL: ${DATABASE_URL}"
echo "  WORKER_CONCURRENCY: ${WORKER_CONCURRENCY}"
echo "  WORKER_POLL_INTERVAL: ${WORKER_POLL_INTERVAL}"
echo "  EVENT_PUBLISHER: ${EVENT_PUBLISHER}"

cd "$(dirname "$0")/../backend"
python -m app.worker.pool
