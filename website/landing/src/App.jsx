import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { useState } from 'react';
import {
  Zap, Shield, Activity, ArrowRight,
  CheckCircle, Terminal, Clock,
  ChevronRight, ChevronDown, Github, BookOpen, Mail,
  AlertTriangle, FileText, BarChart3, Settings,
  Scale, Search, TrendingDown, Workflow,
  Play, Sparkles, X, Check, Users, Building2
} from 'lucide-react';
import { BuildYourApp } from './pages/build/BuildYourApp';
import { IncidentConsolePage } from './pages/incident-console/IncidentConsolePage';

// Capability Cluster Component
function CapabilityCluster({ icon: Icon, title, items, color, link }) {
  return (
    <div className="glass rounded-xl p-6 hover:bg-white/5 transition-all group h-full flex flex-col">
      <div className={`w-12 h-12 rounded-lg ${color} flex items-center justify-center mb-4`}>
        <Icon className="w-6 h-6 text-white" />
      </div>
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      <ul className="space-y-2 flex-1">
        {items.map((item, i) => (
          <li key={i} className="text-gray-400 text-sm flex items-start gap-2">
            <ChevronRight className="w-4 h-4 text-gray-600 mt-0.5 flex-shrink-0" />
            {item}
          </li>
        ))}
      </ul>
      <a href={link} className="mt-4 text-primary-400 text-sm font-medium flex items-center gap-1 group-hover:gap-2 transition-all">
        Learn More <ArrowRight className="w-4 h-4" />
      </a>
    </div>
  );
}

// Entry Path Component
function EntryPath({ icon: Icon, title, description, cta, link }) {
  return (
    <div className="glass rounded-xl p-6 text-center hover:bg-white/5 transition-all group">
      <div className="w-14 h-14 rounded-full bg-white/5 flex items-center justify-center mx-auto mb-4 group-hover:bg-white/10 transition-all">
        <Icon className="w-7 h-7 text-primary-400" />
      </div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-gray-400 text-sm mb-4">{description}</p>
      <a href={link} className="inline-flex items-center gap-2 px-5 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition-all font-medium text-sm">
        {cta} <ArrowRight className="w-4 h-4" />
      </a>
    </div>
  );
}

// Products Dropdown
function ProductsDropdown({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="absolute top-full left-0 mt-2 w-72 glass rounded-xl overflow-hidden shadow-xl z-50">
      <a href="/incident-console" className="block px-4 py-3 hover:bg-white/10 transition-colors border-b border-white/5">
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400" />
          <div>
            <div className="font-medium">Incident Console</div>
            <div className="text-xs text-gray-400">Investigate AI failures</div>
          </div>
        </div>
      </a>
      <a href="/build" className="block px-4 py-3 hover:bg-white/10 transition-colors border-b border-white/5">
        <div className="flex items-center gap-3">
          <Sparkles className="w-5 h-5 text-purple-400" />
          <div>
            <div className="font-medium">Build Your App</div>
            <div className="text-xs text-gray-400">No-code AI app builder</div>
          </div>
        </div>
      </a>
      <a href="https://docs.agenticverz.com/api" className="block px-4 py-3 hover:bg-white/10 transition-colors">
        <div className="flex items-center gap-3">
          <Terminal className="w-5 h-5 text-green-400" />
          <div>
            <div className="font-medium">API</div>
            <div className="text-xs text-gray-400">OpenAI-compatible proxy</div>
          </div>
        </div>
      </a>
    </div>
  );
}

// Landing Page Component
function LandingPage() {
  const [productsOpen, setProductsOpen] = useState(false);

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
              <div className="relative">
                <button
                  onClick={() => setProductsOpen(!productsOpen)}
                  className="text-gray-400 hover:text-white transition-colors flex items-center gap-1"
                >
                  Products <ChevronDown className={`w-4 h-4 transition-transform ${productsOpen ? 'rotate-180' : ''}`} />
                </button>
                <ProductsDropdown isOpen={productsOpen} onClose={() => setProductsOpen(false)} />
              </div>
              <a href="#capabilities" className="text-gray-400 hover:text-white transition-colors">Capabilities</a>
              <a href="https://docs.agenticverz.com" className="text-gray-400 hover:text-white transition-colors">Docs</a>
              <a href="#pricing" className="text-gray-400 hover:text-white transition-colors">Pricing</a>
              <a href="/console" className="px-4 py-2 glass hover:bg-white/10 rounded-lg transition-colors font-medium">
                Request Demo
              </a>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section - Problem Domain Statement */}
      <section className="pt-32 pb-16 px-6">
        <div className="max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-8 animate-fade-in">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            <span className="text-sm text-gray-300">Now in Private Beta</span>
          </div>

          <h1 className="text-4xl md:text-6xl font-bold mb-6 animate-slide-up">
            AI decisions happen fast.{' '}
            <span className="gradient-text">Yours should too.</span>
          </h1>

          <p className="text-xl md:text-2xl text-gray-400 mb-4 max-w-3xl mx-auto animate-slide-up" style={{ animationDelay: '0.1s' }}>
            We help teams investigate, govern, and prevent AI failures
            — before they become support tickets.
          </p>

          <p className="text-lg text-gray-500 mb-10 max-w-2xl mx-auto animate-slide-up" style={{ animationDelay: '0.15s' }}>
            Drop-in proxy between your app and any LLM. Full audit trail included.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center animate-slide-up" style={{ animationDelay: '0.2s' }}>
            <a href="#capabilities" className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white text-black font-semibold rounded-xl hover:bg-gray-100 transition-all hover:scale-105">
              See How It Works <ArrowRight className="w-5 h-5" />
            </a>
          </div>
        </div>
      </section>

      {/* Capability Clusters */}
      <section id="capabilities" className="py-20 px-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              What you can do with Agenticverz
            </h2>
            <p className="text-xl text-gray-400">
              Four capability clusters. One goal: AI you can trust.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <CapabilityCluster
              icon={AlertTriangle}
              title="Incident & Failure Management"
              color="bg-red-500/80"
              items={[
                "Incident Console",
                "Evidence Export (PDF/JSON)",
                "Deterministic Replay"
              ]}
              link="/incident-console"
            />
            <CapabilityCluster
              icon={Scale}
              title="Governance & Policy Evaluation"
              color="bg-blue-500/80"
              items={[
                "Policy Evaluation Engine",
                "Coverage Analysis",
                "Counterfactual Prevention"
              ]}
              link="https://docs.agenticverz.com/governance"
            />
            <CapabilityCluster
              icon={TrendingDown}
              title="Risk, Cost & Exposure"
              color="bg-yellow-500/80"
              items={[
                "Severity Scoring",
                "Cost Attribution",
                "Audit Trails"
              ]}
              link="https://docs.agenticverz.com/risk"
            />
            <CapabilityCluster
              icon={Workflow}
              title="Automation & Remediation"
              color="bg-green-500/80"
              items={[
                "Safeguard Suggestions",
                "Incident-to-Fix Workflows",
                "Runtime Controls"
              ]}
              link="https://docs.agenticverz.com/automation"
            />
          </div>
        </div>
      </section>

      {/* How It Fits Into Your Stack */}
      <section className="py-16 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold mb-4">
              How it fits into your stack
            </h2>
            <p className="text-gray-400">
              One line change. Full observability.
            </p>
          </div>

          <div className="glass rounded-2xl p-8">
            <div className="flex flex-col md:flex-row items-center justify-center gap-4 md:gap-8 text-center">
              <div className="flex flex-col items-center">
                <div className="w-16 h-16 rounded-xl bg-gray-800 flex items-center justify-center mb-2">
                  <Terminal className="w-8 h-8 text-gray-400" />
                </div>
                <span className="text-sm text-gray-400">Your App</span>
              </div>

              <ArrowRight className="w-6 h-6 text-gray-600 rotate-90 md:rotate-0" />

              <div className="flex flex-col items-center">
                <div className="w-16 h-16 rounded-xl bg-primary-500/20 border border-primary-500/50 flex items-center justify-center mb-2">
                  <Shield className="w-8 h-8 text-primary-400" />
                </div>
                <span className="text-sm text-primary-400 font-medium">AOS Proxy</span>
              </div>

              <ArrowRight className="w-6 h-6 text-gray-600 rotate-90 md:rotate-0" />

              <div className="flex flex-col items-center">
                <div className="w-16 h-16 rounded-xl bg-blue-500/20 flex items-center justify-center mb-2">
                  <Scale className="w-8 h-8 text-blue-400" />
                </div>
                <span className="text-sm text-gray-400">Policy Check</span>
              </div>

              <ArrowRight className="w-6 h-6 text-gray-600 rotate-90 md:rotate-0" />

              <div className="flex flex-col items-center">
                <div className="w-16 h-16 rounded-xl bg-green-500/20 flex items-center justify-center mb-2">
                  <CheckCircle className="w-8 h-8 text-green-400" />
                </div>
                <span className="text-sm text-gray-400">Decision</span>
              </div>

              <ArrowRight className="w-6 h-6 text-gray-600 rotate-90 md:rotate-0" />

              <div className="flex flex-col items-center">
                <div className="w-16 h-16 rounded-xl bg-purple-500/20 flex items-center justify-center mb-2">
                  <FileText className="w-8 h-8 text-purple-400" />
                </div>
                <span className="text-sm text-gray-400">Audit Log</span>
              </div>
            </div>

            <div className="mt-8 text-center">
              <code className="text-sm text-gray-400 bg-black/30 px-4 py-2 rounded-lg font-mono">
                base_url = "https://api.agenticverz.com/v1" <span className="text-gray-600"># That's it</span>
              </code>
            </div>
          </div>
        </div>
      </section>

      {/* Who This Is For */}
      <section className="py-16 px-6 border-t border-white/5">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold mb-4">
              Who this is for
            </h2>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <div className="glass rounded-xl p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                  <Check className="w-5 h-5 text-green-400" />
                </div>
                <h3 className="text-lg font-semibold text-green-400">Good Fit</h3>
              </div>
              <ul className="space-y-3">
                {[
                  "Teams with AI in production that need audit trails",
                  "Products requiring SOC2 or compliance evidence",
                  "Support teams debugging AI responses",
                  "Engineering teams building AI-powered features"
                ].map((item, i) => (
                  <li key={i} className="flex items-start gap-3 text-gray-300">
                    <Users className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            <div className="glass rounded-xl p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg bg-red-500/20 flex items-center justify-center">
                  <X className="w-5 h-5 text-red-400" />
                </div>
                <h3 className="text-lg font-semibold text-red-400">Not For You</h3>
              </div>
              <ul className="space-y-3">
                {[
                  "Teams still prototyping or in early R&D",
                  "Hobby projects or side experiments",
                  "Single LLM with no policy or audit needs",
                  '"Move fast, break things" mindset'
                ].map((item, i) => (
                  <li key={i} className="flex items-start gap-3 text-gray-400">
                    <Building2 className="w-5 h-5 text-gray-600 mt-0.5 flex-shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Proof of Seriousness */}
      <section className="py-16 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold mb-4">
              No magic. Just facts.
            </h2>
            <p className="text-gray-400">
              See exactly what happened. Export evidence. Move on.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <div className="glass rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <Play className="w-6 h-6 text-primary-400" />
                <h3 className="text-lg font-semibold">Deterministic Replay</h3>
              </div>
              <ul className="space-y-2 text-gray-400 text-sm mb-4">
                <li className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-green-400" /> Full decision trace (input → policy → output)</li>
                <li className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-green-400" /> Before/after comparison</li>
                <li className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-green-400" /> "What if" counterfactual analysis</li>
              </ul>
              <a href="/incident-console" className="text-primary-400 text-sm font-medium flex items-center gap-1 hover:gap-2 transition-all">
                See Demo <ArrowRight className="w-4 h-4" />
              </a>
            </div>

            <div className="glass rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <FileText className="w-6 h-6 text-purple-400" />
                <h3 className="text-lg font-semibold">Evidence Export</h3>
              </div>
              <ul className="space-y-2 text-gray-400 text-sm mb-4">
                <li className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-green-400" /> SOC2-compatible evidence format</li>
                <li className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-green-400" /> Timestamped, immutable records</li>
                <li className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-green-400" /> PDF & JSON export options</li>
              </ul>
              <a href="https://docs.agenticverz.com/evidence" className="text-primary-400 text-sm font-medium flex items-center gap-1 hover:gap-2 transition-all">
                Learn More <ArrowRight className="w-4 h-4" />
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Entry Paths */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold mb-4">
              Where do you want to start?
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <EntryPath
              icon={Search}
              title="Explore Incident Tools"
              description="Interactive tour of the console. See how investigation works."
              cta="Try Now"
              link="/incident-console"
            />
            <EntryPath
              icon={BookOpen}
              title="Read Documentation"
              description="API reference, integration guides, and examples."
              cta="Go to Docs"
              link="https://docs.agenticverz.com"
            />
            <EntryPath
              icon={BarChart3}
              title="Request Demo"
              description="Talk to us. See the live environment with your data."
              cta="Schedule"
              link="mailto:demo@agenticverz.com"
            />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-6 h-6 rounded bg-gradient-to-br from-primary-500 to-purple-500 flex items-center justify-center">
                  <Zap className="w-4 h-4 text-white" />
                </div>
                <span className="font-semibold">Agenticverz</span>
              </div>
              <p className="text-sm text-gray-500">
                AI observability and governance for teams that ship.
              </p>
            </div>

            <div>
              <h4 className="font-medium mb-4">Products</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><a href="/incident-console" className="hover:text-white transition-colors">Incident Console</a></li>
                <li><a href="/build" className="hover:text-white transition-colors">Build Your App</a></li>
                <li><a href="https://docs.agenticverz.com/api" className="hover:text-white transition-colors">API</a></li>
              </ul>
            </div>

            <div>
              <h4 className="font-medium mb-4">Resources</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><a href="https://docs.agenticverz.com" className="hover:text-white transition-colors">Documentation</a></li>
                <li><a href="https://blog.agenticverz.com" className="hover:text-white transition-colors">Blog</a></li>
                <li><a href="https://status.agenticverz.com" className="hover:text-white transition-colors">Status</a></li>
              </ul>
            </div>

            <div>
              <h4 className="font-medium mb-4">Company</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><a href="/about" className="hover:text-white transition-colors">About</a></li>
                <li><a href="mailto:hello@agenticverz.com" className="hover:text-white transition-colors">Contact</a></li>
                <li><a href="/terms" className="hover:text-white transition-colors">Terms</a></li>
                <li><a href="/privacy" className="hover:text-white transition-colors">Privacy</a></li>
              </ul>
            </div>
          </div>

          <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-8 border-t border-white/5">
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

// App with Routing
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/build" element={<BuildYourApp />} />
        <Route path="/incident-console" element={<IncidentConsolePage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
