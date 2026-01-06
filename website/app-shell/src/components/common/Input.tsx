import { forwardRef } from 'react';
import { cn } from '@/lib/utils';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, hint, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="space-y-1">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={cn(
            'block w-full px-3 py-2 text-sm rounded-lg border transition-colors',
            'bg-white dark:bg-gray-900',
            'text-gray-900 dark:text-gray-100',
            'placeholder-gray-400 dark:placeholder-gray-500',
            'focus:outline-none focus:ring-2 focus:ring-offset-0',
            error
              ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20'
              : 'border-gray-300 dark:border-gray-600 focus:border-primary-500 focus:ring-primary-500/20',
            'disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed',
            className
          )}
          {...props}
        />
        {error && <p className="text-sm text-red-500">{error}</p>}
        {hint && !error && (
          <p className="text-sm text-gray-500 dark:text-gray-400">{hint}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
