import { cn } from '@/lib/utils';

type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'info' | 'primary';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
  dot?: boolean;
  className?: string;
}

export function Badge({
  children,
  variant = 'default',
  size = 'md',
  dot = false,
  className,
}: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 font-medium rounded-full',
        {
          'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300':
            variant === 'default',
          'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400':
            variant === 'success',
          'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400':
            variant === 'warning',
          'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400':
            variant === 'error',
          'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400':
            variant === 'info',
          'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400':
            variant === 'primary',
        },
        {
          'px-1.5 py-0.5 text-xs': size === 'sm',
          'px-2 py-0.5 text-xs': size === 'md',
        },
        className
      )}
    >
      {dot && (
        <span
          className={cn('w-1.5 h-1.5 rounded-full', {
            'bg-gray-500': variant === 'default',
            'bg-green-500': variant === 'success',
            'bg-yellow-500': variant === 'warning',
            'bg-red-500': variant === 'error',
            'bg-blue-500': variant === 'info',
            'bg-primary-500': variant === 'primary',
          })}
        />
      )}
      {children}
    </span>
  );
}

// Status-specific badge helper
export function StatusBadge({ status }: { status: string }) {
  const variantMap: Record<string, BadgeVariant> = {
    active: 'success',
    idle: 'default',
    stale: 'warning',
    running: 'info',
    completed: 'success',
    failed: 'error',
    cancelled: 'default',
    pending: 'warning',
    claimed: 'info',
    delivered: 'success',
    read: 'success',
    success: 'success',
    timeout: 'error',
  };

  return (
    <Badge variant={variantMap[status] || 'default'} dot>
      {status}
    </Badge>
  );
}
