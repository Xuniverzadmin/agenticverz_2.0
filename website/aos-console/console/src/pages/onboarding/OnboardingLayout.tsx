import { ReactNode } from 'react';
import { useAuthStore } from '@/stores/authStore';

interface OnboardingLayoutProps {
  children: ReactNode;
  step: number;
  title: string;
  subtitle?: string;
}

const steps = [
  { id: 1, name: 'Connect' },
  { id: 2, name: 'Safety' },
  { id: 3, name: 'Alerts' },
  { id: 4, name: 'Verify' },
  { id: 5, name: 'Complete' },
];

export default function OnboardingLayout({ children, step, title, subtitle }: OnboardingLayoutProps) {
  const { user } = useAuthStore();

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-white" viewBox="0 0 32 32" fill="none">
                <path d="M8 22L16 10L24 22H8Z" fill="currentColor"/>
                <circle cx="16" cy="18" r="3" fill="rgba(255,255,255,0.3)"/>
              </svg>
            </div>
            <span className="text-white font-semibold">Agenticverz</span>
          </div>
          {user && (
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <span>{user.email}</span>
            </div>
          )}
        </div>
      </header>

      {/* Progress */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        <nav aria-label="Progress">
          <ol className="flex items-center justify-between">
            {steps.map((s, idx) => (
              <li key={s.id} className="relative flex-1">
                <div className="flex items-center">
                  <div
                    className={`
                      relative z-10 flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium
                      ${s.id < step
                        ? 'bg-blue-600 text-white'
                        : s.id === step
                        ? 'bg-blue-600 text-white ring-4 ring-blue-600/20'
                        : 'bg-slate-800 text-slate-500 border border-slate-700'
                      }
                    `}
                  >
                    {s.id < step ? (
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    ) : (
                      s.id
                    )}
                  </div>
                  {idx < steps.length - 1 && (
                    <div
                      className={`absolute left-8 top-4 -z-10 h-0.5 w-[calc(100%-2rem)] ${
                        s.id < step ? 'bg-blue-600' : 'bg-slate-800'
                      }`}
                    />
                  )}
                </div>
                <span
                  className={`mt-2 block text-xs ${
                    s.id <= step ? 'text-white' : 'text-slate-500'
                  }`}
                >
                  {s.name}
                </span>
              </li>
            ))}
          </ol>
        </nav>
      </div>

      {/* Content */}
      <main className="max-w-2xl mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-white">{title}</h1>
          {subtitle && <p className="text-slate-400 mt-2">{subtitle}</p>}
        </div>
        {children}
      </main>
    </div>
  );
}
