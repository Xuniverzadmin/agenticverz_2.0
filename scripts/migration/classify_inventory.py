#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Classify Migration Inventory - Iteration 1
# artifact_class: CODE
"""
Classify Migration Inventory - Iteration 1

This script performs automated classification of files based on:
1. Directory patterns (audience detection)
2. Filename patterns (layer detection)
3. Content patterns (domain detection)

Reference: docs/architecture/migration/PHASE1_MIGRATION_PLAN.md
"""

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Classification:
    """Classification result for a file."""
    audience: str
    domain: str
    layer: str
    target_path: str
    action: str
    notes: str
    confidence: str  # HIGH, MEDIUM, LOW


# Audience patterns by directory
# NOTE: No "SHARED" audience - everything must be CUSTOMER, FOUNDER, or INTERNAL
AUDIENCE_PATTERNS = [
    # Already in app/hoc/ structure
    (r"^app/hoc/cus/", "CUSTOMER"),
    (r"^app/hoc/fdr/", "FOUNDER"),
    (r"^app/hoc/int/", "INTERNAL"),
    (r"^app/hoc/duplicate/", "DEPRECATED"),  # Mark for deletion
    (r"^app/hoc/__init__\.py$", "INTERNAL"),  # HOC root init

    # API routes - detect audience from path or filename
    (r"^app/api/founder", "FOUNDER"),
    (r"^app/api/internal", "INTERNAL"),
    (r"^app/api/customer", "CUSTOMER"),
    (r"^app/api/ops", "FOUNDER"),  # ops = founder
    (r"^app/api/debug/", "INTERNAL"),  # Debug APIs internal
    (r"^app/api/middleware/", "INTERNAL"),  # Middleware is internal
    (r"^app/api/dependencies/", "INTERNAL"),  # Dependencies are internal
    (r"^app/api/limits/", "CUSTOMER"),  # Limits API customer-facing
    (r"^app/api/", "CUSTOMER"),  # Default API routes are customer

    # Adapters - external service adapters → CUSTOMER/integrations
    (r"^app/adapters/", "CUSTOMER"),

    # Models stay in app/ - L7 (audience doesn't matter for STAYS)
    (r"^app/cus/models/", "CUSTOMER"),
    (r"^app/fdr/models/", "FOUNDER"),
    (r"^app/int/models/", "INTERNAL"),
    (r"^app/models/", "INTERNAL"),  # Shared models → INTERNAL (but they STAY)

    # Infrastructure (internal platform)
    (r"^app/auth/", "INTERNAL"),
    (r"^app/auth\.py$", "INTERNAL"),
    (r"^app/core/", "INTERNAL"),
    (r"^app/events/", "INTERNAL"),
    (r"^app/middleware/", "INTERNAL"),
    (r"^app/infra/", "INTERNAL"),
    (r"^app/startup/", "INTERNAL"),
    (r"^app/storage/", "INTERNAL"),
    (r"^app/stores/", "INTERNAL"),
    (r"^app/secrets/", "INTERNAL"),
    (r"^app/security/", "INTERNAL"),

    # Worker/jobs - internal infrastructure
    (r"^app/worker/", "INTERNAL"),
    (r"^app/workers/", "INTERNAL"),
    (r"^app/jobs/", "INTERNAL"),
    (r"^app/tasks/", "INTERNAL"),

    # Domain-specific (customer unless labeled otherwise)
    (r"^app/policy/", "CUSTOMER"),
    (r"^app/governance/", "CUSTOMER"),
    (r"^app/billing/", "CUSTOMER"),
    (r"^app/traces/", "CUSTOMER"),
    (r"^app/evidence/", "CUSTOMER"),
    (r"^app/discovery/", "CUSTOMER"),

    # Services - default to customer unless labeled
    (r"^app/services/ops", "FOUNDER"),
    (r"^app/services/founder", "FOUNDER"),
    (r"^app/services/internal", "INTERNAL"),
    (r"^app/services/", "CUSTOMER"),  # Default services are customer

    # Skills/agents - INTERNAL/agent
    (r"^app/skills/", "INTERNAL"),
    (r"^app/agents/", "INTERNAL"),

    # INTERNAL platform infrastructure
    (r"^app/workflow/", "INTERNAL"),
    (r"^app/memory/", "INTERNAL"),
    (r"^app/routing/", "INTERNAL"),
    (r"^app/observability/", "INTERNAL"),
    (r"^app/runtime/", "INTERNAL"),
    (r"^app/learning/", "INTERNAL"),
    (r"^app/planner", "INTERNAL"),
    (r"^app/domain/", "INTERNAL"),
    (r"^app/config/", "INTERNAL"),
    (r"^app/errors/", "INTERNAL"),
    (r"^app/runtime_projections/", "INTERNAL"),

    # CUSTOMER-facing features
    (r"^app/utils/", "CUSTOMER"),  # → customer/general
    (r"^app/contracts/", "CUSTOMER"),  # → customer/general
    (r"^app/costsim/", "CUSTOMER"),  # → customer/analytics
    (r"^app/integrations/", "CUSTOMER"),  # → customer/integrations
    (r"^app/dsl/", "CUSTOMER"),  # → customer/policies
    (r"^app/optimization/", "CUSTOMER"),  # → customer/analytics
    (r"^app/protection/", "CUSTOMER"),  # → customer/policies
    (r"^app/commands/", "CUSTOMER"),  # → customer/policies
    (r"^app/predictions/", "CUSTOMER"),

    # Schemas - distribute by content, default CUSTOMER
    (r"^app/schemas/", "CUSTOMER"),
    (r"^app/specs/", "CUSTOMER"),

    # FOUNDER
    (r"^app/quarantine/", "FOUNDER"),  # → founder/ops

    # Root-level files → INTERNAL platform
    (r"^app/[^/]+\.py$", "INTERNAL"),
]

# Domain patterns by directory/filename
DOMAIN_PATTERNS = [
    # Explicit domain directories in hoc
    (r"/overview/", "overview"),
    (r"/activity/", "activity"),
    (r"/incidents/", "incidents"),
    (r"/policies/", "policies"),
    (r"/logs/", "logs"),
    (r"/analytics/", "analytics"),
    (r"/integrations/", "integrations"),
    (r"/api_keys/", "api_keys"),
    (r"/account/", "account"),
    (r"/ops/", "ops"),
    (r"/platform/", "platform"),
    (r"/recovery/", "recovery"),
    (r"/agent/", "agent"),
    (r"/general/", "general"),

    # Directory-based domain assignments (user corrections)
    (r"^app/adapters/", "integrations"),  # External adapters → integrations
    (r"^app/utils/", "general"),  # Utilities → general
    (r"^app/contracts/", "general"),  # Contracts → general
    (r"^app/skills/", "agent"),  # Skills → agent
    (r"^app/agents/", "agent"),  # Agents → agent
    (r"^app/costsim/", "analytics"),  # Cost simulation → analytics
    (r"^app/optimization/", "analytics"),  # Optimization → analytics
    (r"^app/dsl/", "policies"),  # DSL → policies
    (r"^app/protection/", "policies"),  # Protection → policies
    (r"^app/commands/", "policies"),  # Commands → policies
    (r"^app/quarantine/", "ops"),  # Quarantine → ops (founder)
    (r"^app/workflow/", "platform"),  # Workflow → platform
    (r"^app/memory/", "platform"),  # Memory → platform
    (r"^app/routing/", "platform"),  # Routing → platform
    (r"^app/observability/", "platform"),  # Observability → platform
    (r"^app/runtime/", "platform"),  # Runtime → platform
    (r"^app/learning/", "platform"),  # Learning → platform
    (r"^app/planner", "platform"),  # Planners → platform
    (r"^app/domain/", "platform"),  # Domain logic → platform
    (r"^app/config/", "platform"),  # Config → platform
    (r"^app/errors/", "platform"),  # Errors → platform
    (r"^app/integrations/", "integrations"),  # Integrations → integrations

    # Filename-based domain detection
    (r"overview", "overview"),
    (r"activity|attention|run_", "activity"),
    (r"incident|postmortem|failure", "incidents"),
    (r"policy|limit|constraint|governance|killswitch", "policies"),
    (r"log|trace|audit|evidence|certificate", "logs"),
    (r"analytics|cost|anomaly|prediction|pattern", "analytics"),
    (r"integration|connector|credential|datasource|mcp|webhook", "integrations"),
    (r"api_key|key_service", "api_keys"),
    (r"account|tenant|user|profile|billing|notification", "account"),
    (r"panel|console|ui|frontend", "agent"),
    (r"scheduler|sandbox|pool|executor", "platform"),
    (r"orphan|compensation|recovery", "recovery"),
]

# Layer patterns by filename
LAYER_PATTERNS = [
    # L3 - Adapters
    (r"_facade\.py$", "L3", "L3 Facade → Adapter"),
    (r"_adapter\.py$", "L3", "L3 Adapter"),
    (r"^app/adapters/[^/]+\.py$", "L3", "In adapters/ dir"),
    (r"^app/adapters/[^/]+/[^/]+\.py$", "L3", "In adapters/ subdir"),

    # L4 - Runtime (governance, orchestration)
    (r"governance[_/]", "L4", "Governance runtime"),
    (r"orchestrat", "L4", "Orchestration"),
    (r"lifecycle_", "L4", "Lifecycle management"),
    (r"/runtime/", "L4", "In runtime/ dir"),
    (r"authority", "L4", "Authority decisions"),
    (r"execution_context", "L4", "Execution context"),

    # L5 - Engines/Workers
    (r"_engine\.py$", "L5", "L5 Engine"),
    (r"_worker\.py$", "L5", "L5 Worker"),
    (r"/engines/[^/]+\.py$", "L5", "In engines/ dir"),
    (r"/workers/[^/]+\.py$", "L5", "In workers/ dir"),
    (r"^app/workers/", "L5", "In workers/ dir"),
    (r"^app/worker/", "L5", "In worker/ dir"),
    (r"^app/jobs/", "L5", "In jobs/ dir"),
    (r"^app/tasks/", "L5", "In tasks/ dir"),

    # L6 - Schemas (data contracts) - merged with L6 Data Layer
    (r"/schemas/[^/]+\.py$", "L6", "L6 Data Layer (Schema)"),
    (r"^app/schemas/", "L6", "L6 Data Layer (Schema)"),
    (r"_schema\.py$", "L6", "L6 Data Layer (Schema)"),

    # L5 - Business logic / services
    (r"^app/agents/", "L5", "Agent logic"),
    (r"^app/skills/", "L5", "Skills"),
    (r"^app/workflow/", "L5", "Workflow logic"),
    (r"^app/optimization/", "L5", "Optimization logic"),
    (r"^app/learning/", "L5", "Learning logic"),
    (r"^app/planner", "L5", "Planning logic"),

    # L6 - Drivers (read/write services)
    (r"_driver\.py$", "L6", "L6 Driver"),
    (r"/drivers/[^/]+\.py$", "L6", "In drivers/ dir"),
    (r"_read_service\.py$", "L6", "Read service → Driver"),
    (r"_write_service\.py$", "L6", "Write service → Driver"),

    # ==========================================================================
    # ITERATION 2: Resolved L5/L6 Services
    # Based on file header analysis - these are NOT L5/L6 ambiguous
    # ==========================================================================

    # L3 Boundary Adapters (services that are actually adapters)
    (r"^app/services/export_bundle_service\.py$", "L3", "L3 Boundary Adapter"),

    # L4 Domain Engines (services with business logic)
    (r"^app/services/activity/.*_service\.py$", "L4", "L4 Domain Engine (Activity)"),
    (r"^app/services/cus_.*_service\.py$", "L4", "L4 Domain Engine (Customer)"),
    (r"^app/services/iam/.*_service\.py$", "L4", "L4 Domain Engine (IAM)"),
    (r"^app/services/incidents/.*_service\.py$", "L4", "L4 Domain Engine (Incidents)"),
    (r"^app/services/keys_service\.py$", "L4", "L4 Domain Engine (Keys)"),
    (r"^app/services/limits/.*_service\.py$", "L4", "L4 Domain Engine (Limits)"),
    (r"^app/services/llm_failure_service\.py$", "L4", "L4 Domain Engine (Failures)"),
    (r"^app/services/llm_threshold_service\.py$", "L4", "L4 Domain Engine (Thresholds)"),
    (r"^app/services/notifications/.*_service\.py$", "L4", "L4 Domain Engine (Notifications)"),
    (r"^app/services/ops_incident_service\.py$", "L4", "L4 Domain Engine (Ops)"),
    (r"^app/services/platform/.*_service\.py$", "L4", "L4 Domain Engine (Platform)"),
    (r"^app/services/policy/.*_service\.py$", "L4", "L4 Domain Engine (Policy)"),
    (r"^app/services/policy_violation_service\.py$", "L4", "L4 Domain Engine (Violations)"),
    (r"^app/services/sandbox/.*_service\.py$", "L4", "L4 Domain Engine (Sandbox)"),

    # L4 Domain Engines in HOC (already migrated)
    (r"^app/hoc/.*/platform_health_service\.py$", "L4", "L4 Domain Engine (Health)"),

    # L6 Platform Substrate (services that are data stores)
    (r"^app/services/tenant_service\.py$", "L6", "L6 Platform Substrate (Tenant)"),
    (r"^app/services/worker_registry_service\.py$", "L6", "L6 Platform Substrate (Registry)"),
    (r"^app/services/external_response_service\.py$", "L6", "L6 Platform Substrate (External)"),

    # L4 Domain Engines (auth services)
    (r"^app/auth/api_key_service\.py$", "L4", "L4 Domain Engine (Auth)"),

    # L6 Platform Substrate (memory services)
    (r"^app/memory/memory_service\.py$", "L6", "L6 Platform Substrate (Memory)"),

    # DELETE - Quarantined duplicates in HOC/duplicate
    (r"^app/hoc/duplicate/.*_service\.py$", "DELETE", "Quarantined duplicate"),

    # Catch-all for remaining _service.py (should be empty after above patterns)
    (r"_service\.py$", "L5/L6", "Service (needs manual check)"),

    # L6 - Platform substrate
    (r"^app/infra/", "L6", "Infrastructure"),
    (r"^app/storage/", "L6", "Storage"),
    (r"^app/stores/", "L6", "Stores"),
    (r"^app/core/", "L6", "Core utilities"),
    (r"^app/integrations/", "L6", "Integrations"),
    (r"^app/observability/", "L6", "Observability"),
    (r"^app/events/", "L6", "Events"),
    (r"^app/memory/", "L6", "Memory"),
    (r"^app/routing/", "L6", "Routing"),
    (r"^app/secrets/", "L6", "Secrets"),
    (r"^app/security/", "L6", "Security"),

    # L7 - Models (stays)
    (r"/models/[^/]+\.py$", "L7", "Model file"),

    # L2 - API routes
    (r"^app/api/[^/]+\.py$", "L2", "API route"),
    (r"^app/api/[^/]+/[^/]+\.py$", "L2", "API route in subdir"),
    (r"/routes/", "L2", "Routes"),
    (r"/api/middleware/", "L2-Infra", "API middleware"),
    (r"/api/dependencies/", "L2-Infra", "API dependencies"),

    # Auth - internal infrastructure
    (r"^app/auth/", "L4", "Auth infrastructure"),
    (r"^app/auth\.py$", "L4", "Auth module"),

    # Config/contracts - L6 Data Layer
    (r"^app/config/", "L6", "L6 Data Layer (Config)"),
    (r"^app/contracts/", "L6", "L6 Data Layer (Contracts)"),
    (r"^app/dsl/", "L5", "DSL"),
    (r"^app/errors/", "L6", "L6 Data Layer (Errors)"),
    (r"^app/specs/", "L6", "L6 Data Layer (Specs)"),
    (r"^app/utils/", "L6", "Utilities"),
    (r"^app/commands/", "L5", "Commands"),
    (r"^app/domain/", "L5", "Domain logic"),

    # Misc root-level files
    (r"^app/costsim/", "L5", "Cost simulation"),
    (r"^app/billing/", "L5", "Billing logic"),
    (r"^app/protection/", "L5", "Protection logic"),
    (r"^app/quarantine/", "L5", "Quarantine logic"),
    (r"^app/startup/", "L6", "Startup"),
    (r"^app/discovery/", "L5", "Discovery"),
    (r"^app/policy/", "L5", "Policy logic"),
    (r"^app/traces/", "L6", "Trace storage"),
    (r"^app/evidence/", "L6", "Evidence storage"),

    # CLI tools
    (r"_cli\.py$", "L2", "CLI tool"),
    (r"^app/aos_cli\.py$", "L2", "AOS CLI"),

    # Catch-all: __init__.py files
    (r"__init__\.py$", "L5", "Package init"),
    (r"base\.py$", "L5", "Base class"),

    # Additional patterns for remaining UNKNOWN layers
    (r"^app/db\.py$", "L6", "Database connection"),
    (r"^app/db_async\.py$", "L6", "Async database"),
    (r"^app/db_helpers\.py$", "L6", "Database helpers"),
    (r"^app/main\.py$", "L2", "FastAPI main"),
    (r"^app/middleware/", "L2-Infra", "Middleware"),
    (r"^app/predictions/", "L5", "Predictions"),
    (r"^app/runtime_projections/", "L5", "Runtime projections"),

    # Services directory patterns
    (r"^app/services/[^/]+/[^/]+\.py$", "L5", "Service module"),
    (r"^app/services/[^/]+\.py$", "L5", "Top-level service"),

    # HOC internal patterns - L6 Data Layer
    (r"/utils/", "L6", "L6 Data Layer (Utilities)"),
    (r"/types\.py$", "L6", "L6 Data Layer (Types)"),
    (r"protocol\.py$", "L6", "L6 Data Layer (Protocol)"),

    # Remaining root-level files
    (r"^app/logging_config\.py$", "L6", "Logging configuration"),
    (r"^app/metrics\.py$", "L6", "Metrics"),
    (r"^app/skill_http\.py$", "L5", "HTTP skill"),

    # Deprecated duplicate files (will be deleted)
    (r"^app/hoc/duplicate/", "DELETE", "Deprecated duplicate"),
]


def detect_audience(path: str) -> tuple[str, str]:
    """Detect audience from path. Returns (audience, confidence)."""
    for pattern, audience in AUDIENCE_PATTERNS:
        if re.search(pattern, path):
            return audience, "HIGH"
    return "UNKNOWN", "LOW"


def detect_domain(path: str, file_header: str = "") -> tuple[str, str]:
    """Detect domain from path and header. Returns (domain, confidence)."""
    combined = f"{path} {file_header}".lower()

    # Check explicit patterns first
    for pattern, domain in DOMAIN_PATTERNS:
        if re.search(pattern, combined):
            return domain, "MEDIUM"

    return "general", "LOW"


def detect_layer(path: str, file_header: str = "") -> tuple[str, str, str]:
    """Detect layer from path. Returns (layer, confidence, notes)."""
    for pattern, layer, notes in LAYER_PATTERNS:
        if re.search(pattern, path):
            return layer, "HIGH" if "dir" in notes else "MEDIUM", notes

    return "UNKNOWN", "LOW", "Could not detect layer"


def get_source_subdirectory(source_path: str) -> str:
    """Extract meaningful subdirectory from source path for disambiguation.

    E.g., app/services/audit/store.py -> audit
          app/adapters/file_storage/base.py -> file_storage
    """
    parts = source_path.split('/')
    if len(parts) >= 3:
        # Get the directory just before the filename
        parent = parts[-2]
        # Skip generic parents
        if parent not in ('services', 'adapters', 'api', 'hoc', 'customer',
                          'internal', 'founder', 'engines', 'facades', 'drivers', 'schemas'):
            return parent
    return ""


def generate_target_path(
    source_path: str,
    audience: str,
    domain: str,
    layer: str
) -> str:
    """Generate target path in app/hoc/ structure.

    Option B Decision: HOC files stay within app/ directory.
    Legacy code in app/services/ will be deleted in Phase 5 after migration.

    Disambiguation: For files with common names (facade.py, base.py, etc.),
    include source subdirectory in target to avoid collisions.
    """

    filename = Path(source_path).name

    # Common filenames that need disambiguation (avoid collisions)
    COMMON_NAMES = {'facade.py', 'base.py', 'provider.py', 'parser.py', '__init__.py',
                    'types.py', 'models.py', 'utils.py', 'helpers.py', 'constants.py',
                    'conflict_resolver.py', 'store.py', 'reconciler.py', 'durability.py',
                    'completeness_checker.py'}

    # Models stay in app/
    if layer == "L7":
        return source_path  # No change

    # Files already in app/hoc/ stay in place
    if source_path.startswith("app/hoc/"):
        return source_path  # No change for already-migrated files

    # Normalize audience for path
    aud_lower = audience.lower() if audience not in ("UNKNOWN", "DEPRECATED") else "unclassified"

    # Get subdirectory for disambiguation if needed
    subdir = get_source_subdirectory(source_path) if filename in COMMON_NAMES else ""

    # Create disambiguated filename if needed
    if subdir and filename != '__init__.py':
        base = filename.replace('.py', '')
        disambig_filename = f"{subdir}_{base}.py"
    else:
        disambig_filename = filename

    # L6 Data Layer: Determine if schema or driver based on source path
    if layer == "L6":
        # Schema patterns: /schemas/, _schema.py, app/schemas/, app/contracts/, app/specs/
        is_schema = (
            "/schemas/" in source_path or
            "_schema.py" in source_path or
            source_path.startswith("app/schemas/") or
            source_path.startswith("app/contracts/") or
            source_path.startswith("app/specs/") or
            "/types.py" in source_path or
            "protocol.py" in source_path
        )
        if is_schema:
            return f"app/hoc/{aud_lower}/{domain}/schemas/{disambig_filename}"
        else:
            return f"app/hoc/{aud_lower}/{domain}/drivers/{disambig_filename}"

    # Map layer to directory (Option B: app/hoc/ as root)
    # FIX: L2 must preserve filename (not consolidate to single domain file)
    # FIX: L4 must respect domain (not all go to general/runtime)
    # FIX: L3 goes to facades/ (consistent with existing HOC structure)
    layer_dirs = {
        "L2": f"app/hoc/api/{aud_lower}/{domain}/{disambig_filename}",
        "L2-Infra": f"app/hoc/api/infrastructure/{disambig_filename}",
        "L3": f"app/hoc/{aud_lower}/{domain}/facades/{disambig_filename}",
        "L4": f"app/hoc/{aud_lower}/{domain}/engines/{disambig_filename}",
        "L5": f"app/hoc/{aud_lower}/{domain}/engines/{disambig_filename}",
        "L5/L6": f"app/hoc/{aud_lower}/{domain}/services/{disambig_filename}",
        "UNKNOWN": f"app/hoc/unclassified/{disambig_filename}",
        "N/A": "",
    }

    if layer in layer_dirs:
        return layer_dirs[layer]

    # Default path
    return f"app/hoc/{audience.lower()}/{domain}/{disambig_filename}"


def determine_action(
    source_path: str,
    audience: str,
    layer: str,
    auto_status: str
) -> str:
    """Determine migration action."""

    if auto_status == "DEPRECATED_DUPLICATE":
        return "DELETE"

    if auto_status == "STAYS" or layer == "L7":
        return "STAYS"

    if audience == "DEPRECATED":
        return "DELETE"

    if "hoc/duplicate" in source_path:
        return "DELETE"

    return "TRANSFER"


def classify_file(row: dict) -> Classification:
    """Classify a single file from inventory row."""

    source_path = row['source_path']
    auto_status = row['auto_status']
    file_header = row.get('file_header', '')
    docstring = row.get('docstring', '')

    # Handle pre-classified statuses
    if auto_status == "STAYS":
        # Determine audience for L7 models based on directory
        if "/cus/" in source_path:
            model_audience = "CUSTOMER"
        elif "/fdr/" in source_path:
            model_audience = "FOUNDER"
        elif "/int/" in source_path:
            model_audience = "INTERNAL"
        else:
            model_audience = "INTERNAL"  # Shared models default to INTERNAL

        return Classification(
            audience=model_audience,
            domain="models",
            layer="L7",
            target_path=source_path,
            action="STAYS",
            notes="L7 model - stays in app/",
            confidence="HIGH"
        )

    if auto_status == "DEPRECATED_DUPLICATE":
        return Classification(
            audience="DEPRECATED",
            domain="deprecated",
            layer="N/A",
            target_path="",
            action="DELETE",
            notes="Deprecated duplicate file",
            confidence="HIGH"
        )

    # Detect classification
    audience, aud_conf = detect_audience(source_path)
    domain, dom_conf = detect_domain(source_path, file_header)
    layer, lay_conf, layer_notes = detect_layer(source_path, file_header)

    # Generate target path
    target_path = generate_target_path(source_path, audience, domain, layer)

    # Determine action
    action = determine_action(source_path, audience, layer, auto_status)

    # Build notes
    notes_parts = []
    if layer_notes:
        notes_parts.append(layer_notes)
    if aud_conf == "LOW":
        notes_parts.append("Audience uncertain")
    if dom_conf == "LOW":
        notes_parts.append("Domain uncertain")
    if lay_conf == "LOW":
        notes_parts.append("Layer uncertain")

    # Overall confidence
    confidences = [aud_conf, dom_conf, lay_conf]
    if all(c == "HIGH" for c in confidences):
        confidence = "HIGH"
    elif any(c == "LOW" for c in confidences):
        confidence = "LOW"
    else:
        confidence = "MEDIUM"

    return Classification(
        audience=audience,
        domain=domain,
        layer=layer,
        target_path=target_path,
        action=action,
        notes="; ".join(notes_parts) if notes_parts else "",
        confidence=confidence
    )


def classify_inventory(input_path: Path, output_path: Path):
    """Classify all files in inventory and output updated CSV."""

    # Read input CSV
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Read {len(rows)} rows from {input_path}")

    # Classify each row
    stats = {
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
        "actions": {},
        "audiences": {},
        "domains": {},
        "layers": {},
    }

    classified_rows = []
    for row in rows:
        classification = classify_file(row)

        # Update row with classification
        row['audience'] = classification.audience
        row['domain'] = classification.domain
        row['layer'] = classification.layer
        row['target_path'] = classification.target_path
        row['action'] = classification.action
        row['audit_notes'] = classification.notes
        row['audit_status'] = 'ITERATION_1'

        classified_rows.append(row)

        # Track stats
        stats[classification.confidence] += 1
        stats["actions"][classification.action] = stats["actions"].get(classification.action, 0) + 1
        stats["audiences"][classification.audience] = stats["audiences"].get(classification.audience, 0) + 1
        stats["domains"][classification.domain] = stats["domains"].get(classification.domain, 0) + 1
        stats["layers"][classification.layer] = stats["layers"].get(classification.layer, 0) + 1

    # Write output CSV
    fieldnames = [
        's_no', 'source_path', 'audience', 'domain', 'layer', 'target_path',
        'file_header', 'docstring', 'existing_hoc_path',
        'auto_status', 'audit_status', 'audit_notes', 'action'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(classified_rows)

    print(f"\nWrote {len(classified_rows)} classified rows to {output_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("ITERATION 1 CLASSIFICATION SUMMARY")
    print("=" * 60)

    print(f"\n### Confidence Levels ###")
    print(f"  HIGH:   {stats['HIGH']:4d} ({stats['HIGH']/len(rows)*100:.1f}%)")
    print(f"  MEDIUM: {stats['MEDIUM']:4d} ({stats['MEDIUM']/len(rows)*100:.1f}%)")
    print(f"  LOW:    {stats['LOW']:4d} ({stats['LOW']/len(rows)*100:.1f}%)")

    print(f"\n### Actions ###")
    for action, count in sorted(stats["actions"].items(), key=lambda x: -x[1]):
        print(f"  {action:12s}: {count:4d}")

    print(f"\n### Audiences ###")
    for aud, count in sorted(stats["audiences"].items(), key=lambda x: -x[1]):
        print(f"  {aud:12s}: {count:4d}")

    print(f"\n### Domains (Top 15) ###")
    for dom, count in sorted(stats["domains"].items(), key=lambda x: -x[1])[:15]:
        print(f"  {dom:15s}: {count:4d}")

    print(f"\n### Layers ###")
    for layer, count in sorted(stats["layers"].items(), key=lambda x: -x[1]):
        print(f"  {layer:12s}: {count:4d}")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Classify Migration Inventory (Iteration 1)")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("docs/architecture/migration/MIGRATION_INVENTORY.csv"),
        help="Input inventory CSV"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/architecture/migration/MIGRATION_INVENTORY_ITER1.csv"),
        help="Output classified CSV"
    )

    args = parser.parse_args()

    # Resolve paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent

    input_path = repo_root / args.input if not args.input.is_absolute() else args.input
    output_path = repo_root / args.output if not args.output.is_absolute() else args.output

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1

    classify_inventory(input_path, output_path)
    return 0


if __name__ == "__main__":
    exit(main())
