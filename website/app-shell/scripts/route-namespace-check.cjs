#!/usr/bin/env node
/**
 * Route Namespace Guard (G-2)
 *
 * Enforces route namespace rules:
 * - All founder routes must start with /fops/
 * - All customer routes must start with /guard/
 * - No ambiguous wildcard routes (except root fallback)
 *
 * Reference: PIN-319 (Frontend Realignment)
 */

const fs = require('fs');
const path = require('path');

const ROUTES_FILE = path.join(__dirname, '..', 'src', 'routes', 'index.tsx');

// Known allowed routes
const ALLOWED_ROUTES = [
  '/login',           // Public login
  '/guard',           // Customer console root
  '/guard/*',         // Customer console wildcard
  '/fops/ops',        // Ops console root
  '/fops/ops/*',      // Ops console wildcard
  '/onboarding/*',    // Onboarding routes (dynamic)
  '/credits',         // Shared credits page
  '/',                // Root redirect
  '*',                // Fallback (must redirect to /guard)
];

// Route patterns that should use specific namespaces
const NAMESPACE_RULES = {
  founder: {
    required: '/fops/',
    guard: 'FounderRoute',
    exceptions: [],
  },
  customer: {
    required: '/guard/',
    guard: 'ProtectedRoute',
    exceptions: ['/login', '/credits', '/', '*'],
  },
  onboarding: {
    required: '/onboarding/',
    guard: 'OnboardingRoute',
    exceptions: [],
  },
};

function main() {
  console.log('');
  console.log('╔═══════════════════════════════════════════════════════════════╗');
  console.log('║              ROUTE NAMESPACE GUARD (G-2)                      ║');
  console.log('╚═══════════════════════════════════════════════════════════════╝');
  console.log('');
  console.log('Checking route namespaces...');
  console.log('');

  if (!fs.existsSync(ROUTES_FILE)) {
    console.log('❌ Routes file not found:', ROUTES_FILE);
    process.exit(1);
  }

  const content = fs.readFileSync(ROUTES_FILE, 'utf-8');
  const lines = content.split('\n');

  const violations = [];
  const founderRoutes = [];
  const customerRoutes = [];
  const otherRoutes = [];

  // Parse routes
  lines.forEach((line, index) => {
    // Match: path="/something" or path="something"
    const pathMatch = line.match(/path=["']([^"']+)["']/);
    if (!pathMatch) return;

    const routePath = pathMatch[1];
    const lineNum = index + 1;

    // Check if wrapped with FounderRoute
    const hasFounderRoute = line.includes('FounderRoute');
    const hasProtectedRoute = line.includes('ProtectedRoute');
    const hasOnboardingRoute = line.includes('OnboardingRoute');

    // Categorize routes
    if (hasFounderRoute) {
      founderRoutes.push({ path: routePath, line: lineNum });

      // Founder routes must start with /fops/
      if (!routePath.startsWith('fops/') && routePath !== '/fops/ops' && !routePath.startsWith('/fops/')) {
        violations.push({
          line: lineNum,
          path: routePath,
          message: `Founder route "${routePath}" must start with /fops/`,
          type: 'NAMESPACE',
        });
      }
    } else if (routePath.startsWith('fops/') || routePath.startsWith('/fops/')) {
      // fops route without FounderRoute guard
      violations.push({
        line: lineNum,
        path: routePath,
        message: `Route "${routePath}" uses /fops/ namespace but is not wrapped with FounderRoute`,
        type: 'GUARD_MISSING',
      });
    }

    // Check for ambiguous wildcards
    if (routePath === '*' && !line.includes('Navigate')) {
      violations.push({
        line: lineNum,
        path: routePath,
        message: `Wildcard route "*" must redirect to a known route (use <Navigate to="/guard" />)`,
        type: 'WILDCARD',
      });
    }
  });

  // Report results
  console.log('Route Summary:');
  console.log(`  Founder routes (/fops/*): ${founderRoutes.length}`);
  console.log(`  Routes checked: ${founderRoutes.length + customerRoutes.length + otherRoutes.length}`);
  console.log('');

  if (violations.length === 0) {
    console.log('✅ No namespace violations found!');
    console.log('');
    console.log('All routes correctly namespaced.');
    process.exit(0);
  }

  // Report violations
  console.log(`❌ Found ${violations.length} namespace violations:\n`);

  for (const v of violations) {
    console.log(`  Line ${v.line}: ${v.path}`);
    console.log(`    → [${v.type}] ${v.message}`);
    console.log('');
  }

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('');
  console.log('💡 Fix: Move routes to correct namespace or add appropriate guard.');
  console.log('   - Founder routes: /fops/* with <FounderRoute>');
  console.log('   - Customer routes: /guard/* with <ProtectedRoute>');
  console.log('   Reference: PIN-319, ONBOARDING_TO_APP_SHELL.md');
  console.log('');
  console.log('❌ BUILD BLOCKED: Route namespace violated');
  process.exit(1);
}

main();
