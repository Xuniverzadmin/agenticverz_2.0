import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import * as Tabs from '@radix-ui/react-tabs';
import { Download, Plus } from 'lucide-react';
import { getCreditBalance, getLedger, getCreditUsage, getInvokeAudit } from '@/api/credits';
import { Card, CardHeader, CardBody, Button, DataTable, Badge, StatusBadge } from '@/components/common';
import { formatCredits, formatTimeAgo, formatDurationMs, truncateId } from '@/lib/utils';
import { cn } from '@/lib/utils';
import type { LedgerEntry, InvokeAudit } from '@/types/credit';

export default function CreditsPage() {
  const [activeTab, setActiveTab] = useState('ledger');

  const { data: balance } = useQuery({
    queryKey: ['credits-balance'],
    queryFn: getCreditBalance,
    refetchInterval: 30000,
  });

  const { data: usage } = useQuery({
    queryKey: ['credits-usage-month'],
    queryFn: () => getCreditUsage({ range: 'month' }),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
          Credits & Audit
        </h1>
        <Button icon={<Plus size={16} />}>Add Credits</Button>
      </div>

      {/* Balance Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="md:col-span-2">
          <CardBody>
            <div className="text-sm text-gray-500">Current Balance</div>
            <div className="text-3xl font-bold mt-1">
              {formatCredits(balance?.balance || 0)}
            </div>
            <div className="text-sm text-gray-500 mt-2">
              Reserved: {formatCredits(balance?.reserved || 0)} | Available:{' '}
              {formatCredits(balance?.available || 0)}
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <div className="text-sm text-gray-500">This Month</div>
            <div className="text-2xl font-semibold mt-1">
              {formatCredits((usage as { total_spent?: number })?.total_spent || 0)}
            </div>
            <div className="text-sm text-gray-500">spent</div>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <div className="text-sm text-gray-500">Refunded</div>
            <div className="text-2xl font-semibold text-green-600 mt-1">
              {formatCredits((usage as { total_refunded?: number })?.total_refunded || 0)}
            </div>
            <div className="text-sm text-gray-500">this month</div>
          </CardBody>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs.Root value={activeTab} onValueChange={setActiveTab}>
        <Tabs.List className="flex gap-1 border-b border-gray-200 dark:border-gray-700">
          {['ledger', 'audit', 'analytics'].map((tab) => (
            <Tabs.Trigger
              key={tab}
              value={tab}
              className={cn(
                'px-4 py-2 text-sm font-medium capitalize border-b-2 -mb-px transition-colors',
                activeTab === tab
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              )}
            >
              {tab}
            </Tabs.Trigger>
          ))}
        </Tabs.List>

        <Tabs.Content value="ledger" className="mt-6">
          <LedgerTab />
        </Tabs.Content>

        <Tabs.Content value="audit" className="mt-6">
          <AuditTab />
        </Tabs.Content>

        <Tabs.Content value="analytics" className="mt-6">
          <AnalyticsTab />
        </Tabs.Content>
      </Tabs.Root>
    </div>
  );
}

function LedgerTab() {
  const [page, setPage] = useState(1);

  const { data: ledger, isLoading } = useQuery({
    queryKey: ['ledger', { page }],
    queryFn: () => getLedger({ page, limit: 25 }),
  });

  const typeVariants: Record<string, 'default' | 'success' | 'error' | 'warning'> = {
    reserve: 'warning',
    charge: 'error',
    refund: 'success',
    topup: 'success',
  };

  const columns = [
    {
      key: 'created_at',
      header: 'Time',
      render: (entry: LedgerEntry) => (
        <span className="text-sm text-gray-500">{formatTimeAgo(entry.created_at)}</span>
      ),
    },
    {
      key: 'type',
      header: 'Type',
      render: (entry: LedgerEntry) => (
        <Badge variant={typeVariants[entry.type] || 'default'} size="sm">
          {entry.type}
        </Badge>
      ),
    },
    {
      key: 'amount',
      header: 'Amount',
      render: (entry: LedgerEntry) => (
        <span
          className={cn(
            'font-medium',
            entry.amount > 0 ? 'text-green-600' : 'text-red-600'
          )}
        >
          {entry.amount > 0 ? '+' : ''}
          {formatCredits(entry.amount)}
        </span>
      ),
    },
    {
      key: 'balance_after',
      header: 'Balance',
      render: (entry: LedgerEntry) => (
        <span className="text-sm">{formatCredits(entry.balance_after)}</span>
      ),
    },
    {
      key: 'job_id',
      header: 'Job',
      render: (entry: LedgerEntry) => (
        <span className="font-mono text-sm text-gray-500">
          {entry.job_id ? truncateId(entry.job_id, 8) : '-'}
        </span>
      ),
    },
  ];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <span className="font-semibold">Transaction Ledger</span>
          <Button variant="outline" size="sm" icon={<Download size={14} />}>
            Export
          </Button>
        </div>
      </CardHeader>
      <DataTable
        columns={columns}
        data={ledger?.items || []}
        loading={isLoading}
        emptyMessage="No transactions"
        rowKey={(entry) => entry.id}
        pagination={
          ledger
            ? {
                page,
                pageSize: 25,
                total: ledger.total,
                onPageChange: setPage,
              }
            : undefined
        }
      />
    </Card>
  );
}

function AuditTab() {
  const [page, setPage] = useState(1);

  const { data: audits, isLoading } = useQuery({
    queryKey: ['invoke-audit', { page }],
    queryFn: () => getInvokeAudit({ page, limit: 25 }),
  });

  const columns = [
    {
      key: 'started_at',
      header: 'Time',
      render: (audit: InvokeAudit) => (
        <span className="text-sm text-gray-500">{formatTimeAgo(audit.started_at)}</span>
      ),
    },
    {
      key: 'invoke_id',
      header: 'Invoke ID',
      render: (audit: InvokeAudit) => (
        <span className="font-mono text-sm">{truncateId(audit.invoke_id, 10)}</span>
      ),
    },
    {
      key: 'caller',
      header: 'Caller',
      render: (audit: InvokeAudit) => (
        <span className="font-mono text-sm">{truncateId(audit.caller_agent, 10)}</span>
      ),
    },
    {
      key: 'target',
      header: 'Target',
      render: (audit: InvokeAudit) => (
        <span className="font-mono text-sm">{truncateId(audit.target_agent, 10)}</span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (audit: InvokeAudit) => <StatusBadge status={audit.status} />,
    },
    {
      key: 'duration_ms',
      header: 'Duration',
      render: (audit: InvokeAudit) => (
        <span className="text-sm">{formatDurationMs(audit.duration_ms)}</span>
      ),
    },
    {
      key: 'credits_charged',
      header: 'Credits',
      render: (audit: InvokeAudit) => (
        <span className="text-sm">{formatCredits(audit.credits_charged)}</span>
      ),
    },
  ];

  return (
    <Card>
      <CardHeader title="Invoke Audit Trail" />
      <DataTable
        columns={columns}
        data={audits?.items || []}
        loading={isLoading}
        emptyMessage="No invoke audits"
        rowKey={(audit) => audit.invoke_id}
        pagination={
          audits
            ? {
                page,
                pageSize: 25,
                total: audits.total,
                onPageChange: setPage,
              }
            : undefined
        }
      />
    </Card>
  );
}

function AnalyticsTab() {
  return (
    <Card>
      <CardBody className="py-16 text-center text-gray-500">
        Usage analytics coming soon
      </CardBody>
    </Card>
  );
}
