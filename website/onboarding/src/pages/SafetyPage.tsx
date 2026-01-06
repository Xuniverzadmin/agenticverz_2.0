import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import OnboardingLayout from './OnboardingLayout';
import { toastSuccess } from '@/components/common/Toast';

interface SafetyConfig {
  killswitch: boolean;
  autoBlock: boolean;
  budgetLimit: number;
  humanApproval: 'always' | 'high_risk' | 'never';
}

export default function SafetyPage() {
  const navigate = useNavigate();
  const { setOnboardingStep } = useAuthStore();

  const [config, setConfig] = useState<SafetyConfig>({
    killswitch: true,
    autoBlock: true,
    budgetLimit: 100,
    humanApproval: 'high_risk',
  });

  useEffect(() => {
    setOnboardingStep(2);
  }, []);

  const handleToggle = (key: keyof SafetyConfig) => {
    setConfig(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleContinue = () => {
    toastSuccess('Safety settings saved');
    navigate('/onboarding/alerts');
  };

  return (
    <OnboardingLayout
      step={2}
      title="Configure Safety Defaults"
      subtitle="Set up safety guardrails for your AI agents"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
        {/* Killswitch */}
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-white font-medium">Emergency Killswitch</h3>
            <p className="text-sm text-slate-400 mt-1">
              Instantly halt all agent operations when triggered
            </p>
          </div>
          <button
            onClick={() => handleToggle('killswitch')}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              config.killswitch ? 'bg-blue-600' : 'bg-slate-700'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                config.killswitch ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>

        {/* Auto-Block */}
        <div className="flex items-center justify-between pt-4 border-t border-slate-800">
          <div>
            <h3 className="text-white font-medium">Auto-Block Suspicious Patterns</h3>
            <p className="text-sm text-slate-400 mt-1">
              Automatically block agents showing anomalous behavior
            </p>
          </div>
          <button
            onClick={() => handleToggle('autoBlock')}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              config.autoBlock ? 'bg-blue-600' : 'bg-slate-700'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                config.autoBlock ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>

        {/* Budget Limit */}
        <div className="pt-4 border-t border-slate-800">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-white font-medium">Daily Budget Limit</h3>
              <p className="text-sm text-slate-400 mt-1">
                Maximum daily spend across all agents
              </p>
            </div>
            <span className="text-xl font-semibold text-white">${config.budgetLimit}</span>
          </div>
          <input
            type="range"
            min="10"
            max="1000"
            step="10"
            value={config.budgetLimit}
            onChange={(e) => setConfig(prev => ({ ...prev, budgetLimit: parseInt(e.target.value) }))}
            className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
          />
          <div className="flex justify-between text-xs text-slate-500 mt-1">
            <span>$10</span>
            <span>$1,000</span>
          </div>
        </div>

        {/* Human Approval */}
        <div className="pt-4 border-t border-slate-800">
          <h3 className="text-white font-medium mb-3">Human Approval Required</h3>
          <div className="space-y-2">
            {[
              { value: 'always', label: 'Always', desc: 'Approve every action' },
              { value: 'high_risk', label: 'High-Risk Only', desc: 'Approve destructive or expensive operations' },
              { value: 'never', label: 'Never', desc: 'Agents operate autonomously' },
            ].map((option) => (
              <label
                key={option.value}
                className={`flex items-center p-3 rounded-xl cursor-pointer transition-colors ${
                  config.humanApproval === option.value
                    ? 'bg-blue-600/20 border border-blue-500/30'
                    : 'bg-slate-800 border border-slate-700 hover:border-slate-600'
                }`}
              >
                <input
                  type="radio"
                  name="humanApproval"
                  value={option.value}
                  checked={config.humanApproval === option.value}
                  onChange={(e) => setConfig(prev => ({ ...prev, humanApproval: e.target.value as SafetyConfig['humanApproval'] }))}
                  className="sr-only"
                />
                <div className={`w-4 h-4 rounded-full border-2 mr-3 flex items-center justify-center ${
                  config.humanApproval === option.value
                    ? 'border-blue-500'
                    : 'border-slate-600'
                }`}>
                  {config.humanApproval === option.value && (
                    <div className="w-2 h-2 bg-blue-500 rounded-full" />
                  )}
                </div>
                <div className="flex-1">
                  <span className="text-white font-medium">{option.label}</span>
                  <p className="text-sm text-slate-400">{option.desc}</p>
                </div>
              </label>
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
          onClick={() => navigate('/onboarding/alerts')}
          className="w-full text-sm text-slate-400 hover:text-white transition-colors"
        >
          Skip for now
        </button>
      </div>
    </OnboardingLayout>
  );
}
