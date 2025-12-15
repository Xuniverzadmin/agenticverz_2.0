# CLI commands for Business Builder Worker
"""
Usage:
    # Run worker
    python -m app.workers.business_builder.cli build-business "AI tool for podcasters" \
        --brand brand.json \
        --budget 3000 \
        --strict

    # Replay previous execution
    python -m app.workers.business_builder.cli replay token.json

    # Inspect execution
    python -m app.workers.business_builder.cli inspect <run-id> --failures
    python -m app.workers.business_builder.cli inspect <run-id> --policy
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import click

from .worker import BusinessBuilderWorker, WorkerResult, replay
from .schemas.brand import BrandSchema, create_minimal_brand, ToneLevel


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
def build_business(
    task: str,
    brand: Optional[str],
    budget: Optional[int],
    strict: bool,
    depth: str,
    output: str,
    json_output: bool,
):
    """
    Build a complete launch package from an idea.

    Examples:
        # Basic usage
        python -m app.workers.business_builder.cli build-business "AI tool for podcasters"

        # With brand constraints
        python -m app.workers.business_builder.cli build-business "SaaS for developers" \\
            --brand my_brand.json --budget 5000 --strict

        # Output as JSON
        python -m app.workers.business_builder.cli build-business "E-commerce platform" --json-output
    """
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
    result = asyncio.run(worker.run(
        task=task,
        brand=brand_schema,
        budget=budget,
        strict_mode=strict,
        depth=depth,
    ))

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
        click.echo(json.dumps({
            "success": result.success,
            "error": result.error,
        }, indent=2))
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
def inspect_cmd(
    run_id: str,
    failures: bool,
    policy: bool,
    routing: bool,
):
    """
    Inspect details of a run.

    Examples:
        python -m app.workers.business_builder.cli inspect plan_abc123 --failures
        python -m app.workers.business_builder.cli inspect plan_abc123 --policy
        python -m app.workers.business_builder.cli inspect plan_abc123 --routing
    """
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


@cli.command("create-brand")
@click.argument("output_file", type=click.Path())
@click.option("--name", prompt="Company name", help="Company/product name")
@click.option("--mission", prompt="Mission statement", help="Mission statement")
@click.option("--value-prop", prompt="Value proposition", help="Value proposition")
@click.option("--tone", type=click.Choice(["casual", "neutral", "professional", "formal", "luxury"]), default="professional")
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
