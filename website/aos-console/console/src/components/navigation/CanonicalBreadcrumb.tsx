/**
 * CanonicalBreadcrumb - PIN-186 INV-5 Enforcement
 *
 * Phase A-Fix-3: Closes V-003
 *
 * RULES (STRICT):
 * 1. Max breadcrumb length = 2 (Root > Entity)
 * 2. No third segment. Ever.
 * 3. Cross-entity navigation MUST reset breadcrumb
 * 4. Only this component may render breadcrumbs
 *
 * Usage:
 * <CanonicalBreadcrumb
 *   root={{ label: "Incidents", path: "/guard/incidents" }}
 *   entity={{ label: "INC-442", path: "/guard/incidents/442" }}
 * />
 *
 * Cross-entity navigation resets:
 *   Incidents > INC-442 → click "View Run" → Runs > RUN-9812
 *   NOT: Incidents > INC-442 > RUN-9812 (FORBIDDEN)
 */

import { Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';

// =============================================================================
// Types (Contract - No Variants)
// =============================================================================

export type BreadcrumbEntity = {
  label: string;   // "Runs", "Incidents", "Traces", or entity ID like "RUN-9812"
  id?: string;     // Optional ID for display truncation
  path: string;    // Navigation path
};

export type CanonicalBreadcrumbProps = {
  root: BreadcrumbEntity;       // Always present (O2 list page)
  entity?: BreadcrumbEntity;    // O3 entity (optional - only on detail pages)
};

// =============================================================================
// Truncation for IDs (INV-6 alignment)
// =============================================================================

function truncateId(id: string, maxLength = 12): string {
  if (id.length <= maxLength) return id;
  return `${id.slice(0, maxLength)}...`;
}

// =============================================================================
// Component
// =============================================================================

export function CanonicalBreadcrumb({ root, entity }: CanonicalBreadcrumbProps) {
  return (
    <nav
      aria-label="Breadcrumb"
      className="flex items-center gap-2 text-sm text-slate-400 mb-6"
    >
      {/* Root (always linked) */}
      <Link
        to={root.path}
        className="hover:text-white transition-colors"
      >
        {root.label}
      </Link>

      {/* Entity (O3 - current page, not linked) */}
      {entity && (
        <>
          <ChevronRight className="w-3 h-3 text-slate-600" />
          <span className="text-white font-mono">
            {entity.id ? truncateId(entity.id) : entity.label}
          </span>
        </>
      )}
    </nav>
  );
}

export default CanonicalBreadcrumb;
