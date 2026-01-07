import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import OnboardingLayout from './OnboardingLayout';
import { toastSuccess, toastError } from '@/components/common/Toast';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || '';

type TestStatus = 'idle' | 'running' | 'success' | 'failed';

interface TestResult {
  status: TestStatus;
  message: string;
  details?: string;
  incidentId?: string;
  wasBlocked?: boolean;
  blockedBy?: string;
  alertSent?: boolean;
}

export default function VerifyPage() {
  const navigate = useNavigate();
  const { token, tenantId, setOnboardingStep } = useAuthStore();

  const [testStatus, setTestStatus] = useState<TestStatus>('idle');
  const [testResult, setTestResult] = useState<TestResult | null>(null);

  useEffect(() => {
    setOnboardingStep(4);
  }, []);

  const runTest = async () => {
    setTestStatus('running');
    setTestResult(null);

    try {
      // Fire a REAL request through the guard verification endpoint
      // This will:
      // 1. Make a real API call with a prompt injection pattern
      // 2. Get blocked by the guardrail (zero cost)
      // 3. Create a real incident in the database
      // 4. Send a real alert if configured
      const response = await axios.post(
        `${API_BASE}/guard/onboarding/verify?tenant_id=${tenantId || 'demo-tenant'}`,
        {
          test_type: 'guardrail_block',
          trigger_alert: true
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'X-Tenant-ID': tenantId || 'demo-tenant',
            'Content-Type': 'application/json'
          }
        }
      );

      const data = response.data;

      if (data.was_blocked) {
        // Success! The guardrail blocked the malicious request
        setTestStatus('success');
        setTestResult({
          status: 'success',
          message: '🛡️ Your AI is now protected!',
          details: `Blocked by: ${data.blocked_by || 'guardrail'}`,
          incidentId: data.incident_id,
          wasBlocked: true,
          blockedBy: data.blocked_by,
          alertSent: data.alert_sent
        });
        toastSuccess('Safety test passed! Guardrails are active.');
      } else {
        // Request wasn't blocked - could be a configuration issue
        setTestStatus('success');
        setTestResult({
          status: 'success',
          message: '⚠️ Request was processed',
          details: `Tokens used: ${data.tokens_consumed}. Check your guardrail configuration.`,
          wasBlocked: false
        });
      }
    } catch (err: unknown) {
      const error = err as { response?: { status: number; data?: { detail?: string } } };

      setTestStatus('failed');
      setTestResult({
        status: 'failed',
        message: 'Could not run safety test',
        details: error.response?.data?.detail || 'Please check your API connection.'
      });
      toastError('Verification failed');
    }
  };

  const handleContinue = () => {
    navigate('/onboarding/complete');
  };

  return (
    <OnboardingLayout
      step={4}
      title="Verify Your Setup"
      subtitle="We'll fire a REAL request to prove your guardrails work"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
        {/* Test Card */}
        <div className="text-center">
          <div className={`w-20 h-20 mx-auto mb-4 rounded-2xl flex items-center justify-center ${
            testStatus === 'idle' ? 'bg-slate-800' :
            testStatus === 'running' ? 'bg-blue-600/20' :
            testStatus === 'success' ? 'bg-green-600/20' :
            'bg-red-600/20'
          }`}>
            {testStatus === 'idle' && (
              <svg className="w-10 h-10 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            )}
            {testStatus === 'running' && (
              <svg className="w-10 h-10 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            )}
            {testStatus === 'success' && (
              <svg className="w-10 h-10 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
            {testStatus === 'failed' && (
              <svg className="w-10 h-10 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
          </div>

          {testResult ? (
            <>
              <h3 className={`text-lg font-medium ${
                testResult.wasBlocked ? 'text-green-400' : testResult.status === 'failed' ? 'text-red-400' : 'text-amber-400'
              }`}>
                {testResult.message}
              </h3>
              {testResult.details && (
                <p className="text-sm text-slate-400 mt-2">{testResult.details}</p>
              )}
              {testResult.incidentId && (
                <p className="text-xs text-slate-500 mt-1">
                  Incident: <span className="font-mono text-blue-400">{testResult.incidentId}</span>
                </p>
              )}
              {testResult.alertSent && (
                <p className="text-xs text-green-500 mt-1">✓ Alert sent to your configured channel</p>
              )}
            </>
          ) : (
            <>
              <h3 className="text-lg font-medium text-white">
                {testStatus === 'running' ? 'Sending real AI request...' : 'Ready to test your guardrails'}
              </h3>
              <p className="text-sm text-slate-400 mt-2">
                {testStatus === 'running'
                  ? "We're sending a prompt injection through your API..."
                  : 'This sends a REAL malicious prompt. Your guardrail should block it.'}
              </p>
            </>
          )}
        </div>

        {/* Test Button */}
        {testStatus !== 'success' && (
          <button
            onClick={runTest}
            disabled={testStatus === 'running'}
            className={`w-full px-4 py-3 font-medium rounded-xl transition-colors ${
              testStatus === 'running'
                ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                : 'bg-amber-600 hover:bg-amber-500 text-white'
            }`}
          >
            {testStatus === 'running' ? 'Testing...' : testStatus === 'failed' ? 'Retry Test' : '🔥 Fire Live Test'}
          </button>
        )}

        {/* What happens section */}
        <div className="bg-slate-800/50 rounded-xl p-4">
          <h4 className="text-sm font-medium text-white mb-2">What happens when you click:</h4>
          <ul className="text-sm text-slate-400 space-y-1">
            <li className="flex items-start gap-2">
              <span className="text-green-400 mt-0.5">✓</span>
              <span><strong className="text-white">Real API call</strong> sent through your proxy</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400 mt-0.5">✓</span>
              <span><strong className="text-white">Prompt injection pattern</strong> triggers guardrail</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400 mt-0.5">✓</span>
              <span><strong className="text-white">Real incident</strong> created (visible in console)</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400 mt-0.5">✓</span>
              <span><strong className="text-white">Alert fires</strong> to Slack/email (if configured)</span>
            </li>
          </ul>
          <p className="text-xs text-slate-500 mt-3">
            💡 Cost: $0.00 — blocked requests don't consume tokens
          </p>
        </div>

        {/* View Incident Button (only after success) */}
        {testResult?.incidentId && (
          <a
            href={`/console/guard?incident=${testResult.incidentId}`}
            target="_blank"
            rel="noopener noreferrer"
            className="block w-full px-4 py-3 bg-slate-800 hover:bg-slate-700 text-center text-blue-400 font-medium rounded-xl transition-colors"
          >
            View Incident in Console →
          </a>
        )}

        {/* Continue Button */}
        <button
          onClick={handleContinue}
          className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-xl transition-colors"
        >
          {testStatus === 'success' ? 'Continue' : 'Skip & Continue'}
        </button>
      </div>
    </OnboardingLayout>
  );
}
