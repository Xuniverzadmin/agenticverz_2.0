/**
 * Customer API Keys Page
 *
 * Phase 5E-4: Customer Essentials
 *
 * Key Management:
 * - Create key (show ONCE, never again)
 * - Rotate key (generates new, invalidates old)
 * - Revoke key (permanent disable)
 *
 * Security Principle:
 * Keys are shown ONCE at creation time.
 * After that, only prefix (e.g., sk-prod-****) is displayed.
 */

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { logger } from '@/lib/consoleLogger';

interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  status: 'active' | 'frozen' | 'revoked';
  created_at: string;
  last_used_at: string | null;
  requests_today: number;
  spend_today_cents: number;
}

interface CreateKeyResponse {
  id: string;
  name: string;
  key: string; // Full key - shown ONCE only
  prefix: string;
  created_at: string;
}

const STATUS_CONFIG: Record<string, { label: string; color: string; border: string }> = {
  active: { label: 'Active', color: 'text-green-400', border: 'border-green-400/40' },
  frozen: { label: 'Frozen', color: 'text-amber-400', border: 'border-amber-400/40' },
  revoked: { label: 'Revoked', color: 'text-red-400', border: 'border-red-400/40' },
};

function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export function KeysPage() {
  const queryClient = useQueryClient();
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showRotateDialog, setShowRotateDialog] = useState<ApiKey | null>(null);
  const [showRevokeDialog, setShowRevokeDialog] = useState<ApiKey | null>(null);
  const [newKeyData, setNewKeyData] = useState<CreateKeyResponse | null>(null);
  const [newKeyName, setNewKeyName] = useState('');
  const [keyCopied, setKeyCopied] = useState(false);

  useEffect(() => {
    logger.componentMount('CustomerKeysPage');
    return () => logger.componentUnmount('CustomerKeysPage');
  }, []);

  // Fetch keys
  const { data: keys, isLoading } = useQuery<ApiKey[]>({
    queryKey: ['customer', 'keys'],
    queryFn: async () => {
      // In production, this would call: GET /api/v1/keys
      return [
        {
          id: 'key_prod_001',
          name: 'Production',
          prefix: 'sk-prod-****1a2b',
          status: 'active',
          created_at: new Date(Date.now() - 30 * 24 * 3600000).toISOString(),
          last_used_at: new Date(Date.now() - 60000).toISOString(),
          requests_today: 1234,
          spend_today_cents: 234,
        },
        {
          id: 'key_dev_002',
          name: 'Development',
          prefix: 'sk-dev-****3c4d',
          status: 'active',
          created_at: new Date(Date.now() - 14 * 24 * 3600000).toISOString(),
          last_used_at: new Date(Date.now() - 3600000).toISOString(),
          requests_today: 56,
          spend_today_cents: 12,
        },
        {
          id: 'key_test_003',
          name: 'Testing (Old)',
          prefix: 'sk-test-****5e6f',
          status: 'revoked',
          created_at: new Date(Date.now() - 60 * 24 * 3600000).toISOString(),
          last_used_at: null,
          requests_today: 0,
          spend_today_cents: 0,
        },
      ];
    },
    refetchInterval: 30000,
    staleTime: 10000,
  });

  // Create key mutation
  const createKeyMutation = useMutation({
    mutationFn: async (name: string): Promise<CreateKeyResponse> => {
      // In production, this would call: POST /api/v1/keys
      // Simulate API response with a new key
      const keyId = `key_${Math.random().toString(36).slice(2, 8)}`;
      const fullKey = `sk-${name.toLowerCase().slice(0, 4)}-${Math.random().toString(36).slice(2, 10)}${Math.random().toString(36).slice(2, 10)}`;

      return {
        id: keyId,
        name,
        key: fullKey,
        prefix: `${fullKey.slice(0, 7)}****${fullKey.slice(-4)}`,
        created_at: new Date().toISOString(),
      };
    },
    onSuccess: (data) => {
      setNewKeyData(data);
      setShowCreateDialog(false);
      setNewKeyName('');
      queryClient.invalidateQueries({ queryKey: ['customer', 'keys'] });
    },
  });

  // Rotate key mutation
  const rotateKeyMutation = useMutation({
    mutationFn: async (keyId: string): Promise<CreateKeyResponse> => {
      // In production: POST /api/v1/keys/{keyId}/rotate
      const key = keys?.find(k => k.id === keyId);
      const fullKey = `sk-${key?.name.toLowerCase().slice(0, 4) || 'key'}-${Math.random().toString(36).slice(2, 10)}${Math.random().toString(36).slice(2, 10)}`;

      return {
        id: keyId,
        name: key?.name || 'Rotated Key',
        key: fullKey,
        prefix: `${fullKey.slice(0, 7)}****${fullKey.slice(-4)}`,
        created_at: new Date().toISOString(),
      };
    },
    onSuccess: (data) => {
      setNewKeyData(data);
      setShowRotateDialog(null);
      queryClient.invalidateQueries({ queryKey: ['customer', 'keys'] });
    },
  });

  // Revoke key mutation
  const revokeKeyMutation = useMutation({
    mutationFn: async (keyId: string) => {
      // In production: DELETE /api/v1/keys/{keyId}
      return { success: true };
    },
    onSuccess: () => {
      setShowRevokeDialog(null);
      queryClient.invalidateQueries({ queryKey: ['customer', 'keys'] });
    },
  });

  const handleCopyKey = async () => {
    if (newKeyData?.key) {
      await navigator.clipboard.writeText(newKeyData.key);
      setKeyCopied(true);
      setTimeout(() => setKeyCopied(false), 2000);
    }
  };

  const handleDismissNewKey = () => {
    setNewKeyData(null);
    setKeyCopied(false);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-slate-400">Loading keys...</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <span>🔑</span> API Keys
          </h1>
          <p className="text-slate-400 mt-1">
            Manage your API keys for accessing the service
          </p>
        </div>
        <button
          onClick={() => setShowCreateDialog(true)}
          className="px-4 py-2 bg-accent-info hover:bg-accent-info/80 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
        >
          + Create Key
        </button>
      </div>

      {/* New Key Alert (shown ONCE after creation) */}
      {newKeyData && (
        <div className="mb-6 bg-green-500/10 border border-green-400/40 rounded-xl p-6">
          <div className="flex items-start gap-3">
            <span className="text-2xl">🔐</span>
            <div className="flex-1">
              <h3 className="font-bold text-green-400">
                {newKeyData.name} Key Created
              </h3>
              <p className="text-sm text-slate-300 mt-1">
                Copy this key now. <span className="text-amber-400 font-medium">You will not see it again.</span>
              </p>

              <div className="mt-4 flex items-center gap-2">
                <code className="flex-1 bg-navy-inset border border-navy-border rounded-lg px-4 py-3 font-mono text-sm text-white break-all">
                  {newKeyData.key}
                </code>
                <button
                  onClick={handleCopyKey}
                  className={`
                    px-4 py-3 rounded-lg text-sm font-medium transition-colors
                    ${keyCopied
                      ? 'bg-green-500 text-white'
                      : 'bg-navy-elevated border border-navy-border text-white hover:bg-navy-subtle'
                    }
                  `}
                >
                  {keyCopied ? '✓ Copied' : 'Copy'}
                </button>
              </div>

              <button
                onClick={handleDismissNewKey}
                className="mt-4 text-sm text-slate-400 hover:text-white transition-colors"
              >
                I have copied the key, dismiss this message
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Keys Table */}
      <div className="bg-navy-surface rounded-xl border border-navy-border overflow-hidden">
        <table className="w-full">
          <thead className="bg-navy-elevated">
            <tr className="text-left text-sm text-slate-400">
              <th className="p-4">Name</th>
              <th className="p-4">Key</th>
              <th className="p-4">Status</th>
              <th className="p-4">Created</th>
              <th className="p-4">Today</th>
              <th className="p-4">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-navy-border">
            {keys?.map((key) => {
              const statusConfig = STATUS_CONFIG[key.status];

              return (
                <tr key={key.id}>
                  <td className="p-4 font-medium text-white">{key.name}</td>
                  <td className="p-4 font-mono text-sm text-slate-400">{key.prefix}</td>
                  <td className="p-4">
                    <span className={`
                      px-2 py-1 rounded border text-xs font-medium bg-transparent
                      ${statusConfig.color} ${statusConfig.border}
                    `}>
                      {statusConfig.label}
                    </span>
                  </td>
                  <td className="p-4 text-sm text-slate-400">
                    {formatDate(key.created_at)}
                  </td>
                  <td className="p-4 text-sm text-slate-400">
                    {key.status === 'active' ? (
                      <span>
                        {key.requests_today} req • ${(key.spend_today_cents / 100).toFixed(2)}
                      </span>
                    ) : (
                      <span className="text-slate-600">—</span>
                    )}
                  </td>
                  <td className="p-4">
                    {key.status === 'active' && (
                      <div className="flex gap-2">
                        <button
                          onClick={() => setShowRotateDialog(key)}
                          className="px-3 py-1 text-sm text-amber-400 hover:bg-amber-500/10 rounded transition-colors"
                        >
                          Rotate
                        </button>
                        <button
                          onClick={() => setShowRevokeDialog(key)}
                          className="px-3 py-1 text-sm text-red-400 hover:bg-red-500/10 rounded transition-colors"
                        >
                          Revoke
                        </button>
                      </div>
                    )}
                    {key.status === 'revoked' && (
                      <span className="text-sm text-slate-600">Revoked</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Security Tips */}
      <div className="mt-6 bg-navy-elevated border border-accent-info/20 rounded-lg p-4">
        <h4 className="font-medium text-accent-info flex items-center gap-2">
          <span>🔒</span> Security Best Practices
        </h4>
        <ul className="text-sm text-slate-300 mt-2 space-y-1">
          <li>• Never share your API keys or commit them to version control</li>
          <li>• Use environment variables to store keys in your applications</li>
          <li>• Rotate keys regularly and after any suspected compromise</li>
          <li>• Use separate keys for production and development</li>
        </ul>
      </div>

      {/* Create Key Dialog */}
      {showCreateDialog && (
        <Dialog
          title="Create New API Key"
          onClose={() => setShowCreateDialog(false)}
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Key Name
              </label>
              <input
                type="text"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                placeholder="e.g., Production, Development"
                className="w-full px-4 py-2 bg-navy-inset border border-navy-border rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-accent-info"
                autoFocus
              />
            </div>

            <div className="bg-amber-500/10 border border-amber-400/30 rounded-lg p-3">
              <p className="text-sm text-amber-400">
                The key will only be shown once after creation. Make sure to copy it immediately.
              </p>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowCreateDialog(false)}
                className="px-4 py-2 text-slate-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => createKeyMutation.mutate(newKeyName)}
                disabled={!newKeyName.trim() || createKeyMutation.isPending}
                className="px-4 py-2 bg-accent-info hover:bg-accent-info/80 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
              >
                {createKeyMutation.isPending ? 'Creating...' : 'Create Key'}
              </button>
            </div>
          </div>
        </Dialog>
      )}

      {/* Rotate Key Dialog */}
      {showRotateDialog && (
        <Dialog
          title="Rotate API Key"
          onClose={() => setShowRotateDialog(null)}
        >
          <div className="space-y-4">
            <p className="text-slate-300">
              Rotating <span className="font-medium text-white">{showRotateDialog.name}</span> will:
            </p>
            <ul className="text-sm text-slate-400 space-y-1 ml-4">
              <li>• Generate a new key</li>
              <li>• Immediately invalidate the current key</li>
              <li>• Any applications using the old key will stop working</li>
            </ul>

            <div className="bg-amber-500/10 border border-amber-400/30 rounded-lg p-3">
              <p className="text-sm text-amber-400">
                Make sure to update your applications with the new key immediately.
              </p>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowRotateDialog(null)}
                className="px-4 py-2 text-slate-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => rotateKeyMutation.mutate(showRotateDialog.id)}
                disabled={rotateKeyMutation.isPending}
                className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg font-medium transition-colors"
              >
                {rotateKeyMutation.isPending ? 'Rotating...' : 'Rotate Key'}
              </button>
            </div>
          </div>
        </Dialog>
      )}

      {/* Revoke Key Dialog */}
      {showRevokeDialog && (
        <Dialog
          title="Revoke API Key"
          onClose={() => setShowRevokeDialog(null)}
        >
          <div className="space-y-4">
            <p className="text-slate-300">
              Are you sure you want to revoke <span className="font-medium text-white">{showRevokeDialog.name}</span>?
            </p>

            <div className="bg-red-500/10 border border-red-400/30 rounded-lg p-3">
              <p className="text-sm text-red-400 font-medium">
                This action cannot be undone.
              </p>
              <p className="text-sm text-red-300 mt-1">
                The key will be permanently disabled and cannot be recovered.
              </p>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowRevokeDialog(null)}
                className="px-4 py-2 text-slate-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => revokeKeyMutation.mutate(showRevokeDialog.id)}
                disabled={revokeKeyMutation.isPending}
                className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors"
              >
                {revokeKeyMutation.isPending ? 'Revoking...' : 'Revoke Key'}
              </button>
            </div>
          </div>
        </Dialog>
      )}
    </div>
  );
}

/**
 * Simple Dialog Component
 */
function Dialog({
  title,
  children,
  onClose,
}: {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative bg-navy-surface border border-navy-border rounded-xl p-6 w-full max-w-md shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-white">{title}</h3>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

export default KeysPage;
