/**
 * Console Roots — Authoritative Route Prefixes
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Temporal:
 *   Trigger: build-time (derived from consoleContext)
 *   Execution: sync
 * Role: Define root paths for each console × environment combination
 * Reference: PIN-352, Routing Authority Model
 *
 * INFRASTRUCTURE: FROZEN
 * Owner: platform
 * Churn: low (deliberate changes only)
 * Last Frozen: 2026-01-08
 *
 * ROUTING AUTHORITY MODEL (4 DISTINCT CONSOLES):
 * ┌──────────────┬─────────────┬───────────┐
 * │ Console Kind │ Environment │ Root Path │
 * ├──────────────┼─────────────┼───────────┤
 * │ customer     │ preflight   │ /precus   │
 * ├──────────────┼─────────────┼───────────┤
 * │ customer     │ production  │ /cus      │
 * ├──────────────┼─────────────┼───────────┤
 * │ founder      │ preflight   │ /prefops  │
 * ├──────────────┼─────────────┼───────────┤
 * │ founder      │ production  │ /fops     │
 * └──────────────┴─────────────┴───────────┘
 *
 * INVARIANTS:
 * - 4 distinct console roots, NO mixing
 * - All route prefixes derived from this file ONLY
 * - No hardcoded paths allowed elsewhere
 * - CONSOLE_ROOT is the single source of truth
 */

import {
  IS_PREFLIGHT,
  CONSOLE_KIND,
  IS_CUSTOMER_CONSOLE,
  IS_FOUNDER_CONSOLE,
} from './consoleContext';

// =============================================================================
// CONSOLE ROOT DEFINITIONS (4 DISTINCT CONSOLES)
// =============================================================================

/**
 * Root paths for Customer Console
 */
const CUSTOMER_ROOTS = {
  preflight: '/precus',     // Preflight Customer Console (L2.1 projections)
  production: '/cus',       // Production Customer Console
} as const;

/**
 * Root paths for Founder Console
 */
const FOUNDER_ROOTS = {
  preflight: '/prefops',    // Preflight Founder Console
  production: '/fops',      // Production Founder Console
} as const;

// =============================================================================
// DERIVED CONSOLE ROOT (Single Export)
// =============================================================================

/**
 * CONSOLE_ROOT — The authoritative root path for this console instance.
 *
 * This is THE path prefix that all routes must use.
 * Derived from CONSOLE_KIND × IS_PREFLIGHT at build time.
 *
 * Examples:
 * - Customer + Preflight  → '/precus'
 * - Customer + Production → '/cus'
 * - Founder + Preflight   → '/prefops'
 * - Founder + Production  → '/fops'
 */
export const CONSOLE_ROOT: string = (() => {
  if (IS_CUSTOMER_CONSOLE) {
    return IS_PREFLIGHT ? CUSTOMER_ROOTS.preflight : CUSTOMER_ROOTS.production;
  }
  if (IS_FOUNDER_CONSOLE) {
    return IS_PREFLIGHT ? FOUNDER_ROOTS.preflight : FOUNDER_ROOTS.production;
  }
  // Fallback (should never happen)
  return '/cus';
})();

/**
 * Customer Console roots (for cross-console navigation)
 */
export const PRECUS_ROOT = CUSTOMER_ROOTS.preflight;   // /precus
export const CUS_ROOT = CUSTOMER_ROOTS.production;     // /cus

/**
 * Founder Console roots (for cross-console navigation)
 */
export const PREFOPS_ROOT = FOUNDER_ROOTS.preflight;   // /prefops
export const FOPS_ROOT = FOUNDER_ROOTS.production;     // /fops

/**
 * Environment-aware customer root
 */
export const CUSTOMER_ROOT = IS_PREFLIGHT
  ? CUSTOMER_ROOTS.preflight
  : CUSTOMER_ROOTS.production;

/**
 * Environment-aware founder root
 */
export const FOUNDER_ROOT = IS_PREFLIGHT
  ? FOUNDER_ROOTS.preflight
  : FOUNDER_ROOTS.production;

// =============================================================================
// DOMAIN ROOTS (Preflight Customer Console - L2.1 Domains)
// =============================================================================

/**
 * L2.1 Domain roots for Preflight Customer Console (/precus).
 * These are the five frozen domains from Customer Console v1 Constitution.
 *
 * In preflight: /precus/overview, /precus/activity, etc.
 * In production: /cus/overview, /cus/activity, etc.
 */
export const DOMAIN_ROOTS = {
  overview: IS_PREFLIGHT ? '/precus/overview' : '/cus/overview',
  activity: IS_PREFLIGHT ? '/precus/activity' : '/cus/activity',
  incidents: IS_PREFLIGHT ? '/precus/incidents' : '/cus/incidents',
  policies: IS_PREFLIGHT ? '/precus/policies' : '/cus/policies',
  logs: IS_PREFLIGHT ? '/precus/logs' : '/cus/logs',
} as const;

/**
 * Secondary navigation roots (not L2.1 domains)
 */
export const SECONDARY_ROOTS = {
  keys: IS_PREFLIGHT ? '/precus/keys' : '/cus/keys',
  integrations: IS_PREFLIGHT ? '/precus/integrations' : '/cus/integrations',
  settings: IS_PREFLIGHT ? '/precus/settings' : '/cus/settings',
  account: IS_PREFLIGHT ? '/precus/account' : '/cus/account',
} as const;

// =============================================================================
// FOUNDER DOMAIN ROOTS (Preflight Founder Console - /prefops)
// =============================================================================

/**
 * Founder domain roots.
 * In preflight: /prefops/*, In production: /fops/*
 */
export const FOUNDER_DOMAIN_ROOTS = {
  ops: IS_PREFLIGHT ? '/prefops/ops' : '/fops/ops',
  traces: IS_PREFLIGHT ? '/prefops/traces' : '/fops/traces',
  workers: IS_PREFLIGHT ? '/prefops/workers' : '/fops/workers',
  recovery: IS_PREFLIGHT ? '/prefops/recovery' : '/fops/recovery',
  integration: IS_PREFLIGHT ? '/prefops/integration' : '/fops/integration',
  timeline: IS_PREFLIGHT ? '/prefops/timeline' : '/fops/timeline',
  controls: IS_PREFLIGHT ? '/prefops/controls' : '/fops/controls',
  replay: IS_PREFLIGHT ? '/prefops/replay' : '/fops/replay',
  scenarios: IS_PREFLIGHT ? '/prefops/scenarios' : '/fops/scenarios',
  explorer: IS_PREFLIGHT ? '/prefops/explorer' : '/fops/explorer',
  review: IS_PREFLIGHT ? '/prefops/review' : '/fops/review',
  sba: IS_PREFLIGHT ? '/prefops/sba' : '/fops/sba',
} as const;

// =============================================================================
// TYPE EXPORTS
// =============================================================================

export type DomainKey = keyof typeof DOMAIN_ROOTS;
export type SecondaryKey = keyof typeof SECONDARY_ROOTS;
export type FounderDomainKey = keyof typeof FOUNDER_DOMAIN_ROOTS;
