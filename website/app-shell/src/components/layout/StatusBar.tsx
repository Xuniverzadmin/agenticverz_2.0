import { useQuery } from '@tanstack/react-query';
import { getHealthStatus } from '@/api/metrics';
import { cn } from '@/lib/utils';

interface ServiceStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  latency_ms?: number;
}

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  services: {
    api?: ServiceStatus;
    database?: ServiceStatus;
    redis?: ServiceStatus;
    workers?: ServiceStatus;
  };
}

function StatusDot({ label, status }: { label: string; status?: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span
        className={cn(
          'w-2 h-2 rounded-full',
          status === 'healthy' && 'bg-green-500',
          status === 'degraded' && 'bg-yellow-500',
          status === 'unhealthy' && 'bg-red-500',
          !status && 'bg-gray-400 animate-pulse'
        )}
      />
      <span className="text-gray-400">{label}</span>
    </div>
  );
}

export function StatusBar() {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: getHealthStatus,
    refetchInterval: 30000,
    retry: 1,
  });

  const services = (health as HealthStatus)?.services || {};

  return (
    <footer className="h-8 border-t border-gray-700 bg-gray-800 px-6 flex items-center justify-between text-xs">
      <div className="flex items-center gap-4">
        <StatusDot label="API" status={services.api?.status} />
        <StatusDot label="DB" status={services.database?.status} />
        <StatusDot label="Redis" status={services.redis?.status} />
        <StatusDot label="Workers" status={services.workers?.status} />
      </div>
      <div className="text-gray-400 flex items-center gap-4">
        <span>v1.0.0</span>
        <span>{new Date().toISOString().slice(0, 19).replace('T', ' ')} UTC</span>
      </div>
    </footer>
  );
}
