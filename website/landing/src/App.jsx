import {
  Zap, Shield, Activity, GitBranch, ArrowRight,
  CheckCircle, Terminal, Layers, Clock, Database,
  ChevronRight, Github, BookOpen, Mail, Target,
  Lock, Eye, Gauge
} from 'lucide-react';

function App() {
  return (
    <div className="min-h-screen gradient-bg">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-purple-500 flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-semibold">Agenticverz</span>
            </div>
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-gray-400 hover:text-white transition-colors">Features</a>
              <a href="#how-it-works" className="text-gray-400 hover:text-white transition-colors">How it Works</a>
              <a href="#reliability" className="text-gray-400 hover:text-white transition-colors">Why AOS</a>
              <a href="/console" className="px-4 py-2 bg-primary-600 hover:bg-primary-500 rounded-lg transition-colors font-medium">
                Console
              </a>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-8 animate-fade-in">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            <span className="text-sm text-gray-300">Now in Private Beta</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-bold mb-6 animate-slide-up">
            Agents that{' '}
            <span className="gradient-text">just work.</span>
          </h1>

          <p className="text-xl md:text-2xl text-gray-400 mb-4 max-w-3xl mx-auto animate-slide-up" style={{ animationDelay: '0.1s' }}>
            Build reliable, self-healing AI agents that scale.
          </p>

          <p className="text-lg text-gray-500 mb-10 max-w-2xl mx-auto animate-slide-up" style={{ animationDelay: '0.15s' }}>
            Predictable, efficient, outcome-focused workflows for AI teams
            that need reliability — not surprises.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center animate-slide-up" style={{ animationDelay: '0.2s' }}>
            <a href="/console" className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white text-black font-semibold rounded-xl hover:bg-gray-100 transition-all hover:scale-105">
              Get Started <ArrowRight className="w-5 h-5" />
            </a>
            <a href="https://github.com/agenticverz/aos" className="inline-flex items-center justify-center gap-2 px-8 py-4 glass rounded-xl font-semibold hover:bg-white/10 transition-all">
              <Github className="w-5 h-5" /> View on GitHub
            </a>
          </div>
        </div>

        {/* Hero visual - ABSTRACT code snippet */}
        <div className="max-w-4xl mx-auto mt-20 animate-fade-in" style={{ animationDelay: '0.4s' }}>
          <div className="glass rounded-2xl p-8 glow-border">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span className="ml-4 text-sm text-gray-500 font-mono">workflow.json</span>
            </div>
            <pre className="text-sm md:text-base font-mono text-gray-300 overflow-x-auto">
{`{
  "workflow": "customer-insights",
  "steps": ["collect", "analyze", "respond"],
  "mode": "reliable",
  "preview": {
    "ready": true,
    "estimated_time": "~2s",
    "confidence": "high"
  }
}`}
            </pre>
          </div>
        </div>
      </section>

      {/* Why AOS Section */}
      <section id="features" className="py-20 px-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-8">
            <h2 className="text-3xl md:text-5xl font-bold mb-4">
              AI orchestration is chaotic.
            </h2>
            <p className="text-xl text-gray-400 mb-6">
              AOS makes it <span className="text-white font-semibold">predictable</span>.
            </p>
            <p className="text-gray-500 max-w-2xl mx-auto">
              Traditional AI pipelines rely on best-effort execution, inconsistent retries,
              and unstructured state. AOS brings reliability, predictability, and clarity.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mt-12">
            {[
              { icon: Zap, title: 'Efficient Execution', desc: 'Workflows that run predictably every time' },
              { icon: GitBranch, title: 'Adaptive Workflows', desc: 'Structured paths that handle edge cases' },
              { icon: Database, title: 'Contextual Memory', desc: 'State that persists and informs decisions' },
              { icon: Shield, title: 'Self-Healing Flows', desc: 'Issues detected and resolved automatically' },
              { icon: Clock, title: 'Predictive Simulation', desc: 'Know costs and outcomes before you run' },
              { icon: Activity, title: 'Resource-Aware', desc: 'Workload contracts enforced at runtime' },
              { icon: Layers, title: 'Smart Caching', desc: 'Results that compound over time' },
              { icon: CheckCircle, title: 'Outcome-Focused', desc: 'Guaranteed completion paths' },
            ].map((feature, i) => (
              <div key={i} className="glass rounded-xl p-6 hover:bg-white/5 transition-all group">
                <feature.icon className="w-10 h-10 text-primary-400 mb-4 group-hover:scale-110 transition-transform" />
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-gray-400 text-sm">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20 px-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold mb-4">
              Build once, run reliably.
            </h2>
            <p className="text-xl text-gray-400">
              From design to execution in minutes.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: '01',
                title: 'Define Your Workflow',
                desc: 'Create workflows using composable operations. Data collection, analysis, responses — all in one definition.',
                code: '{"steps": ["init", "operate", "complete"]}'
              },
              {
                step: '02',
                title: 'Preview First',
                desc: 'Know your outcomes and constraints before committing any resources. No surprises, no wasted runs.',
                code: '"ready": true, "confidence": "high"'
              },
              {
                step: '03',
                title: 'Execute & Observe',
                desc: 'Run with confidence. Real-time visibility, automatic recovery, and structured results.',
                code: '"status": "completed", "reliable": true'
              },
            ].map((item, i) => (
              <div key={i} className="relative">
                <div className="text-6xl font-bold text-white/5 absolute -top-4 -left-2">{item.step}</div>
                <div className="glass rounded-xl p-6 relative">
                  <h3 className="text-xl font-semibold mb-3">{item.title}</h3>
                  <p className="text-gray-400 mb-4">{item.desc}</p>
                  <div className="bg-black/30 rounded-lg p-3 font-mono text-sm text-primary-400">
                    {item.code}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* NEW: Built for Reliability Section */}
      <section id="reliability" className="py-20 px-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-5xl font-bold mb-4">
              Built for reliability-first AI teams.
            </h2>
            <p className="text-xl text-gray-400">
              When AI operations must work, every time.
            </p>
          </div>

          <div className="grid md:grid-cols-5 gap-6">
            {[
              { icon: Target, label: 'Predictable Workflows' },
              { icon: Eye, label: 'Transparent Operations' },
              { icon: Lock, label: 'Guaranteed Boundaries' },
              { icon: Gauge, label: 'Clear Execution Paths' },
              { icon: Shield, label: 'Safe Automation' },
            ].map((item, i) => (
              <div key={i} className="glass rounded-xl p-6 text-center hover:bg-white/5 transition-all">
                <item.icon className="w-8 h-8 text-primary-400 mx-auto mb-3" />
                <p className="text-sm font-medium">{item.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Moat Section */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold mb-4">
              Your advantage isn't the code.
            </h2>
            <p className="text-xl text-gray-400">
              It's the <span className="text-white font-semibold">data</span>.
            </p>
          </div>

          <div className="glass rounded-2xl overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left p-4 text-gray-400 font-medium">What You Get</th>
                  <th className="text-left p-4 text-gray-400 font-medium">Defensibility</th>
                  <th className="text-left p-4 text-gray-400 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { feature: 'Failure Pattern Learning', defensibility: 'Very High', status: 'Operational' },
                  { feature: 'Execution Outcome Data', defensibility: 'High', status: 'Accelerating' },
                  { feature: 'Cost Optimization Models', defensibility: 'High', status: 'Operational' },
                  { feature: 'Workflow Templates', defensibility: 'Medium', status: 'Expanding' },
                ].map((row, i) => (
                  <tr key={i} className="border-b border-white/5 hover:bg-white/5">
                    <td className="p-4 font-medium">{row.feature}</td>
                    <td className="p-4">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        row.defensibility === 'Very High' ? 'bg-green-500/20 text-green-400' :
                        row.defensibility === 'High' ? 'bg-blue-500/20 text-blue-400' :
                        'bg-yellow-500/20 text-yellow-400'
                      }`}>
                        {row.defensibility}
                      </span>
                    </td>
                    <td className="p-4 text-gray-400">{row.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-5xl font-bold mb-6">
            Start building reliable AI agents today.
          </h2>
          <p className="text-xl text-gray-400 mb-4">
            Deploy workflows that scale, adapt, and self-correct.
          </p>
          <p className="text-gray-500 mb-10">
            No agents required to get started — explore workflows instantly.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a href="/console" className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white text-black font-semibold rounded-xl hover:bg-gray-100 transition-all hover:scale-105">
              Open Console <ChevronRight className="w-5 h-5" />
            </a>
            <a href="https://docs.agenticverz.com" className="inline-flex items-center justify-center gap-2 px-8 py-4 glass rounded-xl font-semibold hover:bg-white/10 transition-all">
              <BookOpen className="w-5 h-5" /> Documentation
            </a>
          </div>

          <div className="mt-16 flex items-center justify-center gap-8 text-gray-500">
            <a href="https://github.com/agenticverz/aos" className="hover:text-white transition-colors flex items-center gap-2">
              <Github className="w-5 h-5" /> GitHub
            </a>
            <a href="mailto:hello@agenticverz.com" className="hover:text-white transition-colors flex items-center gap-2">
              <Mail className="w-5 h-5" /> Contact
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-gradient-to-br from-primary-500 to-purple-500 flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="text-sm text-gray-400">Agenticverz</span>
          </div>
          <p className="text-sm text-gray-500">
            Designed for builders, platform teams, and infra engineers.
          </p>
          <p className="text-sm text-gray-500">
            &copy; {new Date().getFullYear()} Agenticverz. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
