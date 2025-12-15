import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Database, Search, RefreshCw, Plus, Trash2, Edit2, Save, X } from 'lucide-react';
import { Card, CardHeader, CardBody, Spinner, Button, Input } from '@/components/common';
import { getPins, getPin, setPin, deletePin, cleanupPins, type MemoryPin } from '@/api/memory';
import { toastSuccess, toastError } from '@/components/common/Toast';
import { cn } from '@/lib/utils';

export default function BlackboardPage() {
  const [search, setSearch] = useState('');
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');
  const [newTtl, setNewTtl] = useState<number | ''>('');
  const [showCreate, setShowCreate] = useState(false);
  const queryClient = useQueryClient();

  const { data: pins, isLoading, refetch } = useQuery({
    queryKey: ['memory-pins', search],
    queryFn: () => getPins({ prefix: search || undefined, limit: 100 }),
    refetchInterval: 30000,
  });

  const { data: pinDetail, isLoading: loadingDetail } = useQuery({
    queryKey: ['memory-pin', selectedKey],
    queryFn: () => selectedKey ? getPin(selectedKey) : null,
    enabled: !!selectedKey,
  });

  const createMutation = useMutation({
    mutationFn: () => {
      try {
        const value = JSON.parse(newValue);
        return setPin(newKey, value, newTtl || undefined);
      } catch {
        throw new Error('Invalid JSON');
      }
    },
    onSuccess: () => {
      toastSuccess('Pin created');
      setShowCreate(false);
      setNewKey('');
      setNewValue('');
      setNewTtl('');
      queryClient.invalidateQueries({ queryKey: ['memory-pins'] });
    },
    onError: () => toastError('Failed to create pin'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ key, value, ttl }: { key: string; value: unknown; ttl?: number }) =>
      setPin(key, value, ttl),
    onSuccess: () => {
      toastSuccess('Pin updated');
      setEditMode(false);
      queryClient.invalidateQueries({ queryKey: ['memory-pins'] });
      queryClient.invalidateQueries({ queryKey: ['memory-pin', selectedKey] });
    },
    onError: () => toastError('Failed to update pin'),
  });

  const deleteMutation = useMutation({
    mutationFn: (key: string) => deletePin(key),
    onSuccess: () => {
      toastSuccess('Pin deleted');
      setSelectedKey(null);
      queryClient.invalidateQueries({ queryKey: ['memory-pins'] });
    },
    onError: () => toastError('Failed to delete pin'),
  });

  const cleanupMutation = useMutation({
    mutationFn: cleanupPins,
    onSuccess: (data) => {
      toastSuccess(`Cleaned up ${data?.deleted || 0} expired pins`);
      queryClient.invalidateQueries({ queryKey: ['memory-pins'] });
    },
    onError: () => toastError('Cleanup failed'),
  });

  const pinList = Array.isArray(pins) ? pins : [];

  const handleSaveEdit = () => {
    if (!pinDetail) return;
    try {
      const value = JSON.parse(newValue);
      updateMutation.mutate({ key: pinDetail.key, value, ttl: newTtl || undefined });
    } catch {
      toastError('Invalid JSON value');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
            Memory Pins
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Structured key-value storage for agent state
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => cleanupMutation.mutate()}>
            Cleanup Expired
          </Button>
          <Button size="sm" onClick={() => setShowCreate(true)}>
            <Plus size={16} className="mr-1" />
            Create Pin
          </Button>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw size={16} />
          </Button>
        </div>
      </div>

      {/* Create Modal */}
      {showCreate && (
        <Card>
          <CardHeader title="Create New Pin" />
          <CardBody className="space-y-4">
            <Input
              label="Key"
              value={newKey}
              onChange={(e) => setNewKey(e.target.value)}
              placeholder="my:key:name"
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Value (JSON)
              </label>
              <textarea
                value={newValue}
                onChange={(e) => setNewValue(e.target.value)}
                className="w-full h-24 px-3 py-2 text-sm font-mono border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900"
                placeholder='{"key": "value"}'
              />
            </div>
            <Input
              label="TTL (seconds, optional)"
              type="number"
              value={newTtl}
              onChange={(e) => setNewTtl(e.target.value ? Number(e.target.value) : '')}
              placeholder="3600"
            />
            <div className="flex gap-2">
              <Button onClick={() => createMutation.mutate()} loading={createMutation.isPending}>
                Create
              </Button>
              <Button variant="outline" onClick={() => setShowCreate(false)}>
                Cancel
              </Button>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Search */}
      <Card>
        <CardBody>
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search by key prefix..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900"
            />
          </div>
        </CardBody>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pins List */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader title={`Pins (${pinList.length})`} />
            <CardBody className="p-0">
              {isLoading ? (
                <div className="flex justify-center py-8"><Spinner size="lg" /></div>
              ) : (
                <table className="w-full">
                  <thead className="bg-gray-50 dark:bg-gray-700/50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Key
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Type
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Expires
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {pinList.map((pin: MemoryPin) => (
                      <tr
                        key={pin.key}
                        className={cn(
                          'hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer',
                          selectedKey === pin.key && 'bg-blue-50 dark:bg-blue-900/20'
                        )}
                        onClick={() => {
                          setSelectedKey(pin.key);
                          setEditMode(false);
                        }}
                      >
                        <td className="px-4 py-3">
                          <span className="font-mono text-sm">{pin.key}</span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                          {typeof pin.value}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                          {pin.expires_at ? new Date(pin.expires_at).toLocaleString() : 'Never'}
                        </td>
                        <td className="px-4 py-3">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              if (confirm('Delete this pin?')) {
                                deleteMutation.mutate(pin.key);
                              }
                            }}
                            className="text-red-500 hover:text-red-700"
                          >
                            <Trash2 size={14} />
                          </button>
                        </td>
                      </tr>
                    ))}
                    {!pinList.length && (
                      <tr>
                        <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                          <Database className="mx-auto mb-2 text-gray-400" size={32} />
                          No memory pins found
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              )}
            </CardBody>
          </Card>
        </div>

        {/* Pin Detail */}
        <div>
          <Card>
            <CardHeader title="Pin Details">
              {selectedKey && !editMode && (
                <button
                  onClick={() => {
                    setEditMode(true);
                    setNewValue(JSON.stringify(pinDetail?.value, null, 2));
                    setNewTtl(pinDetail?.ttl_seconds || '');
                  }}
                  className="text-primary-600 hover:text-primary-700"
                >
                  <Edit2 size={16} />
                </button>
              )}
            </CardHeader>
            <CardBody>
              {selectedKey ? (
                loadingDetail ? (
                  <div className="flex justify-center py-4"><Spinner /></div>
                ) : pinDetail ? (
                  <div className="space-y-4">
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase mb-1">Key</p>
                      <p className="font-mono text-sm break-all">{pinDetail.key}</p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase mb-1">Value</p>
                      {editMode ? (
                        <textarea
                          value={newValue}
                          onChange={(e) => setNewValue(e.target.value)}
                          className="w-full h-32 px-3 py-2 text-xs font-mono border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900"
                        />
                      ) : (
                        <pre className="bg-gray-50 dark:bg-gray-800 p-3 rounded text-xs overflow-auto max-h-48">
                          {JSON.stringify(pinDetail.value, null, 2)}
                        </pre>
                      )}
                    </div>
                    {editMode && (
                      <Input
                        label="TTL (seconds)"
                        type="number"
                        value={newTtl}
                        onChange={(e) => setNewTtl(e.target.value ? Number(e.target.value) : '')}
                      />
                    )}
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase mb-1">Created</p>
                      <p className="text-sm">{new Date(pinDetail.created_at).toLocaleString()}</p>
                    </div>
                    {pinDetail.expires_at && (
                      <div>
                        <p className="text-xs font-medium text-gray-500 uppercase mb-1">Expires</p>
                        <p className="text-sm">{new Date(pinDetail.expires_at).toLocaleString()}</p>
                      </div>
                    )}
                    {editMode && (
                      <div className="flex gap-2 pt-2">
                        <Button size="sm" onClick={handleSaveEdit} loading={updateMutation.isPending}>
                          <Save size={14} className="mr-1" />
                          Save
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => setEditMode(false)}>
                          <X size={14} className="mr-1" />
                          Cancel
                        </Button>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">Pin not found</p>
                )
              ) : (
                <p className="text-sm text-gray-500">Select a pin to view details</p>
              )}
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}
