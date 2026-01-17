#!/usr/bin/env python3
# Layer: L7 — Ops & Deployment
# Product: system-wide
# Temporal:
#   Trigger: scheduler, operator
#   Execution: async (CLI wrapper)
# Role: CLI tool for customer LLM integration health checks
# Callers: cron jobs, operators, CI/CD
# Allowed Imports: L4 (services), L6 (models, db)
# Forbidden Imports: L1, L2, L3
# Reference: docs/architecture/CUSTOMER_INTEGRATIONS_ARCHITECTURE.md

"""Customer Integration Health Check CLI

PURPOSE:
    Command-line tool for running health checks on customer LLM integrations.
    Can be run manually or scheduled via cron.

USAGE:
    # Check single integration
    python -m cli.cus_health_check --tenant <tenant_id> --integration <id>

    # Check all integrations for a tenant
    python -m cli.cus_health_check --tenant <tenant_id> --all

    # Check all stale integrations (not checked in 5+ minutes)
    python -m cli.cus_health_check --tenant <tenant_id> --stale

    # Get health summary
    python -m cli.cus_health_check --tenant <tenant_id> --summary

CRON EXAMPLE:
    # Check all stale integrations every 5 minutes
    */5 * * * * cd /app && python -m cli.cus_health_check --all-tenants --stale

OUTPUT:
    JSON format for easy parsing by monitoring systems.
    Exit code 0 on success, 1 on failures.
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlmodel import Session, select

# Setup path for imports
sys.path.insert(0, "/root/agenticverz2.0/backend")

from app.db import get_engine
from app.models.cus_models import CusIntegration
from app.services.cus_health_service import CusHealthService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""

    def default(self, o: Any) -> Any:
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


def json_output(data: Any) -> str:
    """Format data as JSON with datetime support."""
    return json.dumps(data, cls=DateTimeEncoder, indent=2)


async def check_single_integration(
    tenant_id: str,
    integration_id: str,
    force: bool = False,
) -> Dict[str, Any]:
    """Check health of a single integration.

    Args:
        tenant_id: Tenant ID
        integration_id: Integration ID
        force: Force check even if recently checked

    Returns:
        Health check result
    """
    service = CusHealthService()
    result = await service.check_health(
        tenant_id=tenant_id,
        integration_id=integration_id,
        force=force,
    )
    result["integration_id"] = integration_id
    return result


async def check_all_integrations(
    tenant_id: str,
    stale_only: bool = False,
    stale_threshold_minutes: int = 5,
) -> List[Dict[str, Any]]:
    """Check health of all integrations.

    Args:
        tenant_id: Tenant ID
        stale_only: Only check stale integrations
        stale_threshold_minutes: Threshold for stale check

    Returns:
        List of health check results
    """
    service = CusHealthService()

    if stale_only:
        return await service.check_all_integrations(
            tenant_id=tenant_id,
            stale_threshold_minutes=stale_threshold_minutes,
        )
    else:
        # Check all integrations
        engine = get_engine()
        with Session(engine) as session:
            integrations = list(
                session.exec(
                    select(CusIntegration).where(
                        CusIntegration.tenant_id == tenant_id,
                    )
                ).all()
            )

        results = []
        for integration in integrations:
            result = await service.check_health(
                tenant_id=tenant_id,
                integration_id=str(integration.id),
                force=True,
            )
            result["integration_id"] = str(integration.id)
            result["integration_name"] = integration.name
            results.append(result)
            await asyncio.sleep(0.5)  # Rate limiting

        return results


async def get_health_summary(tenant_id: str) -> Dict[str, Any]:
    """Get health summary for a tenant.

    Args:
        tenant_id: Tenant ID

    Returns:
        Health summary
    """
    service = CusHealthService()
    return await service.get_health_summary(tenant_id=tenant_id)


def get_all_tenant_ids() -> List[str]:
    """Get all tenant IDs with integrations.

    Returns:
        List of tenant IDs
    """
    engine = get_engine()
    with Session(engine) as session:
        # Get distinct tenant IDs
        result = session.exec(
            select(CusIntegration.tenant_id).distinct()
        )
        return [str(tid) for tid in result.all()]


async def check_all_tenants(
    stale_only: bool = False,
    stale_threshold_minutes: int = 5,
) -> Dict[str, List[Dict[str, Any]]]:
    """Check all integrations for all tenants.

    Args:
        stale_only: Only check stale integrations
        stale_threshold_minutes: Threshold for stale check

    Returns:
        Dict mapping tenant_id to list of results
    """
    tenant_ids = get_all_tenant_ids()
    results: Dict[str, List[Dict[str, Any]]] = {}

    for tenant_id in tenant_ids:
        tenant_results = await check_all_integrations(
            tenant_id=tenant_id,
            stale_only=stale_only,
            stale_threshold_minutes=stale_threshold_minutes,
        )
        results[tenant_id] = tenant_results

    return results


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for failures)
    """
    parser = argparse.ArgumentParser(
        description="Customer LLM Integration Health Check CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Tenant selection
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--tenant",
        "-t",
        type=str,
        help="Tenant ID to check",
    )
    group.add_argument(
        "--all-tenants",
        action="store_true",
        help="Check all tenants",
    )

    # Check type
    check_group = parser.add_mutually_exclusive_group()
    check_group.add_argument(
        "--integration",
        "-i",
        type=str,
        help="Single integration ID to check",
    )
    check_group.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Check all integrations",
    )
    check_group.add_argument(
        "--stale",
        "-s",
        action="store_true",
        help="Check only stale integrations (not checked recently)",
    )
    check_group.add_argument(
        "--summary",
        action="store_true",
        help="Get health summary only (no checks)",
    )

    # Options
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force check even if recently checked",
    )
    parser.add_argument(
        "--stale-threshold",
        type=int,
        default=5,
        help="Stale threshold in minutes (default: 5)",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only output JSON result, no logging",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    # Configure logging
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run the appropriate check
    try:
        if args.all_tenants:
            # Check all tenants
            results = asyncio.run(
                check_all_tenants(
                    stale_only=args.stale,
                    stale_threshold_minutes=args.stale_threshold,
                )
            )
            output = {
                "type": "all_tenants",
                "stale_only": args.stale,
                "results": results,
                "checked_at": datetime.now(timezone.utc),
            }

        elif args.summary:
            # Get summary for single tenant
            result = asyncio.run(get_health_summary(args.tenant))
            output = {
                "type": "summary",
                "tenant_id": args.tenant,
                "result": result,
            }

        elif args.integration:
            # Check single integration
            result = asyncio.run(
                check_single_integration(
                    tenant_id=args.tenant,
                    integration_id=args.integration,
                    force=args.force,
                )
            )
            output = {
                "type": "single",
                "tenant_id": args.tenant,
                "integration_id": args.integration,
                "result": result,
            }

        else:
            # Check all or stale integrations
            results = asyncio.run(
                check_all_integrations(
                    tenant_id=args.tenant,
                    stale_only=args.stale,
                    stale_threshold_minutes=args.stale_threshold,
                )
            )
            output = {
                "type": "batch",
                "tenant_id": args.tenant,
                "stale_only": args.stale,
                "count": len(results),
                "results": results,
                "checked_at": datetime.now(timezone.utc),
            }

        # Output results
        print(json_output(output))

        # Determine exit code based on health states
        has_failures = False

        if "results" in output:
            if isinstance(output["results"], dict):
                # All tenants mode
                for tenant_results in output["results"].values():
                    for r in tenant_results:
                        if r.get("health_state") and hasattr(
                            r["health_state"], "value"
                        ):
                            if r["health_state"].value == "unhealthy":
                                has_failures = True
                        elif r.get("health_state") == "unhealthy":
                            has_failures = True
            else:
                # List of results
                for r in output["results"]:
                    if r.get("health_state") and hasattr(r["health_state"], "value"):
                        if r["health_state"].value == "unhealthy":
                            has_failures = True
                    elif r.get("health_state") == "unhealthy":
                        has_failures = True
        elif "result" in output:
            r = output["result"]
            if r.get("overall_health") == "unhealthy":
                has_failures = True
            elif r.get("health_state"):
                if hasattr(r["health_state"], "value"):
                    if r["health_state"].value == "unhealthy":
                        has_failures = True
                elif r["health_state"] == "unhealthy":
                    has_failures = True

        return 1 if has_failures else 0

    except Exception as e:
        logger.exception(f"Health check failed: {e}")
        error_output = {
            "type": "error",
            "error": str(e),
            "checked_at": datetime.now(timezone.utc),
        }
        print(json_output(error_output), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
