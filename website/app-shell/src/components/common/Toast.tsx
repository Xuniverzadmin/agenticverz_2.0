import { create } from 'zustand';
import { cn } from '@/lib/utils';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';

interface Toast {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
  duration?: number;
}

interface ToastStore {
  toasts: Toast[];
  add: (toast: Omit<Toast, 'id'>) => void;
  remove: (id: string) => void;
}

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  add: (toast) => {
    const id = Math.random().toString(36).slice(2);
    const duration = toast.duration ?? 5000;
    set((state) => ({ toasts: [...state.toasts, { ...toast, id }] }));
    if (duration > 0) {
      setTimeout(() => {
        set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) }));
      }, duration);
    }
  },
  remove: (id) => set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
}));

export function toast(type: Toast['type'], message: string, duration?: number) {
  useToastStore.getState().add({ type, message, duration });
}

export const toastSuccess = (message: string) => toast('success', message);
export const toastError = (message: string) => toast('error', message);
export const toastInfo = (message: string) => toast('info', message);
export const toastWarning = (message: string) => toast('warning', message);

const icons = {
  success: CheckCircle,
  error: AlertCircle,
  info: Info,
  warning: AlertTriangle,
};

export function Toaster() {
  const toasts = useToastStore((state) => state.toasts);
  const remove = useToastStore((state) => state.remove);

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2">
      {toasts.map((t) => {
        const Icon = icons[t.type];
        return (
          <div
            key={t.id}
            className={cn(
              'flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg min-w-[300px] max-w-[400px]',
              'animate-in slide-in-from-right fade-in duration-200',
              {
                'bg-green-600 text-white': t.type === 'success',
                'bg-red-600 text-white': t.type === 'error',
                'bg-blue-600 text-white': t.type === 'info',
                'bg-yellow-500 text-white': t.type === 'warning',
              }
            )}
          >
            <Icon size={18} className="flex-shrink-0" />
            <span className="flex-1 text-sm">{t.message}</span>
            <button
              onClick={() => remove(t.id)}
              className="flex-shrink-0 hover:opacity-80"
            >
              <X size={16} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
