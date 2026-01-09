/**
 * Confirmation Modal - Phase-2A.2 Simulation
 *
 * Layer: L1 — Product Experience (UI)
 * Role: Confirm destructive or important simulated actions
 * Reference: PIN-368, Phase-2A.2 Simulation Specification
 */

import { Modal } from '@/components/common/Modal';
import { Button } from '@/components/common/Button';
import { AlertTriangle, Info } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ConfirmationModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  subtitle?: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'default' | 'destructive';
}

export function ConfirmationModal({
  open,
  onClose,
  onConfirm,
  title,
  subtitle,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'default',
}: ConfirmationModalProps) {
  const isDestructive = variant === 'destructive';
  const Icon = isDestructive ? AlertTriangle : Info;

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      description={subtitle}
      size="sm"
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            {cancelText}
          </Button>
          <Button
            variant={isDestructive ? 'destructive' : 'default'}
            onClick={onConfirm}
          >
            {confirmText}
          </Button>
        </>
      }
    >
      <div className="flex items-start gap-4">
        <div className={cn(
          'p-2 rounded-full',
          isDestructive ? 'bg-red-900/30' : 'bg-amber-900/30'
        )}>
          <Icon
            size={24}
            className={cn(
              isDestructive ? 'text-red-400' : 'text-amber-400'
            )}
          />
        </div>
        <div className="flex-1">
          <p className="text-sm text-gray-300">{message}</p>
          <div className="mt-3 p-3 rounded bg-gray-900/50 border border-gray-700">
            <p className="text-xs text-gray-400">
              <span className="text-amber-400 font-medium">Simulation Mode:</span>{' '}
              No actual changes will be made to the system.
            </p>
          </div>
        </div>
      </div>
    </Modal>
  );
}
