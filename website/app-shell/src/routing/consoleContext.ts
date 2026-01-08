/**
 * Console Context — Single Source of Truth for Console Identity
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Temporal:
 *   Trigger: build-time (Vite env vars)
 *   Execution: sync
 * Role: Determine console kind and environment from env vars ONLY
 * Reference: PIN-352, Routing Authority Model
 *
 * INFRASTRUCTURE: FROZEN
 * Owner: platform
 * Churn: low (deliberate changes only)
 * Last Frozen: 2026-01-08
 *
 * INVARIANTS:
 * - No hostname sniffing
 * - No runtime detection
 * - All values derived from VITE_* env vars at build time
 * - These values are FROZEN after build
 */

// =============================================================================
// ENVIRONMENT DETECTION (Build-Time Only)
// =============================================================================

/**
 * Is this a preflight environment?
 * Determined by VITE_PREFLIGHT_MODE env var at build time.
 */
export const IS_PREFLIGHT = import.meta.env.VITE_PREFLIGHT_MODE === 'true';

/**
 * Is this a production environment?
 * Inverse of preflight.
 */
export const IS_PRODUCTION = !IS_PREFLIGHT;

/**
 * Console Kind — Which console surface is this?
 * - 'customer': Customer Console (console.agenticverz.com, preflight-console.*)
 * - 'founder': Founder Console (fops.agenticverz.com, preflight-fops.*)
 *
 * Determined by VITE_CONSOLE_KIND env var.
 * Defaults to 'customer' if not specified.
 */
export type ConsoleKind = 'customer' | 'founder';

export const CONSOLE_KIND: ConsoleKind =
  (import.meta.env.VITE_CONSOLE_KIND as ConsoleKind) || 'customer';

/**
 * Is this the customer console?
 */
export const IS_CUSTOMER_CONSOLE = CONSOLE_KIND === 'customer';

/**
 * Is this the founder console (FOPS)?
 */
export const IS_FOUNDER_CONSOLE = CONSOLE_KIND === 'founder';

// =============================================================================
// ENVIRONMENT LABELS (For Display/Debugging)
// =============================================================================

/**
 * Human-readable environment label
 */
export const ENVIRONMENT_LABEL = IS_PREFLIGHT ? 'preflight' : 'production';

/**
 * Human-readable console label
 */
export const CONSOLE_LABEL = CONSOLE_KIND === 'customer' ? 'Customer Console' : 'Founder Console';

/**
 * Full environment identifier (e.g., "customer-preflight", "founder-production")
 */
export const ENVIRONMENT_ID = `${CONSOLE_KIND}-${ENVIRONMENT_LABEL}`;

// =============================================================================
// DEBUG LOGGING (Preflight Only)
// =============================================================================

if (IS_PREFLIGHT && typeof window !== 'undefined') {
  console.log(
    '%c CONSOLE CONTEXT %c',
    'background: #059669; color: white; padding: 2px 6px; border-radius: 3px; font-weight: bold;',
    '',
    {
      IS_PREFLIGHT,
      CONSOLE_KIND,
      ENVIRONMENT_ID,
    }
  );
}
