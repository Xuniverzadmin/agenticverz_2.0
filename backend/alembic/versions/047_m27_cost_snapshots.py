"""M27 Cost Snapshots - Deterministic Enforcement Barrier

Revision ID: 047_m27_snapshots
Revises: 046_m26_cost
Create Date: 2025-12-23

THE PROBLEM:
  Async cost ingestion races with synchronous anomaly detection.
  Result: Anomalies see stale/partial data → wrong severity → under-enforcement.

THE SOLUTION:
  Explicit snapshot barrier between ingestion and enforcement.

  cost_records (async, streaming)
         ↓
  cost_snapshots (explicit "complete" marker)
         ↓
  anomaly detection (reads only from complete snapshots)

DESIGN INVARIANTS:
  1. Anomaly detection NEVER reads from cost_records directly
  2. Snapshots have explicit status: pending → computing → complete
  3. Rolling baselines computed from historical snapshots (not live data)
  4. Version field enables idempotent recomputation

Tables:
  - cost_snapshots: Point-in-time snapshot definitions
  - cost_snapshot_aggregates: Per-entity aggregates within a snapshot
  - cost_snapshot_baselines: Rolling averages for anomaly thresholds
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers
revision = "047_m27_snapshots"
down_revision = "046_m26_cost"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create M27 cost snapshot tables."""

    # ==========================================================================
    # 1. cost_snapshots - Point-in-time snapshot definitions
    # ==========================================================================
    # This is the CRITICAL barrier between async ingestion and enforcement.
    # A snapshot is only valid for anomaly detection when status = 'complete'.
    op.create_table(
        "cost_snapshots",
        # Identity
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        # Snapshot period
        sa.Column("snapshot_type", sa.String(16), nullable=False),  # 'hourly', 'daily'
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        # Status machine: pending → computing → complete (or failed)
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        # Computation metadata
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("records_processed", sa.Integer(), nullable=True),
        sa.Column("computation_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        # Prevent duplicate snapshots for same period
        sa.UniqueConstraint("tenant_id", "snapshot_type", "period_start", name="uq_cost_snapshots_tenant_type_period"),
    )
    # Index for finding latest complete snapshot
    op.create_index("ix_cost_snapshots_tenant_status", "cost_snapshots", ["tenant_id", "status", "period_end"])
    # Index for time-range queries
    op.create_index("ix_cost_snapshots_period", "cost_snapshots", ["tenant_id", "period_start", "period_end"])

    # ==========================================================================
    # 2. cost_snapshot_aggregates - Per-entity aggregates within a snapshot
    # ==========================================================================
    # Aggregated at multiple levels: tenant, user, feature, model
    # Anomaly detection reads ONLY from this table via complete snapshots.
    op.create_table(
        "cost_snapshot_aggregates",
        # Identity
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "snapshot_id",
            sa.String(64),
            sa.ForeignKey("cost_snapshots.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        # Entity being aggregated
        sa.Column("entity_type", sa.String(16), nullable=False),  # 'tenant', 'user', 'feature', 'model'
        sa.Column("entity_id", sa.String(128), nullable=True),  # null for tenant-level
        # Core metrics
        sa.Column("total_cost_cents", sa.Float(), nullable=False, server_default="0"),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_input_tokens", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("total_output_tokens", sa.BigInteger(), nullable=False, server_default="0"),
        # Derived metrics (for quick access)
        sa.Column("avg_cost_per_request_cents", sa.Float(), nullable=True),
        sa.Column("avg_tokens_per_request", sa.Float(), nullable=True),
        # Comparison to baselines (populated during snapshot computation)
        sa.Column("baseline_7d_avg_cents", sa.Float(), nullable=True),
        sa.Column("baseline_30d_avg_cents", sa.Float(), nullable=True),
        sa.Column("deviation_from_7d_pct", sa.Float(), nullable=True),
        sa.Column("deviation_from_30d_pct", sa.Float(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        # Composite unique constraint
        sa.UniqueConstraint("snapshot_id", "entity_type", "entity_id", name="uq_cost_snapshot_agg_entity"),
    )
    # Index for entity lookups
    op.create_index(
        "ix_cost_snapshot_agg_entity", "cost_snapshot_aggregates", ["tenant_id", "entity_type", "entity_id"]
    )
    # Index for deviation queries (find anomalies)
    op.create_index(
        "ix_cost_snapshot_agg_deviation", "cost_snapshot_aggregates", ["tenant_id", "deviation_from_7d_pct"]
    )

    # ==========================================================================
    # 3. cost_snapshot_baselines - Rolling averages for anomaly thresholds
    # ==========================================================================
    # Pre-computed baselines that anomaly detection uses for comparison.
    # Updated after each daily snapshot completes.
    op.create_table(
        "cost_snapshot_baselines",
        # Identity
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        # Entity being baselined
        sa.Column("entity_type", sa.String(16), nullable=False),  # 'tenant', 'user', 'feature', 'model'
        sa.Column("entity_id", sa.String(128), nullable=True),
        # Baseline values
        sa.Column("avg_daily_cost_cents", sa.Float(), nullable=False),
        sa.Column("stddev_daily_cost_cents", sa.Float(), nullable=True),
        sa.Column("avg_daily_requests", sa.Float(), nullable=False),
        sa.Column("max_daily_cost_cents", sa.Float(), nullable=True),
        sa.Column("min_daily_cost_cents", sa.Float(), nullable=True),
        # Baseline computation window
        sa.Column("window_days", sa.Integer(), nullable=False),  # 7 or 30
        sa.Column("samples_count", sa.Integer(), nullable=False),  # How many days of data
        # Validity period
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="true"),
        # Source tracking
        sa.Column("last_snapshot_id", sa.String(64), nullable=True),
        # Composite unique constraint for current baseline per entity
        sa.UniqueConstraint(
            "tenant_id", "entity_type", "entity_id", "window_days", "is_current", name="uq_cost_baselines_current"
        ),
    )
    # Index for finding current baselines
    op.create_index(
        "ix_cost_baselines_current", "cost_snapshot_baselines", ["tenant_id", "entity_type", "entity_id", "is_current"]
    )

    # ==========================================================================
    # 4. cost_anomaly_evaluations - Audit trail for anomaly checks
    # ==========================================================================
    # Records each anomaly evaluation with snapshot reference.
    # Enables replay and debugging of "why did/didn't this trigger?"
    op.create_table(
        "cost_anomaly_evaluations",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        sa.Column(
            "snapshot_id",
            sa.String(64),
            sa.ForeignKey("cost_snapshots.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        # What was evaluated
        sa.Column("entity_type", sa.String(16), nullable=False),
        sa.Column("entity_id", sa.String(128), nullable=True),
        # Evaluation inputs (frozen at evaluation time)
        sa.Column("current_value_cents", sa.Float(), nullable=False),
        sa.Column("baseline_value_cents", sa.Float(), nullable=False),
        sa.Column("threshold_pct", sa.Float(), nullable=False),
        sa.Column("deviation_pct", sa.Float(), nullable=False),
        # Evaluation output
        sa.Column("triggered", sa.Boolean(), nullable=False),
        sa.Column("severity_computed", sa.String(16), nullable=True),  # If triggered
        sa.Column("anomaly_id", sa.String(64), nullable=True),  # If anomaly was created
        # Why (for debugging)
        sa.Column("evaluation_reason", sa.Text(), nullable=True),
        # Timestamps
        sa.Column("evaluated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_cost_eval_tenant_time", "cost_anomaly_evaluations", ["tenant_id", "evaluated_at"])
    op.create_index("ix_cost_eval_snapshot", "cost_anomaly_evaluations", ["snapshot_id", "triggered"])

    # ==========================================================================
    # 5. Add snapshot_id reference to existing cost_anomalies table
    # ==========================================================================
    # Link anomalies back to the snapshot that triggered them
    op.add_column("cost_anomalies", sa.Column("snapshot_id", sa.String(64), nullable=True))
    op.create_index("ix_cost_anomalies_snapshot", "cost_anomalies", ["snapshot_id"])

    # Also add baseline_source for traceability
    op.add_column("cost_anomalies", sa.Column("baseline_id", sa.String(64), nullable=True))


def downgrade() -> None:
    """Drop M27 cost snapshot tables."""
    # Remove columns from cost_anomalies
    op.drop_index("ix_cost_anomalies_snapshot", "cost_anomalies")
    op.drop_column("cost_anomalies", "snapshot_id")
    op.drop_column("cost_anomalies", "baseline_id")

    # Drop new tables
    op.drop_table("cost_anomaly_evaluations")
    op.drop_table("cost_snapshot_baselines")
    op.drop_table("cost_snapshot_aggregates")
    op.drop_table("cost_snapshots")
