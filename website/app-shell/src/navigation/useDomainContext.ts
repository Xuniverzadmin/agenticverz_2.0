/**
 * useDomainContext - Hook for Domain/Subdomain Context
 *
 * Layer: L1 — Product Experience (UI)
 * Product: customer-console
 * Temporal:
 *   Trigger: route change
 *   Execution: sync
 * Role: Derive domain/subdomain context from current route + projection
 * Reference: PIN-358 Task Group C
 *
 * GROUP C: Domain/Subdomain Context
 * - Derives context from route + projection
 * - Returns domain, subdomain, topic, order info
 * - Used by DomainContextHeader for display
 */

import { useMemo } from 'react';
import { useLocation } from 'react-router-dom';
import {
  getDomainContextForRoute,
  isProjectionLoaded,
  type DomainContext,
} from '@/contracts/ui_projection_loader';

// ============================================================================
// Hook Return Type
// ============================================================================

export interface DomainContextState {
  /** Current domain context derived from route */
  context: DomainContext;
  /** Is projection loaded and context available */
  isLoaded: boolean;
  /** Human-readable subdomain label */
  subdomainLabel: string | null;
  /** Human-readable topic label */
  topicLabel: string | null;
  /** Order level (O1-O5) */
  orderLevel: string | null;
}

// ============================================================================
// Label Formatters
// ============================================================================

/**
 * Convert SNAKE_CASE subdomain to Title Case label.
 * e.g., "SYSTEM_HEALTH" -> "System Health"
 */
function formatSubdomainLabel(subdomain: string | null): string | null {
  if (!subdomain) return null;
  return subdomain
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

/**
 * Convert SNAKE_CASE topic to Title Case label.
 * e.g., "ACTIVE_RUNS" -> "Active Runs"
 */
function formatTopicLabel(topic: string | null): string | null {
  if (!topic) return null;
  return topic
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

// ============================================================================
// Hook
// ============================================================================

/**
 * Hook to get domain/subdomain context from current route.
 * Requires projection to be loaded.
 */
export function useDomainContext(): DomainContextState {
  const location = useLocation();

  return useMemo(() => {
    const isLoaded = isProjectionLoaded();

    if (!isLoaded) {
      return {
        context: {
          domain: null,
          subdomain: null,
          topic: null,
          topicId: null,
          order: null,
          panelId: null,
          panelName: null,
        },
        isLoaded: false,
        subdomainLabel: null,
        topicLabel: null,
        orderLevel: null,
      };
    }

    const context = getDomainContextForRoute(location.pathname);

    return {
      context,
      isLoaded: true,
      subdomainLabel: formatSubdomainLabel(context.subdomain),
      topicLabel: formatTopicLabel(context.topic),
      orderLevel: context.order,
    };
  }, [location.pathname]);
}

export default useDomainContext;
