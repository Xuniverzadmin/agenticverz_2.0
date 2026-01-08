/**
 * DomainContextHeader - Domain/Subdomain Context Display
 *
 * Layer: L1 — Product Experience (UI)
 * Product: customer-console
 * Temporal:
 *   Trigger: render
 *   Execution: sync
 * Role: Display current domain + subdomain context in page header
 * Reference: PIN-358 Task Group C
 *
 * GROUP C: Domain/Subdomain Context
 * - Shows Domain → Subdomain hierarchy
 * - Displays order level badge (O1-O5) in INSPECTOR mode
 * - Topic shown as secondary info
 */

import { Layers, Hash, Tag } from 'lucide-react';
import { useDomainContext } from './useDomainContext';
import { useRenderer, InspectorOnly } from '@/contexts/RendererContext';
import { cn } from '@/lib/utils';

// ============================================================================
// Order Level Badge Colors
// ============================================================================

const ORDER_COLORS: Record<string, string> = {
  O1: 'bg-emerald-900/50 text-emerald-400 border-emerald-700',
  O2: 'bg-blue-900/50 text-blue-400 border-blue-700',
  O3: 'bg-purple-900/50 text-purple-400 border-purple-700',
  O4: 'bg-orange-900/50 text-orange-400 border-orange-700',
  O5: 'bg-red-900/50 text-red-400 border-red-700',
};

// ============================================================================
// Component
// ============================================================================

interface DomainContextHeaderProps {
  className?: string;
}

export function DomainContextHeader({ className }: DomainContextHeaderProps) {
  const { context, isLoaded, subdomainLabel, topicLabel, orderLevel } =
    useDomainContext();
  const renderer = useRenderer();

  // Don't render if projection not loaded or no domain context
  if (!isLoaded || !context.domain) {
    return null;
  }

  const orderColorClass = orderLevel
    ? ORDER_COLORS[orderLevel] || 'bg-gray-700 text-gray-400'
    : null;

  return (
    <div className={cn('mb-6', className)}>
      {/* Domain + Subdomain Header */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <Layers size={20} className="text-primary-400" />
          <h1 className="text-2xl font-semibold text-gray-100">
            {context.domain}
          </h1>
        </div>

        {subdomainLabel && (
          <>
            <span className="text-gray-600">/</span>
            <span className="text-xl text-gray-300">{subdomainLabel}</span>
          </>
        )}

        {/* Order Level Badge - INSPECTOR mode only or always visible */}
        {orderLevel && (
          <span
            className={cn(
              'ml-2 px-2 py-0.5 text-xs font-mono rounded border',
              orderColorClass
            )}
          >
            {orderLevel}
          </span>
        )}
      </div>

      {/* Topic + Metadata - INSPECTOR mode shows extra info */}
      {topicLabel && (
        <div className="mt-2 flex items-center gap-4 text-sm">
          <div className="flex items-center gap-1.5 text-gray-400">
            <Tag size={14} />
            <span>Topic: {topicLabel}</span>
          </div>

          <InspectorOnly>
            {context.topicId && (
              <div className="flex items-center gap-1.5 text-gray-500 font-mono text-xs">
                <Hash size={12} />
                <span>{context.topicId}</span>
              </div>
            )}
          </InspectorOnly>
        </div>
      )}

      {/* Panel Info - INSPECTOR mode */}
      <InspectorOnly>
        {context.panelId && (
          <div className="mt-2 px-3 py-2 bg-gray-800/50 rounded-lg border border-gray-700">
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span className="font-mono">
                Panel: <span className="text-gray-400">{context.panelId}</span>
              </span>
              {context.panelName && (
                <span>
                  Name:{' '}
                  <span className="text-gray-400">{context.panelName}</span>
                </span>
              )}
            </div>
          </div>
        )}
      </InspectorOnly>
    </div>
  );
}

export default DomainContextHeader;
