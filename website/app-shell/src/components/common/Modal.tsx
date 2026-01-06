import * as Dialog from '@radix-ui/react-dialog';
import * as VisuallyHidden from '@radix-ui/react-visually-hidden';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from './Button';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  footer?: React.ReactNode;
}

export function Modal({
  open,
  onClose,
  title,
  description,
  children,
  size = 'md',
  footer,
}: ModalProps) {
  return (
    <Dialog.Root open={open} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50 animate-in fade-in" />
        <Dialog.Content
          className={cn(
            'fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50',
            'bg-white dark:bg-gray-800 rounded-lg shadow-xl',
            'animate-in fade-in zoom-in-95 duration-200',
            'max-h-[90vh] overflow-hidden flex flex-col',
            {
              'w-[400px]': size === 'sm',
              'w-[560px]': size === 'md',
              'w-[720px]': size === 'lg',
              'w-[960px]': size === 'xl',
            }
          )}
        >
          {/* Hidden description for accessibility when no visible description provided */}
          {!description && (
            <VisuallyHidden.Root asChild>
              <Dialog.Description>
                {title ? `${title} dialog` : 'Modal dialog'}
              </Dialog.Description>
            </VisuallyHidden.Root>
          )}
          {(title || description) && (
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-start justify-between">
              <div>
                {title && (
                  <Dialog.Title className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {title}
                  </Dialog.Title>
                )}
                {description && (
                  <Dialog.Description className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {description}
                  </Dialog.Description>
                )}
              </div>
              <Dialog.Close asChild>
                <Button variant="ghost" size="sm" className="p-1">
                  <X size={18} />
                </Button>
              </Dialog.Close>
            </div>
          )}

          {/* Content: only show scroll when content exceeds container */}
          <div className="px-6 py-4 flex-1 overflow-y-auto max-h-[calc(90vh-120px)]">{children}</div>

          {footer && (
            <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
              {footer}
            </div>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
