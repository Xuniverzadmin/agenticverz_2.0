#!/usr/bin/env node
/**
 * UI Hygiene Checker v2.1 - Enforced Quality Gates
 *
 * Checks for:
 * 1. STALE_BUTTON - Empty or TODO onClick handlers (ERROR)
 * 2. TODO_BUTTON - Handlers with TODO comments (ERROR)
 * 3. MUTATION_NO_ERROR - Missing onError handler (WARNING)
 * 4. MUTATION_NO_SUCCESS - Missing onSuccess handler (WARNING)
 * 5. MUTATION_NO_LOADING - Mutation without loading state (WARNING)
 * 6. PAGE_NO_LOGGER - Page missing componentMount (WARNING)
 * 7. ORPHANED_PAGE - Page not imported anywhere (WARNING/ERROR in CI)
 * 8. NAV_PAGE_MISMATCH - Guard nav items without renderPage case (ERROR)
 *
 * Budget Caps:
 * - Max 30 warnings allowed
 * - Warnings must not increase from baseline
 *
 * Run: npm run hygiene
 * CI:  npm run hygiene:ci
 */

const fs = require('fs');
const path = require('path');

const issues = [];
const SRC_DIR = path.join(__dirname, '..', 'src');
const BASELINE_FILE = path.join(__dirname, '..', '.hygiene-baseline.json');

// ============== CONFIGURATION ==============

const CONFIG = {
  MAX_WARNINGS: 35,           // Hard cap on warnings (v2.0: raised for MUTATION_NO_LOADING rule)
  ORPHAN_ERROR_IN_CI: true,   // ORPHANED_PAGE becomes error in CI
  REQUIRE_LOADING_STATE: true, // Check for mutation loading states
};

// Suggested fixes for each category
const FIX_HINTS = {
  STALE_BUTTON: `
  Fix: Replace empty handler with actual logic:
    onClick={() => {
      logger.userEvent('click', 'button_name');
      // Add actual logic here
    }}`,
  TODO_BUTTON: `
  Fix: Implement the handler or remove the button:
    onClick={() => {
      logger.userEvent('click', 'action_name');
      doSomething();
    }}`,
  MUTATION_NO_ERROR: `
  Fix: Add onError handler for user feedback:
    useMutation({
      mutationFn: ...,
      onError: (error) => {
        logger.error('MUTATION', 'Failed', error);
        toast.error('Operation failed');
      }
    })`,
  MUTATION_NO_SUCCESS: `
  Fix: Add onSuccess handler for user feedback:
    useMutation({
      mutationFn: ...,
      onSuccess: () => {
        logger.info('MUTATION', 'Success');
        queryClient.invalidateQueries(['key']);
      }
    })`,
  MUTATION_NO_LOADING: `
  Fix: Use mutation.isPending for loading state:
    <Button
      disabled={mutation.isPending}
      onClick={() => mutation.mutate()}
    >
      {mutation.isPending ? 'Loading...' : 'Submit'}
    </Button>`,
  PAGE_NO_LOGGER: `
  Fix: Add componentMount in useEffect:
    useEffect(() => {
      logger.componentMount('PageName');
      return () => logger.componentUnmount('PageName');
    }, []);`,
  ORPHANED_PAGE: `
  Fix: Either:
    1. Add route in src/routes/index.tsx
    2. Import in another component
    3. Delete if truly unused`,
  NAV_PAGE_MISMATCH: `
  Fix: GuardConsoleEntry.tsx is the PRODUCTION entry point!
    1. Add import for missing page (e.g., import { AccountPage } from './AccountPage')
    2. Add case in renderPage() switch (e.g., case 'account': return <AccountPage />)
    3. Ensure NAV_ITEMS in GuardLayout.tsx matches cases in GuardConsoleEntry.tsx`,
};

// ============== PATTERNS ==============

// Buttons that just have TODO or empty handlers
const STALE_ONCLICK_PATTERNS = [
  /onClick=\{\s*\(\)\s*=>\s*\{\s*\/\*\s*TODO[^}]*\}\s*\}/g,
  /onClick=\{\s*\(\)\s*=>\s*\{\s*\}\s*\}/g,
  /onClick=\{\s*\(\)\s*=>\s*\{\s*\/\/[^}]*\}\s*\}/g,
  /onClick=\{\(\)\s*=>\s*undefined\}/g,
  /onClick=\{\(\)\s*=>\s*null\}/g,
];

// Mutations without proper handlers
const MUTATION_PATTERN = /useMutation\s*\(\s*\{/g;
const ON_SUCCESS_PATTERN = /onSuccess\s*:/;
const ON_ERROR_PATTERN = /onError\s*:/;

// Mutation loading state patterns
const MUTATION_VAR_PATTERN = /(?:const|let)\s+(\w+)\s*=\s*useMutation/g;
const IS_PENDING_PATTERN = /\.isPending|\.isLoading|isLoading\s*:/;

// Page component pattern
const PAGE_COMPONENT_PATTERN = /export\s+(function|const)\s+(\w+Page|\w+Console|\w+Dashboard)/;

// Logger pattern
const LOGGER_MOUNT_PATTERN = /logger\.componentMount/;

// ============== HELPERS ==============

function getAllFiles(dir, ext) {
  const files = [];

  function walk(currentDir) {
    if (!fs.existsSync(currentDir)) return;
    const entries = fs.readdirSync(currentDir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(currentDir, entry.name);
      if (entry.isDirectory() && !entry.name.startsWith('.') && entry.name !== 'node_modules') {
        walk(fullPath);
      } else if (entry.isFile() && entry.name.endsWith(ext)) {
        files.push(fullPath);
      }
    }
  }

  walk(dir);
  return files;
}

function getLineNumber(content, index) {
  return content.substring(0, index).split('\n').length;
}

function extractContext(content, index, length = 100) {
  const start = Math.max(0, index - 20);
  const end = Math.min(content.length, index + length);
  return content.substring(start, end).replace(/\n/g, ' ').trim();
}

function loadBaseline() {
  if (fs.existsSync(BASELINE_FILE)) {
    try {
      return JSON.parse(fs.readFileSync(BASELINE_FILE, 'utf-8'));
    } catch (e) {
      return null;
    }
  }
  return null;
}

function saveBaseline(data) {
  fs.writeFileSync(BASELINE_FILE, JSON.stringify(data, null, 2));
}

// ============== CHECKS ==============

function checkStaleOnClick(filePath, content) {
  for (const pattern of STALE_ONCLICK_PATTERNS) {
    let match;
    const regex = new RegExp(pattern.source, 'g');
    while ((match = regex.exec(content)) !== null) {
      issues.push({
        file: filePath,
        line: getLineNumber(content, match.index),
        type: 'error',
        category: 'STALE_BUTTON',
        message: 'Button has empty or TODO onClick handler',
        code: extractContext(content, match.index, 60),
      });
    }
  }
}

function checkMutationHandlers(filePath, content) {
  let match;
  const regex = new RegExp(MUTATION_PATTERN.source, 'g');

  while ((match = regex.exec(content)) !== null) {
    // Find the closing brace of the mutation config
    let braceCount = 1;
    let endIndex = match.index + match[0].length;

    while (braceCount > 0 && endIndex < content.length) {
      if (content[endIndex] === '{') braceCount++;
      if (content[endIndex] === '}') braceCount--;
      endIndex++;
    }

    const mutationBlock = content.substring(match.index, endIndex);
    const hasOnSuccess = ON_SUCCESS_PATTERN.test(mutationBlock);
    const hasOnError = ON_ERROR_PATTERN.test(mutationBlock);

    if (!hasOnSuccess) {
      issues.push({
        file: filePath,
        line: getLineNumber(content, match.index),
        type: 'warning',
        category: 'MUTATION_NO_SUCCESS',
        message: 'useMutation missing onSuccess handler - no user feedback on success',
        code: extractContext(content, match.index, 50),
      });
    }

    if (!hasOnError) {
      issues.push({
        file: filePath,
        line: getLineNumber(content, match.index),
        type: 'warning',
        category: 'MUTATION_NO_ERROR',
        message: 'useMutation missing onError handler - errors will be silent',
        code: extractContext(content, match.index, 50),
      });
    }
  }
}

function checkMutationLoadingState(filePath, content) {
  if (!CONFIG.REQUIRE_LOADING_STATE) return;

  // Find all mutation variable names
  const mutationVars = [];
  let varMatch;
  const varRegex = new RegExp(MUTATION_VAR_PATTERN.source, 'g');

  while ((varMatch = varRegex.exec(content)) !== null) {
    mutationVars.push({
      name: varMatch[1],
      line: getLineNumber(content, varMatch.index),
      index: varMatch.index
    });
  }

  for (const mutation of mutationVars) {
    // Check if isPending is used for this mutation
    const isPendingUsed = new RegExp(`${mutation.name}\\.isPending|${mutation.name}\\.isLoading`).test(content);

    // Also check for disabled={mutation.isPending} pattern
    const disabledPattern = new RegExp(`disabled=\\{[^}]*${mutation.name}\\.isPending`).test(content);

    if (!isPendingUsed && !disabledPattern) {
      issues.push({
        file: filePath,
        line: mutation.line,
        type: 'warning',
        category: 'MUTATION_NO_LOADING',
        message: `Mutation "${mutation.name}" has no loading state - users can double-trigger`,
        code: extractContext(content, mutation.index, 60),
      });
    }
  }
}

function checkPageLogger(filePath, content) {
  // Only check page components
  if (!PAGE_COMPONENT_PATTERN.test(content)) return;

  // Skip if it's a small component file
  if (content.length < 500) return;

  if (!LOGGER_MOUNT_PATTERN.test(content)) {
    const match = content.match(PAGE_COMPONENT_PATTERN);
    issues.push({
      file: filePath,
      line: 1,
      type: 'warning',
      category: 'PAGE_NO_LOGGER',
      message: `Page component "${match?.[2] || 'unknown'}" missing logger.componentMount()`,
    });
  }
}

function checkButtonFeedback(filePath, content) {
  // Look for ActionButton or button with onClick that leads to TODO
  const todoButtonPattern = /onClick=\{\s*\(\)\s*=>\s*\{[^}]*TODO[^}]*\}\}/g;
  let match;

  while ((match = todoButtonPattern.exec(content)) !== null) {
    issues.push({
      file: filePath,
      line: getLineNumber(content, match.index),
      type: 'error',
      category: 'TODO_BUTTON',
      message: 'Button handler contains TODO - not implemented',
      code: extractContext(content, match.index, 80),
    });
  }
}

function checkGuardNavMismatch() {
  // Check that GuardLayout NAV_ITEMS match GuardConsoleEntry renderPage cases
  const layoutPath = path.join(SRC_DIR, 'pages', 'guard', 'GuardLayout.tsx');
  const entryPath = path.join(SRC_DIR, 'pages', 'guard', 'GuardConsoleEntry.tsx');

  if (!fs.existsSync(layoutPath) || !fs.existsSync(entryPath)) return;

  const layoutContent = fs.readFileSync(layoutPath, 'utf-8');
  const entryContent = fs.readFileSync(entryPath, 'utf-8');

  // Extract nav item IDs from layout (e.g., id: 'account')
  const navItemPattern = /id:\s*['"]([^'"]+)['"]/g;
  const navItems = new Set();
  let match;
  while ((match = navItemPattern.exec(layoutContent)) !== null) {
    navItems.add(match[1]);
  }

  // Extract case IDs from entry (e.g., case 'account':)
  const casePattern = /case\s*['"]([^'"]+)['"]:/g;
  const caseItems = new Set();
  while ((match = casePattern.exec(entryContent)) !== null) {
    caseItems.add(match[1]);
  }

  // Check for mismatches - nav items without corresponding cases
  for (const navItem of navItems) {
    if (!caseItems.has(navItem) && navItem !== 'overview') { // overview is default
      issues.push({
        file: 'src/pages/guard/GuardConsoleEntry.tsx',
        line: 1,
        type: 'error',
        category: 'NAV_PAGE_MISMATCH',
        message: `Navigation item "${navItem}" has no renderPage() case in GuardConsoleEntry.tsx - page will not render!`,
      });
    }
  }
}

function checkOrphanedPages(isCI) {
  // Read routes file
  const routesPath = path.join(SRC_DIR, 'routes', 'index.tsx');
  if (!fs.existsSync(routesPath)) return;

  const routesContent = fs.readFileSync(routesPath, 'utf-8');

  // Get all page files
  const pageFiles = getAllFiles(path.join(SRC_DIR, 'pages'), '.tsx');

  for (const pageFile of pageFiles) {
    const fileName = path.basename(pageFile, '.tsx');

    // Skip component files (not pages)
    if (!fileName.includes('Page') && !fileName.includes('Console') && !fileName.includes('Dashboard')) {
      continue;
    }

    // Skip entry files and layouts
    if (fileName.includes('Entry') || fileName.includes('Layout') || fileName.includes('App')) {
      continue;
    }

    // Check if this page is imported in routes
    const importPattern = new RegExp(`from\\s+['"][^'"]*${fileName}['"]`);
    const componentPattern = new RegExp(`<${fileName}`);

    if (!importPattern.test(routesContent) && !componentPattern.test(routesContent)) {
      // Check if it's imported elsewhere
      let isUsed = false;
      const allFiles = getAllFiles(SRC_DIR, '.tsx');

      for (const file of allFiles) {
        if (file === pageFile) continue;
        const content = fs.readFileSync(file, 'utf-8');
        if (importPattern.test(content)) {
          isUsed = true;
          break;
        }
      }

      if (!isUsed) {
        // In CI, orphaned pages are errors
        const issueType = (isCI && CONFIG.ORPHAN_ERROR_IN_CI) ? 'error' : 'warning';

        issues.push({
          file: pageFile,
          line: 1,
          type: issueType,
          category: 'ORPHANED_PAGE',
          message: `Page "${fileName}" is not imported anywhere - ${isCI ? 'dead code' : 'may be stale'}`,
        });
      }
    }
  }
}

// ============== MAIN ==============

function main() {
  const isCI = process.argv.includes('--ci');
  const isStrict = process.argv.includes('--strict');
  const updateBaseline = process.argv.includes('--update-baseline');

  console.log('');
  console.log('╔═══════════════════════════════════════════════════════════════╗');
  console.log('║                    UI HYGIENE CHECK v2.0                      ║');
  console.log('╚═══════════════════════════════════════════════════════════════╝');
  console.log('');
  console.log('Scanning for stale buttons, missing feedback, orphaned pages...');
  console.log('');

  const tsxFiles = getAllFiles(SRC_DIR, '.tsx');

  console.log(`Checking ${tsxFiles.length} files...\n`);

  for (const file of tsxFiles) {
    const content = fs.readFileSync(file, 'utf-8');
    const relativePath = path.relative(process.cwd(), file);

    checkStaleOnClick(relativePath, content);
    checkMutationHandlers(relativePath, content);
    checkMutationLoadingState(relativePath, content);
    checkPageLogger(relativePath, content);
    checkButtonFeedback(relativePath, content);
  }

  checkOrphanedPages(isCI);
  checkGuardNavMismatch();

  // Group issues by category
  const byCategory = {};
  for (const issue of issues) {
    if (!byCategory[issue.category]) {
      byCategory[issue.category] = [];
    }
    byCategory[issue.category].push(issue);
  }

  // Print results
  const errors = issues.filter(i => i.type === 'error');
  const warnings = issues.filter(i => i.type === 'warning');

  if (issues.length === 0) {
    console.log('✅ No hygiene issues found!\n');
    process.exit(0);
  }

  console.log(`Found ${errors.length} errors, ${warnings.length} warnings\n`);

  for (const [category, categoryIssues] of Object.entries(byCategory)) {
    console.log(`\n━━━ ${category} (${categoryIssues.length}) ━━━`);

    for (const issue of categoryIssues) {
      const icon = issue.type === 'error' ? '❌' : '⚠️';
      console.log(`\n${icon} ${issue.file}:${issue.line}`);
      console.log(`   ${issue.message}`);
      if (issue.code) {
        console.log(`   → ${issue.code.substring(0, 80)}...`);
      }
    }

    // Print fix hint for this category
    if (FIX_HINTS[category]) {
      console.log('\n   💡 Suggested fix:');
      const hint = FIX_HINTS[category].split('\n').map(l => '   ' + l).join('\n');
      console.log(hint);
    }
  }

  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  // Check warning budget
  const baseline = loadBaseline();

  if (updateBaseline) {
    saveBaseline({
      timestamp: new Date().toISOString(),
      warnings: warnings.length,
      errors: errors.length,
      byCategory: Object.fromEntries(
        Object.entries(byCategory).map(([k, v]) => [k, v.length])
      )
    });
    console.log(`📊 Baseline updated: ${warnings.length} warnings, ${errors.length} errors\n`);
  }

  // Budget checks
  let budgetViolation = false;

  if (warnings.length > CONFIG.MAX_WARNINGS) {
    console.log(`❌ WARNING BUDGET EXCEEDED: ${warnings.length} > ${CONFIG.MAX_WARNINGS} max allowed\n`);
    budgetViolation = true;
  }

  if (baseline && warnings.length > baseline.warnings) {
    console.log(`❌ WARNING REGRESSION: ${warnings.length} warnings (was ${baseline.warnings})`);
    console.log(`   Run with --update-baseline after fixing to reset\n`);
    budgetViolation = true;
  }

  // Output JSON for CI
  if (isCI) {
    const report = {
      timestamp: new Date().toISOString(),
      errors: errors.length,
      warnings: warnings.length,
      budgetExceeded: warnings.length > CONFIG.MAX_WARNINGS,
      regressionDetected: baseline ? warnings.length > baseline.warnings : false,
      issues: issues,
    };
    fs.writeFileSync('hygiene-report.json', JSON.stringify(report, null, 2));
    console.log('📄 Report written to hygiene-report.json\n');
  }

  // Exit conditions
  if (errors.length > 0) {
    console.log('❌ BUILD BLOCKED: Fix errors before continuing\n');
    process.exit(1);
  }

  if (isCI && budgetViolation) {
    console.log('❌ CI BLOCKED: Warning budget exceeded or regression detected\n');
    process.exit(1);
  }

  if (isStrict && budgetViolation) {
    console.log('❌ STRICT MODE: Warning budget violated\n');
    process.exit(1);
  }

  console.log('✓ No blocking errors');
  if (warnings.length > 0) {
    console.log(`  ${warnings.length} warnings remaining (budget: ${CONFIG.MAX_WARNINGS})`);
    if (baseline) {
      const delta = warnings.length - baseline.warnings;
      if (delta === 0) {
        console.log('  Baseline: unchanged');
      } else if (delta < 0) {
        console.log(`  Baseline: improved by ${Math.abs(delta)} 🎉`);
      }
    }
  }
  console.log('');
}

main();
