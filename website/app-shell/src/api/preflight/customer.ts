/**
 * @audience customer
 *
 * Customer Experience Preflight API
 *
 * Runtime v1 Feature Freeze - PIN-183
 *
 * Domain: preflight-console.agenticverz.com
 * Plane: Customer Experience
 * Stage: Preflight
 * Audience: Founder / Dev / Internal QA (NEVER customers)
 *
 * PURPOSE:
 * Verify customer experience before exposure.
 * This is NOT for customers. It is a shadow environment for founders/developers
 * to see exactly what customers would see before shipping.
 *
 * Like iOS TestFlight - internal validation of the customer-facing surface.
 *
 * WHAT IT VALIDATES:
 * - UI correctness (pixel-for-pixel clone of customer console)
 * - Data quality (using test tenants)
 * - Copy & surfacing
 * - Feature completeness
 * - Performance at UX layer
 *
 * HARD RULES:
 * - VPN / IP allowlist (internal only)
 * - Founder auth only
 * - No SEO, no public DNS discovery
 * - Same routes/components as console.agenticverz.com
 * - Different data source (ENV-level switch, not UI-level)
 * - No `if (preflight)` in components
 * - Customers must NEVER know this exists
 */

// =============================================================================
// SCHEMA: CustomerPreflightDTO
// =============================================================================

export interface CustomerPreflightDTO {
  // Identity
  plane: 'customer';
  environment: 'preflight';
  timestamp: string;
  tenant_id: string;

  // Account Status
  account: {
    status: 'active' | 'suspended' | 'pending';
    plan: string;
    created_at: string;
  };

  // API Keys (count only, no secrets)
  keys: {
    total_count: number;
    active_count: number;
    has_valid_key: boolean;
  };

  // Limits (What applies to this customer)
  limits: {
    budget_limit_cents: number;
    rate_limit_per_minute: number;
    rate_limit_per_day: number;
    max_cost_per_request_cents: number;
  };

  // Readiness
  readiness: {
    account_configured: boolean;
    api_key_valid: boolean;
    limits_set: boolean;
    ready_to_use: boolean;
  };

  // Recent Activity (Customer's own data only)
  recent: {
    runs_last_24h: number;
    spend_last_24h_cents: number;
    incidents_last_24h: number;
  };
}

// =============================================================================
// PROMOTION CHECKLIST
// =============================================================================

export interface CustomerPromotionChecklist {
  account_configured: boolean;
  api_key_valid: boolean;
  limits_set: boolean;
  customer_auth_verified: boolean;

  // Derived
  ready_to_use: boolean;
  blocking_reasons: string[];
}

// =============================================================================
// API CLIENT
// =============================================================================

const PREFLIGHT_CONSOLE_BASE = import.meta.env.VITE_PREFLIGHT_CONSOLE_BASE || 'https://preflight-console.agenticverz.com';

/**
 * Fetch customer preflight status
 * Requires customer-level authentication (tenant-scoped)
 */
export async function getCustomerPreflight(): Promise<CustomerPreflightDTO> {
  const response = await fetch(`${PREFLIGHT_CONSOLE_BASE}/api/v1/preflight`, {
    headers: {
      'Authorization': `Bearer ${getCustomerToken()}`,
      'X-Plane': 'customer',
      'X-Environment': 'preflight',
    },
  });

  if (!response.ok) {
    throw new Error(`Customer preflight failed: ${response.status}`);
  }

  return response.json();
}

/**
 * Get promotion checklist
 * Evaluates readiness to use production console
 */
export async function getCustomerPromotionChecklist(): Promise<CustomerPromotionChecklist> {
  const preflight = await getCustomerPreflight();

  const account_configured = preflight.account.status === 'active';
  const api_key_valid = preflight.keys.has_valid_key;
  const limits_set = preflight.limits.budget_limit_cents > 0;
  const customer_auth_verified = true; // Already authenticated if we got here

  const blocking_reasons: string[] = [];
  if (!account_configured) blocking_reasons.push('Account not configured');
  if (!api_key_valid) blocking_reasons.push('No valid API key');
  if (!limits_set) blocking_reasons.push('Limits not configured');

  return {
    account_configured,
    api_key_valid,
    limits_set,
    customer_auth_verified,
    ready_to_use: blocking_reasons.length === 0,
    blocking_reasons,
  };
}

/**
 * Get customer auth token
 * This should be implemented based on your auth system
 */
function getCustomerToken(): string {
  // In production, this would retrieve the customer's auth token
  // For now, use localStorage or auth store
  return localStorage.getItem('customer-auth-token') || '';
}

// =============================================================================
// TYPE GUARDS
// =============================================================================

export function isCustomerPreflight(obj: unknown): obj is CustomerPreflightDTO {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    (obj as CustomerPreflightDTO).plane === 'customer' &&
    (obj as CustomerPreflightDTO).environment === 'preflight'
  );
}

// =============================================================================
// SAFETY ASSERTIONS
// =============================================================================

/**
 * Verify this DTO contains NO founder-level data
 * Call this before sending any preflight response to ensure no leakage
 */
export function assertNoFounderLeakage(dto: CustomerPreflightDTO): void {
  // These fields should NEVER exist on customer preflight
  const forbidden = [
    'infra',
    'cost_pipeline',
    'recovery',
    'system',
    'feature_flags',
    'frozen_tenants',
    'frozen_keys',
    'active_guardrails',
  ];

  for (const field of forbidden) {
    if (field in dto) {
      throw new Error(`SECURITY: Founder field "${field}" leaked to customer preflight`);
    }
  }
}
