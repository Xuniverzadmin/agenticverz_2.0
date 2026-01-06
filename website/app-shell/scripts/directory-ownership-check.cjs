#!/usr/bin/env node
/**
 * Directory Ownership Check (G-1)
 *
 * Enforces directory import boundaries:
 * - products/ai-console/** may only import: shared UI, customer API clients
 * - fops/** may import: shared UI, founder + shared API clients
 * - onboarding/** may NOT import from: app-shell products, fops
 *
 * Reference: PIN-319 (Frontend Realignment)
 */

const fs = require('fs');
const path = require('path');

const SRC_DIR = path.join(__dirname, '..', 'src');
const FOPS_DIR = path.join(__dirname, '..', '..', 'fops', 'src');
const ONBOARDING_DIR = path.join(__dirname, '..', '..', 'onboarding', 'src');

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
function checkImports(filePath, forbiddenPatterns, context) {
  const violations = [];
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');

  lines.forEach((line, index) => {
    for (const pattern of forbiddenPatterns) {
      if (pattern.regex.test(line)) {
        violations.push({
          file: filePath,
          line: index + 1,
          context,
          message: pattern.message,
          code: line.trim(),
        });
      }
    }
  });

  return violations;
}

function main() {
  console.log('');
  console.log('╔═══════════════════════════════════════════════════════════════╗');
  console.log('║            DIRECTORY OWNERSHIP CHECK (G-1)                    ║');
  console.log('╚═══════════════════════════════════════════════════════════════╝');
  console.log('');
  console.log('Checking directory import boundaries...');
  console.log('');

  const allViolations = [];

  // Rule 1: onboarding/** may NOT import from app-shell products or fops
  console.log('Checking: onboarding/** imports...');
  const onboardingFiles = getAllFiles(ONBOARDING_DIR, '.tsx');
  const onboardingForbidden = [
    { regex: /from\s+['"]@ai-console\//, message: 'Onboarding cannot import from @ai-console/' },
    { regex: /from\s+['"]@fops\//, message: 'Onboarding cannot import from @fops/' },
    { regex: /from\s+['"]\.\.\/\.\.\/app-shell\/src\/products\//, message: 'Onboarding cannot import from products/' },
  ];

  for (const file of onboardingFiles) {
    const violations = checkImports(file, onboardingForbidden, 'onboarding');
    allViolations.push(...violations);
  }
  console.log(`  Checked ${onboardingFiles.length} files`);

  // Rule 2: fops/** may NOT import from ai-console products
  console.log('Checking: fops/** imports...');
  const fopsFiles = getAllFiles(FOPS_DIR, '.tsx');
  const fopsForbidden = [
    { regex: /from\s+['"]@ai-console\//, message: 'Fops cannot import from @ai-console/' },
  ];

  for (const file of fopsFiles) {
    const violations = checkImports(file, fopsForbidden, 'fops');
    allViolations.push(...violations);
  }
  console.log(`  Checked ${fopsFiles.length} files`);

  // Rule 3: ai-console products may NOT import from fops or onboarding
  console.log('Checking: ai-console/** imports...');
  const aiConsoleDir = path.join(SRC_DIR, 'products', 'ai-console');
  const aiConsoleFiles = getAllFiles(aiConsoleDir, '.tsx');
  const aiConsoleForbidden = [
    { regex: /from\s+['"]@fops\//, message: 'AI-Console cannot import from @fops/' },
    { regex: /from\s+['"]@onboarding\//, message: 'AI-Console cannot import from @onboarding/' },
  ];

  for (const file of aiConsoleFiles) {
    const violations = checkImports(file, aiConsoleForbidden, 'ai-console');
    allViolations.push(...violations);
  }
  console.log(`  Checked ${aiConsoleFiles.length} files`);

  console.log('');

  if (allViolations.length === 0) {
    console.log('✅ No directory ownership violations found!');
    console.log('');
    console.log('All directories correctly isolated.');
    process.exit(0);
  }

  // Report violations
  console.log(`❌ Found ${allViolations.length} ownership violations:\n`);

  for (const v of allViolations) {
    const relPath = path.relative(process.cwd(), v.file);
    console.log(`  ${relPath}:${v.line} [${v.context}]`);
    console.log(`    → ${v.message}`);
    console.log(`    Code: ${v.code}`);
    console.log('');
  }

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('');
  console.log('💡 Fix: Remove cross-boundary imports or use shared components.');
  console.log('   Reference: PIN-319, APP_SHELL_SCOPE.md');
  console.log('');
  console.log('❌ BUILD BLOCKED: Directory ownership violated');
  process.exit(1);
}

main();
