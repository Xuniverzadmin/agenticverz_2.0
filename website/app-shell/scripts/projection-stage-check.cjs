#!/usr/bin/env node
/**
 * Projection Stage Validator - Phase-2A Pipeline Check
 *
 * Layer: L8 — Catalyst / Meta
 * Role: Validate projection file stage matches loader expectations
 * Reference: PIN-368, Phase-2A.2 Simulation Specification
 *
 * Ensures ui_projection_lock.json stage is accepted by ui_projection_loader.ts
 * before build, preventing runtime failures in preflight/production.
 *
 * Run: node scripts/projection-stage-check.cjs
 */

const fs = require('fs');
const path = require('path');

// ============== CONFIGURATION ==============

// Valid stages that ui_projection_loader.ts accepts
// MUST stay in sync with: src/contracts/ui_projection_loader.ts validStages
const VALID_STAGES = [
  'LOCKED',              // Base frozen state
  'PHASE_2A1_APPLIED',   // Affordance surfacing complete
  'PHASE_2A2_SIMULATED', // Simulation mode active
];

const PROJECTION_FILE = path.join(__dirname, '..', 'public', 'projection', 'ui_projection_lock.json');
// V2 CONSTITUTION SOURCE - Decoupled from AURORA pipeline (2026-01-20)
// This is the authoritative source for V2 Constitution structure
// DO NOT change back to design/l2_1/ui_contract/ - that is AURORA-generated
const DESIGN_FILE = path.join(__dirname, '..', '..', '..', 'design', 'v2_constitution', 'ui_projection_lock.json');
const LOADER_FILE = path.join(__dirname, '..', 'src', 'contracts', 'ui_projection_loader.ts');

// ============== MAIN ==============

console.log('\n╔═══════════════════════════════════════════════════════════════╗');
console.log('║              PROJECTION STAGE CHECK (Phase-2A)                ║');
console.log('╚═══════════════════════════════════════════════════════════════╝\n');

let hasError = false;

// 1. Check projection file exists
if (!fs.existsSync(PROJECTION_FILE)) {
  console.log('❌ MISSING: ui_projection_lock.json not found');
  console.log(`   Path: ${PROJECTION_FILE}\n`);
  process.exit(1);
}

// 2. Parse projection file
let projection;
try {
  const content = fs.readFileSync(PROJECTION_FILE, 'utf-8');
  projection = JSON.parse(content);
} catch (err) {
  console.log('❌ PARSE ERROR: ui_projection_lock.json is invalid JSON');
  console.log(`   Error: ${err.message}\n`);
  process.exit(1);
}

// 3. Extract stage from _meta
const meta = projection._meta;
if (!meta) {
  console.log('❌ INVALID: ui_projection_lock.json missing _meta block');
  process.exit(1);
}

const stage = meta.processing_stage;
if (!stage) {
  console.log('❌ INVALID: _meta.processing_stage is missing');
  process.exit(1);
}

console.log(`Projection file: ui_projection_lock.json`);
console.log(`Current stage:   ${stage}`);
console.log(`Valid stages:    [${VALID_STAGES.join(', ')}]\n`);

// 4. Validate stage
if (!VALID_STAGES.includes(stage)) {
  console.log('━━━ STAGE MISMATCH (BLOCKING) ━━━\n');
  console.log(`❌ Stage '${stage}' is NOT in valid stages list`);
  console.log('');
  console.log('   This will cause a runtime error in preflight/production.');
  console.log('');
  console.log('   💡 To fix:');
  console.log('   1. Update src/contracts/ui_projection_loader.ts validStages array');
  console.log('   2. Update scripts/projection-stage-check.cjs VALID_STAGES array');
  console.log('   3. Both must include the new stage');
  console.log('');
  hasError = true;
}

// 5. Cross-check with loader file (belt and suspenders)
if (fs.existsSync(LOADER_FILE)) {
  const loaderContent = fs.readFileSync(LOADER_FILE, 'utf-8');

  // Extract validStages array from loader
  const stagesMatch = loaderContent.match(/const validStages\s*=\s*\[([\s\S]*?)\]/);
  if (stagesMatch) {
    const loaderStagesStr = stagesMatch[1];
    const loaderStages = loaderStagesStr
      .split(',')
      .map(s => s.trim().replace(/['"]/g, ''))
      .filter(s => s.length > 0);

    // Check if current stage is in loader
    if (!loaderStages.includes(stage)) {
      console.log('━━━ LOADER SYNC ERROR (BLOCKING) ━━━\n');
      console.log(`❌ Stage '${stage}' found in projection but NOT in loader validStages`);
      console.log(`   Loader accepts: [${loaderStages.join(', ')}]`);
      console.log('');
      console.log('   💡 Update ui_projection_loader.ts validStages to include this stage');
      console.log('');
      hasError = true;
    } else {
      console.log(`✓ Loader validation: Stage '${stage}' is in loader validStages`);
    }

    // Sync check: this script's VALID_STAGES should match loader
    const missingInScript = loaderStages.filter(s => !VALID_STAGES.includes(s));
    const missingInLoader = VALID_STAGES.filter(s => !loaderStages.includes(s));

    if (missingInScript.length > 0 || missingInLoader.length > 0) {
      console.log('\n⚠️  SYNC WARNING: VALID_STAGES arrays are out of sync');
      if (missingInScript.length > 0) {
        console.log(`   Missing in this script: ${missingInScript.join(', ')}`);
      }
      if (missingInLoader.length > 0) {
        console.log(`   Missing in loader: ${missingInLoader.join(', ')}`);
      }
      console.log('   Keep both in sync to prevent future issues.\n');
    }
  }
}

// 6. Check design file sync (authoritative source)
if (fs.existsSync(DESIGN_FILE)) {
  let designProjection;
  try {
    designProjection = JSON.parse(fs.readFileSync(DESIGN_FILE, 'utf-8'));
  } catch (err) {
    console.log('\n⚠️  Could not parse design file for sync check');
  }

  if (designProjection) {
    const designStage = designProjection._meta?.processing_stage;
    const publicContent = fs.readFileSync(PROJECTION_FILE, 'utf-8');
    const designContent = fs.readFileSync(DESIGN_FILE, 'utf-8');

    if (publicContent !== designContent) {
      console.log('\n━━━ DESIGN SYNC ERROR (BLOCKING) ━━━\n');
      console.log('❌ public/projection/ui_projection_lock.json is OUT OF SYNC with design file');
      console.log(`   Design stage:  ${designStage}`);
      console.log(`   Public stage:  ${stage}`);
      console.log('');
      console.log('   💡 To fix, run:');
      console.log('   npm run projection:sync');
      console.log('');
      hasError = true;
    } else {
      console.log('✓ Design sync: public/projection matches design/l2_1/ui_contract');
    }
  }
} else {
  console.log('⚠️  Design file not found, skipping sync check');
}

// 7. Final result
console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

if (hasError) {
  console.log('❌ Projection stage check FAILED\n');
  process.exit(1);
} else {
  console.log('✅ Projection stage check PASSED\n');
  process.exit(0);
}
