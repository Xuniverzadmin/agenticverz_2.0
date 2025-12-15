import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Download } from 'lucide-react';
import { getJobs } from '@/api/jobs';
import { Card, CardBody, Button, Select, DataTable, StatusBadge } from '@/components/common';
import { formatCredits, formatTimeAgo, truncateId } from '@/lib/utils';
import type { Job } from '@/types/job';

export default function JobHistoryPage() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');

  const { data: jobs, isLoading } = useQuery({
    queryKey: ['jobs', 'history', { page, status: statusFilter }],
    queryFn: () =>
      getJobs({
        status: statusFilter || 'completed,failed,cancelled',
        page,
        limit: 25,
      }),
  });

  const columns = [
    {
      key: 'id',
      header: 'Job ID',
      render: (job: Job) => (
        <span className="font-mono text-sm">{truncateId(job.id)}</span>
      ),
    },
    {
      key: 'task',
      header: 'Task',
      render: (job: Job) => (
        <span className="text-sm max-w-[200px] truncate block">{job.task}</span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (job: Job) => <StatusBadge status={job.status} />,
    },
    {
      key: 'items',
      header: 'Items',
      render: (job: Job) => (
        <span className="text-sm">
          {job.completed_items}/{job.total_items}
          {job.failed_items > 0 && (
            <span className="text-red-500 ml-1">({job.failed_items} failed)</span>
          )}
        </span>
      ),
    },
    {
      key: 'credits',
      header: 'Credits',
      render: (job: Job) => (
        <span className="text-sm">{formatCredits(job.credits_spent)}</span>
      ),
    },
    {
      key: 'completed_at',
      header: 'Completed',
      render: (job: Job) => (
        <span className="text-sm text-gray-500">
          {job.completed_at ? formatTimeAgo(job.completed_at) : '-'}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
          Job History
        </h1>
        <Button variant="outline" icon={<Download size={16} />}>
          Export CSV
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardBody className="py-3">
          <div className="flex gap-4">
            <Select
              options={[
                { value: '', label: 'All Statuses' },
                { value: 'completed', label: 'Completed' },
                { value: 'failed', label: 'Failed' },
                { value: 'cancelled', label: 'Cancelled' },
              ]}
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
            />
          </div>
        </CardBody>
      </Card>

      {/* Jobs Table */}
      <Card>
        <DataTable
          columns={columns}
          data={jobs?.items || []}
          loading={isLoading}
          emptyMessage="No job history"
          rowKey={(job) => job.id}
          pagination={
            jobs
              ? {
                  page,
                  pageSize: 25,
                  total: jobs.total,
                  onPageChange: setPage,
                }
              : undefined
          }
        />
      </Card>
    </div>
  );
}
