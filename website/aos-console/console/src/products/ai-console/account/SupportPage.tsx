/**
 * Support Page - Customer Help & Feedback
 *
 * Essential customer support features:
 * - Contact support
 * - Report an issue
 * - System status
 * - Documentation links
 */

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { guardApi } from '@/api/guard';
import { logger } from '@/lib/consoleLogger';
import { healthMonitor, HealthState, toHealthState } from '@/lib/healthCheck';

export function SupportPage() {
  const [issueDescription, setIssueDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [healthState, setHealthState] = useState<HealthState | null>(null);

  useEffect(() => {
    logger.componentMount('SupportPage');

    // Get current health state and subscribe to updates
    setHealthState(toHealthState(healthMonitor.getHealth()));
    const unsubscribe = healthMonitor.subscribe((system) => {
      setHealthState(toHealthState(system));
    });

    return () => {
      logger.componentUnmount('SupportPage');
      unsubscribe();
    };
  }, []);

  // Fetch snapshot for system metrics
  const { data: snapshot } = useQuery({
    queryKey: ['guard', 'snapshot'],
    queryFn: guardApi.getTodaySnapshot,
    refetchInterval: 30000,
  });

  const handleSubmitIssue = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!issueDescription.trim()) return;

    setIsSubmitting(true);
    logger.userEvent('click', 'submit_issue', { length: issueDescription.length });

    // Simulate submission
    await new Promise(resolve => setTimeout(resolve, 1000));

    setIsSubmitting(false);
    setSubmitted(true);
    setIssueDescription('');

    // Reset after 5 seconds
    setTimeout(() => setSubmitted(false), 5000);
  };

  const systemServices = [
    { name: 'API Gateway', status: healthState?.status === 'healthy' ? 'healthy' : 'degraded' },
    { name: 'Incident Processing', status: 'healthy' },
    { name: 'Guardrail Engine', status: 'healthy' },
    { name: 'Kill Switch', status: 'healthy' },
  ];

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      {/* Demo Mode Banner */}
      <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg px-4 py-2 text-center">
        <span className="text-amber-400 text-sm">
          ⚠️ You are viewing <strong>Demo mode</strong> — support tickets are simulated.
        </span>
      </div>

      {/* System Status */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        <div className="p-4 border-b border-slate-700 flex items-center justify-between">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <span>🌐</span> System Status
          </h2>
          <span className={`px-2 py-1 rounded text-xs font-medium ${
            healthState?.status === 'healthy' ? 'bg-emerald-500/20 text-emerald-400' :
            healthState?.status === 'degraded' ? 'bg-amber-500/20 text-amber-400' :
            'bg-slate-600 text-slate-300'
          }`}>
            {healthState?.status === 'healthy' ? 'All Systems Operational' :
             healthState?.status === 'degraded' ? 'Partially Degraded' : 'Checking...'}
          </span>
        </div>
        <div className="p-4">
          <div className="space-y-3">
            {systemServices.map((service, idx) => (
              <div key={idx} className="flex items-center justify-between py-2 border-b border-slate-700 last:border-0">
                <span className="font-medium">{service.name}</span>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${
                    service.status === 'healthy' ? 'bg-emerald-500' :
                    service.status === 'degraded' ? 'bg-amber-500' : 'bg-red-500'
                  }`} />
                  <span className={`text-sm ${
                    service.status === 'healthy' ? 'text-emerald-400' :
                    service.status === 'degraded' ? 'text-amber-400' : 'text-red-400'
                  }`}>
                    {service.status.charAt(0).toUpperCase() + service.status.slice(1)}
                  </span>
                </div>
              </div>
            ))}
          </div>
          {healthState?.lastCheck && (
            <p className="text-xs text-slate-500 mt-4">
              Last checked: {new Date(healthState.lastCheck).toLocaleTimeString()}
            </p>
          )}
        </div>
      </div>

      {/* Contact Support */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        <div className="p-4 border-b border-slate-700">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <span>💬</span> Contact Support
          </h2>
        </div>
        <div className="p-4">
          <div className="grid grid-cols-2 gap-4">
            <a
              href="mailto:support@agenticverz.com"
              className="p-4 bg-slate-700/50 hover:bg-slate-700 rounded-lg transition-colors flex items-center gap-3"
            >
              <span className="text-2xl">📧</span>
              <div>
                <span className="font-medium block">Email Support</span>
                <span className="text-sm text-slate-400">support@agenticverz.com</span>
              </div>
            </a>
            <a
              href="https://docs.agenticverz.com"
              target="_blank"
              rel="noopener noreferrer"
              className="p-4 bg-slate-700/50 hover:bg-slate-700 rounded-lg transition-colors flex items-center gap-3"
            >
              <span className="text-2xl">📚</span>
              <div>
                <span className="font-medium block">Documentation</span>
                <span className="text-sm text-slate-400">docs.agenticverz.com</span>
              </div>
            </a>
          </div>
        </div>
      </div>

      {/* Report an Issue */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        <div className="p-4 border-b border-slate-700">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <span>🐛</span> Report an Issue
          </h2>
        </div>
        <div className="p-4">
          {submitted ? (
            <div className="bg-emerald-500/20 border border-emerald-500/30 rounded-lg p-4 text-center">
              <span className="text-emerald-400 text-lg">✓</span>
              <p className="text-emerald-400 font-medium mt-2">Issue reported successfully!</p>
              <p className="text-sm text-slate-400 mt-1">We'll get back to you within 24 hours.</p>
            </div>
          ) : (
            <form onSubmit={handleSubmitIssue}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Describe the issue
                </label>
                <textarea
                  value={issueDescription}
                  onChange={(e) => setIssueDescription(e.target.value)}
                  placeholder="What happened? What did you expect to happen?"
                  rows={4}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
                />
              </div>
              <div className="flex items-center justify-between">
                <p className="text-xs text-slate-500">
                  Include as much detail as possible (incident IDs, timestamps, etc.)
                </p>
                <button
                  type="submit"
                  disabled={isSubmitting || !issueDescription.trim()}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed rounded-lg font-medium transition-colors"
                >
                  {isSubmitting ? 'Submitting...' : 'Submit Issue'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>

      {/* Quick Links */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        <div className="p-4 border-b border-slate-700">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <span>🔗</span> Quick Links
          </h2>
        </div>
        <div className="p-4 grid grid-cols-3 gap-4">
          <QuickLink icon="📖" label="API Reference" href="https://docs.agenticverz.com/api" />
          <QuickLink icon="🎓" label="Getting Started" href="https://docs.agenticverz.com/quickstart" />
          <QuickLink icon="🛡️" label="Security" href="https://agenticverz.com/security" />
          <QuickLink icon="📋" label="Changelog" href="https://docs.agenticverz.com/changelog" />
          <QuickLink icon="💡" label="Feature Requests" href="https://feedback.agenticverz.com" />
          <QuickLink icon="🤝" label="Community" href="https://discord.gg/agenticverz" />
        </div>
      </div>

      {/* Debug Info (collapsible) */}
      <details className="text-xs text-slate-500">
        <summary className="cursor-pointer hover:text-slate-400">Debug Information</summary>
        <div className="mt-2 p-3 bg-slate-800 rounded-lg font-mono">
          <p>Health: {healthState?.status || 'unknown'}</p>
          <p>Latency: {healthState?.latency ? `${healthState.latency}ms` : 'N/A'}</p>
          <p>Requests Today: {snapshot?.requests_today || 0}</p>
          <p>Circuit Breaker: {healthState?.circuitOpen ? 'OPEN' : 'CLOSED'}</p>
        </div>
      </details>
    </div>
  );
}

function QuickLink({ icon, label, href }: { icon: string; label: string; href: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-2 p-3 bg-slate-700/30 hover:bg-slate-700/50 rounded-lg transition-colors"
    >
      <span className="text-lg">{icon}</span>
      <span className="text-sm font-medium">{label}</span>
    </a>
  );
}

export default SupportPage;
