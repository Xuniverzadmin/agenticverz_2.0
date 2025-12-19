import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { useState } from 'react';
import {
  Zap, Shield, Activity, ArrowRight,
  CheckCircle, Terminal, Clock,
  ChevronRight, ChevronDown, Github, BookOpen, Mail,
  AlertTriangle, FileText, BarChart3, Settings,
  Scale, Search, TrendingDown, Workflow,
  Play, Sparkles, X, Check, Users, Building2,
  Menu, Newspaper, ExternalLink
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

// Article Card Component
function ArticleCard({ category, title, description, readTime, link, isNew }) {
  return (
    <a href={link} className="glass rounded-xl p-6 hover:bg-white/5 transition-all group block h-full">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xs uppercase tracking-wider text-primary-400 font-medium">{category}</span>
        {isNew && (
          <span className="text-[10px] uppercase tracking-wider bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full font-medium">New</span>
        )}
      </div>
      <h3 className="text-lg font-semibold mb-2 group-hover:text-primary-400 transition-colors">{title}</h3>
      <p className="text-gray-400 text-sm mb-4 line-clamp-2">{description}</p>
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>{readTime} read</span>
        <ExternalLink className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
      </div>
    </a>
  );
}

// Products Dropdown - Simplified, no Build Your App
function ProductsDropdown({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <>
      {/* Click-away overlay */}
      <div className="fixed inset-0 z-40" onClick={onClose}></div>
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
        <a href="/documentation" className="block px-4 py-3 hover:bg-white/10 transition-colors">
          <div className="flex items-center gap-3">
            <Terminal className="w-5 h-5 text-green-400" />
            <div>
              <div className="font-medium">API & Documentation</div>
              <div className="text-xs text-gray-400">Integration guides & reference</div>
            </div>
          </div>
        </a>
      </div>
    </>
  );
}

// Mobile Menu Component
function MobileMenu({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 md:hidden">
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose}></div>
      <div className="fixed top-0 right-0 w-72 h-full glass border-l border-white/10 p-6 overflow-y-auto">
        <div className="flex justify-end mb-8">
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-lg transition-colors">
            <X className="w-6 h-6" />
          </button>
        </div>
        <div className="space-y-6">
          <div>
            <h3 className="text-xs uppercase text-gray-500 mb-3 font-medium">Products</h3>
            <div className="space-y-2">
              <a href="/incident-console" onClick={onClose} className="flex items-center gap-3 p-3 hover:bg-white/10 rounded-lg transition-colors">
                <AlertTriangle className="w-5 h-5 text-red-400" />
                <div>
                  <div className="font-medium">Incident Console</div>
                  <div className="text-xs text-gray-400">Investigate AI failures</div>
                </div>
              </a>
              <a href="/documentation" onClick={onClose} className="flex items-center gap-3 p-3 hover:bg-white/10 rounded-lg transition-colors">
                <Terminal className="w-5 h-5 text-green-400" />
                <div>
                  <div className="font-medium">API & Documentation</div>
                  <div className="text-xs text-gray-400">Integration guides</div>
                </div>
              </a>
            </div>
          </div>
          <div className="border-t border-white/10 pt-6 space-y-2">
            <a href="#capabilities" onClick={onClose} className="block p-3 hover:bg-white/10 rounded-lg transition-colors">Capabilities</a>
            <a href="#insights" onClick={onClose} className="block p-3 hover:bg-white/10 rounded-lg transition-colors">Insights</a>
            <a href="#pricing" onClick={onClose} className="block p-3 hover:bg-white/10 rounded-lg transition-colors">Pricing</a>
          </div>
          <div className="border-t border-white/10 pt-6">
            <a href="/console" onClick={onClose} className="block w-full text-center px-4 py-3 bg-gradient-to-r from-primary-600 to-purple-600 rounded-lg font-medium">
              Request Demo
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

// Landing Page Component
function LandingPage() {
  const [productsOpen, setProductsOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen gradient-bg">
      {/* Mobile Menu */}
      <MobileMenu isOpen={mobileMenuOpen} onClose={() => setMobileMenuOpen(false)} />

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

            {/* Mobile menu button */}
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="md:hidden p-2 hover:bg-white/10 rounded-lg transition-colors"
            >
              <Menu className="w-6 h-6" />
            </button>

            {/* Desktop navigation */}
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
              <a href="#insights" className="text-gray-400 hover:text-white transition-colors">Insights</a>
              <a href="/documentation" className="text-gray-400 hover:text-white transition-colors">Docs</a>
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
            Making AI systems{' '}
            <span className="gradient-text">reliable, safe, and controllable</span>{' '}
            in production.
          </h1>

          <p className="text-xl md:text-2xl text-gray-400 mb-4 max-w-3xl mx-auto animate-slide-up" style={{ animationDelay: '0.1s' }}>
            Investigate incidents. Enforce policies. Export evidence.
            One proxy between your app and any LLM.
          </p>

          <p className="text-lg text-gray-500 mb-10 max-w-2xl mx-auto animate-slide-up" style={{ animationDelay: '0.15s' }}>
            For teams that need audit trails, not log files.
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

      {/* Insights & Articles */}
      <section id="insights" className="py-20 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center justify-between mb-12">
            <div>
              <h2 className="text-2xl md:text-3xl font-bold mb-2">
                Insights
              </h2>
              <p className="text-gray-400">
                Thinking on AI reliability, governance, and operational patterns.
              </p>
            </div>
            <a href="/insights" className="hidden md:inline-flex items-center gap-2 text-primary-400 hover:text-primary-300 transition-colors">
              View all <ArrowRight className="w-4 h-4" />
            </a>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <ArticleCard
              category="Architecture"
              title="Why Proxy-Based AI Observability Beats SDK Instrumentation"
              description="The tradeoffs between embedded SDKs and proxy-based approaches for production AI systems. Spoiler: proxies win for governance."
              readTime="5 min"
              link="/insights/proxy-vs-sdk"
              isNew={true}
            />
            <ArticleCard
              category="Governance"
              title="AI Audit Trails That Actually Work in Court"
              description="What legal and compliance teams need from AI decision logs, and why most observability tools fall short."
              readTime="7 min"
              link="/insights/audit-trails-legal"
            />
            <ArticleCard
              category="Operations"
              title="The Three Types of AI Incidents (And How to Handle Each)"
              description="Not all AI failures are equal. Classification framework for triage, investigation, and remediation."
              readTime="6 min"
              link="/insights/ai-incident-types"
            />
          </div>

          <div className="mt-8 text-center md:hidden">
            <a href="/insights" className="inline-flex items-center gap-2 text-primary-400 hover:text-primary-300 transition-colors">
              View all articles <ArrowRight className="w-4 h-4" />
            </a>
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
              link="/documentation"
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
                <li><a href="/documentation" className="hover:text-white transition-colors">API & Docs</a></li>
              </ul>
            </div>

            <div>
              <h4 className="font-medium mb-4">Resources</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><a href="/documentation" className="hover:text-white transition-colors">Documentation</a></li>
                <li><a href="/insights" className="hover:text-white transition-colors">Insights</a></li>
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

// Docs Page (Placeholder)
function DocsPage() {
  return (
    <div className="min-h-screen gradient-bg">
      <nav className="fixed top-0 left-0 right-0 z-50 glass">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <a href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-purple-500 flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-semibold">Agenticverz</span>
            </a>
            <a href="/" className="text-gray-400 hover:text-white transition-colors">← Back to Home</a>
          </div>
        </div>
      </nav>

      <div className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl font-bold mb-6">Documentation</h1>
          <p className="text-xl text-gray-400 mb-12">
            API reference, integration guides, and examples for the Agenticverz platform.
          </p>

          <div className="space-y-8">
            <div className="glass rounded-xl p-6">
              <h2 className="text-2xl font-semibold mb-4 flex items-center gap-3">
                <Terminal className="w-6 h-6 text-green-400" />
                Quick Start
              </h2>
              <p className="text-gray-400 mb-4">
                Get started with Agenticverz in under 5 minutes. Point your OpenAI client at our proxy.
              </p>
              <pre className="bg-black/50 rounded-lg p-4 overflow-x-auto text-sm">
                <code className="text-gray-300">{`from openai import OpenAI

client = OpenAI(
    base_url="https://api.agenticverz.com/v1",
    api_key="YOUR_API_KEY"  # Get from dashboard  # pragma: allowlist secret
)

# That's it - all calls now have full audit trails`}</code>
              </pre>
            </div>

            <div className="glass rounded-xl p-6">
              <h2 className="text-2xl font-semibold mb-4 flex items-center gap-3">
                <BookOpen className="w-6 h-6 text-blue-400" />
                API Reference
              </h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                  <div>
                    <code className="text-primary-400">POST /v1/chat/completions</code>
                    <p className="text-sm text-gray-500 mt-1">OpenAI-compatible completions endpoint</p>
                  </div>
                  <ArrowRight className="w-5 h-5 text-gray-600" />
                </div>
                <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                  <div>
                    <code className="text-primary-400">GET /v1/incidents</code>
                    <p className="text-sm text-gray-500 mt-1">List and search incidents</p>
                  </div>
                  <ArrowRight className="w-5 h-5 text-gray-600" />
                </div>
                <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                  <div>
                    <code className="text-primary-400">GET /v1/incidents/:id/evidence</code>
                    <p className="text-sm text-gray-500 mt-1">Export evidence for an incident</p>
                  </div>
                  <ArrowRight className="w-5 h-5 text-gray-600" />
                </div>
              </div>
            </div>

            <div className="glass rounded-xl p-6">
              <h2 className="text-2xl font-semibold mb-4 flex items-center gap-3">
                <Scale className="w-6 h-6 text-purple-400" />
                Policy Configuration
              </h2>
              <p className="text-gray-400 mb-4">
                Define policies to govern AI behavior. Policies are evaluated before each request.
              </p>
              <pre className="bg-black/50 rounded-lg p-4 overflow-x-auto text-sm">
                <code className="text-gray-300">{`{
  "name": "content-safety",
  "rules": [
    {
      "if": "output.contains_pii",
      "action": "block",
      "message": "Response contains PII"
    }
  ]
}`}</code>
              </pre>
            </div>

            <div className="text-center pt-8">
              <p className="text-gray-500 mb-4">Full documentation coming soon.</p>
              <a href="mailto:docs@agenticverz.com" className="text-primary-400 hover:text-primary-300 transition-colors">
                Request specific documentation →
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Insights Page (Placeholder)
function InsightsPage() {
  const articles = [
    {
      category: "Architecture",
      title: "Why Proxy-Based AI Observability Beats SDK Instrumentation",
      description: "The tradeoffs between embedded SDKs and proxy-based approaches for production AI systems. Spoiler: proxies win for governance.",
      readTime: "5 min",
      slug: "proxy-vs-sdk",
      isNew: true
    },
    {
      category: "Governance",
      title: "AI Audit Trails That Actually Work in Court",
      description: "What legal and compliance teams need from AI decision logs, and why most observability tools fall short.",
      readTime: "7 min",
      slug: "audit-trails-legal"
    },
    {
      category: "Operations",
      title: "The Three Types of AI Incidents (And How to Handle Each)",
      description: "Not all AI failures are equal. Classification framework for triage, investigation, and remediation.",
      readTime: "6 min",
      slug: "ai-incident-types"
    }
  ];

  return (
    <div className="min-h-screen gradient-bg">
      <nav className="fixed top-0 left-0 right-0 z-50 glass">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <a href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-purple-500 flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-semibold">Agenticverz</span>
            </a>
            <a href="/" className="text-gray-400 hover:text-white transition-colors">← Back to Home</a>
          </div>
        </div>
      </nav>

      <div className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl font-bold mb-4">Insights</h1>
          <p className="text-xl text-gray-400 mb-12">
            Thinking on AI reliability, governance, and operational patterns.
          </p>

          <div className="space-y-6">
            {articles.map((article, i) => (
              <a
                key={i}
                href={`/insights/${article.slug}`}
                className="glass rounded-xl p-6 hover:bg-white/5 transition-all group block"
              >
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-xs uppercase tracking-wider text-primary-400 font-medium">{article.category}</span>
                  {article.isNew && (
                    <span className="text-[10px] uppercase tracking-wider bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full font-medium">New</span>
                  )}
                </div>
                <h2 className="text-xl font-semibold mb-2 group-hover:text-primary-400 transition-colors">{article.title}</h2>
                <p className="text-gray-400 mb-4">{article.description}</p>
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span>{article.readTime} read</span>
                  <span className="text-primary-400 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    Read article <ArrowRight className="w-4 h-4" />
                  </span>
                </div>
              </a>
            ))}
          </div>

          <div className="text-center pt-12">
            <p className="text-gray-500 mb-4">More articles coming soon.</p>
            <a href="mailto:hello@agenticverz.com" className="text-primary-400 hover:text-primary-300 transition-colors">
              Subscribe to updates →
            </a>
          </div>
        </div>
      </div>
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
        <Route path="/documentation" element={<DocsPage />} />
        <Route path="/insights" element={<InsightsPage />} />
        <Route path="/insights/:slug" element={<InsightsPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
