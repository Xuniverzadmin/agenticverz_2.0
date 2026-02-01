# Layer: L5 — Domain Package
# AUDIENCE: CUSTOMER
# Role: Controls domain - usage limits, cost controls, credit management, RAG access auditing

"""
Controls Domain (Customer)

This domain handles all customer-facing control configurations:
- Token usage limits and thresholds
- Cost usage limits and budgets
- Credit usage tracking and alerts
- RAG access auditing (LLM verification before inference)

Layer Structure:
- adapters/     : Cross-domain adapters (policies, analytics integration)
- L5_engines/   : Business logic for control evaluation and enforcement
- L5_schemas/   : Pydantic models for control configurations
- L6_drivers/   : Database operations for control persistence

Reference: docs/architecture/hoc/CONTROLS_DOMAIN.md
"""
