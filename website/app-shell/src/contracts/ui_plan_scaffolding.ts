/**
 * UI Plan Scaffolding — Structural Authority from V2 Constitution
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Temporal:
 *   Trigger: build-time (static data)
 *   Execution: sync
 * Role: Provide domain/subdomain/topic structure when projection is incomplete
 * Reference: CUSTOMER_CONSOLE_V2_CONSTITUTION.md
 *
 * AUTHORITY MODEL:
 * ┌─────────────────────────────────────────────────────────────┐
 * │ V2 Constitution (human constraint) — HIGHEST AUTHORITY      │
 * │      ↓                                                      │
 * │ ui_projection_lock.json (machine mirror, partial)           │
 * │      ↓                                                      │
 * │ Frontend renderer (dumb consumer)                           │
 * └─────────────────────────────────────────────────────────────┘
 *
 * SYNC NOTICE:
 * This file is derived from: docs/contracts/CUSTOMER_CONSOLE_V2_CONSTITUTION.md
 * Last synced: 2026-01-20
 */

import type { DomainName } from './ui_projection_types';

// ============================================================================
// Scaffolding Types
// ============================================================================

export interface ScaffoldingTopic {
  id: string;
  name: string;
  description: string;
  display_order: number;
}

export interface ScaffoldingSubdomain {
  id: string;
  name: string;
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
// Domain Scaffolding Data (derived from V2 Constitution)
// ============================================================================

export const UI_PLAN_SCAFFOLDING: ScaffoldingDomain[] = [
  {
    id: "Overview",
    question: "Is the system okay right now?",
    primary_object: "Health",
    order: 0,
    route: "/overview",
    subdomains: [
      {
        id: "summary",
        name: "Summary",
        topics: [
          { id: "highlights", name: "Highlights", description: "System pulse, status", display_order: 0 },
          { id: "decisions", name: "Decisions", description: "Pending actions, approvals", display_order: 1 },
        ],
      },
    ],
  },
  {
    id: "Activity",
    question: "What ran / is running?",
    primary_object: "Run",
    order: 1,
    route: "/activity",
    subdomains: [
      {
        id: "llm_runs",
        name: "LLM Runs",
        topics: [
          { id: "live", name: "Live", description: "Currently executing", display_order: 0 },
          { id: "completed", name: "Completed", description: "Finished runs", display_order: 1 },
          { id: "signals", name: "Signals", description: "Predictions, anomalies, risks", display_order: 2 },
        ],
      },
    ],
  },
  {
    id: "Incidents",
    question: "What went wrong?",
    primary_object: "Incident",
    order: 2,
    route: "/incidents",
    subdomains: [
      {
        id: "events",
        name: "Events",
        topics: [
          { id: "active", name: "Active", description: "Requires attention", display_order: 0 },
          { id: "resolved", name: "Resolved", description: "Acknowledged, closed", display_order: 1 },
          { id: "historical", name: "Historical", description: "Audit trail", display_order: 2 },
        ],
      },
    ],
  },
  {
    id: "Policies",
    question: "How is behavior defined?",
    primary_object: "Policy",
    order: 3,
    route: "/policies",
    subdomains: [
      {
        id: "governance",
        name: "Governance",
        topics: [
          { id: "active", name: "Active", description: "Enforced policies", display_order: 0 },
          { id: "lessons", name: "Lessons", description: "Learned patterns, proposals", display_order: 1 },
          { id: "policy_library", name: "Policy Library", description: "Templates, ethical constraints", display_order: 2 },
        ],
      },
      {
        id: "limits",
        name: "Limits",
        topics: [
          { id: "controls", name: "Controls", description: "Configured limits", display_order: 0 },
          { id: "violations", name: "Violations", description: "Limit breaches", display_order: 1 },
        ],
      },
    ],
  },
  {
    id: "Logs",
    question: "What is the raw truth?",
    primary_object: "Trace",
    order: 4,
    route: "/logs",
    subdomains: [
      {
        id: "records",
        name: "Records",
        topics: [
          { id: "llm_runs", name: "LLM Runs", description: "Execution records", display_order: 0 },
          { id: "system_logs", name: "System Logs", description: "Worker events", display_order: 1 },
          { id: "audit_logs", name: "Audit Logs", description: "Governance actions", display_order: 2 },
        ],
      },
    ],
  },
  {
    id: "Analytics",
    question: "What can we learn?",
    primary_object: "Metric",
    order: 5,
    route: "/analytics",
    subdomains: [
      {
        id: "insights",
        name: "Insights",
        topics: [
          { id: "cost_intelligence", name: "Cost Intelligence", description: "Spend, anomalies, forecasts", display_order: 0 },
        ],
      },
      {
        id: "usage_statistics",
        name: "Usage Stats",
        topics: [
          { id: "policies_usage", name: "Policies Usage", description: "Effectiveness, coverage", display_order: 0 },
          { id: "productivity", name: "Productivity", description: "Saved time, efficiency gains", display_order: 1 },
        ],
      },
    ],
  },
  {
    id: "Connectivity",
    question: "How does the system connect?",
    primary_object: "Connection",
    order: 6,
    route: "/connectivity",
    subdomains: [
      {
        id: "integrations",
        name: "Integrations",
        topics: [
          { id: "sdk_integration", name: "SDK Integration", description: "aos_sdk setup, future platforms", display_order: 0 },
        ],
      },
      {
        id: "api",
        name: "API",
        topics: [
          { id: "api_keys", name: "API Keys", description: "Create, rotate, revoke", display_order: 0 },
        ],
      },
    ],
  },
  {
    id: "Account",
    question: "Who am I and what do I own?",
    primary_object: "Account",
    order: 7,
    route: "/account",
    subdomains: [
      {
        id: "profile",
        name: "Profile",
        topics: [
          { id: "overview", name: "Overview", description: "Organization identity", display_order: 0 },
        ],
      },
      {
        id: "billing",
        name: "Billing",
        topics: [
          { id: "subscription", name: "Subscription", description: "Plan details", display_order: 0 },
          { id: "invoices", name: "Invoices", description: "Payment history", display_order: 1 },
        ],
      },
      {
        id: "team",
        name: "Team",
        topics: [
          { id: "members", name: "Members", description: "Team members, RBAC (admin only)", display_order: 0 },
        ],
      },
      {
        id: "settings",
        name: "Settings",
        topics: [
          { id: "account_management", name: "Account Management", description: "Suspend, terminate", display_order: 0 },
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
 * Get subdomain objects for a domain from scaffolding.
 */
export function getScaffoldingSubdomainObjects(domainName: DomainName): ScaffoldingSubdomain[] {
  const domain = getScaffoldingDomain(domainName);
  if (!domain) return [];
  return domain.subdomains;
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

/**
 * Get subdomain display name.
 */
export function getSubdomainName(domainName: DomainName, subdomainId: string): string {
  const domain = getScaffoldingDomain(domainName);
  if (!domain) return subdomainId;
  const subdomain = domain.subdomains.find(s => s.id === subdomainId);
  return subdomain?.name || subdomainId;
}
