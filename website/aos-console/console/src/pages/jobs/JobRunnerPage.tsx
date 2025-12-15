import { useQuery } from '@tanstack/react-query';
import { useSearchParams, Link } from 'react-router-dom';
import { Play, XCircle } from 'lucide-react';
import { getJobs, getJob } from '@/api/jobs';
import { Card, CardHeader, CardBody, Button, StatusBadge, Spinner } from '@/components/common';
import { formatCredits, formatTimeAgo, truncateId } from '@/lib/utils';
import { cn } from '@/lib/utils';

export default function JobRunnerPage() {
  const [searchParams] = useSearchParams();
  const selectedJobId = searchParams.get('job');

  const { data: jobs, isLoading } = useQuery({
    queryKey: ['jobs', 'active'],
    queryFn: () => getJobs({ status: 'running,pending', limit: 20 }),
    refetchInterval: 5000,
  });

  const { data: selectedJob } = useQuery({
    queryKey: ['job', selectedJobId],
    queryFn: () => getJob(selectedJobId!),
    enabled: !!selectedJobId,
    refetchInterval: 2000,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
          Job Runner
        </h1>
        <Link to="/jobs/simulator">
          <Button icon={<Play size={16} />}>Create New Job</Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Jobs List */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader title="Active Jobs" />
            <CardBody className="p-0">
              {jobs?.items?.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  No active jobs
                </div>
              ) : (
                <div className="divide-y divide-gray-200 dark:divide-gray-700">
                  {jobs?.items?.map((job) => (
                    <Link
                      key={job.id}
                      to={`?job=${job.id}`}
                      className={cn(
                        'block p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors',
                        selectedJobId === job.id && 'bg-primary-50 dark:bg-primary-900/20'
                      )}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-mono text-sm">{truncateId(job.id)}</span>
                        <StatusBadge status={job.status} />
                      </div>
                      <div className="text-sm text-gray-500 truncate">{job.task}</div>
                      <div className="mt-2">
                        <div className="w-full h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                          <div
                            className={cn(
                              'h-full rounded-full transition-all',
                              job.status === 'running' && 'bg-blue-500',
                              job.status === 'pending' && 'bg-yellow-500'
                            )}
                            style={{ width: `${job.progress_percent || 0}%` }}
                          />
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {job.completed_items}/{job.total_items} items
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </CardBody>
          </Card>
        </div>

        {/* Job Detail */}
        <div className="lg:col-span-2">
          {selectedJob ? (
            <JobDetail job={selectedJob} />
          ) : (
            <Card>
              <CardBody className="py-16 text-center text-gray-500">
                Select a job to view details
              </CardBody>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

function JobDetail({ job }: { job: ReturnType<typeof getJob> extends Promise<infer T> ? T : never }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-semibold">Job {truncateId(job.id)}</h2>
            <p className="text-sm text-gray-500 mt-1">{job.task}</p>
          </div>
          <StatusBadge status={job.status} />
        </div>
      </CardHeader>
      <CardBody className="space-y-6">
        {/* Progress */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Progress</span>
            <span className="text-sm text-gray-500">{job.progress_percent}%</span>
          </div>
          <div className="w-full h-3 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary-500 rounded-full transition-all"
              style={{ width: `${job.progress_percent || 0}%` }}
            />
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
            <div className="text-2xl font-semibold text-green-600">
              {job.completed_items}
            </div>
            <div className="text-sm text-gray-500">Completed</div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
            <div className="text-2xl font-semibold text-blue-600">
              {job.total_items - job.completed_items - job.failed_items}
            </div>
            <div className="text-sm text-gray-500">Pending</div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
            <div className="text-2xl font-semibold text-red-600">
              {job.failed_items}
            </div>
            <div className="text-sm text-gray-500">Failed</div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
            <div className="text-2xl font-semibold">{job.total_items}</div>
            <div className="text-sm text-gray-500">Total</div>
          </div>
        </div>

        {/* Credits */}
        <div className="grid grid-cols-3 gap-4">
          <div>
            <div className="text-sm text-gray-500">Reserved</div>
            <div className="font-semibold">{formatCredits(job.credits_reserved)}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Spent</div>
            <div className="font-semibold">{formatCredits(job.credits_spent)}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Refunded</div>
            <div className="font-semibold">{formatCredits(job.credits_refunded)}</div>
          </div>
        </div>

        {/* Metadata */}
        <div className="border-t border-gray-200 dark:border-gray-700 pt-4 space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-500">Orchestrator</span>
            <span className="font-mono">{truncateId(job.orchestrator_agent)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Worker</span>
            <span className="font-mono">{truncateId(job.worker_agent)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Parallelism</span>
            <span>{job.parallelism}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Created</span>
            <span>{formatTimeAgo(job.created_at)}</span>
          </div>
          {job.started_at && (
            <div className="flex justify-between">
              <span className="text-gray-500">Started</span>
              <span>{formatTimeAgo(job.started_at)}</span>
            </div>
          )}
        </div>

        {/* Actions */}
        {job.status === 'running' && (
          <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
            <Button variant="danger" icon={<XCircle size={16} />}>
              Cancel Job
            </Button>
          </div>
        )}
      </CardBody>
    </Card>
  );
}
