#!/usr/bin/env node
/**
 * Projection Route Validator - CI Guard for Route Prefixes
 *
 * Layer: L8 — Catalyst / Meta
 * Role: Ensure projection routes are relative (no console prefixes)
 * Reference: PIN-387, Projection Route Separation
 *
 * INVARIANT:
 * Projection routes MUST be relative (e.g., "/overview", "/activity").
 * Console prefixes (/precus, /cus, /prefops, /fops) are applied at RUNTIME only.
 * This prevents environment leakage into design-time artifacts.
 *
 * Run: node scripts/projection-route-check.cjs
 */

const fs = require('fs');
const path = require('path');

// ============== CONFIGURATION ==============

// FORBIDDEN prefixes - these belong in runtime only, never in projection
const FORBIDDEN_PREFIXES = [
  '/precus/',   // Customer preflight
  '/precus',    // Customer preflight (exact)
  '/cus/',      // Customer production
  '/cus',       // Customer production (exact)
  '/prefops/',  // Founder preflight
  '/prefops',   // Founder preflight (exact)
  '/fops/',     // Founder production
  '/fops',      // Founder production (exact)
];

const PROJECTION_FILE = path.join(__dirname, '..', 'public', 'projection', 'ui_projection_lock.json');
const DESIGN_FILE = path.join(__dirname, '..', '..', '..', 'design', 'l2_1', 'ui_contract', 'ui_projection_lock.json');

// ============== HELPERS ==============

function hasForbiddenPrefix(route) {
  if (typeof route !== 'string') return false;
  return FORBIDDEN_PREFIXES.some(prefix =>
    route === prefix || route.startsWith(prefix + '/') || route.startsWith(prefix)
  );
}

function extractViolatingPrefix(route) {
  for (const prefix of FORBIDDEN_PREFIXES) {
    if (route === prefix || route.startsWith(prefix)) {
      return prefix;
    }
  }
  return null;
}

function validateProjection(projection, filePath) {
  const violations = [];
  const fileLabel = path.basename(filePath);

  // Check domain routes
  if (projection.domains && Array.isArray(projection.domains)) {
    for (const domain of projection.domains) {
      // Check domain route
      if (domain.route && hasForbiddenPrefix(domain.route)) {
        violations.push({
          type: 'domain',
          name: domain.domain,
          route: domain.route,
          prefix: extractViolatingPrefix(domain.route),
          file: fileLabel,
        });
      }

      // Check panel routes
      if (domain.panels && Array.isArray(domain.panels)) {
        for (const panel of domain.panels) {
          if (panel.route && hasForbiddenPrefix(panel.route)) {
            violations.push({
              type: 'panel',
              name: panel.panel_id,
              domain: domain.domain,
              route: panel.route,
              prefix: extractViolatingPrefix(panel.route),
              file: fileLabel,
            });
          }
        }
      }
    }
  }

  return violations;
}

// ============== MAIN ==============

console.log('\n╔═══════════════════════════════════════════════════════════════╗');
console.log('║           PROJECTION ROUTE CHECK (CI Guard)                   ║');
console.log('╚═══════════════════════════════════════════════════════════════╝\n');

console.log('INVARIANT: Projection routes must be RELATIVE only.');
console.log('           Console prefixes are applied at runtime.\n');
console.log(`FORBIDDEN: ${FORBIDDEN_PREFIXES.slice(0, 4).join(', ')}`);
console.log(`           ${FORBIDDEN_PREFIXES.slice(4).join(', ')}\n`);

let allViolations = [];
let filesChecked = 0;

// 1. Check public projection file
if (fs.existsSync(PROJECTION_FILE)) {
  filesChecked++;
  console.log(`Checking: public/projection/ui_projection_lock.json`);

  try {
    const content = fs.readFileSync(PROJECTION_FILE, 'utf-8');
    const projection = JSON.parse(content);
    const violations = validateProjection(projection, PROJECTION_FILE);
    allViolations = allViolations.concat(violations);

    if (violations.length === 0) {
      console.log('  ✓ All routes are relative\n');
    } else {
      console.log(`  ✗ Found ${violations.length} violation(s)\n`);
    }
  } catch (err) {
    console.log(`  ✗ Parse error: ${err.message}\n`);
    process.exit(1);
  }
} else {
  console.log('⚠️  public/projection/ui_projection_lock.json not found\n');
}

// 2. Check design file (authoritative source)
if (fs.existsSync(DESIGN_FILE)) {
  filesChecked++;
  console.log(`Checking: design/l2_1/ui_contract/ui_projection_lock.json`);

  try {
    const content = fs.readFileSync(DESIGN_FILE, 'utf-8');
    const projection = JSON.parse(content);
    const violations = validateProjection(projection, DESIGN_FILE);
    allViolations = allViolations.concat(violations);

    if (violations.length === 0) {
      console.log('  ✓ All routes are relative\n');
    } else {
      console.log(`  ✗ Found ${violations.length} violation(s)\n`);
    }
  } catch (err) {
    console.log(`  ✗ Parse error: ${err.message}\n`);
    process.exit(1);
  }
} else {
  console.log('⚠️  design/l2_1/ui_contract/ui_projection_lock.json not found\n');
}

// 3. Report violations
if (allViolations.length > 0) {
  console.log('━━━ ROUTE VIOLATIONS (BLOCKING) ━━━\n');

  for (const v of allViolations) {
    if (v.type === 'domain') {
      console.log(`❌ Domain "${v.name}"`);
      console.log(`   Route:  ${v.route}`);
      console.log(`   Prefix: ${v.prefix} (FORBIDDEN)`);
      console.log(`   File:   ${v.file}`);
    } else {
      console.log(`❌ Panel "${v.name}" in domain "${v.domain}"`);
      console.log(`   Route:  ${v.route}`);
      console.log(`   Prefix: ${v.prefix} (FORBIDDEN)`);
      console.log(`   File:   ${v.file}`);
    }
    console.log('');
  }

  console.log('━━━ HOW TO FIX ━━━\n');
  console.log('Projection routes must be RELATIVE (no console prefix).\n');
  console.log('  ❌ WRONG: "/precus/overview", "/cus/activity"');
  console.log('  ✅ RIGHT: "/overview", "/activity"\n');
  console.log('Console prefixes are applied at runtime by ui_projection_loader.ts');
  console.log('using CONSOLE_ROOT from consoleRoots.ts.\n');
  console.log('Reference: PIN-387, assertValidRelativeRoute()');
}

// 4. Summary
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

console.log(`Files checked:     ${filesChecked}`);
console.log(`Violations found:  ${allViolations.length}`);
console.log('');

if (allViolations.length > 0) {
  console.log('❌ Projection route check FAILED\n');
  process.exit(1);
} else {
  console.log('✅ Projection route check PASSED\n');
  process.exit(0);
}
