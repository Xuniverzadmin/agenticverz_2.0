// SBA Detail Modal Component
// M16 Agent Governance Console - Profile, Activity, Health Tabs

import { useState } from 'react';
import {
  X,
  User,
  Activity,
  Heart,
  CheckCircle,
  XCircle,
  Store,
  AlertTriangle,
} from 'lucide-react';
import { Spinner, Button } from '@/components/common';
import { checkSpawnEligibility } from '@/api/sba';
import type { SBAAgent } from '@/types/sba';
import { cn } from '@/lib/utils';
import { ProfileTab } from './tabs/ProfileTab';
import { ActivityTab } from './tabs/ActivityTab';
import { HealthTab } from './tabs/HealthTab';

type TabId = 'profile' | 'activity' | 'health';

interface Tab {
  id: TabId;
  label: string;
  icon: typeof User;
}

const TABS: Tab[] = [
  { id: 'profile', label: 'Profile', icon: User },
  { id: 'activity', label: 'Activity', icon: Activity },
  { id: 'health', label: 'Health', icon: Heart },
];

interface SBADetailModalProps {
  agent: SBAAgent | null;
  isLoading: boolean;
  onClose: () => void;
}

export function SBADetailModal({ agent, isLoading, onClose }: SBADetailModalProps) {
  const [activeTab, setActiveTab] = useState<TabId>('profile');
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

  // Calculate completion score for display
  const completionScore = agent?.sba?.how_to_win?.fulfillment_metric
    ? Math.round(agent.sba.how_to_win.fulfillment_metric * 100)
    : 0;
  const isReady = completionScore >= 80;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b dark:border-gray-700">
          <div className="flex items-center gap-4">
            {/* Agent Info */}
            {agent && (
              <>
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {agent.agent_name || agent.agent_id}
                  </h2>
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
                  {isReady && (
                    <span className="flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300">
                      <Store size={12} />
                      Ready
                    </span>
                  )}
                  <span className={cn(
                    'text-xs px-2 py-1 rounded-full',
                    agent.sba_validated
                      ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                      : 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                  )}>
                    {agent.sba_validated ? 'Validated' : 'Not Validated'}
                  </span>
                </div>
              </>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          >
            <X size={20} />
          </button>
        </div>

        {/* Tab Navigation */}
        {agent && (
          <div className="flex border-b dark:border-gray-700 px-6">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    'flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors',
                    isActive
                      ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
                  )}
                >
                  <Icon size={16} />
                  {tab.label}
                </button>
              );
            })}
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex justify-center py-12">
              <Spinner size="lg" />
            </div>
          ) : agent ? (
            agent.sba ? (
              <>
                {activeTab === 'profile' && <ProfileTab agent={agent} />}
                {activeTab === 'activity' && <ActivityTab agent={agent} />}
                {activeTab === 'health' && <HealthTab agent={agent} />}
              </>
            ) : (
              <div className="text-center py-8">
                <AlertTriangle className="mx-auto mb-2 text-yellow-500" size={32} />
                <p className="text-gray-500">No configuration found for this agent</p>
                <p className="text-sm text-gray-400 mt-1">
                  Register an agent profile to enable governance features
                </p>
              </div>
            )
          ) : (
            <div className="text-center py-12 text-gray-500">
              Agent not found
            </div>
          )}
        </div>

        {/* Footer */}
        {agent && (
          <div className="flex items-center justify-between px-6 py-4 border-t dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
            <div className="flex items-center gap-4">
              {/* Completion Score */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500">Score:</span>
                <span className={cn(
                  'text-lg font-bold',
                  completionScore >= 80 ? 'text-green-600' :
                  completionScore >= 60 ? 'text-yellow-600' :
                  completionScore >= 40 ? 'text-orange-600' :
                  'text-red-600'
                )}>
                  {completionScore}%
                </span>
              </div>

              {/* Spawn Result */}
              {spawnResult && (
                <div className={cn(
                  'flex items-center gap-2 text-sm',
                  spawnResult.allowed ? 'text-green-600' : 'text-red-600'
                )}>
                  {spawnResult.allowed ? <CheckCircle size={16} /> : <XCircle size={16} />}
                  {spawnResult.allowed ? 'Can run' : spawnResult.error || 'Cannot run'}
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
                {checkingSpawn ? <Spinner size="sm" /> : 'Check if Ready'}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
