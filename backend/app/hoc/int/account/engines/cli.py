# capability_id: CAP-012
# Layer: L4 — Engine
# AUDIENCE: CUSTOMER
# Role: Business builder CLI
# Product: product-builder
# Temporal:
#   Trigger: user (CLI)
#   Execution: sync
# Callers: shell
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: Business Builder

# CLI commands for Business Builder Worker

"""
Usage:
    # Run worker locally
    python -m app.workers.business_builder.cli build-business "AI tool for podcasters" \
        --brand brand.json \
        --budget 3000 \
        --strict

    # Run worker via hosted API
    python -m app.workers.business_builder.cli build-business "AI tool for podcasters" \
        --api https://api.agenticverz.com \
        --api-key AGZ_live_xxx

    # Replay previous execution
    python -m app.workers.business_builder.cli replay token.json

    # Inspect execution
    python -m app.workers.business_builder.cli inspect <run-id> --failures
    python -m app.workers.business_builder.cli inspect <run-id> --policy

Environment variables:
    AGENTICVERZ_API_URL - Default API URL
    AGENTICVERZ_API_KEY - Default API key
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Optional

import click

# Optional httpx for API mode
try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

from .schemas.brand import BrandSchema, ToneLevel, create_minimal_brand
from .worker import BusinessBuilderWorker, WorkerResult, replay

# =============================================================================
# API Client Functions
# =============================================================================


def _get_api_client(api_url: str, api_key: str) -> "httpx.Client":
    """Get an HTTP client configured for the API."""
    if not HAS_HTTPX:
        raise click.ClickException("httpx is required for API mode. Install with: pip install httpx")
    return httpx.Client(
        base_url=api_url.rstrip("/"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        timeout=300.0,  # 5 minutes for long-running workers
    )


def _run_via_api(
    api_url: str,
    api_key: str,
    task: str,
    brand_data: Optional[dict],
    budget: Optional[int],
    strict: bool,
    depth: str,
    async_mode: bool,
) -> dict:
    """Execute worker via API."""
    client = _get_api_client(api_url, api_key)

    payload = {
        "task": task,
        "budget": budget,
        "strict_mode": strict,
        "depth": depth,
        "async_mode": async_mode,
    }
    if brand_data:
        payload["brand"] = brand_data

    try:
        response = client.post(
            "/workers/business-builder/run",
            json=payload,
        )
        response.raise_for_status()
        result = response.json()

        # If async, poll for completion
        if async_mode and result.get("status") == "queued":
            run_id = result["run_id"]
            click.echo(f"Run queued: {run_id}")
            click.echo("Polling for completion...")

            for _ in range(120):  # Max 10 minutes
                time.sleep(5)
                poll_response = client.get(f"/workers/business-builder/runs/{run_id}")
                poll_response.raise_for_status()
                result = poll_response.json()

                status = result.get("status", "unknown")
                if status in ("completed", "failed"):
                    break
                click.echo(f"  Status: {status}...")

        return result

    except httpx.HTTPStatusError as e:
        raise click.ClickException(f"API error: {e.response.status_code} - {e.response.text}")
    finally:
        client.close()


def _replay_via_api(api_url: str, api_key: str, token: dict) -> dict:
    """Replay execution via API."""
    client = _get_api_client(api_url, api_key)

    try:
        response = client.post(
            "/workers/business-builder/replay",
            json={"replay_token": token},
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise click.ClickException(f"API error: {e.response.status_code} - {e.response.text}")
    finally:
        client.close()


def _inspect_via_api(api_url: str, api_key: str, run_id: str) -> dict:
    """Get run details via API."""
    client = _get_api_client(api_url, api_key)

    try:
        response = client.get(f"/workers/business-builder/runs/{run_id}")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise click.ClickException(f"API error: {e.response.status_code} - {e.response.text}")
    finally:
        client.close()


def _list_runs_via_api(api_url: str, api_key: str, limit: int) -> dict:
    """List runs via API."""
    client = _get_api_client(api_url, api_key)

    try:
        response = client.get(
            "/workers/business-builder/runs",
            params={"limit": limit},
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise click.ClickException(f"API error: {e.response.status_code} - {e.response.text}")
    finally:
        client.close()


@click.group()
def cli():
    """Business Builder Worker CLI."""
    pass


@cli.command("build-business")
@click.argument("task")
@click.option("--brand", "-b", type=click.Path(exists=True), help="Brand JSON file")
@click.option("--budget", type=int, default=None, help="Token budget limit")
@click.option("--strict/--no-strict", default=False, help="Strict policy mode")
@click.option("--depth", type=click.Choice(["auto", "shallow", "deep"]), default="auto")
@click.option("--output", "-o", type=click.Path(), default="./launch_bundle", help="Output directory")
@click.option("--json-output/--no-json-output", default=False, help="Output as JSON")
@click.option("--api", envvar="AGENTICVERZ_API_URL", help="API URL (enables remote mode)")
@click.option("--api-key", envvar="AGENTICVERZ_API_KEY", help="API key for authentication")
@click.option("--async/--sync", "async_mode", default=False, help="Run async (poll for result)")
def build_business(
    task: str,
    brand: Optional[str],
    budget: Optional[int],
    strict: bool,
    depth: str,
    output: str,
    json_output: bool,
    api: Optional[str],
    api_key: Optional[str],
    async_mode: bool,
):
    """
    Build a complete launch package from an idea.

    Examples:
        # Local execution
        python -m app.workers.business_builder.cli build-business "AI tool for podcasters"

        # With brand constraints
        python -m app.workers.business_builder.cli build-business "SaaS for developers" \\
            --brand my_brand.json --budget 5000 --strict

        # Via hosted API
        python -m app.workers.business_builder.cli build-business "E-commerce platform" \\
            --api https://api.agenticverz.com --api-key AGZ_live_xxx

        # Output as JSON
        python -m app.workers.business_builder.cli build-business "E-commerce platform" --json-output
    """
    # API mode
    if api:
        if not api_key:
            raise click.ClickException("API key required. Use --api-key or set AGENTICVERZ_API_KEY")

        click.echo(f"Connecting to API: {api}")

        # Load brand data for API
        brand_data = None
        if brand:
            with open(brand, "r") as f:
                brand_data = json.load(f)

        result = _run_via_api(
            api_url=api,
            api_key=api_key,
            task=task,
            brand_data=brand_data,
            budget=budget,
            strict=strict,
            depth=depth,
            async_mode=async_mode,
        )

        if json_output:
            click.echo(json.dumps(result, indent=2))
        else:
            _print_api_result(result, output)
        return

    # Local mode
    # Load brand
    brand_schema = None
    if brand:
        brand_schema = BrandSchema.from_file(brand)
    else:
        # Create minimal brand from task
        brand_schema = create_minimal_brand(
            company_name=task.split()[0].title() + " Co",
            mission=f"To revolutionize {task} through innovation",
            value_proposition=f"The simplest way to achieve {task}",
            tone=ToneLevel.PROFESSIONAL,
        )

    # Run worker
    worker = BusinessBuilderWorker()
    result = asyncio.run(
        worker.run(
            task=task,
            brand=brand_schema,
            budget=budget,
            strict_mode=strict,
            depth=depth,
        )
    )

    # Output
    if json_output:
        output_data = {
            "success": result.success,
            "error": result.error,
            "artifacts": list(result.artifacts.keys()),
            "replay_token": result.replay_token,
            "cost_report": result.cost_report,
            "policy_violations": result.policy_violations,
            "recovery_log": result.recovery_log,
            "drift_metrics": result.drift_metrics,
            "total_tokens": result.total_tokens_used,
            "latency_ms": result.total_latency_ms,
        }
        click.echo(json.dumps(output_data, indent=2))
    else:
        _print_result(result, output)


def _print_api_result(result: dict, output_dir: str):
    """Print formatted API result to console."""
    click.echo("")
    if result.get("success"):
        click.secho("BUILD SUCCESSFUL", fg="green", bold=True)
    else:
        click.secho(f"BUILD FAILED: {result.get('error', 'Unknown error')}", fg="red", bold=True)

    click.echo("")
    click.echo("=== Execution Summary ===")
    click.echo(f"Run ID: {result.get('run_id', 'N/A')}")
    click.echo(f"Status: {result.get('status', 'N/A')}")
    click.echo(f"Total tokens: {result.get('total_tokens_used', 0)}")
    click.echo(f"Latency: {result.get('total_latency_ms', 0):.0f}ms")

    traces = result.get("execution_trace", [])
    click.echo(f"Stages completed: {len(traces)}")

    violations = result.get("policy_violations", [])
    if violations:
        click.echo("")
        click.secho(f"Policy Violations: {len(violations)}", fg="yellow")
        for v in violations[:3]:
            click.echo(f"  - {v.get('policy', 'unknown')}: {v.get('reason', '')}")

    recoveries = result.get("recovery_log", [])
    if recoveries:
        click.echo("")
        click.secho(f"Recoveries Applied: {len(recoveries)}", fg="cyan")
        for r in recoveries:
            click.echo(f"  - Stage {r.get('stage', '')}: {r.get('recovery', '')}")

    drift = result.get("drift_metrics", {})
    if drift:
        click.echo("")
        click.echo("Drift Scores:")
        for stage, score in drift.items():
            color = "green" if score < 0.2 else "yellow" if score < 0.35 else "red"
            click.secho(f"  - {stage}: {score:.2f}", fg=color)

    artifacts = result.get("artifacts", {})
    if artifacts:
        click.echo("")
        click.echo("=== Artifacts ===")
        for name in sorted(artifacts.keys()):
            click.echo(f"  - {name}")

    replay_token = result.get("replay_token")
    if replay_token:
        click.echo("")
        click.echo("=== Replay Token ===")
        click.echo(f"  Plan ID: {replay_token.get('plan_id', 'N/A')}")
        click.echo(f"  Seed: {replay_token.get('seed', 'N/A')}")

    # Save outputs
    if result.get("success"):
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save replay token
        if replay_token:
            token_path = output_path / "replay_token.json"
            with open(token_path, "w") as f:
                json.dump(replay_token, f, indent=2)
            click.echo(f"\nReplay token saved: {token_path}")

        # Save cost report
        cost_report = result.get("cost_report")
        if cost_report:
            cost_path = output_path / "cost_report.json"
            with open(cost_path, "w") as f:
                json.dump(cost_report, f, indent=2)
            click.echo(f"Cost report saved: {cost_path}")

        # Save full result
        full_path = output_path / "result.json"
        with open(full_path, "w") as f:
            json.dump(result, f, indent=2)
        click.echo(f"Full result saved: {full_path}")

        click.echo(f"\nOutput directory: {output_path}")


def _print_result(result: WorkerResult, output_dir: str):
    """Print formatted result to console."""
    click.echo("")
    if result.success:
        click.secho("BUILD SUCCESSFUL", fg="green", bold=True)
    else:
        click.secho(f"BUILD FAILED: {result.error}", fg="red", bold=True)

    click.echo("")
    click.echo("=== Execution Summary ===")
    click.echo(f"Total tokens: {result.total_tokens_used}")
    click.echo(f"Latency: {result.total_latency_ms:.0f}ms")
    click.echo(f"Stages completed: {len(result.execution_trace)}")

    if result.policy_violations:
        click.echo("")
        click.secho(f"Policy Violations: {len(result.policy_violations)}", fg="yellow")
        for v in result.policy_violations[:3]:
            click.echo(f"  - {v.get('policy', 'unknown')}: {v.get('reason', '')}")

    if result.recovery_log:
        click.echo("")
        click.secho(f"Recoveries Applied: {len(result.recovery_log)}", fg="cyan")
        for r in result.recovery_log:
            click.echo(f"  - Stage {r.get('stage', '')}: {r.get('recovery', '')}")

    if result.drift_metrics:
        click.echo("")
        click.echo("Drift Scores:")
        for stage, score in result.drift_metrics.items():
            color = "green" if score < 0.2 else "yellow" if score < 0.35 else "red"
            click.secho(f"  - {stage}: {score:.2f}", fg=color)

    if result.artifacts:
        click.echo("")
        click.echo("=== Artifacts ===")
        for name in sorted(result.artifacts.keys()):
            click.echo(f"  - {name}")

    if result.replay_token:
        click.echo("")
        click.echo("=== Replay Token ===")
        click.echo(f"  Plan ID: {result.replay_token.get('plan_id', 'N/A')}")
        click.echo(f"  Seed: {result.replay_token.get('seed', 'N/A')}")

    # Save outputs
    if result.success:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save replay token
        token_path = output_path / "replay_token.json"
        with open(token_path, "w") as f:
            json.dump(result.replay_token, f, indent=2)
        click.echo(f"\nReplay token saved: {token_path}")

        # Save cost report
        if result.cost_report:
            cost_path = output_path / "cost_report.json"
            with open(cost_path, "w") as f:
                json.dump(result.cost_report, f, indent=2)
            click.echo(f"Cost report saved: {cost_path}")

        click.echo(f"\nOutput directory: {output_path}")


@cli.command("replay")
@click.argument("token_file", type=click.Path(exists=True))
@click.option("--json-output/--no-json-output", default=False)
def replay_cmd(token_file: str, json_output: bool):
    """
    Replay a previous execution (Golden Replay - M4).

    The replay will produce identical outputs given the same seed.

    Example:
        python -m app.workers.business_builder.cli replay ./launch_bundle/replay_token.json
    """
    with open(token_file, "r") as f:
        token = json.load(f)

    click.echo(f"Replaying execution: {token.get('plan_id', 'unknown')}")
    click.echo(f"Seed: {token.get('seed', 'N/A')}")

    result = asyncio.run(replay(token))

    if json_output:
        click.echo(
            json.dumps(
                {
                    "success": result.success,
                    "error": result.error,
                },
                indent=2,
            )
        )
    else:
        if result.success:
            click.secho("REPLAY SUCCESSFUL", fg="green", bold=True)
        else:
            click.secho(f"REPLAY FAILED: {result.error}", fg="red")


@cli.command("trace")
@click.argument("run_id")
def trace_cmd(run_id: str):
    """
    View execution trace for a run.

    Example:
        python -m app.workers.business_builder.cli trace plan_abc123
    """
    click.echo(f"Trace for run: {run_id}")
    click.echo("(Would fetch from database)")


@cli.command("inspect")
@click.argument("run_id")
@click.option("--failures", is_flag=True, help="Show failure patterns")
@click.option("--policy", is_flag=True, help="Show policy violations")
@click.option("--routing", is_flag=True, help="Show routing decisions")
@click.option("--api", envvar="AGENTICVERZ_API_URL", help="API URL")
@click.option("--api-key", envvar="AGENTICVERZ_API_KEY", help="API key")
@click.option("--json-output/--no-json-output", default=False, help="Output as JSON")
def inspect_cmd(
    run_id: str,
    failures: bool,
    policy: bool,
    routing: bool,
    api: Optional[str],
    api_key: Optional[str],
    json_output: bool,
):
    """
    Inspect details of a run.

    Examples:
        # Via API
        python -m app.workers.business_builder.cli inspect abc123 \\
            --api https://api.agenticverz.com --api-key AGZ_live_xxx

        # Show specific details
        python -m app.workers.business_builder.cli inspect abc123 --failures --api ...
        python -m app.workers.business_builder.cli inspect abc123 --policy --api ...
        python -m app.workers.business_builder.cli inspect abc123 --routing --api ...
    """
    # API mode
    if api:
        if not api_key:
            raise click.ClickException("API key required")

        result = _inspect_via_api(api, api_key, run_id)

        if json_output:
            click.echo(json.dumps(result, indent=2))
            return

        click.echo(f"Run ID: {result.get('run_id')}")
        click.echo(f"Status: {result.get('status')}")
        click.echo(f"Success: {result.get('success')}")

        if failures:
            click.echo("\n=== Failure Patterns (M9) ===")
            recovery_log = result.get("recovery_log", [])
            if recovery_log:
                for r in recovery_log:
                    click.echo(f"  - Stage {r.get('stage')}: {r.get('recovery')}")
            else:
                click.echo("  No failures recorded")

        if policy:
            click.echo("\n=== Policy Violations (M19) ===")
            violations = result.get("policy_violations", [])
            if violations:
                for v in violations:
                    click.echo(f"  - {v.get('policy')}: {v.get('reason')}")
            else:
                click.echo("  No violations")

        if routing:
            click.echo("\n=== Routing Decisions (M17) ===")
            routing_decisions = result.get("routing_decisions", [])
            if routing_decisions:
                for r in routing_decisions:
                    click.echo(f"  - {r}")
            else:
                click.echo("  No routing decisions recorded")

        if not any([failures, policy, routing]):
            click.echo("\nUse --failures, --policy, or --routing to view details")
        return

    # Local mode (placeholder)
    click.echo(f"Inspecting run: {run_id}")

    if failures:
        click.echo("\n=== Failure Patterns (M9) ===")
        click.echo("(Would show matched failure patterns)")

    if policy:
        click.echo("\n=== Policy Violations (M19) ===")
        click.echo("(Would show policy violations)")

    if routing:
        click.echo("\n=== Routing Decisions (M17) ===")
        click.echo("(Would show CARE routing decisions)")

    if not any([failures, policy, routing]):
        click.echo("Use --failures, --policy, or --routing to view details")


@cli.command("list-runs")
@click.option("--limit", "-n", type=int, default=20, help="Number of runs to show")
@click.option("--api", envvar="AGENTICVERZ_API_URL", help="API URL", required=True)
@click.option("--api-key", envvar="AGENTICVERZ_API_KEY", help="API key", required=True)
@click.option("--json-output/--no-json-output", default=False, help="Output as JSON")
def list_runs_cmd(
    limit: int,
    api: str,
    api_key: str,
    json_output: bool,
):
    """
    List recent worker runs.

    Example:
        python -m app.workers.business_builder.cli list-runs \\
            --api https://api.agenticverz.com --api-key AGZ_live_xxx
    """
    result = _list_runs_via_api(api, api_key, limit)

    if json_output:
        click.echo(json.dumps(result, indent=2))
        return

    runs = result.get("runs", [])
    click.echo(f"Recent runs ({len(runs)} of {result.get('total', 0)}):")
    click.echo("")

    for run in runs:
        status_color = "green" if run.get("success") else "red" if run.get("success") is False else "yellow"
        click.echo(f"  {run.get('run_id', 'N/A')[:8]}...")
        click.secho(f"    Status: {run.get('status', 'unknown')}", fg=status_color)
        click.echo(f"    Task: {run.get('task', 'N/A')[:50]}...")
        click.echo(f"    Created: {run.get('created_at', 'N/A')}")
        latency = run.get("total_latency_ms")
        if latency:
            click.echo(f"    Latency: {latency:.0f}ms")
        click.echo("")


@cli.command("create-brand")
@click.argument("output_file", type=click.Path())
@click.option("--name", prompt="Company name", help="Company/product name")
@click.option("--mission", prompt="Mission statement", help="Mission statement")
@click.option("--value-prop", prompt="Value proposition", help="Value proposition")
@click.option(
    "--tone", type=click.Choice(["casual", "neutral", "professional", "formal", "luxury"]), default="professional"
)
def create_brand_cmd(
    output_file: str,
    name: str,
    mission: str,
    value_prop: str,
    tone: str,
):
    """
    Create a brand.json file interactively.

    Example:
        python -m app.workers.business_builder.cli create-brand brand.json
    """
    brand = create_minimal_brand(
        company_name=name,
        mission=mission,
        value_proposition=value_prop,
        tone=ToneLevel(tone),
    )

    brand.to_file(output_file)
    click.secho(f"Brand file created: {output_file}", fg="green")


if __name__ == "__main__":
    cli()
