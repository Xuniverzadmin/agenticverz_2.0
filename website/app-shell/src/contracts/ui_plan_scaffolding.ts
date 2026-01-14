/**
 * UI Plan Scaffolding — Structural Authority from ui_plan.yaml
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Temporal:
 *   Trigger: build-time (static data)
 *   Execution: sync
 * Role: Provide domain/subdomain/topic structure when projection is incomplete
 * Reference: UI-as-Constraint Doctrine, ARCHITECTURE_CONSTRAINTS_V1.yaml
 *
 * AUTHORITY MODEL:
 * ┌─────────────────────────────────────────────────────────────┐
 * │ ui_plan.yaml (human constraint) — HIGHEST AUTHORITY        │
 * │      ↓                                                      │
 * │ ui_projection_lock.json (machine mirror, partial)           │
 * │      ↓                                                      │
 * │ Frontend renderer (dumb consumer)                           │
 * └─────────────────────────────────────────────────────────────┘
 *
 * RULE (CONSTITUTIONAL):
 * If a domain/subdomain/topic exists in ui_plan.yaml but not in projection,
 * the UI MUST render structural scaffolding using this file as fallback authority.
 *
 * WHAT THIS FILE PROVIDES:
 * - Domain existence
 * - Subdomain existence
 * - Topic existence
 * - Navigation structure
 *
 * WHAT THIS FILE DOES NOT PROVIDE:
 * - Panel instances (projection only)
 * - Binding states (projection only)
 * - Data rendering (projection only)
 *
 * SYNC NOTICE:
 * This file is derived from: design/l2_1/ui_plan.yaml
 * Keep in sync when ui_plan.yaml structure changes.
 * Last synced: 2026-01-14
 */

import type { DomainName } from './ui_projection_types';

// ============================================================================
// Scaffolding Types
// ============================================================================

export interface ScaffoldingTopic {
  id: string;
  display_order: number;
}

export interface ScaffoldingSubdomain {
  id: string;
  topics: ScaffoldingTopic[];
}

export interface ScaffoldingDomain {
  id: DomainName;
  question: string;
  primary_object: string;
  order: number;
  route: string;
  subdomains: ScaffoldingSubdomain[];
}

// ============================================================================
// Domain Scaffolding Data (derived from ui_plan.yaml)
// ============================================================================

export const UI_PLAN_SCAFFOLDING: ScaffoldingDomain[] = [
  {
    id: "Overview",
    question: "Is the system okay right now?",
    primary_object: "Health",
    order: 1,
    route: "/precus/overview",
    subdomains: [
      {
        id: "SYSTEM_HEALTH",
        topics: [
          { id: "CURRENT_STATUS", display_order: 1 },
          { id: "HEALTH_METRICS", display_order: 2 },
        ],
      },
    ],
  },
  {
    id: "Activity",
    question: "What ran / is running?",
    primary_object: "Run",
    order: 2,
    route: "/precus/activity",
    subdomains: [
      {
        id: "EXECUTIONS",
        topics: [
          { id: "ACTIVE_RUNS", display_order: 1 },
          { id: "COMPLETED_RUNS", display_order: 2 },
          { id: "RUN_DETAILS", display_order: 3 },
          { id: "LIVE_RUNS", display_order: 4 },
          { id: "SUMMARY", display_order: 5 },
        ],
      },
    ],
  },
  {
    id: "Incidents",
    question: "What went wrong?",
    primary_object: "Incident",
    order: 3,
    route: "/precus/incidents",
    subdomains: [
      {
        id: "ACTIVE_INCIDENTS",
        topics: [
          { id: "INCIDENT_DETAILS", display_order: 1 },
          { id: "OPEN_INCIDENTS", display_order: 2 },
          { id: "SUMMARY", display_order: 3 },
        ],
      },
      {
        id: "HISTORICAL_INCIDENTS",
        topics: [
          { id: "RESOLVED_INCIDENTS", display_order: 1 },
        ],
      },
    ],
  },
  {
    id: "Policies",
    question: "How is behavior defined?",
    primary_object: "Policy",
    order: 4,
    route: "/precus/policies",
    subdomains: [
      {
        id: "ACTIVE_POLICIES",
        topics: [
          { id: "APPROVAL_RULES", display_order: 1 },
          { id: "BUDGET_POLICIES", display_order: 2 },
          { id: "RATE_LIMITS", display_order: 3 },
          { id: "SUMMARY", display_order: 4 },
        ],
      },
      {
        id: "POLICY_AUDIT",
        topics: [
          { id: "POLICY_CHANGES", display_order: 1 },
        ],
      },
      {
        id: "PROPOSALS",
        topics: [
          { id: "PENDING_PROPOSALS", display_order: 1 },
        ],
      },
    ],
  },
  {
    id: "Logs",
    question: "What is the raw truth?",
    primary_object: "Trace",
    order: 5,
    route: "/precus/logs",
    subdomains: [
      {
        id: "AUDIT_LOGS",
        topics: [
          { id: "SYSTEM_AUDIT", display_order: 1 },
          { id: "USER_AUDIT", display_order: 2 },
          { id: "SUMMARY", display_order: 3 },
        ],
      },
      {
        id: "EXECUTION_TRACES",
        topics: [
          { id: "TRACE_DETAILS", display_order: 1 },
          { id: "LIVE_STREAMS", display_order: 2 },
        ],
      },
    ],
  },
  {
    id: "Account",
    question: "Who am I and what do I own?",
    primary_object: "Account",
    order: 6,
    route: "/precus/account",
    subdomains: [
      {
        id: "PROFILE",
        topics: [
          { id: "ACCOUNT_INFO", display_order: 1 },
          { id: "SECURITY_SETTINGS", display_order: 2 },
        ],
      },
      {
        id: "BILLING",
        topics: [
          { id: "PAYMENT_METHODS", display_order: 1 },
          { id: "INVOICES", display_order: 2 },
          { id: "USAGE_SUMMARY", display_order: 3 },
        ],
      },
      {
        id: "PLANS_SUBSCRIPTIONS",
        topics: [
          { id: "CURRENT_PLAN", display_order: 1 },
          { id: "PLAN_LIMITS", display_order: 2 },
          { id: "UPGRADE_OPTIONS", display_order: 3 },
        ],
      },
      {
        id: "SUBUSERS",
        topics: [
          { id: "SUBUSER_LIST", display_order: 1 },
          { id: "PERMISSIONS", display_order: 2 },
          { id: "INVITE_SUBUSER", display_order: 3 },
        ],
      },
    ],
  },
  {
    id: "Connectivity",
    question: "How does the system connect?",
    primary_object: "Connection",
    order: 7,
    route: "/precus/connectivity",
    subdomains: [
      {
        id: "INTEGRATIONS",
        topics: [
          { id: "CONNECTED_SERVICES", display_order: 1 },
          { id: "AVAILABLE_INTEGRATIONS", display_order: 2 },
          { id: "INTEGRATION_HEALTH", display_order: 3 },
        ],
      },
      {
        id: "API",
        topics: [
          { id: "API_KEYS", display_order: 1 },
          { id: "WEBHOOKS", display_order: 2 },
          { id: "API_USAGE", display_order: 3 },
        ],
      },
    ],
  },
];

// ============================================================================
// Lookup Functions
// ============================================================================

/**
 * Get scaffolding for a domain by name.
 * Returns undefined if domain not in ui_plan.
 */
export function getScaffoldingDomain(domainName: DomainName): ScaffoldingDomain | undefined {
  return UI_PLAN_SCAFFOLDING.find(d => d.id === domainName);
}

/**
 * Get all scaffolding domains.
 */
export function getAllScaffoldingDomains(): ScaffoldingDomain[] {
  return UI_PLAN_SCAFFOLDING;
}

/**
 * Get subdomains for a domain from scaffolding.
 */
export function getScaffoldingSubdomains(domainName: DomainName): string[] {
  const domain = getScaffoldingDomain(domainName);
  if (!domain) return [];
  return domain.subdomains.map(s => s.id);
}

/**
 * Get topics for a subdomain from scaffolding.
 */
export function getScaffoldingTopics(domainName: DomainName, subdomainId: string): ScaffoldingTopic[] {
  const domain = getScaffoldingDomain(domainName);
  if (!domain) return [];
  const subdomain = domain.subdomains.find(s => s.id === subdomainId);
  if (!subdomain) return [];
  return subdomain.topics;
}

/**
 * Check if a domain exists in the ui_plan scaffolding.
 */
export function hasScaffoldingDomain(domainName: DomainName): boolean {
  return UI_PLAN_SCAFFOLDING.some(d => d.id === domainName);
}
