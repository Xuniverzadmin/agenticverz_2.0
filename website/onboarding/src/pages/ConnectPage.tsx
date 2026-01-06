import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import OnboardingLayout from './OnboardingLayout';
import { toastSuccess, toastError } from '@/components/common/Toast';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'https://agenticverz.com';

export default function ConnectPage() {
  const navigate = useNavigate();
  const { token, tenantId, setOnboardingStep } = useAuthStore();
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [showKey, setShowKey] = useState(false);

  useEffect(() => {
    setOnboardingStep(1);
    fetchOrCreateApiKey();
  }, []);

  const fetchOrCreateApiKey = async () => {
    try {
      // First try to get existing API key
      const response = await axios.get(`${API_BASE}/api/v1/tenants/${tenantId}/api-keys`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.keys && response.data.keys.length > 0) {
        setApiKey(response.data.keys[0].key);
      } else {
        // Create a new API key
        const createResponse = await axios.post(
          `${API_BASE}/api/v1/tenants/${tenantId}/api-keys`,
          { name: 'Default API Key' },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setApiKey(createResponse.data.key);
      }
    } catch (err) {
      console.error('Failed to fetch API key:', err);
      // Fallback: show a placeholder
      setApiKey('aos_' + 'x'.repeat(32));
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    if (apiKey) {
      try {
        await navigator.clipboard.writeText(apiKey);
        setCopied(true);
        toastSuccess('API key copied to clipboard');
        setTimeout(() => setCopied(false), 2000);
      } catch (err) {
        toastError('Failed to copy');
      }
    }
  };

  const handleContinue = () => {
    navigate('/onboarding/safety');
  };

  const maskedKey = apiKey ? apiKey.slice(0, 8) + '•'.repeat(24) + apiKey.slice(-4) : '';

  return (
    <OnboardingLayout
      step={1}
      title="Connect Your Application"
      subtitle="Use this API key to connect your AI agents to Agenticverz"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        {/* API Key Display */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Your API Key
          </label>
          <div className="relative">
            {loading ? (
              <div className="h-12 bg-slate-800 rounded-xl animate-pulse" />
            ) : (
              <div className="flex items-center gap-2">
                <div className="flex-1 px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl font-mono text-sm text-slate-300 overflow-hidden">
                  {showKey ? apiKey : maskedKey}
                </div>
                <button
                  onClick={() => setShowKey(!showKey)}
                  className="p-3 bg-slate-800 border border-slate-700 rounded-xl text-slate-400 hover:text-white transition-colors"
                  title={showKey ? 'Hide' : 'Show'}
                >
                  {showKey ? (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
                <button
                  onClick={handleCopy}
                  className={`p-3 rounded-xl transition-colors ${
                    copied
                      ? 'bg-green-600/20 text-green-400 border border-green-600/30'
                      : 'bg-slate-800 border border-slate-700 text-slate-400 hover:text-white'
                  }`}
                  title="Copy"
                >
                  {copied ? (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Quick Start Code */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Quick Start
          </label>
          <div className="bg-slate-950 rounded-xl p-4 font-mono text-sm overflow-x-auto">
            <pre className="text-slate-300">
              <span className="text-blue-400">pip install</span> agenticverz{'\n\n'}
              <span className="text-slate-500"># In your code</span>{'\n'}
              <span className="text-purple-400">from</span> agenticverz <span className="text-purple-400">import</span> AOSClient{'\n\n'}
              client = AOSClient({'\n'}
              {'  '}api_key=<span className="text-green-400">"{showKey && apiKey ? apiKey : 'YOUR_API_KEY'}"</span>{'\n'}
              ){'\n\n'}
              <span className="text-slate-500"># Execute with governance</span>{'\n'}
              result = client.run({'\n'}
              {'  '}skill=<span className="text-green-400">"code_execute"</span>,{'\n'}
              {'  '}input={'{'}task: <span className="text-green-400">"Analyze data"</span>{'}'}{'\n'}
              )
            </pre>
          </div>
        </div>

        {/* Security Note */}
        <div className="flex items-start gap-3 p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl mb-6">
          <svg className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div className="text-sm">
            <p className="text-amber-200 font-medium">Keep this key secure</p>
            <p className="text-amber-200/70 mt-1">
              Never commit your API key to version control. Use environment variables in production.
            </p>
          </div>
        </div>

        {/* Continue Button */}
        <button
          onClick={handleContinue}
          className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-xl transition-colors"
        >
          Continue
        </button>
      </div>
    </OnboardingLayout>
  );
}
