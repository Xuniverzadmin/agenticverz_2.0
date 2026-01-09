#!/usr/bin/env node
/**
 * Simulation Render Check - Phase-2A Pipeline Validation
 *
 * Layer: L8 — Catalyst / Meta
 * Role: Ensure SimulatedControl is rendered in ALL panel rendering paths
 * Reference: PIN-368, Phase-2A.2 Simulation Specification
 *
 * Problem this solves:
 * - DomainPage.tsx renders panels via FullPanelSurface
 * - PanelView.tsx renders individual panels
 * - Both MUST render SimulatedControl for action controls
 * - If one path is missed, simulation controls won't appear
 *
 * Run: node scripts/simulation-render-check.cjs
 */

const fs = require('fs');
const path = require('path');

// ============== CONFIGURATION ==============

// Files that MUST render SimulatedControl for action controls
const REQUIRED_RENDER_PATHS = [
  {
    file: 'src/pages/domains/DomainPage.tsx',
    description: 'Domain overview page (FullPanelSurface)',
    mustImport: ['SimulatedControl', 'useSimulation'],
    mustRender: 'SimulatedControl',
  },
  {
    file: 'src/pages/panels/PanelView.tsx',
    description: 'Individual panel view',
    mustImport: ['SimulatedControl', 'useSimulation'],
    mustRender: 'SimulatedControl',
  },
];

// ============== MAIN ==============

console.log('\n╔═══════════════════════════════════════════════════════════════╗');
console.log('║           SIMULATION RENDER CHECK (Phase-2A.2)                ║');
console.log('╚═══════════════════════════════════════════════════════════════╝\n');

let hasError = false;
let hasWarning = false;

for (const check of REQUIRED_RENDER_PATHS) {
  const filePath = path.join(__dirname, '..', check.file);

  console.log(`Checking: ${check.file}`);
  console.log(`  → ${check.description}`);

  // Check file exists
  if (!fs.existsSync(filePath)) {
    console.log(`  ❌ FILE NOT FOUND\n`);
    hasError = true;
    continue;
  }

  const content = fs.readFileSync(filePath, 'utf-8');

  // Check required imports
  let importsMissing = [];
  for (const imp of check.mustImport) {
    // Check for import statement containing the required import
    const importPattern = new RegExp(`import\\s+.*\\b${imp}\\b.*from`);
    if (!importPattern.test(content)) {
      importsMissing.push(imp);
    }
  }

  if (importsMissing.length > 0) {
    console.log(`  ❌ MISSING IMPORTS: ${importsMissing.join(', ')}`);
    hasError = true;
  } else {
    console.log(`  ✓ Imports: ${check.mustImport.join(', ')}`);
  }

  // Check component is rendered (JSX usage)
  const renderPattern = new RegExp(`<${check.mustRender}[\\s/>]`);
  if (!renderPattern.test(content)) {
    console.log(`  ❌ NOT RENDERING: <${check.mustRender} />`);
    console.log(`    This file must render SimulatedControl for action controls`);
    hasError = true;
  } else {
    console.log(`  ✓ Renders: <${check.mustRender} />`);
  }

  // Check action control filtering (best practice)
  if (!content.includes('action') || !content.includes('category')) {
    console.log(`  ⚠️  WARNING: No action control filtering detected`);
    console.log(`    Consider filtering controls by category === 'action'`);
    hasWarning = true;
  } else {
    console.log(`  ✓ Action control filtering present`);
  }

  console.log('');
}

// ============== CROSS-FILE CONSISTENCY ==============

console.log('━━━ Cross-File Consistency ━━━\n');

// Check that SimulatedControl component exists
const simulatedControlPath = path.join(__dirname, '..', 'src/components/simulation/SimulatedControl.tsx');
if (!fs.existsSync(simulatedControlPath)) {
  console.log('❌ SimulatedControl.tsx NOT FOUND');
  console.log('   Path: src/components/simulation/SimulatedControl.tsx\n');
  hasError = true;
} else {
  console.log('✓ SimulatedControl.tsx exists');
}

// Check that SimulationContext exists
const simulationContextPath = path.join(__dirname, '..', 'src/contexts/SimulationContext.tsx');
if (!fs.existsSync(simulationContextPath)) {
  console.log('❌ SimulationContext.tsx NOT FOUND');
  console.log('   Path: src/contexts/SimulationContext.tsx\n');
  hasError = true;
} else {
  console.log('✓ SimulationContext.tsx exists');
}

// Check App.tsx wraps with SimulationProvider
const appPath = path.join(__dirname, '..', 'src/App.tsx');
if (fs.existsSync(appPath)) {
  const appContent = fs.readFileSync(appPath, 'utf-8');
  if (!appContent.includes('SimulationProvider')) {
    console.log('❌ App.tsx missing SimulationProvider');
    console.log('   SimulationProvider must wrap the app for simulation to work\n');
    hasError = true;
  } else {
    console.log('✓ App.tsx uses SimulationProvider');
  }
} else {
  console.log('⚠️  App.tsx not found');
  hasWarning = true;
}

// ============== RESULT ==============

console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

if (hasError) {
  console.log('❌ Simulation render check FAILED\n');
  console.log('   Action controls will NOT appear in some views.');
  console.log('   Fix the issues above before deploying.\n');
  process.exit(1);
} else if (hasWarning) {
  console.log('⚠️  Simulation render check PASSED with warnings\n');
  process.exit(0);
} else {
  console.log('✅ Simulation render check PASSED\n');
  process.exit(0);
}
