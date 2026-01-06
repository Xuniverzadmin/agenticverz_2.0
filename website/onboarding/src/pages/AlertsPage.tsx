import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import OnboardingLayout from './OnboardingLayout';
import { toastSuccess } from '@/components/common/Toast';

interface AlertConfig {
  email: boolean;
  slack: boolean;
  slackWebhook: string;
  incidents: boolean;
  budgetAlerts: boolean;
  anomalies: boolean;
}

export default function AlertsPage() {
  const navigate = useNavigate();
  const { user, setOnboardingStep } = useAuthStore();

  const [config, setConfig] = useState<AlertConfig>({
    email: true,
    slack: false,
    slackWebhook: '',
    incidents: true,
    budgetAlerts: true,
    anomalies: true,
  });

  useEffect(() => {
    setOnboardingStep(3);
  }, []);

  const handleToggle = (key: keyof AlertConfig) => {
    setConfig(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleContinue = () => {
    toastSuccess('Alert preferences saved');
    navigate('/onboarding/verify');
  };

  return (
    <OnboardingLayout
      step={3}
      title="Set Up Alerts"
      subtitle="Choose how you want to be notified about incidents"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
        {/* Notification Channels */}
        <div>
          <h3 className="text-white font-medium mb-4">Notification Channels</h3>
          <div className="space-y-3">
            {/* Email */}
            <div className="flex items-center justify-between p-4 bg-slate-800 rounded-xl">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-slate-700 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <div>
                  <p className="text-white font-medium">Email</p>
                  <p className="text-sm text-slate-400">{user?.email || 'your@email.com'}</p>
                </div>
              </div>
              <button
                onClick={() => handleToggle('email')}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  config.email ? 'bg-blue-600' : 'bg-slate-700'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    config.email ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Slack */}
            <div className="p-4 bg-slate-800 rounded-xl">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-slate-700 rounded-lg flex items-center justify-center">
                    <svg className="w-5 h-5 text-slate-300" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zM15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z"/>
                    </svg>
                  </div>
                  <div>
                    <p className="text-white font-medium">Slack</p>
                    <p className="text-sm text-slate-400">Get alerts in your Slack channel</p>
                  </div>
                </div>
                <button
                  onClick={() => handleToggle('slack')}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    config.slack ? 'bg-blue-600' : 'bg-slate-700'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      config.slack ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
              {config.slack && (
                <div className="mt-4">
                  <input
                    type="text"
                    placeholder="https://hooks.slack.com/services/..."
                    value={config.slackWebhook}
                    onChange={(e) => setConfig(prev => ({ ...prev, slackWebhook: e.target.value }))}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  />
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Alert Types */}
        <div className="pt-4 border-t border-slate-800">
          <h3 className="text-white font-medium mb-4">Alert Types</h3>
          <div className="space-y-3">
            {[
              {
                key: 'incidents' as const,
                label: 'Safety Incidents',
                desc: 'Blocked operations, policy violations',
                icon: (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                ),
              },
              {
                key: 'budgetAlerts' as const,
                label: 'Budget Alerts',
                desc: '80% and 100% threshold warnings',
                icon: (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                ),
              },
              {
                key: 'anomalies' as const,
                label: 'Anomaly Detection',
                desc: 'Unusual patterns or behaviors',
                icon: (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                ),
              },
            ].map((item) => (
              <div
                key={item.key}
                className="flex items-center justify-between p-4 bg-slate-800 rounded-xl"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-slate-700 rounded-lg flex items-center justify-center text-slate-300">
                    {item.icon}
                  </div>
                  <div>
                    <p className="text-white font-medium">{item.label}</p>
                    <p className="text-sm text-slate-400">{item.desc}</p>
                  </div>
                </div>
                <button
                  onClick={() => handleToggle(item.key)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    config[item.key] ? 'bg-blue-600' : 'bg-slate-700'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      config[item.key] ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Continue Button */}
        <button
          onClick={handleContinue}
          className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-xl transition-colors mt-4"
        >
          Continue
        </button>

        {/* Skip */}
        <button
          onClick={() => navigate('/onboarding/verify')}
          className="w-full text-sm text-slate-400 hover:text-white transition-colors"
        >
          Skip for now
        </button>
      </div>
    </OnboardingLayout>
  );
}
