/**
 * Incident Filters - M23 Component Map
 *
 * Filter panel for incident search.
 * Filters: policy_status, confidence, model, date range.
 */

import React from 'react';
import { IncidentSearchRequest } from '../../../api/guard';

interface IncidentFiltersProps {
  filters: IncidentSearchRequest;
  onChange: (filters: IncidentSearchRequest) => void;
  onClose: () => void;
  isOpen: boolean;
}

const SEVERITY_OPTIONS = [
  { value: '', label: 'All Severities' },
  { value: 'critical', label: 'Critical' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
];

const POLICY_STATUS_OPTIONS = [
  { value: '', label: 'All Status' },
  { value: 'failed', label: 'Failed' },
  { value: 'passed', label: 'Passed' },
];

const MODEL_OPTIONS = [
  { value: '', label: 'All Models' },
  { value: 'gpt-4', label: 'GPT-4' },
  { value: 'gpt-4o', label: 'GPT-4o' },
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
  { value: 'gpt-4.1', label: 'GPT-4.1' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
];

export function IncidentFilters({
  filters,
  onChange,
  onClose,
  isOpen,
}: IncidentFiltersProps) {
  if (!isOpen) return null;

  const handleFilterChange = (key: keyof IncidentSearchRequest, value: any) => {
    onChange({
      ...filters,
      [key]: value || undefined,
    });
  };

  const handleClearFilters = () => {
    onChange({
      query: filters.query,
      limit: filters.limit,
      offset: 0,
    });
  };

  const activeFilterCount = [
    filters.severity,
    filters.policy_status,
    filters.model,
    filters.user_id,
    filters.time_from,
    filters.time_to,
  ].filter(Boolean).length;

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h3 className="font-medium text-gray-900">Filters</h3>
          {activeFilterCount > 0 && (
            <span className="px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full">
              {activeFilterCount} active
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {activeFilterCount > 0 && (
            <button
              onClick={handleClearFilters}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Clear all
            </button>
          )}
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* User ID */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            User ID
          </label>
          <input
            type="text"
            value={filters.user_id || ''}
            onChange={(e) => handleFilterChange('user_id', e.target.value)}
            placeholder="e.g., cust_8372"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm
                       focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Severity */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Severity
          </label>
          <select
            value={filters.severity || ''}
            onChange={(e) => handleFilterChange('severity', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm
                       focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {SEVERITY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Policy Status */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Policy Status
          </label>
          <select
            value={filters.policy_status || ''}
            onChange={(e) => handleFilterChange('policy_status', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm
                       focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {POLICY_STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Model */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Model
          </label>
          <select
            value={filters.model || ''}
            onChange={(e) => handleFilterChange('model', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm
                       focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {MODEL_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* From Date */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            From
          </label>
          <input
            type="date"
            value={filters.time_from ? filters.time_from.split('T')[0] : ''}
            onChange={(e) => handleFilterChange('time_from', e.target.value ? `${e.target.value}T00:00:00Z` : '')}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm
                       focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* To Date */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            To
          </label>
          <input
            type="date"
            value={filters.time_to ? filters.time_to.split('T')[0] : ''}
            onChange={(e) => handleFilterChange('time_to', e.target.value ? `${e.target.value}T23:59:59Z` : '')}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm
                       focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>
    </div>
  );
}

export default IncidentFilters;
