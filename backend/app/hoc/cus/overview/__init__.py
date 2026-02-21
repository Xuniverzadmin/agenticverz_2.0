# capability_id: CAP-012
# Layer: L5 — Domain (Overview)
# NOTE: Header corrected L4→L5 (2026-01-31) — this is a domain package, not L4 spine
# AUDIENCE: CUSTOMER
# Role: Overview domain - System health at a glance
# Reference: DIRECTORY_REORGANIZATION_PLAN.md, HOC_overview_analysis_v1.md

"""
Overview Domain

Topics: cost_intelligence, decisions, highlights
Roles: facades, schemas

DOMAIN CONTRACT (Constitutional)
================================

Overview is a PROJECTION-ONLY domain. It synthesizes status
from other domains but owns no state and triggers no effects.

INVARIANTS (Non-Negotiable):

  INV-OVW-001: Overview DOES NOT own any tables
  INV-OVW-002: Overview NEVER triggers side-effects
  INV-OVW-003: All mutations route to owning domains
  INV-OVW-004: No business rules — composition only

ALLOWED:

  - Read from Activity, Incidents, Policies, Logs
  - Aggregate counts and statuses
  - Return links/references to other domains

FORBIDDEN:

  - Write operations of any kind
  - Inline approval/dismissal/escalation
  - Threshold logic (belongs to Analytics)
  - Anomaly classification (belongs to Analytics)
  - Background jobs
  - Internal caching

BOUNDARY WITH ANALYTICS:

  - Overview: "What is the current status?"
  - Analytics: "What patterns exist? What will happen?"

If any invariant is violated, the domain is compromised.
"""
