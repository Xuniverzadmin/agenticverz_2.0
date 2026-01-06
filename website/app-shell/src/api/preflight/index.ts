/**
 * Preflight API Module
 *
 * Runtime v1 Feature Freeze - PIN-183
 *
 * TWO AXES:
 * - Axis 1 (Plane): Founder Ops vs Customer Experience
 * - Axis 2 (Stage): Preflight vs Production
 *
 * DOMAIN MAP:
 * - preflight-fops.agenticverz.com    → Founder Ops, Preflight (system truth)
 * - fops.agenticverz.com              → Founder Ops, Production (operate system)
 * - preflight-console.agenticverz.com → Customer Experience, Preflight (INTERNAL ONLY)
 * - console.agenticverz.com           → Customer Experience, Production (customers)
 *
 * CRITICAL DISTINCTION:
 * - preflight-console is NOT for customers
 * - It is a shadow environment for founders/developers to verify customer experience
 * - Like iOS TestFlight - internal validation before exposure
 *
 * HARD RULES:
 * 1. preflight-console is INTERNAL ONLY (VPN/IP allowlist, founder auth)
 * 2. preflight-console and console share UI code (same routes, components)
 * 3. Different data sources (ENV-level switch, not UI-level)
 * 4. No `if (preflight)` in components
 * 5. Customers must NEVER know preflight-console exists
 * 6. Cross-plane promotion is NEVER allowed
 */

// Founder Preflight (preflight-fops.agenticverz.com)
export {
  type FounderPreflightDTO,
  type FounderPromotionChecklist,
  type InfraStatus,
  type WorkerStatus,
  type SeverityBreakdown,
  getFounderPreflight,
  getFounderPromotionChecklist,
  isFounderPreflight,
} from './founder';

// Customer Preflight (preflight-console.agenticverz.com)
export {
  type CustomerPreflightDTO,
  type CustomerPromotionChecklist,
  getCustomerPreflight,
  getCustomerPromotionChecklist,
  isCustomerPreflight,
  assertNoFounderLeakage,
} from './customer';

// =============================================================================
// DOMAIN CONSTANTS
// =============================================================================

export const DOMAINS = {
  // Founder Plane
  PREFLIGHT_FOPS: 'preflight-fops.agenticverz.com',
  FOPS: 'fops.agenticverz.com',

  // Customer Plane
  PREFLIGHT_CONSOLE: 'preflight-console.agenticverz.com',
  CONSOLE: 'console.agenticverz.com',
} as const;

// =============================================================================
// PROMOTION RULES
// =============================================================================

export const PROMOTION_RULES = {
  // Founder promotion: preflight-fops → fops
  founder: {
    from: DOMAINS.PREFLIGHT_FOPS,
    to: DOMAINS.FOPS,
    crossPlane: false,
  },

  // Customer promotion: preflight-console → console
  customer: {
    from: DOMAINS.PREFLIGHT_CONSOLE,
    to: DOMAINS.CONSOLE,
    crossPlane: false,
  },
} as const;

/**
 * Validate that a promotion is allowed
 * Cross-plane promotion is NEVER allowed
 */
export function validatePromotion(
  fromDomain: string,
  toDomain: string
): { allowed: boolean; reason: string } {
  // Founder plane
  if (fromDomain === DOMAINS.PREFLIGHT_FOPS) {
    if (toDomain === DOMAINS.FOPS) {
      return { allowed: true, reason: 'Valid founder promotion' };
    }
    return { allowed: false, reason: 'Cross-plane promotion not allowed' };
  }

  // Customer plane
  if (fromDomain === DOMAINS.PREFLIGHT_CONSOLE) {
    if (toDomain === DOMAINS.CONSOLE) {
      return { allowed: true, reason: 'Valid customer promotion' };
    }
    return { allowed: false, reason: 'Cross-plane promotion not allowed' };
  }

  return { allowed: false, reason: 'Unknown domain' };
}
