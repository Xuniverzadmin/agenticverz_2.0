/**
 * Guard Overview - Customer Console Landing Screen
 *
 * "The Money Screen" - Answers 4 questions:
 * 1. Am I safe right now?
 * 2. What did you stop for me?
 * 3. What did it cost / save me?
 * 4. Can I stop it myself instantly?
 *
 * Design principles:
 * - Understandable in 5 seconds
 * - No charts, no knobs
 * - Big, obvious kill switch
 * - Today's snapshot only
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { Modal } from '../../components/common/Modal';
import { Spinner } from '../../components/common/Spinner';
import { guardApi } from '../../api/guard';

// Status types
type ProtectionStatus = 'protected' | 'at_risk' | 'stopped';

interface StatusInfo {
  label: string;
  color: 'green' | 'yellow' | 'red';
  description: string;
}

const STATUS_CONFIG: Record<ProtectionStatus, StatusInfo> = {
  protected: {
    label: 'Protected',
    color: 'green',
    description: 'All guardrails active. Traffic flowing normally.',
  },
  at_risk: {
    label: 'At Risk',
    color: 'yellow',
    description: 'Some guardrails triggered. Review recommended.',
  },
  stopped: {
    label: 'Traffic Stopped',
    color: 'red',
    description: 'Kill switch activated. All traffic halted.',
  },
};

export function GuardOverview() {
  const queryClient = useQueryClient();
  const [showKillConfirm, setShowKillConfirm] = useState(false);
  const [showResumeConfirm, setShowResumeConfirm] = useState(false);

  // Fetch current status
  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ['guard', 'status'],
    queryFn: guardApi.getStatus,
    refetchInterval: 5000, // Poll every 5 seconds
  });

  // Fetch today's snapshot
  const { data: snapshot, isLoading: snapshotLoading } = useQuery({
    queryKey: ['guard', 'snapshot'],
    queryFn: guardApi.getTodaySnapshot,
    refetchInterval: 30000, // Poll every 30 seconds
  });

  // Kill switch mutation
  const killMutation = useMutation({
    mutationFn: guardApi.activateKillSwitch,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['guard'] });
      setShowKillConfirm(false);
    },
  });

  // Resume mutation
  const resumeMutation = useMutation({
    mutationFn: guardApi.deactivateKillSwitch,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['guard'] });
      setShowResumeConfirm(false);
    },
  });

  // Determine protection status
  const getProtectionStatus = (): ProtectionStatus => {
    if (!status) return 'protected';
    if (status.is_frozen) return 'stopped';
    if (status.incidents_blocked_24h > 0) return 'at_risk';
    return 'protected';
  };

  const protectionStatus = getProtectionStatus();
  const statusInfo = STATUS_CONFIG[protectionStatus];

  if (statusLoading || snapshotLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-8 p-6 max-w-4xl mx-auto">
      {/* Status Badge - THE MOST IMPORTANT ELEMENT */}
      <div className="text-center">
        <div className={`
          inline-flex items-center gap-3 px-8 py-4 rounded-full text-2xl font-bold
          ${statusInfo.color === 'green' ? 'bg-green-100 text-green-800' : ''}
          ${statusInfo.color === 'yellow' ? 'bg-yellow-100 text-yellow-800' : ''}
          ${statusInfo.color === 'red' ? 'bg-red-100 text-red-800' : ''}
        `}>
          <span className={`
            w-4 h-4 rounded-full animate-pulse
            ${statusInfo.color === 'green' ? 'bg-green-500' : ''}
            ${statusInfo.color === 'yellow' ? 'bg-yellow-500' : ''}
            ${statusInfo.color === 'red' ? 'bg-red-500' : ''}
          `} />
          {statusInfo.label}
        </div>
        <p className="mt-2 text-gray-600">{statusInfo.description}</p>
      </div>

      {/* Kill Switch - Big, Obvious, Immediate */}
      <Card className="text-center py-8">
        {protectionStatus === 'stopped' ? (
          <>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Traffic is Currently Stopped
            </h2>
            <p className="text-gray-600 mb-6">
              All API traffic is being blocked. Click below to resume.
            </p>
            <Button
              size="lg"
              variant="primary"
              onClick={() => setShowResumeConfirm(true)}
              className="px-12 py-4 text-lg bg-green-600 hover:bg-green-700"
            >
              RESUME TRAFFIC
            </Button>
          </>
        ) : (
          <>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Emergency Stop
            </h2>
            <p className="text-gray-600 mb-6">
              Instantly stop all API traffic. This will block all requests.
            </p>
            <Button
              size="lg"
              variant="danger"
              onClick={() => setShowKillConfirm(true)}
              className="px-12 py-4 text-lg bg-red-600 hover:bg-red-700"
            >
              STOP ALL TRAFFIC
            </Button>
          </>
        )}
      </Card>

      {/* Today's Snapshot - Simple Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Requests Today"
          value={snapshot?.requests_today?.toLocaleString() ?? '0'}
          icon="chart"
        />
        <StatCard
          label="Spend Today"
          value={`$${(snapshot?.spend_today_cents ?? 0) / 100}`}
          icon="dollar"
        />
        <StatCard
          label="Incidents Prevented"
          value={snapshot?.incidents_prevented?.toString() ?? '0'}
          icon="shield"
          highlight={snapshot?.incidents_prevented > 0}
        />
        <StatCard
          label="Last Incident"
          value={snapshot?.last_incident_time ?? 'None'}
          icon="clock"
        />
      </div>

      {/* Active Guardrails Summary */}
      <Card>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Active Protection</h3>
        <div className="space-y-2">
          {status?.active_guardrails?.map((guardrail: string, index: number) => (
            <div key={index} className="flex items-center gap-2 text-sm text-gray-700">
              <span className="w-2 h-2 bg-green-500 rounded-full" />
              {guardrail}
            </div>
          )) ?? (
            <p className="text-gray-500">Default guardrails active</p>
          )}
        </div>
      </Card>

      {/* Kill Switch Confirmation Modal */}
      <Modal
        open={showKillConfirm}
        onClose={() => setShowKillConfirm(false)}
        title="Confirm: Stop All Traffic"
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            This will immediately block all API requests to your endpoint.
            No traffic will flow until you manually resume.
          </p>
          <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
            <p className="text-yellow-800 text-sm">
              <strong>Warning:</strong> Active requests will be terminated.
            </p>
          </div>
          <div className="flex gap-3 justify-end">
            <Button
              variant="secondary"
              onClick={() => setShowKillConfirm(false)}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={() => killMutation.mutate()}
              disabled={killMutation.isPending}
            >
              {killMutation.isPending ? 'Stopping...' : 'STOP ALL TRAFFIC'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Resume Confirmation Modal */}
      <Modal
        open={showResumeConfirm}
        onClose={() => setShowResumeConfirm(false)}
        title="Confirm: Resume Traffic"
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            This will resume all API traffic. Guardrails will continue
            to protect you.
          </p>
          <div className="flex gap-3 justify-end">
            <Button
              variant="secondary"
              onClick={() => setShowResumeConfirm(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={() => resumeMutation.mutate()}
              disabled={resumeMutation.isPending}
            >
              {resumeMutation.isPending ? 'Resuming...' : 'Resume Traffic'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

// Stat Card Component
interface StatCardProps {
  label: string;
  value: string;
  icon: 'chart' | 'dollar' | 'shield' | 'clock';
  highlight?: boolean;
}

function StatCard({ label, value, icon, highlight }: StatCardProps) {
  return (
    <Card className={`text-center p-4 ${highlight ? 'ring-2 ring-green-500' : ''}`}>
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-2xl font-bold mt-1 ${highlight ? 'text-green-600' : 'text-gray-900'}`}>
        {value}
      </p>
    </Card>
  );
}

export default GuardOverview;
