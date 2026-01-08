import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { CUSTOMER_ROUTES } from '@/routing';
import OnboardingLayout from './OnboardingLayout';

export default function CompletePage() {
  const navigate = useNavigate();
  const { setOnboardingStep, setOnboardingComplete } = useAuthStore();

  useEffect(() => {
    setOnboardingStep(5);
  }, []);

  // PIN-352: Environment-aware redirects via routing authority
  const handleGoToGuard = () => {
    setOnboardingComplete(true);
    navigate(CUSTOMER_ROUTES.root, { replace: true });
  };

  const handleGoToPolicies = () => {
    setOnboardingComplete(true);
    navigate(CUSTOMER_ROUTES.policies, { replace: true });
  };

  return (
    <OnboardingLayout
      step={5}
      title="Your AI is Now Protected"
      subtitle="Agenticverz is actively monitoring your AI for failures and cost overruns"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        {/* Success Animation with Active Shield */}
        <div className="text-center mb-8">
          <div className="w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center shadow-lg shadow-green-500/20 relative">
            <svg className="w-12 h-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            {/* Pulsing indicator */}
            <span className="absolute top-1 right-1 w-3 h-3 bg-green-400 rounded-full animate-pulse" />
          </div>
          <h2 className="text-xl font-semibold text-white mb-2">🛡️ Active Protection Enabled</h2>
          <p className="text-green-400 font-medium">
            Your AI is now monitored and protected in real-time
          </p>
          <p className="text-slate-400 text-sm mt-2">
            Every AI request is being watched for failures, cost spikes, and policy violations
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-slate-800 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-green-400 mb-1">Active</div>
            <div className="text-xs text-slate-400">Killswitch</div>
          </div>
          <div className="bg-slate-800 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-blue-400 mb-1">0</div>
            <div className="text-xs text-slate-400">Incidents</div>
          </div>
          <div className="bg-slate-800 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-purple-400 mb-1">$0</div>
            <div className="text-xs text-slate-400">Spent</div>
          </div>
        </div>

        {/* Quick Links */}
        <div className="space-y-3 mb-8">
          <h3 className="text-sm font-medium text-slate-300 mb-3">What would you like to do?</h3>

          <button
            onClick={handleGoToGuard}
            className="w-full flex items-center gap-4 p-4 bg-green-900/30 hover:bg-green-900/50 border border-green-600/30 rounded-xl transition-colors text-left group"
          >
            <div className="w-12 h-12 bg-green-600/20 rounded-xl flex items-center justify-center text-green-400 group-hover:bg-green-600/30">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </div>
            <div className="flex-1">
              <div className="font-medium text-white">View Incidents</div>
              <div className="text-sm text-slate-400">See what your guardrails have blocked</div>
            </div>
            <span className="px-2 py-1 bg-green-600/20 text-green-400 text-xs font-medium rounded">Recommended</span>
          </button>

          <button
            onClick={handleGoToPolicies}
            className="w-full flex items-center gap-4 p-4 bg-slate-800 hover:bg-slate-700 rounded-xl transition-colors text-left group"
          >
            <div className="w-12 h-12 bg-blue-600/20 rounded-xl flex items-center justify-center text-blue-400 group-hover:bg-blue-600/30">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <div className="flex-1">
              <div className="font-medium text-white">Manage Policies</div>
              <div className="text-sm text-slate-400">Adjust guardrails, budgets, and safety rules</div>
            </div>
            <svg className="w-5 h-5 text-slate-500 group-hover:text-white transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        {/* Documentation Link */}
        <div className="text-center">
          <a
            href="https://docs.agenticverz.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:text-blue-300 text-sm inline-flex items-center gap-1"
          >
            View Documentation
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        </div>
      </div>
    </OnboardingLayout>
  );
}
