/**
 * truncateValue - PIN-186 INV-6 Enforcement
 *
 * Phase A-Fix-3: Closes V-004
 *
 * RULES (STRICT):
 * 1. All long values MUST be truncated at O2/O3/O4
 * 2. Full value may ONLY be shown in O5 popup or explicit "View full" action
 * 3. No page-specific truncation logic allowed
 * 4. Use this function EVERYWHERE
 *
 * Usage:
 *   truncateValue(someObject)                    // Default: 120 chars, 2 depth
 *   truncateValue(someObject, { maxChars: 200 }) // Custom char limit
 *   truncateValue(someArray, { maxDepth: 1 })    // Shallow JSON
 */

// =============================================================================
// Types (Contract - No Variants)
// =============================================================================

export type TruncateOptions = {
  maxChars?: number;    // Default: 120
  maxDepth?: number;    // Default: 2 (for objects)
};

// =============================================================================
// Depth-Limited JSON Stringifier
// =============================================================================

function stringifyWithDepth(value: unknown, maxDepth: number, currentDepth = 0): string {
  if (currentDepth >= maxDepth) {
    if (Array.isArray(value)) {
      return `[Array(${value.length})]`;
    }
    if (typeof value === 'object' && value !== null) {
      return '[Object]';
    }
  }

  if (value === null) return 'null';
  if (value === undefined) return 'undefined';

  if (typeof value === 'string') return value;
  if (typeof value === 'number') return String(value);
  if (typeof value === 'boolean') return String(value);

  if (Array.isArray(value)) {
    if (value.length === 0) return '[]';
    if (value.length > 5) {
      const preview = value.slice(0, 3).map(v => stringifyWithDepth(v, maxDepth, currentDepth + 1));
      return `[${preview.join(', ')}, ... +${value.length - 3} more]`;
    }
    const items = value.map(v => stringifyWithDepth(v, maxDepth, currentDepth + 1));
    return `[${items.join(', ')}]`;
  }

  if (typeof value === 'object') {
    const entries = Object.entries(value);
    if (entries.length === 0) return '{}';
    if (entries.length > 4) {
      const preview = entries.slice(0, 3).map(([k, v]) =>
        `${k}: ${stringifyWithDepth(v, maxDepth, currentDepth + 1)}`
      );
      return `{${preview.join(', ')}, ... +${entries.length - 3} more}`;
    }
    const items = entries.map(([k, v]) =>
      `${k}: ${stringifyWithDepth(v, maxDepth, currentDepth + 1)}`
    );
    return `{${items.join(', ')}}`;
  }

  return String(value);
}

// =============================================================================
// Main Export (Single Entry Point)
// =============================================================================

const DEFAULT_MAX_CHARS = 120;
const DEFAULT_MAX_DEPTH = 2;

export function truncateValue(
  value: unknown,
  options?: TruncateOptions
): string {
  const maxChars = options?.maxChars ?? DEFAULT_MAX_CHARS;
  const maxDepth = options?.maxDepth ?? DEFAULT_MAX_DEPTH;

  // Handle null/undefined
  if (value === null) return 'null';
  if (value === undefined) return '—';

  // Handle strings directly
  if (typeof value === 'string') {
    if (value.length <= maxChars) return value;
    return `${value.slice(0, maxChars)}...`;
  }

  // Handle numbers/booleans
  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }

  // Handle objects/arrays with depth limiting
  const str = stringifyWithDepth(value, maxDepth);

  // Final character truncation
  if (str.length <= maxChars) return str;
  return `${str.slice(0, maxChars)}...`;
}

// =============================================================================
// Convenience Exports
// =============================================================================

/**
 * Truncate an ID string (for display in tables/lists)
 * Default: 12 chars with ellipsis
 */
export function truncateId(id: string, maxLength = 12): string {
  if (!id) return '—';
  if (id.length <= maxLength) return id;
  return `${id.slice(0, maxLength)}...`;
}

/**
 * Truncate a hash (show first and last N chars)
 * Default: 8 chars each side
 */
export function truncateHash(hash: string, chars = 8): string {
  if (!hash) return '—';
  if (hash.length <= chars * 2 + 3) return hash;
  return `${hash.slice(0, chars)}...${hash.slice(-chars)}`;
}

export default truncateValue;
