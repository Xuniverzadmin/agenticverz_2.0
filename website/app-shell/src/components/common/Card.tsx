import { cn } from '@/lib/utils';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  onClick?: () => void;
}

export function Card({ children, className, hover = false, onClick }: CardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        'bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm',
        hover && 'hover:shadow-md transition-shadow cursor-pointer',
        className
      )}
    >
      {children}
    </div>
  );
}

interface CardHeaderProps {
  children?: React.ReactNode;
  className?: string;
  title?: string;
  action?: React.ReactNode;
}

export function CardHeader({ children, className, title, action }: CardHeaderProps) {
  if (title || action) {
    return (
      <div
        className={cn(
          'px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between',
          className
        )}
      >
        {title && <h3 className="font-semibold text-gray-900 dark:text-gray-100">{title}</h3>}
        {children}
        {action}
      </div>
    );
  }

  return (
    <div
      className={cn(
        'px-4 py-3 border-b border-gray-200 dark:border-gray-700',
        className
      )}
    >
      {children}
    </div>
  );
}

interface CardBodyProps {
  children: React.ReactNode;
  className?: string;
}

export function CardBody({ children, className }: CardBodyProps) {
  return <div className={cn('p-4', className)}>{children}</div>;
}

interface CardFooterProps {
  children: React.ReactNode;
  className?: string;
}

export function CardFooter({ children, className }: CardFooterProps) {
  return (
    <div
      className={cn(
        'px-4 py-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 rounded-b-lg',
        className
      )}
    >
      {children}
    </div>
  );
}
