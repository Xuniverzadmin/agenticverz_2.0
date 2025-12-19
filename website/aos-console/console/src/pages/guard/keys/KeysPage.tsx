/**
 * Keys & Access Page - Customer Console
 *
 * Very tight scope:
 * - List API keys
 * - Status (Active / Frozen)
 * - Freeze / Unfreeze
 * - Last seen
 *
 * No key creation here - that's in main settings.
 * This is about CONTROL during incidents.
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card } from '../../../components/common/Card';
import { Button } from '../../../components/common/Button';
import { Badge } from '../../../components/common/Badge';
import { Modal } from '../../../components/common/Modal';
import { Spinner } from '../../../components/common/Spinner';
import { guardApi } from '../../../api/guard';

interface ApiKey {
  id: string;
  name: string;
  prefix: string;  // First 8 chars of key
  status: 'active' | 'frozen' | 'revoked';
  created_at: string;
  last_seen_at: string | null;
  requests_today: number;
  spend_today_cents: number;
}

const STATUS_CONFIG = {
  active: { label: 'Active', color: 'green', bgColor: 'bg-green-100', textColor: 'text-green-800' },
  frozen: { label: 'Frozen', color: 'yellow', bgColor: 'bg-yellow-100', textColor: 'text-yellow-800' },
  revoked: { label: 'Revoked', color: 'red', bgColor: 'bg-red-100', textColor: 'text-red-800' },
};

export function KeysPage() {
  const queryClient = useQueryClient();
  const [selectedKey, setSelectedKey] = useState<ApiKey | null>(null);
  const [actionType, setActionType] = useState<'freeze' | 'unfreeze' | null>(null);

  // Fetch API keys
  const { data: keys, isLoading } = useQuery({
    queryKey: ['guard', 'keys'],
    queryFn: guardApi.getApiKeys,
    refetchInterval: 30000,
  });

  // Freeze mutation
  const freezeMutation = useMutation({
    mutationFn: (keyId: string) => guardApi.freezeApiKey(keyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['guard', 'keys'] });
      setSelectedKey(null);
      setActionType(null);
    },
  });

  // Unfreeze mutation
  const unfreezeMutation = useMutation({
    mutationFn: (keyId: string) => guardApi.unfreezeApiKey(keyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['guard', 'keys'] });
      setSelectedKey(null);
      setActionType(null);
    },
  });

  const handleAction = (key: ApiKey, action: 'freeze' | 'unfreeze') => {
    setSelectedKey(key);
    setActionType(action);
  };

  const confirmAction = () => {
    if (!selectedKey || !actionType) return;

    if (actionType === 'freeze') {
      freezeMutation.mutate(selectedKey.id);
    } else {
      unfreezeMutation.mutate(selectedKey.id);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    );
  }

  const keyList = keys?.items ?? [];
  const activeKeys = keyList.filter((k: ApiKey) => k.status === 'active').length;
  const frozenKeys = keyList.filter((k: ApiKey) => k.status === 'frozen').length;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">API Keys</h1>
          <p className="text-gray-600 mt-1">
            Freeze or unfreeze keys instantly during incidents.
          </p>
        </div>
        <div className="flex gap-2">
          <Badge variant="success">{activeKeys} Active</Badge>
          {frozenKeys > 0 && (
            <Badge variant="warning">{frozenKeys} Frozen</Badge>
          )}
        </div>
      </div>

      {keyList.length === 0 ? (
        <Card className="text-center py-12">
          <div className="text-gray-400 text-5xl mb-4">🔑</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No API Keys</h3>
          <p className="text-gray-500">
            Create API keys in your main account settings.
          </p>
        </Card>
      ) : (
        <div className="space-y-4">
          {keyList.map((key: ApiKey) => (
            <KeyCard
              key={key.id}
              apiKey={key}
              onFreeze={() => handleAction(key, 'freeze')}
              onUnfreeze={() => handleAction(key, 'unfreeze')}
            />
          ))}
        </div>
      )}

      {/* Confirmation Modal */}
      <Modal
        isOpen={!!selectedKey && !!actionType}
        onClose={() => {
          setSelectedKey(null);
          setActionType(null);
        }}
        title={actionType === 'freeze' ? 'Freeze API Key' : 'Unfreeze API Key'}
      >
        <div className="space-y-4">
          {actionType === 'freeze' ? (
            <>
              <p className="text-gray-600">
                This will immediately block all requests using this key.
                No traffic will be allowed until you unfreeze it.
              </p>
              <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
                <p className="text-yellow-800 text-sm">
                  <strong>Key:</strong> {selectedKey?.name} ({selectedKey?.prefix}...)
                </p>
              </div>
            </>
          ) : (
            <>
              <p className="text-gray-600">
                This will resume traffic for this key. Guardrails will
                continue to protect you.
              </p>
              <div className="bg-green-50 border border-green-200 rounded p-3">
                <p className="text-green-800 text-sm">
                  <strong>Key:</strong> {selectedKey?.name} ({selectedKey?.prefix}...)
                </p>
              </div>
            </>
          )}

          <div className="flex gap-3 justify-end">
            <Button
              variant="secondary"
              onClick={() => {
                setSelectedKey(null);
                setActionType(null);
              }}
            >
              Cancel
            </Button>
            <Button
              variant={actionType === 'freeze' ? 'danger' : 'primary'}
              onClick={confirmAction}
              disabled={freezeMutation.isPending || unfreezeMutation.isPending}
            >
              {(freezeMutation.isPending || unfreezeMutation.isPending)
                ? 'Processing...'
                : actionType === 'freeze'
                  ? 'Freeze Key'
                  : 'Unfreeze Key'
              }
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

// Key Card Component
interface KeyCardProps {
  apiKey: ApiKey;
  onFreeze: () => void;
  onUnfreeze: () => void;
}

function KeyCard({ apiKey, onFreeze, onUnfreeze }: KeyCardProps) {
  const status = STATUS_CONFIG[apiKey.status];
  const lastSeen = apiKey.last_seen_at
    ? formatTimeAgo(new Date(apiKey.last_seen_at))
    : 'Never';

  return (
    <Card className="hover:shadow-sm transition-shadow">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* Status Indicator */}
          <div className={`w-3 h-3 rounded-full ${
            apiKey.status === 'active' ? 'bg-green-500' :
            apiKey.status === 'frozen' ? 'bg-yellow-500' :
            'bg-red-500'
          }`} />

          {/* Key Info */}
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-medium text-gray-900">{apiKey.name}</h3>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${status.bgColor} ${status.textColor}`}>
                {status.label}
              </span>
            </div>
            <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
              <span className="font-mono">{apiKey.prefix}...</span>
              <span>Last seen: {lastSeen}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-6">
          {/* Today's Stats */}
          <div className="text-right">
            <p className="text-sm text-gray-500">Today</p>
            <p className="font-medium text-gray-900">
              {apiKey.requests_today.toLocaleString()} calls
              <span className="text-gray-400 mx-1">·</span>
              ${(apiKey.spend_today_cents / 100).toFixed(2)}
            </p>
          </div>

          {/* Action Button */}
          {apiKey.status === 'active' && (
            <Button
              variant="secondary"
              size="sm"
              onClick={onFreeze}
              className="text-yellow-700 border-yellow-300 hover:bg-yellow-50"
            >
              Freeze
            </Button>
          )}
          {apiKey.status === 'frozen' && (
            <Button
              variant="secondary"
              size="sm"
              onClick={onUnfreeze}
              className="text-green-700 border-green-300 hover:bg-green-50"
            >
              Unfreeze
            </Button>
          )}
          {apiKey.status === 'revoked' && (
            <span className="text-sm text-gray-400">Revoked</span>
          )}
        </div>
      </div>
    </Card>
  );
}

// Helper function
function formatTimeAgo(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;

  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

export default KeysPage;
