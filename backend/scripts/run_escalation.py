#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Escalation Worker Script
# artifact_class: CODE
"""
Escalation Worker Script

Run this script periodically (e.g., every 30 seconds) via cron, systemd timer,
or as part of a scheduler like celery beat.

Usage:
    # Direct execution
    python scripts/run_escalation.py

    # Via cron (every minute)
    * * * * * cd /app && python scripts/run_escalation.py >> /var/log/aos/escalation.log 2>&1

    # Via systemd timer
    [Unit]
    Description=AOS Escalation Check

    [Timer]
    OnBootSec=60s
    OnUnitActiveSec=30s

    [Install]
    WantedBy=timers.target
"""

import os
import sys

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone


def main():
    """Run escalation check."""
    from app.hoc.api.cus.policies.policy import run_escalation_task

    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting escalation check...")

    try:
        escalated = run_escalation_task()
        print(f"[{datetime.now(timezone.utc).isoformat()}] Escalation check complete: {escalated} requests escalated")
        return 0
    except Exception as e:
        print(f"[{datetime.now(timezone.utc).isoformat()}] ERROR: Escalation check failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
