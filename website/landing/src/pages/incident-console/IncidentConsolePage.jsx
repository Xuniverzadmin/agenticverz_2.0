import {
  Zap, Shield, ArrowRight, ArrowLeft,
  CheckCircle, Terminal, Clock,
  ChevronRight, Github, BookOpen, Mail,
  AlertTriangle, FileText, Search, Filter,
  Play, RefreshCw, Download, Eye, Layers,
  BarChart3, Scale, Lock, Cpu
} from 'lucide-react';

// Feature Card Component
function FeatureCard({ icon: Icon, title, description, color }) {
  return (
    <div className="glass rounded-xl p-6 hover:bg-white/5 transition-all">
      <div className={`w-12 h-12 rounded-lg ${color} flex items-center justify-center mb-4`}>
        <Icon className="w-6 h-6 text-white" />
      </div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-gray-400 text-sm">{description}</p>
    </div>
  );
}

// Step Card Component
function StepCard({ step, title, description, code }) {
  return (
    <div className="relative">
      <div className="text-6xl font-bold text-white/5 absolute -top-4 -left-2">{step}</div>
      <div className="glass rounded-xl p-6 relative h-full">
        <h3 className="text-xl font-semibold mb-3">{title}</h3>
        <p className="text-gray-400 mb-4">{description}</p>
        {code && (
          <div className="bg-black/30 rounded-lg p-3 font-mono text-sm text-primary-400 overflow-x-auto">
            {code}
          </div>
        )}
      </div>
    </div>
  );
}

export function IncidentConsolePage() {
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
            <div className="hidden md:flex items-center gap-8">
              <a href="/" className="text-gray-400 hover:text-white transition-colors flex items-center gap-1">
                <ArrowLeft className="w-4 h-4" /> Back to Home
              </a>
              <a href="https://docs.agenticverz.com" className="text-gray-400 hover:text-white transition-colors">Docs</a>
              <a href="/console" className="px-4 py-2 bg-gradient-to-r from-primary-600 to-purple-600 hover:from-primary-500 hover:to-purple-500 rounded-lg transition-colors font-medium">
                Request Access
              </a>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-16 px-6">
        <div className="max-w-5xl mx-auto">
          <a href="/" className="inline-flex items-center gap-2 text-gray-400 hover:text-white transition-colors mb-8">
            <ArrowLeft className="w-4 h-4" /> Back to Home
          </a>

          <div className="flex items-center gap-3 mb-6">
            <div className="w-14 h-14 rounded-xl bg-red-500/20 flex items-center justify-center">
              <AlertTriangle className="w-7 h-7 text-red-400" />
            </div>
            <div>
              <h1 className="text-4xl md:text-5xl font-bold">AI Incident Console</h1>
              <p className="text-gray-400">Investigate, understand, and prevent AI failures</p>
            </div>
          </div>

          <p className="text-xl text-gray-300 mb-8 max-w-3xl">
            When AI goes wrong, you need answers — not guesses. The Incident Console gives you
            full decision trace, search, deterministic replay, and evidence export.
          </p>

          <div className="flex flex-col sm:flex-row gap-4">
            <a href="/console" className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-gradient-to-r from-primary-600 to-purple-600 text-white font-semibold rounded-xl hover:from-primary-500 hover:to-purple-500 transition-all hover:scale-105 shadow-lg shadow-primary-500/25">
              See Live Demo <Play className="w-5 h-5" />
            </a>
            <a href="https://docs.agenticverz.com/incident-console" className="inline-flex items-center justify-center gap-2 px-8 py-4 glass rounded-xl font-semibold hover:bg-white/10 transition-all">
              <BookOpen className="w-5 h-5" /> Read Docs
            </a>
            <a href="mailto:demo@agenticverz.com" className="inline-flex items-center justify-center gap-2 px-8 py-4 glass rounded-xl font-semibold hover:bg-white/10 transition-all">
              Request Access <ArrowRight className="w-5 h-5" />
            </a>
          </div>
        </div>
      </section>

      {/* Console Preview */}
      <section className="py-12 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="glass rounded-2xl p-2 glow-border">
            <div className="bg-gray-900 rounded-xl overflow-hidden">
              {/* Mock Console Header */}
              <div className="flex items-center gap-2 px-4 py-3 bg-black/50 border-b border-white/5">
                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                <span className="ml-4 text-sm text-gray-500 font-mono">incident-console.agenticverz.com</span>
              </div>

              {/* Mock Console Content */}
              <div className="p-6">
                {/* Search Bar */}
                <div className="flex gap-4 mb-6">
                  <div className="flex-1 flex items-center gap-3 bg-black/30 rounded-lg px-4 py-3">
                    <Search className="w-5 h-5 text-gray-500" />
                    <span className="text-gray-500">Search incidents by user, time, or content...</span>
                  </div>
                  <button className="flex items-center gap-2 px-4 py-3 bg-white/5 rounded-lg text-gray-400">
                    <Filter className="w-5 h-5" /> Filters
                  </button>
                </div>

                {/* Mock Incident List */}
                <div className="space-y-3">
                  {[
                    { severity: 'critical', time: '2 min ago', user: 'user_8372', summary: 'Contract auto-renew assertion without data', policy: 'CONTENT_ACCURACY' },
                    { severity: 'high', time: '5 min ago', user: 'user_1234', summary: 'Payment status claim on null field', policy: 'CONTENT_ACCURACY' },
                    { severity: 'medium', time: '12 min ago', user: 'user_5678', summary: 'Hallucinated study reference detected', policy: 'HALLUCINATION' },
                  ].map((incident, i) => (
                    <div key={i} className="flex items-center gap-4 p-4 bg-black/30 rounded-lg hover:bg-white/5 transition-colors cursor-pointer">
                      <div className={`w-2 h-2 rounded-full ${
                        incident.severity === 'critical' ? 'bg-red-500' :
                        incident.severity === 'high' ? 'bg-orange-500' :
                        'bg-yellow-500'
                      }`}></div>
                      <span className="text-sm text-gray-500 w-20">{incident.time}</span>
                      <span className="text-sm text-gray-400 w-24 font-mono">{incident.user}</span>
                      <span className="flex-1 text-sm text-gray-300 truncate">{incident.summary}</span>
                      <span className="text-xs px-2 py-1 rounded bg-white/5 text-gray-400">{incident.policy}</span>
                      <ChevronRight className="w-4 h-4 text-gray-600" />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-16 px-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">What you get</h2>
            <p className="text-xl text-gray-400">Everything you need to investigate AI incidents</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <FeatureCard
              icon={Search}
              title="Full-Text Search"
              description="Search incidents by user ID, time range, content, severity, or policy type. Find what you need in seconds."
              color="bg-blue-500/80"
            />
            <FeatureCard
              icon={Layers}
              title="Decision Timeline"
              description="Step-by-step trace of every decision: input received, policies checked, action taken, output returned."
              color="bg-purple-500/80"
            />
            <FeatureCard
              icon={RefreshCw}
              title="Deterministic Replay"
              description="Replay any incident with exact same inputs. See what happened. Test counterfactuals."
              color="bg-green-500/80"
            />
            <FeatureCard
              icon={Scale}
              title="Policy Evaluation"
              description="See which policies triggered, which passed, and why. Understand the decision logic."
              color="bg-yellow-500/80"
            />
            <FeatureCard
              icon={Download}
              title="Evidence Export"
              description="Export incident reports in PDF or JSON format. SOC2-compatible evidence for audits."
              color="bg-red-500/80"
            />
            <FeatureCard
              icon={Eye}
              title="Before/After Compare"
              description="Compare original output vs. what would have happened with different policies."
              color="bg-cyan-500/80"
            />
          </div>
        </div>
      </section>

      {/* Integration Section */}
      <section className="py-16 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">One line to integrate</h2>
            <p className="text-xl text-gray-400">Point your OpenAI client at our proxy. That's it.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <StepCard
              step="01"
              title="Get API Key"
              description="Sign up and get your API key from the dashboard."
              code="AOS_API_KEY=your_key"
            />
            <StepCard
              step="02"
              title="Change Base URL"
              description="Update your OpenAI client to use our proxy."
              code='base_url="https://api.agenticverz.com/v1"'
            />
            <StepCard
              step="03"
              title="Start Seeing Data"
              description="Every call is logged, evaluated, and searchable in the console."
              code="// No other changes needed"
            />
          </div>

          <div className="mt-12 glass rounded-xl p-6">
            <h3 className="text-lg font-semibold mb-4">Full Python Example</h3>
            <pre className="text-sm font-mono text-gray-300 overflow-x-auto">
{`from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY",  # pragma: allowlist secret
    base_url="https://api.agenticverz.com/v1"  # ← Only change
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Is my contract auto-renewed?"}],
    user="user_8372"  # Optional: track by user
)

# That's it. Every call is now:
# ✓ Policy-evaluated
# ✓ Logged with full trace
# ✓ Searchable in console
# ✓ Exportable as evidence`}
            </pre>
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="py-16 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Use Cases</h2>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <div className="glass rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <Cpu className="w-6 h-6 text-blue-400" />
                <h3 className="text-lg font-semibold">Support Escalation</h3>
              </div>
              <p className="text-gray-400 mb-4">
                Customer complains AI gave wrong answer? Search by user ID, see the full trace,
                understand exactly what happened, and export evidence for the ticket.
              </p>
              <ul className="space-y-2 text-sm text-gray-400">
                <li className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-green-400" /> Find incident in &lt;10 seconds</li>
                <li className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-green-400" /> See input, context, and output</li>
                <li className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-green-400" /> Export PDF for customer</li>
              </ul>
            </div>

            <div className="glass rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <Lock className="w-6 h-6 text-green-400" />
                <h3 className="text-lg font-semibold">Compliance Audit</h3>
              </div>
              <p className="text-gray-400 mb-4">
                Auditor asks "how do you ensure AI doesn't hallucinate?" Show them the policy layer,
                the incident log, and export evidence of every prevented violation.
              </p>
              <ul className="space-y-2 text-sm text-gray-400">
                <li className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-green-400" /> Timestamped, immutable logs</li>
                <li className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-green-400" /> Policy evaluation trace</li>
                <li className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-green-400" /> SOC2-compatible evidence</li>
              </ul>
            </div>

            <div className="glass rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <BarChart3 className="w-6 h-6 text-yellow-400" />
                <h3 className="text-lg font-semibold">Policy Tuning</h3>
              </div>
              <p className="text-gray-400 mb-4">
                Too many false positives? Too lenient? Search by policy type, see what triggered,
                use counterfactual replay to test new thresholds before deploying.
              </p>
              <ul className="space-y-2 text-sm text-gray-400">
                <li className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-green-400" /> Filter by policy type</li>
                <li className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-green-400" /> Test counterfactual scenarios</li>
                <li className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-green-400" /> Compare before/after</li>
              </ul>
            </div>

            <div className="glass rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <Shield className="w-6 h-6 text-red-400" />
                <h3 className="text-lg font-semibold">Incident Response</h3>
              </div>
              <p className="text-gray-400 mb-4">
                AI said something it shouldn't? Immediately find all similar incidents, understand
                the pattern, and implement a policy fix before it happens again.
              </p>
              <ul className="space-y-2 text-sm text-gray-400">
                <li className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-green-400" /> Pattern detection across incidents</li>
                <li className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-green-400" /> Root cause analysis</li>
                <li className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-green-400" /> Rapid policy deployment</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            Ready to see your AI decisions clearly?
          </h2>
          <p className="text-xl text-gray-400 mb-10">
            Stop guessing. Start investigating.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a href="/console" className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-gradient-to-r from-primary-600 to-purple-600 text-white font-semibold rounded-xl hover:from-primary-500 hover:to-purple-500 transition-all hover:scale-105 shadow-lg shadow-primary-500/25">
              See Live Demo <Play className="w-5 h-5" />
            </a>
            <a href="mailto:demo@agenticverz.com" className="inline-flex items-center justify-center gap-2 px-8 py-4 glass rounded-xl font-semibold hover:bg-white/10 transition-all">
              Request Access <ArrowRight className="w-5 h-5" />
            </a>
            <a href="https://docs.agenticverz.com/incident-console" className="inline-flex items-center justify-center gap-2 px-8 py-4 glass rounded-xl font-semibold hover:bg-white/10 transition-all">
              <BookOpen className="w-5 h-5" /> Documentation
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-gradient-to-br from-primary-500 to-purple-500 flex items-center justify-center">
                <Zap className="w-4 h-4 text-white" />
              </div>
              <span className="text-sm text-gray-400">Agenticverz</span>
            </div>
            <div className="flex items-center gap-6 text-gray-500">
              <a href="https://github.com/agenticverz" className="hover:text-white transition-colors">
                <Github className="w-5 h-5" />
              </a>
              <a href="mailto:hello@agenticverz.com" className="hover:text-white transition-colors">
                <Mail className="w-5 h-5" />
              </a>
            </div>
            <p className="text-sm text-gray-500">
              &copy; {new Date().getFullYear()} Agenticverz. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
