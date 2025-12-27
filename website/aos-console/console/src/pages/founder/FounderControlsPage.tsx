/**
 * Founder Controls Page - Phase 5E-2: Kill-Switch UI Toggle
 *
 * Control room for system-wide freeze/unfreeze operations.
 *
 * Rules:
 * - Verbatim display of freeze state
 * - No status pills or color-coded interpretations
 * - Actions require explicit confirmation
 * - Clear labeling: "ACTIVE" or "FROZEN"
 *
 * This is a control panel, not a dashboard.
 *
 * Stop Condition:
 * A founder can freeze or unfreeze any tenant/key without CLI access.
 */

import { useEffect, useState, useCallback } from 'react';
import {
  ShieldOff,
  ShieldCheck,
  Power,
  RefreshCw,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Shield,
  Key,
  Building,
  Clock,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { BetaBanner } from '@/components/BetaBanner';
import {
  getKillSwitchStatus,
  freezeTenant,
  unfreezeTenant,
  freezeKey,
  unfreezeKey,
  getActiveGuardrails,
  listIncidents,
  getAllTenants,
  type TenantKillSwitchState,
  type GuardrailSummary,
  type IncidentSummary,
} from '@/api/killswitch';

// =============================================================================
// Constants
// =============================================================================

const POLL_INTERVAL_MS = 15000; // 15 seconds

// =============================================================================
// Utility Functions
// =============================================================================

function formatTimestamp(ts: string | null): string {
  if (!ts) return '-';
  const date = new Date(ts);
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
}

function truncateId(id: string | null | undefined, length = 12): string {
  if (!id) return '-';
  return id.length > length ? `${id.substring(0, length)}...` : id;
}

// =============================================================================
// Components
// =============================================================================

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel: string;
  isDestructive: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  reasonRequired?: boolean;
  reason?: string;
  onReasonChange?: (reason: string) => void;
}

function ConfirmDialog({
  isOpen,
  title,
  message,
  confirmLabel,
  isDestructive,
  onConfirm,
  onCancel,
  reasonRequired,
  reason,
  onReasonChange,
}: ConfirmDialogProps) {
  if (!isOpen) return null;

  const canConfirm = !reasonRequired || (reason && reason.trim().length > 0);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70" onClick={onCancel} />

      {/* Dialog */}
      <div className="relative bg-gray-900 border border-gray-700 rounded-lg p-6 max-w-md w-full mx-4">
        <h3 className="text-lg font-bold text-white mb-2">{title}</h3>
        <p className="text-gray-400 text-sm mb-4">{message}</p>

        {reasonRequired && (
          <div className="mb-4">
            <label className="block text-sm text-gray-500 mb-1">Reason (required)</label>
            <input
              type="text"
              value={reason || ''}
              onChange={(e) => onReasonChange?.(e.target.value)}
              placeholder="Enter reason for this action..."
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
            />
          </div>
        )}

        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded text-sm text-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={!canConfirm}
            className={cn(
              'px-4 py-2 rounded text-sm text-white transition-colors',
              isDestructive
                ? 'bg-red-600 hover:bg-red-500 disabled:bg-red-900 disabled:cursor-not-allowed'
                : 'bg-green-600 hover:bg-green-500 disabled:bg-green-900 disabled:cursor-not-allowed'
            )}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

interface TenantCardProps {
  tenantId: string;
  tenantName: string | null;
  state: TenantKillSwitchState | null;
  isLoading: boolean;
  onRefresh: () => void;
  onFreeze: (reason: string) => void;
  onUnfreeze: () => void;
}

function TenantCard({
  tenantId,
  tenantName,
  state,
  isLoading,
  onRefresh,
  onFreeze,
  onUnfreeze,
}: TenantCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showFreezeDialog, setShowFreezeDialog] = useState(false);
  const [showUnfreezeDialog, setShowUnfreezeDialog] = useState(false);
  const [freezeReason, setFreezeReason] = useState('');

  const isFrozen = state?.tenant.is_frozen ?? false;

  const handleFreeze = () => {
    onFreeze(freezeReason);
    setShowFreezeDialog(false);
    setFreezeReason('');
  };

  const handleUnfreeze = () => {
    onUnfreeze();
    setShowUnfreezeDialog(false);
  };

  return (
    <>
      <div
        className={cn(
          'border rounded bg-gray-900/50 overflow-hidden',
          isFrozen ? 'border-red-500/50' : 'border-gray-800'
        )}
      >
        {/* Header */}
        <div className="p-4">
          <div className="flex items-center gap-4">
            {/* Expand toggle */}
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-gray-500 hover:text-white"
            >
              {isExpanded ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
            </button>

            {/* Icon */}
            <Building className={cn('w-5 h-5', isFrozen ? 'text-red-500' : 'text-gray-500')} />

            {/* Name/ID */}
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="font-mono text-white">{tenantName || truncateId(tenantId)}</span>
                {tenantName && (
                  <span className="text-xs font-mono text-gray-500">{truncateId(tenantId)}</span>
                )}
              </div>
            </div>

            {/* State Label */}
            <span
              className={cn(
                'text-xs font-bold uppercase tracking-wide px-2 py-1 rounded',
                isFrozen ? 'bg-red-950 text-red-400' : 'bg-green-950 text-green-400'
              )}
            >
              {isFrozen ? 'FROZEN' : 'ACTIVE'}
            </span>

            {/* Actions */}
            <div className="flex items-center gap-2">
              <button
                onClick={onRefresh}
                disabled={isLoading}
                className="p-1.5 rounded hover:bg-gray-800 text-gray-500 hover:text-white transition-colors"
              >
                <RefreshCw className={cn('w-4 h-4', isLoading && 'animate-spin')} />
              </button>

              {isFrozen ? (
                <button
                  onClick={() => setShowUnfreezeDialog(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 hover:bg-green-500 rounded text-sm text-white transition-colors"
                >
                  <ShieldCheck className="w-4 h-4" />
                  Unfreeze
                </button>
              ) : (
                <button
                  onClick={() => setShowFreezeDialog(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600 hover:bg-red-500 rounded text-sm text-white transition-colors"
                >
                  <ShieldOff className="w-4 h-4" />
                  Freeze
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Expanded Details */}
        {isExpanded && state && (
          <div className="border-t border-gray-800 p-4 bg-gray-950/50">
            {/* Tenant State */}
            <div className="space-y-2 text-sm">
              <div className="text-gray-500 uppercase text-xs tracking-wide mb-2">
                Tenant State
              </div>
              <div className="flex gap-2">
                <span className="text-gray-500 min-w-32">is_frozen:</span>
                <span className="text-gray-200">{String(state.tenant.is_frozen)}</span>
              </div>
              <div className="flex gap-2">
                <span className="text-gray-500 min-w-32">frozen_at:</span>
                <span className="text-gray-200 font-mono text-xs">
                  {formatTimestamp(state.tenant.frozen_at)}
                </span>
              </div>
              <div className="flex gap-2">
                <span className="text-gray-500 min-w-32">frozen_by:</span>
                <span className="text-gray-200">{state.tenant.frozen_by || '-'}</span>
              </div>
              <div className="flex gap-2">
                <span className="text-gray-500 min-w-32">freeze_reason:</span>
                <span className="text-gray-200">{state.tenant.freeze_reason || '-'}</span>
              </div>
              <div className="flex gap-2">
                <span className="text-gray-500 min-w-32">auto_triggered:</span>
                <span className="text-gray-200">{String(state.tenant.auto_triggered)}</span>
              </div>
              <div className="flex gap-2">
                <span className="text-gray-500 min-w-32">trigger_type:</span>
                <span className="text-gray-200">{state.tenant.trigger_type || '-'}</span>
              </div>
              <div className="flex gap-2">
                <span className="text-gray-500 min-w-32">effective_state:</span>
                <span
                  className={cn(
                    'font-bold',
                    state.effective_state === 'frozen' ? 'text-red-400' : 'text-green-400'
                  )}
                >
                  {state.effective_state.toUpperCase()}
                </span>
              </div>
            </div>

            {/* Keys */}
            {state.keys.length > 0 && (
              <div className="mt-4 space-y-2">
                <div className="text-gray-500 uppercase text-xs tracking-wide mb-2">
                  API Keys ({state.keys.length})
                </div>
                {state.keys.map((key) => (
                  <div
                    key={key.key_id}
                    className={cn(
                      'p-3 rounded border',
                      key.is_frozen
                        ? 'border-red-500/30 bg-red-950/20'
                        : 'border-gray-800 bg-gray-900/50'
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <Key
                        className={cn('w-4 h-4', key.is_frozen ? 'text-red-400' : 'text-gray-500')}
                      />
                      <span className="font-mono text-xs text-gray-300">
                        {truncateId(key.key_id)}
                      </span>
                      <span
                        className={cn(
                          'text-xs font-bold',
                          key.is_frozen ? 'text-red-400' : 'text-green-400'
                        )}
                      >
                        {key.is_frozen ? 'FROZEN' : 'ACTIVE'}
                      </span>
                      {key.is_frozen && (
                        <>
                          <span className="text-xs text-gray-500">
                            at {formatTimestamp(key.frozen_at)}
                          </span>
                          <span className="text-xs text-gray-500">by {key.frozen_by}</span>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Freeze Dialog */}
      <ConfirmDialog
        isOpen={showFreezeDialog}
        title="Freeze Tenant"
        message={`This will immediately freeze all operations for tenant "${tenantName || tenantId}". No in-flight retries. Sticky until manually lifted.`}
        confirmLabel="Freeze Tenant"
        isDestructive={true}
        reasonRequired={true}
        reason={freezeReason}
        onReasonChange={setFreezeReason}
        onConfirm={handleFreeze}
        onCancel={() => {
          setShowFreezeDialog(false);
          setFreezeReason('');
        }}
      />

      {/* Unfreeze Dialog */}
      <ConfirmDialog
        isOpen={showUnfreezeDialog}
        title="Unfreeze Tenant"
        message={`This will reactivate all operations for tenant "${tenantName || tenantId}".`}
        confirmLabel="Unfreeze Tenant"
        isDestructive={false}
        onConfirm={handleUnfreeze}
        onCancel={() => setShowUnfreezeDialog(false)}
      />
    </>
  );
}

interface GuardrailCardProps {
  guardrail: GuardrailSummary;
}

function GuardrailCard({ guardrail }: GuardrailCardProps) {
  return (
    <div className="flex items-center gap-4 p-3 bg-gray-900/50 rounded border border-gray-800">
      <Shield className="w-4 h-4 text-blue-500" />
      <div className="flex-1">
        <div className="text-sm text-white">{guardrail.name}</div>
        <div className="text-xs text-gray-500">{guardrail.description}</div>
      </div>
      <span className="text-xs font-mono text-gray-500">{guardrail.category}</span>
      <span className="text-xs uppercase text-yellow-400">{guardrail.action}</span>
      <span
        className={cn(
          'text-xs',
          guardrail.is_enabled ? 'text-green-400' : 'text-gray-500'
        )}
      >
        {guardrail.is_enabled ? 'ENABLED' : 'DISABLED'}
      </span>
    </div>
  );
}

interface IncidentCardProps {
  incident: IncidentSummary;
}

function IncidentCard({ incident }: IncidentCardProps) {
  return (
    <div className="flex items-center gap-4 p-3 bg-gray-900/50 rounded border border-gray-800">
      <AlertTriangle
        className={cn(
          'w-4 h-4',
          incident.severity === 'critical'
            ? 'text-red-500'
            : incident.severity === 'high'
              ? 'text-orange-500'
              : incident.severity === 'medium'
                ? 'text-yellow-500'
                : 'text-gray-500'
        )}
      />
      <div className="flex-1">
        <div className="text-sm text-white">{incident.title}</div>
        <div className="text-xs text-gray-500">
          {incident.calls_affected} calls affected | {incident.cost_delta_cents / 100} USD
        </div>
      </div>
      <span className="text-xs font-mono text-gray-500">{incident.trigger_type}</span>
      <span
        className={cn(
          'text-xs uppercase',
          incident.status === 'open'
            ? 'text-red-400'
            : incident.status === 'acknowledged'
              ? 'text-yellow-400'
              : 'text-green-400'
        )}
      >
        {incident.status}
      </span>
      <span className="text-xs font-mono text-gray-500">{formatTimestamp(incident.started_at)}</span>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export default function FounderControlsPage() {
  const [tenants, setTenants] = useState<Array<{ tenant_id: string; tenant_name: string | null }>>(
    []
  );
  const [tenantStates, setTenantStates] = useState<Record<string, TenantKillSwitchState | null>>(
    {}
  );
  const [loadingTenants, setLoadingTenants] = useState<Set<string>>(new Set());
  const [guardrails, setGuardrails] = useState<GuardrailSummary[]>([]);
  const [incidents, setIncidents] = useState<IncidentSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  // Fetch tenant kill-switch state
  const fetchTenantState = useCallback(async (tenantId: string) => {
    setLoadingTenants((prev) => new Set(prev).add(tenantId));
    try {
      const state = await getKillSwitchStatus(tenantId);
      setTenantStates((prev) => ({ ...prev, [tenantId]: state }));
    } catch (err) {
      console.error(`Failed to fetch state for tenant ${tenantId}:`, err);
      setTenantStates((prev) => ({ ...prev, [tenantId]: null }));
    } finally {
      setLoadingTenants((prev) => {
        const next = new Set(prev);
        next.delete(tenantId);
        return next;
      });
    }
  }, []);

  // Freeze tenant
  const handleFreezeTenant = async (tenantId: string, reason: string) => {
    setLoadingTenants((prev) => new Set(prev).add(tenantId));
    try {
      await freezeTenant(tenantId, { reason, actor: 'founder' });
      await fetchTenantState(tenantId);
    } catch (err) {
      console.error(`Failed to freeze tenant ${tenantId}:`, err);
      setError(err instanceof Error ? err.message : 'Failed to freeze tenant');
    }
  };

  // Unfreeze tenant
  const handleUnfreezeTenant = async (tenantId: string) => {
    setLoadingTenants((prev) => new Set(prev).add(tenantId));
    try {
      await unfreezeTenant(tenantId, 'founder');
      await fetchTenantState(tenantId);
    } catch (err) {
      console.error(`Failed to unfreeze tenant ${tenantId}:`, err);
      setError(err instanceof Error ? err.message : 'Failed to unfreeze tenant');
    }
  };

  // Fetch all data
  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      const [tenantList, guardrailList] = await Promise.all([
        getAllTenants().catch(() => []),
        getActiveGuardrails().catch(() => []),
      ]);

      setTenants(tenantList);
      setGuardrails(guardrailList);

      // Fetch state for each tenant
      for (const tenant of tenantList) {
        fetchTenantState(tenant.tenant_id);
      }

      // Fetch incidents for first tenant (if any)
      if (tenantList.length > 0) {
        const incidentList = await listIncidents({
          tenant_id: tenantList[0].tenant_id,
          limit: 10,
        }).catch(() => []);
        setIncidents(incidentList);
      }

      setLastRefresh(new Date());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
    } finally {
      setIsLoading(false);
    }
  }, [fetchTenantState]);

  // Initial fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Polling
  useEffect(() => {
    const interval = setInterval(fetchData, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchData]);

  // Count frozen tenants
  const frozenCount = Object.values(tenantStates).filter(
    (s) => s?.tenant.is_frozen
  ).length;

  return (
    <>
      {/* PIN-189: Founder Beta banner - remove after subdomain deployment */}
      <BetaBanner />
      <div className="min-h-screen bg-gray-950">
      {/* Header */}
      <div className="bg-gray-900 border-b border-gray-800 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              <Power className="w-5 h-5 text-red-500" />
              Founder Controls
            </h1>
            <p className="text-gray-500 text-sm mt-1">
              Kill-switch operations. Freeze or unfreeze tenants and keys.
            </p>
          </div>

          <div className="flex items-center gap-4">
            {/* Status Summary */}
            <div className="text-sm">
              <span className="text-gray-500">Tenants: </span>
              <span className="text-white">{tenants.length}</span>
              {frozenCount > 0 && (
                <>
                  <span className="text-gray-500"> | </span>
                  <span className="text-red-400">{frozenCount} frozen</span>
                </>
              )}
            </div>

            {/* Last Refresh */}
            {lastRefresh && (
              <div className="flex items-center gap-1 text-xs text-gray-500">
                <Clock className="w-3 h-3" />
                {lastRefresh.toLocaleTimeString()}
              </div>
            )}

            {/* Refresh Button */}
            <button
              onClick={fetchData}
              disabled={isLoading}
              className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded text-sm text-white transition-colors"
            >
              <RefreshCw className={cn('w-4 h-4', isLoading && 'animate-spin')} />
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 max-w-6xl mx-auto space-y-8">
        {/* Error */}
        {error && (
          <div className="p-4 bg-red-950/30 border border-red-500/50 rounded text-red-400 text-sm flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            {error}
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-400 hover:text-white"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Tenants Section */}
        <section>
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Building className="w-5 h-5 text-gray-500" />
            Tenants
          </h2>
          {tenants.length === 0 ? (
            <div className="p-8 text-center text-gray-500 bg-gray-900/50 rounded border border-gray-800">
              No tenants found
            </div>
          ) : (
            <div className="space-y-3">
              {tenants.map((tenant) => (
                <TenantCard
                  key={tenant.tenant_id}
                  tenantId={tenant.tenant_id}
                  tenantName={tenant.tenant_name}
                  state={tenantStates[tenant.tenant_id] || null}
                  isLoading={loadingTenants.has(tenant.tenant_id)}
                  onRefresh={() => fetchTenantState(tenant.tenant_id)}
                  onFreeze={(reason) => handleFreezeTenant(tenant.tenant_id, reason)}
                  onUnfreeze={() => handleUnfreezeTenant(tenant.tenant_id)}
                />
              ))}
            </div>
          )}
        </section>

        {/* Guardrails Section */}
        <section>
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Shield className="w-5 h-5 text-blue-500" />
            Active Guardrails
          </h2>
          {guardrails.length === 0 ? (
            <div className="p-8 text-center text-gray-500 bg-gray-900/50 rounded border border-gray-800">
              No guardrails configured
            </div>
          ) : (
            <div className="space-y-2">
              {guardrails.map((g) => (
                <GuardrailCard key={g.id} guardrail={g} />
              ))}
            </div>
          )}
        </section>

        {/* Recent Incidents Section */}
        <section>
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-500" />
            Recent Incidents
          </h2>
          {incidents.length === 0 ? (
            <div className="p-8 text-center text-gray-500 bg-gray-900/50 rounded border border-gray-800">
              No recent incidents
            </div>
          ) : (
            <div className="space-y-2">
              {incidents.map((i) => (
                <IncidentCard key={i.id} incident={i} />
              ))}
            </div>
          )}
        </section>
      </div>

      {/* Footer */}
      <div className="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-800 px-6 py-2">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Phase 5E-2: Kill-Switch UI Toggle</span>
          <span>Polling every {POLL_INTERVAL_MS / 1000}s | RBAC: killswitch:read, killswitch:activate, killswitch:reset</span>
        </div>
      </div>
      </div>
    </>
  );
}
