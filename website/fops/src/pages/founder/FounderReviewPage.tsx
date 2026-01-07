/**
 * FounderReviewPage - Unified Founder Review Dashboard
 *
 * Combines two review workflows:
 * 1. AUTO_EXECUTE Review (PIN-333) - Evidence-only, read-only
 * 2. Contract Review (CRM) - Approve/reject workflow
 *
 * Reference: PIN-333, PIN-293
 */

import { useState } from 'react';
import { Eye, FileCheck, ClipboardList } from 'lucide-react';

// Import the existing AUTO_EXECUTE review content as a subcomponent
import AutoExecuteReviewContent from './AutoExecuteReviewContent';
import ContractReviewContent from './ContractReviewContent';

// =============================================================================
// Types
// =============================================================================

type ReviewTab = 'auto-execute' | 'contracts';

// =============================================================================
// Main Component
// =============================================================================

export default function FounderReviewPage() {
  const [activeTab, setActiveTab] = useState<ReviewTab>('auto-execute');

  return (
    <div className="min-h-screen bg-gray-900 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <Eye className="h-8 w-8 text-amber-400" />
          <h1 className="text-2xl font-bold text-white">Founder Review</h1>
        </div>
        <p className="text-gray-400">
          Unified dashboard for reviewing AUTO_EXECUTE decisions and CRM contracts
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 mb-6 border-b border-gray-700">
        <button
          onClick={() => setActiveTab('auto-execute')}
          className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2 -mb-px ${
            activeTab === 'auto-execute'
              ? 'text-amber-400 border-amber-400'
              : 'text-gray-400 border-transparent hover:text-gray-300 hover:border-gray-600'
          }`}
        >
          <ClipboardList className="h-4 w-4" />
          AUTO_EXECUTE Decisions
          <span className="ml-2 px-2 py-0.5 text-xs bg-emerald-900/30 text-emerald-400 rounded">
            Evidence-Only
          </span>
        </button>

        <button
          onClick={() => setActiveTab('contracts')}
          className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2 -mb-px ${
            activeTab === 'contracts'
              ? 'text-blue-400 border-blue-400'
              : 'text-gray-400 border-transparent hover:text-gray-300 hover:border-gray-600'
          }`}
        >
          <FileCheck className="h-4 w-4" />
          Contract Review
          <span className="ml-2 px-2 py-0.5 text-xs bg-blue-900/30 text-blue-400 rounded">
            Approve/Reject
          </span>
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'auto-execute' && <AutoExecuteReviewContent />}
      {activeTab === 'contracts' && <ContractReviewContent />}
    </div>
  );
}
