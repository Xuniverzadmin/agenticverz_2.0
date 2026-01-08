/**
 * ProjectionBreadcrumb - Projection-Derived Breadcrumb Component
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Temporal:
 *   Trigger: render
 *   Execution: sync
 * Role: Display breadcrumb derived from route + projection
 * Reference: PIN-358 Task Group B
 *
 * BREADCRUMB FORMAT:
 *   Domain › Subdomain? › Topic? › Panel › Entity?
 *
 * RENDERING RULES:
 * - Active segment is not linked
 * - Domain/Panel segments are always linked
 * - Subdomain/Topic are informational (link to domain)
 * - Entity is always active (terminal)
 */

import { Link } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useBreadcrumb, type BreadcrumbSegment } from './useBreadcrumb';
import { useRenderer, InspectorOnly } from '@/contexts/RendererContext';

// ============================================================================
// Segment Component
// ============================================================================

interface BreadcrumbSegmentItemProps {
  segment: BreadcrumbSegment;
  isLast: boolean;
  showIds: boolean;
}

function BreadcrumbSegmentItem({ segment, isLast, showIds }: BreadcrumbSegmentItemProps) {
  const baseClasses = 'transition-colors text-sm';

  // Active segment (current page) - not linked
  if (segment.isActive) {
    return (
      <span className={cn(baseClasses, 'text-gray-100 font-medium')}>
        {segment.label}
        {showIds && segment.id && (
          <span className="ml-1 text-xs text-gray-500 font-mono">
            ({segment.id})
          </span>
        )}
      </span>
    );
  }

  // Linked segment
  return (
    <Link
      to={segment.path}
      className={cn(baseClasses, 'text-gray-400 hover:text-gray-200')}
    >
      {segment.label}
      {showIds && segment.id && (
        <span className="ml-1 text-xs text-gray-600 font-mono">
          ({segment.id})
        </span>
      )}
    </Link>
  );
}

// ============================================================================
// Separator Component
// ============================================================================

function BreadcrumbSeparator() {
  return (
    <ChevronRight
      size={14}
      className="text-gray-600 flex-shrink-0"
    />
  );
}

// ============================================================================
// Main Component
// ============================================================================

interface ProjectionBreadcrumbProps {
  /** Optional class name for styling */
  className?: string;
  /** Show home icon before first segment */
  showHomeIcon?: boolean;
}

export function ProjectionBreadcrumb({
  className,
  showHomeIcon = false,
}: ProjectionBreadcrumbProps) {
  const breadcrumb = useBreadcrumb();
  const renderer = useRenderer();

  // Don't render if no segments or projection not loaded
  if (!breadcrumb.isLoaded || breadcrumb.segments.length === 0) {
    return null;
  }

  return (
    <nav
      aria-label="Breadcrumb"
      className={cn('flex items-center gap-2', className)}
    >
      {/* Optional home icon */}
      {showHomeIcon && (
        <>
          <Home size={14} className="text-gray-500" />
          <BreadcrumbSeparator />
        </>
      )}

      {/* Breadcrumb segments */}
      {breadcrumb.segments.map((segment, index) => (
        <div key={`${segment.type}-${index}`} className="flex items-center gap-2">
          {/* Separator (not before first segment) */}
          {index > 0 && <BreadcrumbSeparator />}

          {/* Segment */}
          <BreadcrumbSegmentItem
            segment={segment}
            isLast={index === breadcrumb.segments.length - 1}
            showIds={renderer.showInternalIDs}
          />
        </div>
      ))}

      {/* Debug info in inspector mode */}
      <InspectorOnly>
        <span className="ml-4 text-xs text-gray-600 font-mono">
          [depth: {breadcrumb.segments.length}]
        </span>
      </InspectorOnly>
    </nav>
  );
}

export default ProjectionBreadcrumb;
