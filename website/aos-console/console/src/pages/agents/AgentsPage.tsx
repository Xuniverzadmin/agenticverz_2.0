import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, RefreshCw, Search } from 'lucide-react';
import { getAgents, getAgentStats, registerAgent, deregisterAgent } from '@/api/agents';
import {
  Card,
  CardBody,
  Button,
  Input,
  Select,
  DataTable,
  StatusBadge,
  Modal,
} from '@/components/common';
import { toastSuccess, toastError } from '@/components/common/Toast';
import { formatTimeAgo, truncateId } from '@/lib/utils';
import type { Agent } from '@/types/agent';

export default function AgentsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [registerModalOpen, setRegisterModalOpen] = useState(false);

  const { data: agents, isLoading } = useQuery({
    queryKey: ['agents', { page, search, status: statusFilter, type: typeFilter }],
    queryFn: () =>
      getAgents({
        page,
        limit: 25,
        search: search || undefined,
        status: (statusFilter as Agent['status']) || undefined,
        type: (typeFilter as Agent['type']) || undefined,
      }),
    refetchInterval: 30000,
  });

  const { data: stats } = useQuery({
    queryKey: ['agent-stats'],
    queryFn: getAgentStats,
    refetchInterval: 30000,
  });

  const deregisterMutation = useMutation({
    mutationFn: deregisterAgent,
    onSuccess: () => {
      toastSuccess('Agent deregistered');
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      queryClient.invalidateQueries({ queryKey: ['agent-stats'] });
    },
    onError: () => {
      toastError('Failed to deregister agent');
    },
  });

  const columns = [
    {
      key: 'id',
      header: 'Agent ID',
      render: (agent: Agent) => (
        <span className="font-mono text-sm">{truncateId(agent.id)}</span>
      ),
    },
    {
      key: 'name',
      header: 'Name',
      render: (agent: Agent) => (
        <span className="font-medium">{agent.name}</span>
      ),
    },
    {
      key: 'type',
      header: 'Type',
      render: (agent: Agent) => (
        <span className="capitalize text-gray-600 dark:text-gray-400">
          {agent.type}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (agent: Agent) => <StatusBadge status={agent.status} />,
    },
    {
      key: 'last_heartbeat',
      header: 'Last Heartbeat',
      render: (agent: Agent) => (
        <span className="text-gray-500">{formatTimeAgo(agent.last_heartbeat)}</span>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (agent: Agent) => (
        <Button
          variant="ghost"
          size="xs"
          onClick={(e) => {
            e.stopPropagation();
            if (confirm('Deregister this agent?')) {
              deregisterMutation.mutate(agent.id);
            }
          }}
        >
          Deregister
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
          Agents
        </h1>
        <Button onClick={() => setRegisterModalOpen(true)} icon={<Plus size={16} />}>
          Register Agent
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardBody className="py-3">
            <div className="text-2xl font-semibold">{stats?.total || 0}</div>
            <div className="text-sm text-gray-500">Total Agents</div>
          </CardBody>
        </Card>
        <Card>
          <CardBody className="py-3">
            <div className="text-2xl font-semibold text-green-600">
              {stats?.active || 0}
            </div>
            <div className="text-sm text-gray-500">Active</div>
          </CardBody>
        </Card>
        <Card>
          <CardBody className="py-3">
            <div className="text-2xl font-semibold text-gray-500">
              {stats?.idle || 0}
            </div>
            <div className="text-sm text-gray-500">Idle</div>
          </CardBody>
        </Card>
        <Card>
          <CardBody className="py-3">
            <div className="text-2xl font-semibold text-yellow-600">
              {stats?.stale || 0}
            </div>
            <div className="text-sm text-gray-500">Stale</div>
          </CardBody>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardBody className="py-3">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search
                  size={16}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                />
                <input
                  type="text"
                  placeholder="Search agents..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900"
                />
              </div>
            </div>
            <Select
              options={[
                { value: '', label: 'All Statuses' },
                { value: 'active', label: 'Active' },
                { value: 'idle', label: 'Idle' },
                { value: 'stale', label: 'Stale' },
              ]}
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            />
            <Select
              options={[
                { value: '', label: 'All Types' },
                { value: 'orchestrator', label: 'Orchestrator' },
                { value: 'worker', label: 'Worker' },
              ]}
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
            />
            <Button
              variant="outline"
              icon={<RefreshCw size={16} />}
              onClick={() => queryClient.invalidateQueries({ queryKey: ['agents'] })}
            >
              Refresh
            </Button>
          </div>
        </CardBody>
      </Card>

      {/* Agents Table */}
      <Card>
        <DataTable
          columns={columns}
          data={agents?.items || []}
          loading={isLoading}
          emptyMessage="No agents registered"
          rowKey={(agent) => agent.id}
          pagination={
            agents
              ? {
                  page,
                  pageSize: 25,
                  total: agents.total,
                  onPageChange: setPage,
                }
              : undefined
          }
        />
      </Card>

      {/* Register Modal */}
      <RegisterAgentModal
        open={registerModalOpen}
        onClose={() => setRegisterModalOpen(false)}
      />
    </div>
  );
}

function RegisterAgentModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [name, setName] = useState('');
  const [type, setType] = useState<'orchestrator' | 'worker'>('worker');

  const mutation = useMutation({
    mutationFn: () =>
      registerAgent({
        agent_name: name,
        agent_type: type,
        capabilities: ['agent_invoke', 'blackboard_read', 'blackboard_write'],
      }),
    onSuccess: () => {
      toastSuccess('Agent registered successfully');
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      queryClient.invalidateQueries({ queryKey: ['agent-stats'] });
      onClose();
      setName('');
    },
    onError: () => {
      toastError('Failed to register agent');
    },
  });

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Register New Agent"
      size="sm"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={() => mutation.mutate()}
            loading={mutation.isPending}
            disabled={!name}
          >
            Register
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <Input
          label="Agent Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="my-agent-001"
        />
        <Select
          label="Agent Type"
          options={[
            { value: 'worker', label: 'Worker' },
            { value: 'orchestrator', label: 'Orchestrator' },
          ]}
          value={type}
          onChange={(e) => setType(e.target.value as 'orchestrator' | 'worker')}
        />
      </div>
    </Modal>
  );
}
