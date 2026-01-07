// Layer: L1 — Product Experience
// Product: ai-console
// Temporal:
//   Trigger: user
//   Execution: sync
// Role: Placeholder for quarantined credits page
// Reference: PIN-323 (Audit Reinforcement)

// PIN-323: Credits capability (CAP-008) is SDK-only
// Original implementation quarantined to src/quarantine/pages/credits/

import { Card, CardBody } from '@/components/common';

export default function CreditsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
          Credits & Audit
        </h1>
      </div>

      <Card>
        <CardBody className="py-16 text-center">
          <div className="text-gray-500 dark:text-gray-400">
            <p className="text-lg font-medium mb-2">Feature Unavailable</p>
            <p className="text-sm">
              Credits management is available through the SDK.
            </p>
            <p className="text-xs mt-4 text-gray-400">
              Reference: PIN-323 (Capability Quarantine)
            </p>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
