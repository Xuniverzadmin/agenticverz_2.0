// SBA Filters Component
// M15.1.1 Strategy-Bound Agents UI

import { Search } from 'lucide-react';
import type { SBAFilters, AgentType } from '@/types/sba';

interface SBAFiltersBarProps {
  filters: SBAFilters;
  onFilterChange: (filters: SBAFilters) => void;
  domains: string[];
}

export function SBAFiltersBar({ filters, onFilterChange, domains }: SBAFiltersBarProps) {
  const handleChange = (key: keyof SBAFilters, value: string | boolean | null) => {
    onFilterChange({ ...filters, [key]: value });
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search agents..."
          className="pl-9 pr-4 py-2 text-sm border rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700 w-48"
          value={filters.search || ''}
          onChange={(e) => handleChange('search', e.target.value)}
        />
      </div>

      {/* Agent Type */}
      <select
        className="px-3 py-2 text-sm border rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700"
        value={filters.agent_type || ''}
        onChange={(e) => handleChange('agent_type', e.target.value as AgentType | '')}
      >
        <option value="">All Types</option>
        <option value="worker">Worker</option>
        <option value="orchestrator">Orchestrator</option>
        <option value="aggregator">Aggregator</option>
      </select>

      {/* Domain */}
      <select
        className="px-3 py-2 text-sm border rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700"
        value={filters.domain || ''}
        onChange={(e) => handleChange('domain', e.target.value)}
      >
        <option value="">All Domains</option>
        {domains.map((domain) => (
          <option key={domain} value={domain}>
            {domain}
          </option>
        ))}
      </select>

      {/* Validation Status */}
      <select
        className="px-3 py-2 text-sm border rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700"
        value={filters.sba_validated === true ? 'true' : filters.sba_validated === false ? 'false' : ''}
        onChange={(e) => {
          const val = e.target.value;
          handleChange('sba_validated', val === '' ? null : val === 'true');
        }}
      >
        <option value="">All Status</option>
        <option value="true">Validated</option>
        <option value="false">Not Validated</option>
      </select>

      {/* Clear Filters */}
      {(filters.search || filters.agent_type || filters.domain || filters.sba_validated !== undefined) && (
        <button
          className="px-3 py-2 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400"
          onClick={() => onFilterChange({})}
        >
          Clear filters
        </button>
      )}
    </div>
  );
}
