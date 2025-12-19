// BuildYourApp - Human-Centric AI Product Builder
// Flow: Input → Plan Review → Budget → Execution
// Shows agents as "workers" without exposing OS internals

import { useState, useCallback, useEffect, useRef } from 'react';
import {
  Zap, ArrowRight, ArrowLeft, CheckCircle, Loader2,
  Users, Target, Lightbulb, DollarSign, Clock, Rocket,
  ChevronDown, ChevronUp, Play, RefreshCw, Download,
  AlertCircle, Shield, Eye, FileText, Code, Megaphone,
  Sparkles, Brain, Search, Palette, PenTool, BarChart3,
  Home
} from 'lucide-react';

// === DEBUG LOGGER ===
const DEBUG = true;
const log = (area, message, data) => {
  if (DEBUG) {
    const timestamp = new Date().toISOString().split('T')[1].slice(0, 12);
    const style = 'color: #8b5cf6; font-weight: bold; font-size: 12px';
    const prefix = `[${timestamp}] [BUILD-APP] [${area}]`;
    // Use console.warn for better visibility (yellow background in most browsers)
    if (data !== undefined) {
      console.warn(`%c${prefix}`, style, message, data);
    } else {
      console.warn(`%c${prefix}`, style, message);
    }
  }
};

// Immediate visibility test - this MUST show in console
console.warn('%c🟣 BUILD-APP DEBUG MODE ACTIVE 🟣', 'background: #8b5cf6; color: white; font-size: 16px; padding: 4px 8px; border-radius: 4px;');

// === CONSTANTS ===
// Use relative URL for production (proxied through Apache) or localhost for dev
const API_BASE = window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';
log('INIT', `API_BASE resolved to: "${API_BASE || '(relative)'}"`, { hostname: window.location.hostname });

const AUDIENCE_OPTIONS = [
  { value: 'b2b_smb', label: 'B2B SMB Founders', desc: 'Small business owners & startups' },
  { value: 'retail_investor', label: 'Retail Investors', desc: 'Individual investors & traders' },
  { value: 'fintech_operator', label: 'Fintech Operators', desc: 'Fintech company employees' },
  { value: 'developer', label: 'Developers', desc: 'Software engineers & builders' },
];

const DEPTH_OPTIONS = [
  { value: 'quick', label: 'Quick Analysis', time: '~2 min', credits: '2,000' },
  { value: 'balanced', label: 'Balanced', time: '~5 min', credits: '8,000' },
  { value: 'deep', label: 'Deep Research', time: '~10 min', credits: '15,000' },
];

const DEFAULT_CONSTRAINTS = {
  avoid_financial_guarantees: true,
  avoid_absolute_claims: true,
  avoid_medical_legal_claims: true,
  avoid_hype_superlatives: true,
};

// === MAIN COMPONENT ===
export function BuildYourApp() {
  // Flow state: 'input' | 'plan' | 'execution'
  const [flowState, setFlowState] = useState('input');

  // Input state
  const [ideaDescription, setIdeaDescription] = useState('');
  const [problemStatement, setProblemStatement] = useState('');
  const [referenceProducts, setReferenceProducts] = useState(['', '']);
  const [primaryAudience, setPrimaryAudience] = useState('b2b_smb');
  const [analysisDepth, setAnalysisDepth] = useState('balanced');
  const [constraints, setConstraints] = useState(DEFAULT_CONSTRAINTS);
  const [customAvoidPhrases, setCustomAvoidPhrases] = useState('');

  // Plan state (AI-generated)
  const [aiPlan, setAiPlan] = useState(null);
  const [costEstimate, setCostEstimate] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [marketingPlan, setMarketingPlan] = useState(null);

  // Execution state
  const [isGenerating, setIsGenerating] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [runId, setRunId] = useState(null);
  const [agentWorkforce, setAgentWorkforce] = useState([]);
  const [showAgentPane, setShowAgentPane] = useState(false);
  const [executionLogs, setExecutionLogs] = useState([]);
  const [artifacts, setArtifacts] = useState([]);
  const [error, setError] = useState(null);

  // Approval gates
  const [approvals, setApprovals] = useState({
    plan: false,
    budget: false,
    timeline: false,
    deployment: false,
  });

  // Debug: Log on mount
  useEffect(() => {
    console.warn('%c🚀 BuildYourApp MOUNTED', 'background: #10b981; color: white; font-size: 14px; padding: 2px 6px; border-radius: 4px;');
    log('MOUNT', 'Component mounted', { flowState, ideaDescription: ideaDescription.slice(0, 50) });
  }, []);

  // === HANDLERS ===
  const handleGeneratePlan = useCallback(async () => {
    log('ACTION', '▶️ handleGeneratePlan called');
    setIsGenerating(true);
    setError(null);

    try {
      // Build request payload
      const payload = {
        task: `Design an AI-driven product: ${ideaDescription}. ${problemStatement ? `Problem: ${problemStatement}` : ''} Benchmark against: ${referenceProducts.filter(r => r).join(', ')}.`,
        brand: {
          company_name: 'Product Builder',
          mission: ideaDescription.slice(0, 100) || 'Build innovative AI products',
          value_proposition: `Solving ${problemStatement || 'user needs'} with AI-powered solutions for ${AUDIENCE_OPTIONS.find(a => a.value === primaryAudience)?.label || 'users'}`,
          target_audience: [primaryAudience],
          tone: { primary: 'professional', avoid: [] },
          forbidden_claims: Object.entries(constraints)
            .filter(([_, v]) => v)
            .map(([k]) => ({
              pattern: k.replace('avoid_', '').replace(/_/g, ' '),
              reason: 'Compliance guardrail',
              severity: 'error'
            })),
          competitors: referenceProducts.filter(r => r).map(name => ({
            name,
            positioning: 'Competitor',
            differentiate_from: 'Our unique approach'
          })),
          budget_tokens: analysisDepth === 'quick' ? 2000 : analysisDepth === 'balanced' ? 8000 : 15000,
        },
        stream: false, // Get full plan first
      };

      const apiUrl = `${API_BASE}/api/v1/workers/business-builder/run`;
      log('API', `📤 POST ${apiUrl}`, { payload });

      // Call worker API
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-AOS-Key': 'edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf',  // pragma: allowlist secret - demo key
        },
        body: JSON.stringify(payload),
      });

      log('API', `📥 Response status: ${response.status} ${response.statusText}`);

      if (!response.ok) {
        const errorText = await response.text();
        log('API', `❌ Error response body:`, errorText);
        throw new Error(`API error: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      log('API', `✅ Success - run_id: ${data.run_id}`, data);
      setRunId(data.run_id);

      // Generate mock plan (in real implementation, this comes from the worker)
      const mockPlan = generateMockPlan(ideaDescription, referenceProducts, primaryAudience);
      setAiPlan(mockPlan.ai_plan);
      setCostEstimate(mockPlan.cost_estimate);
      setTimeline(mockPlan.timeline);
      setMarketingPlan(mockPlan.marketing_plan);

      // Initialize agent workforce
      setAgentWorkforce([
        { display_name: 'Market Researcher', status: 'completed', current_task: 'Analyzed benchmarks', progress: 100, icon: Search },
        { display_name: 'Product Strategist', status: 'completed', current_task: 'Defined concept', progress: 100, icon: Lightbulb },
        { display_name: 'UX Architect', status: 'queued', current_task: 'Awaiting approval', progress: 0, icon: Palette },
        { display_name: 'Copywriter', status: 'queued', current_task: 'Awaiting approval', progress: 0, icon: PenTool },
        { display_name: 'Marketing Planner', status: 'queued', current_task: 'Awaiting approval', progress: 0, icon: Megaphone },
      ]);

      log('STATE', '📋 Moving to plan state');
      setFlowState('plan');
    } catch (err) {
      log('ERROR', `❌ ${err.message}`, err);
      setError(err.message || 'Failed to generate plan');
    } finally {
      setIsGenerating(false);
    }
  }, [ideaDescription, problemStatement, referenceProducts, primaryAudience, analysisDepth, constraints]);

  const handleApproveAndExecute = useCallback(async () => {
    if (!Object.values(approvals).every(v => v)) {
      setError('Please approve all sections before proceeding');
      return;
    }

    setIsExecuting(true);
    setFlowState('execution');
    setError(null);

    // Simulate agent execution
    simulateExecution();
  }, [approvals]);

  const simulateExecution = useCallback(() => {
    const agents = [...agentWorkforce];
    let currentAgent = 2; // Start with UX Architect

    const updateAgent = () => {
      if (currentAgent >= agents.length) {
        setIsExecuting(false);
        setArtifacts([
          { name: 'competitor_analysis.md', type: 'markdown', size: '12KB' },
          { name: 'product_concept.md', type: 'markdown', size: '8KB' },
          { name: 'feature_list.json', type: 'json', size: '4KB' },
          { name: 'architecture.json', type: 'json', size: '6KB' },
          { name: 'marketing_plan.md', type: 'markdown', size: '10KB' },
        ]);
        return;
      }

      // Update current agent
      agents[currentAgent] = {
        ...agents[currentAgent],
        status: 'working',
        progress: 0,
      };
      setAgentWorkforce([...agents]);
      setShowAgentPane(true);

      // Simulate progress
      let progress = 0;
      const progressInterval = setInterval(() => {
        progress += 10 + Math.random() * 15;
        if (progress >= 100) {
          progress = 100;
          clearInterval(progressInterval);

          agents[currentAgent] = {
            ...agents[currentAgent],
            status: 'completed',
            progress: 100,
            current_task: 'Done',
          };
          setAgentWorkforce([...agents]);

          // Add log
          setExecutionLogs(prev => [...prev, {
            agent: agents[currentAgent].display_name,
            message: `Completed: ${agents[currentAgent].current_task}`,
            timestamp: new Date().toISOString(),
          }]);

          currentAgent++;
          setTimeout(updateAgent, 500);
        } else {
          agents[currentAgent] = {
            ...agents[currentAgent],
            progress: Math.min(progress, 99),
          };
          setAgentWorkforce([...agents]);
        }
      }, 300);
    };

    setTimeout(updateAgent, 500);
  }, [agentWorkforce]);

  const handleReset = useCallback(() => {
    setFlowState('input');
    setAiPlan(null);
    setCostEstimate(null);
    setTimeline(null);
    setMarketingPlan(null);
    setAgentWorkforce([]);
    setExecutionLogs([]);
    setArtifacts([]);
    setApprovals({ plan: false, budget: false, timeline: false, deployment: false });
    setError(null);
    setRunId(null);
    setIsExecuting(false);
  }, []);

  const allApproved = Object.values(approvals).every(v => v);

  return (
    <div className="min-h-screen gradient-bg">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <a href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-purple-500 flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-semibold">Agenticverz</span>
            </a>
            <div className="flex items-center gap-4">
              <a href="/" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
                <Home className="w-4 h-4" />
                Home
              </a>
              <a href="/console" className="px-4 py-2 glass rounded-lg hover:bg-white/10 transition-colors">
                Console
              </a>
            </div>
          </div>
        </div>
      </nav>

      {/* Progress Indicator */}
      <div className="fixed top-20 left-0 right-0 z-40 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="glass rounded-full p-1">
            <div className="flex items-center justify-between">
              {['Input & Intent', 'Plan Review', 'Execution'].map((step, i) => {
                const stepKey = ['input', 'plan', 'execution'][i];
                const isActive = flowState === stepKey;
                const isCompleted = (flowState === 'plan' && i === 0) || (flowState === 'execution' && i < 2);

                return (
                  <div key={step} className="flex-1 flex items-center">
                    <div className={`flex items-center gap-2 px-4 py-2 rounded-full transition-all ${
                      isActive ? 'bg-primary-600 text-white' :
                      isCompleted ? 'text-green-400' : 'text-gray-500'
                    }`}>
                      {isCompleted ? (
                        <CheckCircle className="w-4 h-4" />
                      ) : (
                        <span className="w-5 h-5 rounded-full border-2 flex items-center justify-center text-xs">
                          {i + 1}
                        </span>
                      )}
                      <span className="text-sm font-medium hidden sm:block">{step}</span>
                    </div>
                    {i < 2 && (
                      <div className={`flex-1 h-0.5 mx-2 ${isCompleted ? 'bg-green-500' : 'bg-gray-700'}`} />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="pt-36 pb-20 px-6">
        <div className="max-w-5xl mx-auto">

          {/* === INPUT STATE === */}
          {flowState === 'input' && (
            <div className="animate-fade-in">
              <div className="text-center mb-12">
                <h1 className="text-4xl md:text-5xl font-bold mb-4">
                  Build Your <span className="gradient-text">AI-Powered App</span>
                </h1>
                <p className="text-xl text-gray-400">
                  Describe your idea. Our AI team will research, plan, and build.
                </p>
              </div>

              <div className="glass rounded-2xl p-8 space-y-8">
                {/* Idea Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    <Lightbulb className="w-4 h-4 inline mr-2" />
                    What do you want to build?
                  </label>
                  <textarea
                    value={ideaDescription}
                    onChange={(e) => setIdeaDescription(e.target.value)}
                    placeholder="e.g., An AI-driven fintech product that combines stock analysis with automated portfolio tracking..."
                    className="w-full px-4 py-3 bg-black/30 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                    rows={3}
                  />
                </div>

                {/* Problem Statement (Optional) */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    <Target className="w-4 h-4 inline mr-2" />
                    What problem does it solve? (optional)
                  </label>
                  <textarea
                    value={problemStatement}
                    onChange={(e) => setProblemStatement(e.target.value)}
                    placeholder="e.g., Retail investors lack access to institutional-grade analysis tools..."
                    className="w-full px-4 py-3 bg-black/30 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                    rows={2}
                  />
                </div>

                {/* Reference Products */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    <Eye className="w-4 h-4 inline mr-2" />
                    Benchmark Products (we'll analyze these)
                  </label>
                  <div className="flex gap-4">
                    {referenceProducts.map((ref, i) => (
                      <input
                        key={i}
                        value={ref}
                        onChange={(e) => {
                          const newRefs = [...referenceProducts];
                          newRefs[i] = e.target.value;
                          setReferenceProducts(newRefs);
                        }}
                        placeholder={`Reference ${i + 1} (e.g., Robinhood.com)`}
                        className="flex-1 px-4 py-3 bg-black/30 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:ring-2 focus:ring-primary-500"
                      />
                    ))}
                  </div>
                </div>

                {/* Audience & Depth */}
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Audience */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      <Users className="w-4 h-4 inline mr-2" />
                      Primary Audience
                    </label>
                    <select
                      value={primaryAudience}
                      onChange={(e) => setPrimaryAudience(e.target.value)}
                      className="w-full px-4 py-3 bg-black/30 border border-white/10 rounded-xl text-white focus:ring-2 focus:ring-primary-500"
                    >
                      {AUDIENCE_OPTIONS.map(opt => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  </div>

                  {/* Analysis Depth */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      <BarChart3 className="w-4 h-4 inline mr-2" />
                      Analysis Depth
                    </label>
                    <div className="flex gap-2">
                      {DEPTH_OPTIONS.map(opt => (
                        <button
                          key={opt.value}
                          onClick={() => setAnalysisDepth(opt.value)}
                          className={`flex-1 px-3 py-3 rounded-xl border transition-all ${
                            analysisDepth === opt.value
                              ? 'border-primary-500 bg-primary-500/20 text-white'
                              : 'border-white/10 hover:border-white/20 text-gray-400'
                          }`}
                        >
                          <div className="text-sm font-medium">{opt.label}</div>
                          <div className="text-xs opacity-70">{opt.time}</div>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Constraints */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-3">
                    <Shield className="w-4 h-4 inline mr-2" />
                    Compliance Guardrails
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    {Object.entries(DEFAULT_CONSTRAINTS).map(([key, _]) => (
                      <label key={key} className="flex items-center gap-3 p-3 bg-black/20 rounded-lg cursor-pointer hover:bg-black/30">
                        <input
                          type="checkbox"
                          checked={constraints[key]}
                          onChange={(e) => setConstraints({ ...constraints, [key]: e.target.checked })}
                          className="w-4 h-4 rounded bg-black/30 border-white/20 text-primary-500 focus:ring-primary-500"
                        />
                        <span className="text-sm text-gray-300">
                          {key.replace('avoid_', 'Avoid ').replace(/_/g, ' ')}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Error Display */}
                {error && (
                  <div className="p-4 bg-red-500/20 border border-red-500/50 rounded-xl text-red-300 flex items-center gap-2">
                    <AlertCircle className="w-5 h-5" />
                    {error}
                  </div>
                )}

                {/* Generate Button */}
                <button
                  onClick={handleGeneratePlan}
                  disabled={!ideaDescription.trim() || isGenerating}
                  className="w-full py-4 bg-gradient-to-r from-primary-600 to-purple-600 text-white font-semibold rounded-xl hover:from-primary-500 hover:to-purple-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Generating Plan...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5" />
                      Generate AI Plan
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* === PLAN REVIEW STATE === */}
          {flowState === 'plan' && aiPlan && (
            <div className="animate-fade-in">
              <div className="flex items-center justify-between mb-8">
                <button
                  onClick={() => setFlowState('input')}
                  className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Edit Idea
                </button>
                <h2 className="text-2xl font-bold">Review Your Plan</h2>
                <div className="w-24" /> {/* Spacer */}
              </div>

              <div className="space-y-6">
                {/* Product Concept */}
                <div className={`glass rounded-2xl p-6 border-2 transition-all ${approvals.plan ? 'border-green-500/50' : 'border-transparent'}`}>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-semibold flex items-center gap-2">
                      <Lightbulb className="w-5 h-5 text-primary-400" />
                      Product Concept
                    </h3>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={approvals.plan}
                        onChange={(e) => setApprovals({ ...approvals, plan: e.target.checked })}
                        className="w-5 h-5 rounded bg-black/30 border-white/20 text-green-500 focus:ring-green-500"
                      />
                      <span className="text-sm text-gray-400">Approve</span>
                    </label>
                  </div>
                  <p className="text-gray-300 mb-4">{aiPlan.product_concept}</p>

                  {/* Feature Prioritization */}
                  <div className="mt-4">
                    <h4 className="text-sm font-medium text-gray-400 mb-2">Top Features</h4>
                    <div className="space-y-2">
                      {aiPlan.feature_prioritization.slice(0, 5).map((f, i) => (
                        <div key={i} className="flex items-center justify-between p-2 bg-black/20 rounded-lg">
                          <span className="text-sm">{f.feature}</span>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                            f.impact === 'high' ? 'bg-green-500/20 text-green-400' :
                            f.impact === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                            'bg-gray-500/20 text-gray-400'
                          }`}>
                            {f.impact}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Cost Estimate */}
                <div className={`glass rounded-2xl p-6 border-2 transition-all ${approvals.budget ? 'border-green-500/50' : 'border-transparent'}`}>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-semibold flex items-center gap-2">
                      <DollarSign className="w-5 h-5 text-green-400" />
                      Budget & Costs
                    </h3>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={approvals.budget}
                        onChange={(e) => setApprovals({ ...approvals, budget: e.target.checked })}
                        className="w-5 h-5 rounded bg-black/30 border-white/20 text-green-500 focus:ring-green-500"
                      />
                      <span className="text-sm text-gray-400">Approve</span>
                    </label>
                  </div>
                  <div className="grid md:grid-cols-3 gap-4">
                    <div className="p-4 bg-black/20 rounded-xl text-center">
                      <div className="text-3xl font-bold text-green-400">${costEstimate.ai_execution.usd}</div>
                      <div className="text-sm text-gray-400">AI Execution (one-time)</div>
                      <div className="text-xs text-gray-500">{costEstimate.ai_execution.credits.toLocaleString()} credits</div>
                    </div>
                    <div className="p-4 bg-black/20 rounded-xl text-center">
                      <div className="text-3xl font-bold text-primary-400">{costEstimate.build_guidance.estimated_weeks} weeks</div>
                      <div className="text-sm text-gray-400">Build Timeline</div>
                    </div>
                    <div className="p-4 bg-black/20 rounded-xl text-center">
                      <div className="text-3xl font-bold text-purple-400">${costEstimate.hosting.monthly_usd}</div>
                      <div className="text-sm text-gray-400">Monthly Hosting</div>
                      <div className="text-xs text-gray-500">{costEstimate.hosting.platform}</div>
                    </div>
                  </div>
                  <p className="mt-4 text-sm text-gray-500 flex items-center gap-2">
                    <Shield className="w-4 h-4" />
                    Costs are predictable and replayable. No surprises.
                  </p>
                </div>

                {/* Timeline */}
                <div className={`glass rounded-2xl p-6 border-2 transition-all ${approvals.timeline ? 'border-green-500/50' : 'border-transparent'}`}>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-semibold flex items-center gap-2">
                      <Clock className="w-5 h-5 text-primary-400" />
                      Timeline & Milestones
                    </h3>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={approvals.timeline}
                        onChange={(e) => setApprovals({ ...approvals, timeline: e.target.checked })}
                        className="w-5 h-5 rounded bg-black/30 border-white/20 text-green-500 focus:ring-green-500"
                      />
                      <span className="text-sm text-gray-400">Approve</span>
                    </label>
                  </div>
                  <div className="relative">
                    <div className="absolute top-4 left-0 right-0 h-1 bg-gray-700 rounded-full" />
                    <div className="relative flex justify-between">
                      {timeline.milestones.map((m, i) => (
                        <div key={i} className="flex flex-col items-center" style={{ width: `${100 / timeline.milestones.length}%` }}>
                          <div className="w-3 h-3 rounded-full bg-primary-500 mb-2 relative z-10" />
                          <div className="text-xs text-center">
                            <div className="font-medium">Week {m.week}</div>
                            <div className="text-gray-400 hidden sm:block">{m.label}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Deployment */}
                <div className={`glass rounded-2xl p-6 border-2 transition-all ${approvals.deployment ? 'border-green-500/50' : 'border-transparent'}`}>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-semibold flex items-center gap-2">
                      <Rocket className="w-5 h-5 text-purple-400" />
                      Hosting & Deployment
                    </h3>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={approvals.deployment}
                        onChange={(e) => setApprovals({ ...approvals, deployment: e.target.checked })}
                        className="w-5 h-5 rounded bg-black/30 border-white/20 text-green-500 focus:ring-green-500"
                      />
                      <span className="text-sm text-gray-400">Approve</span>
                    </label>
                  </div>
                  <div className="flex items-center justify-between p-4 bg-black/20 rounded-xl">
                    <div>
                      <div className="font-medium">Agenticverz Hosting</div>
                      <div className="text-sm text-gray-400">Landing page, product overview, marketing site</div>
                    </div>
                    <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm">
                      Custom domain supported
                    </span>
                  </div>
                </div>

                {/* Execute Button */}
                <button
                  onClick={handleApproveAndExecute}
                  disabled={!allApproved || isExecuting}
                  className={`w-full py-4 font-semibold rounded-xl transition-all flex items-center justify-center gap-2 ${
                    allApproved
                      ? 'bg-gradient-to-r from-green-600 to-emerald-600 text-white hover:from-green-500 hover:to-emerald-500'
                      : 'bg-gray-700 text-gray-400 cursor-not-allowed'
                  }`}
                >
                  {allApproved ? (
                    <>
                      <Play className="w-5 h-5" />
                      Proceed with AI Execution
                    </>
                  ) : (
                    <>
                      <AlertCircle className="w-5 h-5" />
                      Approve all sections to proceed
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* === EXECUTION STATE === */}
          {flowState === 'execution' && (
            <div className="animate-fade-in">
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-2xl font-bold">Building Your Product</h2>
                <button
                  onClick={() => setShowAgentPane(!showAgentPane)}
                  className="flex items-center gap-2 px-4 py-2 glass rounded-lg hover:bg-white/10 transition-colors"
                >
                  <Users className="w-4 h-4" />
                  {showAgentPane ? 'Hide' : 'Show'} AI Team
                  {showAgentPane ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>
              </div>

              <div className="grid md:grid-cols-3 gap-6">
                {/* Main Progress */}
                <div className="md:col-span-2 space-y-6">
                  {/* Progress Overview */}
                  <div className="glass rounded-2xl p-6">
                    <h3 className="text-lg font-semibold mb-4">Execution Progress</h3>
                    <div className="space-y-4">
                      {agentWorkforce.map((agent, i) => (
                        <div key={i} className="flex items-center gap-4">
                          <div className={`p-2 rounded-lg ${
                            agent.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                            agent.status === 'working' ? 'bg-primary-500/20 text-primary-400' :
                            'bg-gray-700 text-gray-400'
                          }`}>
                            <agent.icon className="w-5 h-5" />
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-medium">{agent.display_name}</span>
                              <span className="text-sm text-gray-400">
                                {agent.status === 'completed' ? 'Done' :
                                 agent.status === 'working' ? `${Math.round(agent.progress)}%` :
                                 'Queued'}
                              </span>
                            </div>
                            <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                              <div
                                className={`h-full transition-all duration-300 ${
                                  agent.status === 'completed' ? 'bg-green-500' :
                                  agent.status === 'working' ? 'bg-primary-500' : 'bg-gray-600'
                                }`}
                                style={{ width: `${agent.progress}%` }}
                              />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Artifacts */}
                  {artifacts.length > 0 && (
                    <div className="glass rounded-2xl p-6">
                      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <FileText className="w-5 h-5 text-primary-400" />
                        Generated Artifacts
                      </h3>
                      <div className="space-y-2">
                        {artifacts.map((artifact, i) => (
                          <div key={i} className="flex items-center justify-between p-3 bg-black/20 rounded-lg hover:bg-black/30 transition-colors cursor-pointer">
                            <div className="flex items-center gap-3">
                              {artifact.type === 'markdown' ? <FileText className="w-4 h-4 text-gray-400" /> : <Code className="w-4 h-4 text-gray-400" />}
                              <span>{artifact.name}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-gray-500">{artifact.size}</span>
                              <Download className="w-4 h-4 text-gray-400" />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Completion Actions */}
                  {!isExecuting && artifacts.length > 0 && (
                    <div className="glass rounded-2xl p-6">
                      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <CheckCircle className="w-5 h-5 text-green-400" />
                        Execution Complete
                      </h3>
                      <div className="flex gap-4">
                        <button className="flex-1 py-3 bg-primary-600 text-white rounded-xl hover:bg-primary-500 transition-colors flex items-center justify-center gap-2">
                          <Download className="w-4 h-4" />
                          Download All Artifacts
                        </button>
                        <button
                          onClick={handleReset}
                          className="flex-1 py-3 glass rounded-xl hover:bg-white/10 transition-colors flex items-center justify-center gap-2"
                        >
                          <RefreshCw className="w-4 h-4" />
                          Start New Project
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Agent Workforce Pane (Collapsible) */}
                {showAgentPane && (
                  <div className="glass rounded-2xl p-6 h-fit animate-slide-up">
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                      <Brain className="w-5 h-5 text-purple-400" />
                      Your AI Team
                    </h3>
                    <p className="text-sm text-gray-400 mb-4">
                      Your AI team is working...
                    </p>
                    <div className="space-y-3">
                      {agentWorkforce.map((agent, i) => (
                        <div key={i} className={`p-3 rounded-lg transition-all ${
                          agent.status === 'working' ? 'bg-primary-500/10 border border-primary-500/30' :
                          agent.status === 'completed' ? 'bg-green-500/10' : 'bg-black/20'
                        }`}>
                          <div className="flex items-center gap-2 mb-1">
                            <agent.icon className={`w-4 h-4 ${
                              agent.status === 'completed' ? 'text-green-400' :
                              agent.status === 'working' ? 'text-primary-400' : 'text-gray-500'
                            }`} />
                            <span className="font-medium text-sm">{agent.display_name}</span>
                            {agent.status === 'working' && (
                              <Loader2 className="w-3 h-3 animate-spin text-primary-400 ml-auto" />
                            )}
                            {agent.status === 'completed' && (
                              <CheckCircle className="w-3 h-3 text-green-400 ml-auto" />
                            )}
                          </div>
                          <div className="text-xs text-gray-400">{agent.current_task}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

// === HELPER FUNCTIONS ===
function generateMockPlan(idea, references, audience) {
  return {
    ai_plan: {
      product_concept: `An AI-powered platform that combines the best features of ${references.filter(r => r).join(' and ') || 'leading solutions'} to deliver a unique solution for ${AUDIENCE_OPTIONS.find(a => a.value === audience)?.label || 'users'}. ${idea}`,
      competitor_analysis: 'Detailed competitor analysis tables generated...',
      feature_prioritization: [
        { feature: 'AI-Powered Market Analysis', impact: 'high' },
        { feature: 'Automated Portfolio Tracking', impact: 'high' },
        { feature: 'Real-time Alerts & Notifications', impact: 'high' },
        { feature: 'Customizable Dashboards', impact: 'medium' },
        { feature: 'Social Trading Features', impact: 'medium' },
        { feature: 'Advanced Charting Tools', impact: 'medium' },
        { feature: 'API Integrations', impact: 'low' },
      ],
      webapp_architecture: {
        frontend: 'React + TailwindCSS',
        backend: 'FastAPI + PostgreSQL',
        data_sources: ['Market Data APIs', 'User Portfolio Data', 'News Feeds'],
      },
      task_split: {
        ai_handles: [
          'Market research & competitive analysis',
          'Feature prioritization & architecture',
          'Landing page copy & messaging',
          'Marketing plan & campaign structure',
        ],
        founder_handles: [
          'Final product validation',
          'Code implementation & deployment',
          'User testing & feedback',
          'Legal compliance & sign-offs',
        ],
      },
    },
    cost_estimate: {
      ai_execution: {
        credits: 8000,
        usd: 4.80,
      },
      build_guidance: {
        estimated_weeks: 6,
        suggested_roles: ['Frontend Dev', 'Backend Dev'],
      },
      hosting: {
        platform: 'Agenticverz',
        monthly_usd: 0,
      },
    },
    timeline: {
      total_weeks: 6,
      milestones: [
        { week: 1, label: 'Research' },
        { week: 2, label: 'Strategy' },
        { week: 3, label: 'Features' },
        { week: 4, label: 'MVP' },
        { week: 5, label: 'Testing' },
        { week: 6, label: 'Launch' },
      ],
    },
    marketing_plan: {
      phases: [
        {
          phase: 'Pre-Launch',
          ai_does: ['Persona analysis', 'Messaging framework'],
          founder_does: ['Validate ICP'],
          budget_usd: 0,
          metrics: ['waitlist_signups'],
        },
        {
          phase: 'Launch',
          ai_does: ['Landing copy', 'Email drafts', 'Social content'],
          founder_does: ['Publish', 'Outreach'],
          budget_usd: 200,
          metrics: ['traffic', 'conversion'],
        },
      ],
    },
  };
}

export default BuildYourApp;
