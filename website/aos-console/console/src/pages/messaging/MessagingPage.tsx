import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Send } from 'lucide-react';
import { getMessages, getMessageStats } from '@/api/messages';
import { Card, CardBody, Button, Select, DataTable, StatusBadge, Badge } from '@/components/common';
import { formatTimeAgo, truncateId, formatDurationMs } from '@/lib/utils';
import type { Message } from '@/types/message';

export default function MessagingPage() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');

  const { data: messages, isLoading } = useQuery({
    queryKey: ['messages', { page, status: statusFilter, type: typeFilter }],
    queryFn: () =>
      getMessages({
        page,
        limit: 25,
        status: statusFilter || undefined,
        type: typeFilter || undefined,
      }),
    refetchInterval: 10000,
  });

  const { data: stats } = useQuery({
    queryKey: ['message-stats'],
    queryFn: () => getMessageStats('1h'),
    refetchInterval: 30000,
  });

  const columns = [
    {
      key: 'time',
      header: 'Time',
      render: (msg: Message) => (
        <span className="text-sm text-gray-500">{formatTimeAgo(msg.sent_at)}</span>
      ),
    },
    {
      key: 'from',
      header: 'From',
      render: (msg: Message) => (
        <span className="font-mono text-sm">{truncateId(msg.from_agent, 10)}</span>
      ),
    },
    {
      key: 'to',
      header: 'To',
      render: (msg: Message) => (
        <span className="font-mono text-sm">{truncateId(msg.to_agent, 10)}</span>
      ),
    },
    {
      key: 'type',
      header: 'Type',
      render: (msg: Message) => (
        <Badge variant="default" size="sm">
          {msg.type}
        </Badge>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (msg: Message) => <StatusBadge status={msg.status} />,
    },
    {
      key: 'latency',
      header: 'Latency',
      render: (msg: Message) => (
        <span className="text-sm">
          {msg.latency_ms ? formatDurationMs(msg.latency_ms) : '-'}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
          Messaging Inspector
        </h1>
        <Button icon={<Send size={16} />}>Send Message</Button>
      </div>

      {/* Latency Stats */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardBody className="py-3">
            <div className="text-2xl font-semibold">{stats?.latency?.p50_ms || 0}ms</div>
            <div className="text-sm text-gray-500">P50 Latency</div>
          </CardBody>
        </Card>
        <Card>
          <CardBody className="py-3">
            <div className="text-2xl font-semibold text-yellow-600">
              {stats?.latency?.p95_ms || 0}ms
            </div>
            <div className="text-sm text-gray-500">P95 Latency</div>
          </CardBody>
        </Card>
        <Card>
          <CardBody className="py-3">
            <div className="text-2xl font-semibold text-orange-600">
              {stats?.latency?.p99_ms || 0}ms
            </div>
            <div className="text-sm text-gray-500">P99 Latency</div>
          </CardBody>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardBody className="py-3">
          <div className="flex gap-4">
            <Select
              options={[
                { value: '', label: 'All Statuses' },
                { value: 'pending', label: 'Pending' },
                { value: 'delivered', label: 'Delivered' },
                { value: 'read', label: 'Read' },
                { value: 'failed', label: 'Failed' },
              ]}
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
            />
            <Select
              options={[
                { value: '', label: 'All Types' },
                { value: 'invoke', label: 'Invoke' },
                { value: 'response', label: 'Response' },
                { value: 'notification', label: 'Notification' },
              ]}
              value={typeFilter}
              onChange={(e) => {
                setTypeFilter(e.target.value);
                setPage(1);
              }}
            />
          </div>
        </CardBody>
      </Card>

      {/* Messages Table */}
      <Card>
        <DataTable
          columns={columns}
          data={messages?.items || []}
          loading={isLoading}
          emptyMessage="No messages found"
          rowKey={(msg) => msg.id}
          pagination={
            messages
              ? {
                  page,
                  pageSize: 25,
                  total: messages.total,
                  onPageChange: setPage,
                }
              : undefined
          }
        />
      </Card>
    </div>
  );
}
