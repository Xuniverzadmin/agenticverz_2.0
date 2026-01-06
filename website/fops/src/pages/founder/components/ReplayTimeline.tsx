/**
 * Replay Timeline Component
 *
 * H1 Replay UX - Timeline visualization for incident replay
 * Features: scrub, play, pause, category filters
 *
 * INVARIANTS:
 * - READ-ONLY: No edit controls, no mutation buttons
 * - Immutable data display
 * - No annotations v1
 *
 * Reference: Phase H1 - Replay UX Enablement
 */

import React, { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import {
  Eye,
  GitBranch,
  Play,
  Pause,
  Bell,
  ChevronRight,
  ChevronDown,
  Clock,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Info,
} from 'lucide-react';
import {
  ReplayItem,
  ReplayCategory,
  getCategoryColor,
  formatDuration,
  formatCost,
} from '@/api/replay';

// =============================================================================
// Types
// =============================================================================

interface ReplayTimelineProps {
  items: ReplayItem[];
  timelineStart: string;
  timelineEnd: string;
  onItemClick?: (item: ReplayItem) => void;
  selectedItemId?: string;
  isPlaying?: boolean;
  onPlayPause?: () => void;
  currentTime?: number; // Position in timeline (0-1)
  onSeek?: (position: number) => void;
}

// =============================================================================
// Category Icon Component
// =============================================================================

function CategoryIcon({ category }: { category: ReplayCategory }) {
  switch (category) {
    case 'input':
      return <Eye className="w-4 h-4" />;
    case 'decision':
      return <GitBranch className="w-4 h-4" />;
    case 'action':
      return <Play className="w-4 h-4" />;
    case 'side_effect':
      return <Bell className="w-4 h-4" />;
    default:
      return <Info className="w-4 h-4" />;
  }
}

// =============================================================================
// Timeline Item Component
// =============================================================================

interface TimelineItemProps {
  item: ReplayItem;
  isSelected: boolean;
  onClick: () => void;
  isHighlighted: boolean;
}

function TimelineItem({ item, isSelected, onClick, isHighlighted }: TimelineItemProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const colorClass = getCategoryColor(item.category);

  const handleExpand = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsExpanded(!isExpanded);
  };

  return (
    <div
      className={`
        border rounded-lg p-3 mb-2 cursor-pointer transition-all
        ${isSelected ? 'border-blue-500 bg-blue-900/20' : 'border-navy-border hover:border-gray-600'}
        ${isHighlighted ? 'ring-2 ring-blue-400 ring-opacity-50' : ''}
      `}
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {/* Category badge */}
          <span className={`px-2 py-1 rounded text-xs font-medium ${colorClass}`}>
            <CategoryIcon category={item.category} />
          </span>
          <span className="text-white font-medium">{item.label}</span>
        </div>

        <div className="flex items-center gap-3 text-sm text-gray-400">
          {/* Duration */}
          {item.duration_ms && (
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {formatDuration(item.duration_ms)}
            </span>
          )}
          {/* Cost */}
          {item.cost_cents && (
            <span className="flex items-center gap-1">
              <DollarSign className="w-3 h-3" />
              {formatCost(item.cost_cents)}
            </span>
          )}
          {/* Timestamp */}
          <span className="text-xs">
            {new Date(item.timestamp).toLocaleTimeString()}
          </span>
          {/* Expand button */}
          <button
            onClick={handleExpand}
            className="p-1 hover:bg-gray-700 rounded"
          >
            {isExpanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Summary */}
      <p className="text-gray-400 text-sm mt-2">{item.summary}</p>

      {/* Expanded data */}
      {isExpanded && (
        <div className="mt-3 pt-3 border-t border-navy-border">
          <div className="text-xs text-gray-500 mb-2">Details (READ-ONLY)</div>
          <pre className="text-xs text-gray-300 bg-gray-900/50 p-2 rounded overflow-x-auto max-h-48">
            {JSON.stringify(item.data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Timeline Scrubber Component
// =============================================================================

interface TimelineScrubberProps {
  position: number; // 0-1
  onSeek: (position: number) => void;
  isPlaying: boolean;
  onPlayPause: () => void;
  timelineStart: string;
  timelineEnd: string;
  items: ReplayItem[];
}

function TimelineScrubber({
  position,
  onSeek,
  isPlaying,
  onPlayPause,
  timelineStart,
  timelineEnd,
  items,
}: TimelineScrubberProps) {
  const trackRef = useRef<HTMLDivElement>(null);

  const handleTrackClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!trackRef.current) return;
    const rect = trackRef.current.getBoundingClientRect();
    const newPosition = (e.clientX - rect.left) / rect.width;
    onSeek(Math.max(0, Math.min(1, newPosition)));
  };

  // Calculate event markers on timeline
  const startTime = new Date(timelineStart).getTime();
  const endTime = new Date(timelineEnd).getTime();
  const duration = endTime - startTime;

  const markers = items.map((item) => {
    const itemTime = new Date(item.timestamp).getTime();
    return {
      position: duration > 0 ? (itemTime - startTime) / duration : 0,
      category: item.category,
    };
  });

  return (
    <div className="bg-gray-900/50 rounded-lg p-4 mb-4">
      <div className="flex items-center gap-4">
        {/* Play/Pause button */}
        <button
          onClick={onPlayPause}
          className="p-2 bg-blue-600 hover:bg-blue-500 rounded-full transition-colors"
        >
          {isPlaying ? (
            <Pause className="w-5 h-5 text-white" />
          ) : (
            <Play className="w-5 h-5 text-white" />
          )}
        </button>

        {/* Timeline track */}
        <div className="flex-1">
          <div
            ref={trackRef}
            className="relative h-8 bg-gray-800 rounded cursor-pointer"
            onClick={handleTrackClick}
          >
            {/* Event markers */}
            {markers.map((marker, idx) => (
              <div
                key={idx}
                className={`absolute w-1 h-4 top-2 rounded ${getCategoryColor(marker.category as ReplayCategory)}`}
                style={{ left: `${marker.position * 100}%` }}
              />
            ))}

            {/* Progress bar */}
            <div
              className="absolute top-0 left-0 h-full bg-blue-600/30 rounded-l"
              style={{ width: `${position * 100}%` }}
            />

            {/* Playhead */}
            <div
              className="absolute top-0 w-1 h-full bg-blue-500"
              style={{ left: `${position * 100}%` }}
            />
          </div>

          {/* Time labels */}
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>{new Date(timelineStart).toLocaleTimeString()}</span>
            <span>{new Date(timelineEnd).toLocaleTimeString()}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Category Filter Component
// =============================================================================

interface CategoryFilterProps {
  enabledCategories: Set<ReplayCategory>;
  onToggle: (category: ReplayCategory) => void;
  counts: Record<ReplayCategory, number>;
}

function CategoryFilter({ enabledCategories, onToggle, counts }: CategoryFilterProps) {
  const categories: ReplayCategory[] = ['input', 'decision', 'action', 'side_effect'];

  return (
    <div className="flex gap-2 mb-4">
      <span className="text-gray-400 text-sm self-center">Filter:</span>
      {categories.map((cat) => (
        <button
          key={cat}
          onClick={() => onToggle(cat)}
          className={`
            px-3 py-1 rounded text-sm flex items-center gap-2 transition-colors
            ${enabledCategories.has(cat)
              ? getCategoryColor(cat)
              : 'bg-gray-800 text-gray-500 hover:bg-gray-700'}
          `}
        >
          <CategoryIcon category={cat} />
          <span className="capitalize">{cat.replace('_', ' ')}</span>
          <span className="text-xs opacity-70">({counts[cat] || 0})</span>
        </button>
      ))}
    </div>
  );
}

// =============================================================================
// Main Timeline Component
// =============================================================================

export default function ReplayTimeline({
  items,
  timelineStart,
  timelineEnd,
  onItemClick,
  selectedItemId,
  isPlaying = false,
  onPlayPause,
  currentTime = 0,
  onSeek,
}: ReplayTimelineProps) {
  // State
  const [enabledCategories, setEnabledCategories] = useState<Set<ReplayCategory>>(
    new Set(['input', 'decision', 'action', 'side_effect'])
  );
  const [highlightedIndex, setHighlightedIndex] = useState<number>(-1);

  // Calculate category counts
  const categoryCounts = useMemo(() => {
    const counts: Record<ReplayCategory, number> = {
      input: 0,
      decision: 0,
      action: 0,
      side_effect: 0,
    };
    items.forEach((item) => {
      if (item.category in counts) {
        counts[item.category]++;
      }
    });
    return counts;
  }, [items]);

  // Filter items
  const filteredItems = useMemo(() => {
    return items.filter((item) => enabledCategories.has(item.category));
  }, [items, enabledCategories]);

  // Handle category toggle
  const handleCategoryToggle = useCallback((category: ReplayCategory) => {
    setEnabledCategories((prev) => {
      const next = new Set(prev);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }
      return next;
    });
  }, []);

  // Update highlighted index based on current time
  useEffect(() => {
    if (!currentTime || !items.length) return;

    const startTime = new Date(timelineStart).getTime();
    const endTime = new Date(timelineEnd).getTime();
    const duration = endTime - startTime;
    const targetTime = startTime + currentTime * duration;

    // Find the item closest to current time
    let closestIdx = -1;
    let closestDiff = Infinity;

    filteredItems.forEach((item, idx) => {
      const itemTime = new Date(item.timestamp).getTime();
      const diff = Math.abs(itemTime - targetTime);
      if (diff < closestDiff) {
        closestDiff = diff;
        closestIdx = idx;
      }
    });

    setHighlightedIndex(closestIdx);
  }, [currentTime, filteredItems, timelineStart, timelineEnd, items.length]);

  // Default handlers if not provided
  const handlePlayPause = onPlayPause || (() => {});
  const handleSeek = onSeek || (() => {});

  return (
    <div className="flex flex-col h-full">
      {/* Immutability notice */}
      <div className="bg-blue-900/20 border border-blue-800 rounded-lg p-2 mb-4 flex items-center gap-2">
        <Info className="w-4 h-4 text-blue-400" />
        <span className="text-blue-300 text-sm">
          Timeline is read-only. No edits or annotations are possible.
        </span>
      </div>

      {/* Timeline scrubber */}
      <TimelineScrubber
        position={currentTime}
        onSeek={handleSeek}
        isPlaying={isPlaying}
        onPlayPause={handlePlayPause}
        timelineStart={timelineStart}
        timelineEnd={timelineEnd}
        items={items}
      />

      {/* Category filters */}
      <CategoryFilter
        enabledCategories={enabledCategories}
        onToggle={handleCategoryToggle}
        counts={categoryCounts}
      />

      {/* Legend */}
      <div className="flex gap-4 mb-4 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <Eye className="w-3 h-3 text-blue-400" /> What agent saw
        </span>
        <span className="flex items-center gap-1">
          <GitBranch className="w-3 h-3 text-yellow-400" /> Why it decided
        </span>
        <span className="flex items-center gap-1">
          <Play className="w-3 h-3 text-green-400" /> What it executed
        </span>
        <span className="flex items-center gap-1">
          <Bell className="w-3 h-3 text-purple-400" /> Side effects
        </span>
      </div>

      {/* Timeline items */}
      <div className="flex-1 overflow-y-auto">
        {filteredItems.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <Info className="w-8 h-8 mx-auto mb-2" />
            <p>No items match the current filter.</p>
          </div>
        ) : (
          filteredItems.map((item, idx) => (
            <TimelineItem
              key={item.id}
              item={item}
              isSelected={item.id === selectedItemId}
              isHighlighted={idx === highlightedIndex}
              onClick={() => onItemClick?.(item)}
            />
          ))
        )}
      </div>

      {/* Stats footer */}
      <div className="mt-4 pt-4 border-t border-navy-border text-sm text-gray-500">
        <div className="flex justify-between">
          <span>
            Showing {filteredItems.length} of {items.length} events
          </span>
          <span className="flex items-center gap-1">
            <AlertTriangle className="w-4 h-4 text-yellow-500" />
            No edit controls available (immutable replay)
          </span>
        </div>
      </div>
    </div>
  );
}
