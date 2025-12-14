// SBA Detail Modal Component
// M15.1.1 Strategy-Bound Agents UI - Strategy Cascade View

import { useState } from 'react';
import {
  X,
  ChevronDown,
  ChevronRight,
  Trophy,
  MapPin,
  Zap,
  Box,
  Settings,
  CheckCircle,
  XCircle,
  Store,
  AlertTriangle,
} from 'lucide-react';
import { Card, CardBody, Spinner, Button } from '@/components/common';
import { checkSpawnEligibility } from '@/api/sba';
import type { SBAAgent, SBASchema } from '@/types/sba';
import { cn } from '@/lib/utils';
import { FulfillmentHistoryChart } from './FulfillmentHeatmap';

interface SBADetailModalProps {
  agent: SBAAgent | null;
  isLoading: boolean;
  onClose: () => void;
}

export function SBADetailModal({ agent, isLoading, onClose }: SBADetailModalProps) {
  const [checkingSpawn, setCheckingSpawn] = useState(false);
  const [spawnResult, setSpawnResult] = useState<{ allowed: boolean; error?: string } | null>(null);

  const handleCheckSpawn = async () => {
    if (!agent) return;
    setCheckingSpawn(true);
    try {
      const result = await checkSpawnEligibility(agent.agent_id);
      setSpawnResult({ allowed: result.spawn_allowed, error: result.error });
    } catch {
      setSpawnResult({ allowed: false, error: 'Check failed' });
    } finally {
      setCheckingSpawn(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b dark:border-gray-700">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Strategy Cascade
            </h2>
            {agent && (
              <span className={cn(
                'text-xs px-2 py-1 rounded-full',
                agent.sba_validated
                  ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                  : 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
              )}>
                {agent.sba_validated ? 'Validated' : 'Not Validated'}
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex justify-center py-12">
              <Spinner size="lg" />
            </div>
          ) : agent ? (
            <div className="space-y-4">
              {/* Agent Info */}
              <div className="flex items-center justify-between pb-4 border-b dark:border-gray-700">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">
                    {agent.agent_name || agent.agent_id}
                  </h3>
                  <p className="text-sm text-gray-500">{agent.agent_id}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={cn(
                    'text-xs px-2 py-1 rounded-full',
                    agent.agent_type === 'orchestrator' && 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300',
                    agent.agent_type === 'worker' && 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
                    agent.agent_type === 'aggregator' && 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
                  )}>
                    {agent.agent_type}
                  </span>
                </div>
              </div>

              {/* Strategy Cascade Sections */}
              {agent.sba ? (
                <>
                  <StrategyCascadeSection
                    title="Winning Aspiration"
                    icon={Trophy}
                    iconColor="text-yellow-500"
                    defaultOpen
                  >
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {agent.sba.winning_aspiration.description}
                    </p>
                  </StrategyCascadeSection>

                  <StrategyCascadeSection
                    title="Where to Play"
                    icon={MapPin}
                    iconColor="text-blue-500"
                  >
                    <div className="space-y-3 text-sm">
                      <div>
                        <span className="text-gray-500">Domain:</span>{' '}
                        <span className="font-medium">{agent.sba.where_to_play.domain}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Allowed Tools:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {agent.sba.where_to_play.allowed_tools.map((tool) => (
                            <span key={tool} className="px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 rounded">
                              {tool}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <span className="text-gray-500">Allowed Contexts:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {agent.sba.where_to_play.allowed_contexts.map((ctx) => (
                            <span key={ctx} className="px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 rounded">
                              {ctx}
                            </span>
                          ))}
                        </div>
                      </div>
                      {agent.sba.where_to_play.boundaries && (
                        <div>
                          <span className="text-gray-500">Boundaries:</span>
                          <p className="text-gray-600 dark:text-gray-400 mt-1">
                            {agent.sba.where_to_play.boundaries}
                          </p>
                        </div>
                      )}
                    </div>
                  </StrategyCascadeSection>

                  <StrategyCascadeSection
                    title="How to Win"
                    icon={Zap}
                    iconColor="text-orange-500"
                    defaultOpen
                  >
                    <div className="space-y-3 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="text-gray-500">Fulfillment Metric:</span>
                        <FulfillmentBadge value={agent.sba.how_to_win.fulfillment_metric} />
                      </div>
                      <div>
                        <span className="text-gray-500">Tasks:</span>
                        <ul className="mt-1 space-y-1 ml-4 list-disc text-gray-600 dark:text-gray-400">
                          {agent.sba.how_to_win.tasks.map((task, i) => (
                            <li key={i}>{task}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <span className="text-gray-500">Tests:</span>
                        <ul className="mt-1 space-y-1 ml-4 list-disc text-gray-600 dark:text-gray-400">
                          {agent.sba.how_to_win.tests.map((test, i) => (
                            <li key={i}>{test}</li>
                          ))}
                        </ul>
                      </div>
                      {agent.sba.how_to_win.fulfillment_history && agent.sba.how_to_win.fulfillment_history.length > 0 && (
                        <div className="pt-3 border-t dark:border-gray-700">
                          <span className="text-gray-500 block mb-2">Fulfillment History:</span>
                          <FulfillmentHistoryChart history={agent.sba.how_to_win.fulfillment_history} />
                        </div>
                      )}
                    </div>
                  </StrategyCascadeSection>

                  <StrategyCascadeSection
                    title="Capabilities & Capacity"
                    icon={Box}
                    iconColor="text-purple-500"
                  >
                    <div className="space-y-3 text-sm">
                      <div>
                        <span className="text-gray-500">Dependencies:</span>
                        {agent.sba.capabilities_capacity.dependencies.length > 0 ? (
                          <div className="mt-2 space-y-2">
                            {agent.sba.capabilities_capacity.dependencies.map((dep, i) => (
                              <div key={i} className="flex items-center gap-2 text-xs">
                                <span className={cn(
                                  'px-1.5 py-0.5 rounded',
                                  dep.type === 'tool' && 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
                                  dep.type === 'agent' && 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300',
                                  dep.type === 'api' && 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
                                  dep.type === 'service' && 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300',
                                )}>
                                  {dep.type}
                                </span>
                                <span className="font-medium">{dep.name}</span>
                                {dep.version && <span className="text-gray-400">v{dep.version}</span>}
                                {dep.required ? (
                                  <span className="text-red-500">required</span>
                                ) : (
                                  <span className="text-gray-400">optional</span>
                                )}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-gray-400 mt-1">No dependencies declared</p>
                        )}
                      </div>
                      <div>
                        <span className="text-gray-500">Environment:</span>
                        <div className="mt-1 grid grid-cols-2 gap-2 text-xs">
                          {agent.sba.capabilities_capacity.env.cpu && (
                            <div className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">
                              CPU: {agent.sba.capabilities_capacity.env.cpu}
                            </div>
                          )}
                          {agent.sba.capabilities_capacity.env.memory && (
                            <div className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">
                              Memory: {agent.sba.capabilities_capacity.env.memory}
                            </div>
                          )}
                          {agent.sba.capabilities_capacity.env.budget_tokens && (
                            <div className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">
                              Budget: {agent.sba.capabilities_capacity.env.budget_tokens.toLocaleString()} tokens
                            </div>
                          )}
                          {agent.sba.capabilities_capacity.env.timeout_seconds && (
                            <div className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">
                              Timeout: {agent.sba.capabilities_capacity.env.timeout_seconds}s
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </StrategyCascadeSection>

                  <StrategyCascadeSection
                    title="Enabling Management Systems"
                    icon={Settings}
                    iconColor="text-gray-500"
                  >
                    <div className="space-y-2 text-sm">
                      <div>
                        <span className="text-gray-500">Orchestrator:</span>{' '}
                        <span className="font-medium">{agent.sba.enabling_management_systems.orchestrator}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Governance:</span>{' '}
                        <span className={cn(
                          'font-medium',
                          agent.sba.enabling_management_systems.governance === 'BudgetLLM' && 'text-green-600'
                        )}>
                          {agent.sba.enabling_management_systems.governance}
                        </span>
                      </div>
                    </div>
                  </StrategyCascadeSection>
                </>
              ) : (
                <div className="text-center py-8">
                  <AlertTriangle className="mx-auto mb-2 text-yellow-500" size={32} />
                  <p className="text-gray-500">No SBA schema registered for this agent</p>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              Agent not found
            </div>
          )}
        </div>

        {/* Footer */}
        {agent && (
          <div className="flex items-center justify-between px-6 py-4 border-t dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
            <div>
              {spawnResult && (
                <div className={cn(
                  'flex items-center gap-2 text-sm',
                  spawnResult.allowed ? 'text-green-600' : 'text-red-600'
                )}>
                  {spawnResult.allowed ? <CheckCircle size={16} /> : <XCircle size={16} />}
                  {spawnResult.allowed ? 'Spawn allowed' : spawnResult.error || 'Spawn blocked'}
                </div>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={onClose}>
                Close
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleCheckSpawn}
                disabled={checkingSpawn}
              >
                {checkingSpawn ? <Spinner size="sm" /> : 'Check Spawn Eligibility'}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Strategy Cascade Section Component
// ============================================================================

import type { LucideIcon } from 'lucide-react';

interface StrategyCascadeSectionProps {
  title: string;
  icon: LucideIcon;
  iconColor: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}

function StrategyCascadeSection({
  title,
  icon: Icon,
  iconColor,
  defaultOpen = false,
  children,
}: StrategyCascadeSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <Card>
      <button
        className="w-full flex items-center justify-between px-4 py-3 text-left"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center gap-3">
          <Icon size={20} className={iconColor} />
          <span className="font-medium text-gray-900 dark:text-gray-100">{title}</span>
        </div>
        {isOpen ? (
          <ChevronDown className="text-gray-400" size={20} />
        ) : (
          <ChevronRight className="text-gray-400" size={20} />
        )}
      </button>
      {isOpen && (
        <CardBody className="pt-0 pb-4 px-4 pl-11">
          {children}
        </CardBody>
      )}
    </Card>
  );
}

// ============================================================================
// Fulfillment Badge Component (inline)
// ============================================================================

function FulfillmentBadge({ value }: { value: number }) {
  const percent = Math.round(value * 100);
  const isMarketplaceReady = value >= 0.8;

  const colorClass =
    value < 0.2 ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300' :
    value < 0.4 ? 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300' :
    value < 0.6 ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300' :
    value < 0.8 ? 'bg-lime-100 text-lime-700 dark:bg-lime-900 dark:text-lime-300' :
    'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300';

  return (
    <span className={cn(
      'inline-flex items-center gap-1.5 text-sm px-2.5 py-1 rounded-full font-medium',
      colorClass
    )}>
      {percent}%
      {isMarketplaceReady && <Store size={14} className="text-yellow-500" />}
    </span>
  );
}
