#!/usr/bin/env node
/**
 * Import Boundary Checker (R2-2)
 *
 * Enforces audience separation by checking that:
 * - Customer console code does NOT import @audience founder APIs
 * - Violations FAIL the build (HARD GUARD)
 *
 * Reference: docs/inventories/FRONTEND_API_AUDIENCE_MAP.md
 */

const fs = require('fs');
const path = require('path');

const API_DIR = path.join(__dirname, '..', 'src', 'api');
const PRODUCTS_DIR = path.join(__dirname, '..', 'src', 'products', 'ai-console');

// Build audience map from @audience annotations
function buildAudienceMap() {
  const map = {};

  function scanDir(dir, prefix = '') {
    if (!fs.existsSync(dir)) return;

    const files = fs.readdirSync(dir);
    for (const file of files) {
      const fullPath = path.join(dir, file);
      const stat = fs.statSync(fullPath);

      if (stat.isDirectory()) {
        scanDir(fullPath, prefix + file + '/');
      } else if (file.endsWith('.ts')) {
        const content = fs.readFileSync(fullPath, 'utf-8');
        const match = content.match(/@audience\s+(customer|founder|shared)/);
        if (match) {
          const apiName = (prefix + file).replace('.ts', '');
          map[apiName] = match[1];
        }
      }
    }
  }

  scanDir(API_DIR);
  return map;
}

// Get all TypeScript files recursively
function getAllFiles(dir, ext) {
  const results = [];
  if (!fs.existsSync(dir)) return results;

  const files = fs.readdirSync(dir);
  for (const file of files) {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory()) {
      results.push(...getAllFiles(fullPath, ext));
    } else if (file.endsWith(ext)) {
      results.push(fullPath);
    }
  }
  return results;
}

// Check imports in a file
function checkImports(filePath, audienceMap) {
  const violations = [];
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');

  lines.forEach((line, index) => {
    // Match import statements from @/api/*
    const importMatch = line.match(/from\s+['"]@\/api\/([^'"]+)['"]/);
    if (importMatch) {
      const apiPath = importMatch[1];
      const audience = audienceMap[apiPath];

      if (audience === 'founder') {
        violations.push({
          file: filePath,
          line: index + 1,
          api: apiPath,
          message: `Customer code imports founder-only API: @/api/${apiPath}`,
        });
      }
    }
  });

  return violations;
}

function main() {
  console.log('');
  console.log('╔═══════════════════════════════════════════════════════════════╗');
  console.log('║              IMPORT BOUNDARY CHECK (R2-2)                     ║');
  console.log('╚═══════════════════════════════════════════════════════════════╝');
  console.log('');
  console.log('Checking customer console does not import founder APIs...');
  console.log('');

  // Build audience map
  const audienceMap = buildAudienceMap();

  console.log('Audience Map:');
  const founderApis = Object.entries(audienceMap)
    .filter(([_, aud]) => aud === 'founder')
    .map(([api]) => api);
  console.log(`  Founder APIs: ${founderApis.length}`);
  console.log(`    ${founderApis.join(', ')}`);
  console.log('');

  // Get all files in customer console
  const customerFiles = getAllFiles(PRODUCTS_DIR, '.tsx');
  console.log(`Checking ${customerFiles.length} customer console files...`);
  console.log('');

  // Check each file
  const allViolations = [];
  for (const file of customerFiles) {
    const violations = checkImports(file, audienceMap);
    allViolations.push(...violations);
  }

  if (allViolations.length === 0) {
    console.log('✅ No boundary violations found!');
    console.log('');
    console.log('Customer console correctly isolated from founder APIs.');
    process.exit(0);
  }

  // Report violations
  console.log(`❌ Found ${allViolations.length} boundary violations:\n`);

  for (const v of allViolations) {
    const relPath = path.relative(process.cwd(), v.file);
    console.log(`  ${relPath}:${v.line}`);
    console.log(`    → ${v.message}`);
    console.log('');
  }

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('');
  console.log('💡 Fix: Move founder API usage to fops/ or use a shared API instead.');
  console.log('   Reference: docs/inventories/FRONTEND_API_AUDIENCE_MAP.md');
  console.log('');
  console.log('❌ BUILD BLOCKED: Customer/founder boundary violated');
  process.exit(1);
}

main();
