# AgenticVerz — Claude Behavior Library

**Version:** 1.5.0
**Effective:** 2025-12-29
**Status:** ACTIVE (Auto-Enforced)

**Changelog:**
- 1.5.0 (2025-12-29): Added BL-BOUNDARY-001/002/003 for product boundary enforcement (PIN-239)
- 1.4.0 (2025-12-29): Added BL-CODE-REG-001/002/003 for codebase registry enforcement (PIN-237)
- 1.3.0 (2025-12-29): Added BL-FRONTEND-001/002 for frontend architecture enforcement (PIN-235)
- 1.2.0 (2025-12-29): Added BL-CONSOLE-003 for Project Scope enforcement
- 1.1.0 (2025-12-29): Added BL-CONSOLE-001/002 for Customer Console governance
- 1.0.0 (2025-12-27): Initial version

---

## Purpose

This is a **machine-readable** set of behavior rules that Claude must follow.
These rules are **not prose** — they are structured constraints derived from real incidents.

Each rule answers:
> "What behavior would have prevented this class of bug from existing?"

---

## Rule Format

```yaml
- id: BL-XXX-NNN
  name: Rule Name
  class: Incident class this prevents
  triggers:
    - When to apply this rule
  requires:
    - Mandatory steps before proceeding
  forbid:
    - Actions that are never allowed
  violation: What happens if rule is broken
```

---

## Active Rules

### BL-ENV-001: Runtime Sync Before Test

**Class:** Environment-Behavior Drift after Code Change

**Problem:** Claude fixes code assuming runtime has updated, but the execution environment is still running old state.

```yaml
id: BL-ENV-001
name: Runtime Sync Before Test
class: environment_drift
severity: BLOCKING

triggers:
  - Any change to API endpoints
  - Any change to auth/RBAC logic
  - Any change to worker/execution lifecycle
  - Any change to retry behavior
  - Any migration applied

requires:
  step_1:
    action: "Enumerate docker compose services"
    command: "docker compose config --services"
    reason: "Know which services exist"
  step_2:
    action: "Identify target service name"
    command: "docker ps --format '{{.Names}}'"
    reason: "Map container names to services"
  step_3:
    action: "Rebuild target service explicitly"
    command: "docker compose up -d --build <service>"
    reason: "Ensure code changes are deployed"
  step_4:
    action: "Wait for health check"
    command: "curl -s http://localhost:PORT/health"
    condition: "status == healthy"
    reason: "Service must be ready before testing"
  step_5:
    action: "Verify auth contract for endpoint"
    check: "Which headers does this endpoint expect?"
    reason: "Auth mismatch causes false failures"

forbid:
  - Testing before container rebuild
  - Assuming rebuild happened
  - Ignoring health check failures
  - Testing with wrong auth headers

violation:
  type: BLOCKING
  message: "BL-ENV-001 VIOLATION: Runtime not synced before test"
  action: "STOP. Complete runtime sync before proceeding."

output_required: |
  RUNTIME SYNC CHECK
  - Services enumerated: YES / NO
  - Target service: <name>
  - Rebuild command: <command executed>
  - Health status: <healthy / unhealthy>
  - Auth headers verified: <list>
```

---

### BL-DB-001: Timestamp Semantics Alignment

**Class:** Timezone mismatch between Python and PostgreSQL

**Problem:** Python `datetime.now(timezone.utc)` produces timezone-aware datetime, but PostgreSQL `TIMESTAMP WITHOUT TIME ZONE` requires naive datetime.

```yaml
id: BL-DB-001
name: Timestamp Semantics Alignment
class: timezone_mismatch
severity: BLOCKING

triggers:
  - Any datetime helper function created
  - Any model with timestamp fields
  - Any field with `default_factory` returning datetime
  - Any migration adding timestamp columns

requires:
  step_1:
    action: "Check PostgreSQL column type"
    query: |
      SELECT column_name, data_type
      FROM information_schema.columns
      WHERE table_name = '<table>' AND column_name LIKE '%_at';
    check: "WITH TIME ZONE or WITHOUT TIME ZONE?"
  step_2:
    action: "Match Python datetime to column type"
    rule: |
      TIMESTAMP WITHOUT TIME ZONE → datetime.utcnow() (naive)
      TIMESTAMP WITH TIME ZONE → datetime.now(timezone.utc) (aware)
  step_3:
    action: "Add explicit comment explaining choice"
    example: |
      def utc_now() -> datetime:
          """Return naive UTC datetime for TIMESTAMP WITHOUT TIME ZONE columns."""
          return datetime.utcnow()

forbid:
  - Using timezone-aware datetime with WITHOUT TIME ZONE columns
  - Using naive datetime with WITH TIME ZONE columns
  - Mixing datetime semantics in same table
  - Implicit timezone assumptions

violation:
  type: BLOCKING
  message: "BL-DB-001 VIOLATION: Timestamp semantics mismatch"
  error: "asyncpg.exceptions.DataError: can't subtract offset-naive and offset-aware datetimes"
  action: "STOP. Align datetime helper with column type."

output_required: |
  TIMESTAMP SEMANTICS CHECK
  - Table: <name>
  - Column type: WITH TIME ZONE / WITHOUT TIME ZONE
  - Python helper: datetime.utcnow() / datetime.now(timezone.utc)
  - Alignment verified: YES / NO
```

---

### BL-AUTH-001: Auth Contract Enumeration

**Class:** Auth path mismatch causing false 401/403 errors

**Problem:** Endpoint tested with wrong auth headers because auth contract not enumerated first.

```yaml
id: BL-AUTH-001
name: Auth Contract Enumeration Before Endpoint Test
class: auth_mismatch
severity: BLOCKING

triggers:
  - Testing any authenticated endpoint
  - Adding new endpoint with auth dependency
  - Debugging 401/403/422 errors
  - Any RBAC-protected route

requires:
  step_1:
    action: "Identify auth dependency in endpoint"
    check: "What does Depends(...) require?"
    example: "Depends(verify_api_key) → needs X-AOS-Key header"
  step_2:
    action: "Identify RBAC middleware requirements"
    check: "What roles/tokens does middleware accept?"
    options:
      - "X-Machine-Token → machine role"
      - "Authorization: Bearer <JWT> → role from token"
      - "X-Roles → testing override"
  step_3:
    action: "Enumerate all required headers"
    output: "List of headers needed for this endpoint"
  step_4:
    action: "Test with correct headers"
    verify: "Response is not 401/403/422 for auth reasons"

forbid:
  - Testing endpoint without knowing auth contract
  - Assuming headers from other endpoints work
  - Ignoring middleware layer
  - Guessing auth headers

violation:
  type: BLOCKING
  message: "BL-AUTH-001 VIOLATION: Auth contract not enumerated"
  action: "STOP. Enumerate auth contract before testing."

output_required: |
  AUTH CONTRACT CHECK
  - Endpoint: <path>
  - Endpoint auth: <Depends(...)>
  - RBAC policy: <resource:action>
  - Required headers: <list>
  - Test command: <curl with all headers>
```

---

### BL-MIG-001: Migration Head Verification

**Class:** Multiple alembic heads causing migration chaos

**Problem:** Creating migration without checking current heads creates branch forks.

```yaml
id: BL-MIG-001
name: Migration Head Verification
class: migration_fork
severity: BLOCKING

triggers:
  - Creating any new migration
  - Running alembic upgrade
  - Any schema change task

requires:
  step_1:
    action: "Check current migration state"
    command: "alembic current"
    output: "Current revision(s)"
  step_2:
    action: "Check all heads"
    command: "alembic heads"
    output: "List of head revisions"
  step_3:
    action: "Verify single head"
    condition: "Only ONE head should exist"
    if_multiple: "Create merge migration first"
  step_4:
    action: "Identify parent revision"
    value: "Parent for new migration"

forbid:
  - Creating migration without checking heads
  - Assuming parent revision
  - Ignoring multiple heads warning
  - Running upgrade with multiple heads

violation:
  type: BLOCKING
  message: "BL-MIG-001 VIOLATION: Migration heads not verified"
  action: "STOP. Resolve multiple heads before proceeding."

output_required: |
  MIGRATION HEAD CHECK
  - Current: <revision>
  - Heads: <list>
  - Single head: YES / NO
  - Parent for new migration: <revision>
```

---

### BL-DOCKER-001: Service Name Resolution

**Class:** Wrong service/container name causing rebuild failures

**Problem:** Docker service names differ from container names, causing confusion.

```yaml
id: BL-DOCKER-001
name: Docker Service Name Resolution
class: service_name_mismatch
severity: BLOCKING

triggers:
  - Any docker compose command
  - Any container restart
  - Any service rebuild

requires:
  step_1:
    action: "List compose services"
    command: "docker compose config --services"
    output: "Service names as defined in compose file"
  step_2:
    action: "List running containers"
    command: "docker ps --format '{{.Names}}'"
    output: "Actual container names"
  step_3:
    action: "Map service to container"
    example: |
      Service: backend → Container: nova_agent_manager
      Service: worker → Container: nova_worker
  step_4:
    action: "Use correct name for command"
    rule: |
      docker compose commands → use SERVICE name
      docker exec/logs → use CONTAINER name

forbid:
  - Assuming service name equals container name
  - Using container name in compose commands
  - Using service name in docker exec

violation:
  type: WARNING
  message: "BL-DOCKER-001 VIOLATION: Service/container name mismatch"
  action: "Verify correct name type for command."

output_required: |
  DOCKER NAME CHECK
  - Compose services: <list>
  - Running containers: <list>
  - Target service: <name>
  - Target container: <name>
  - Command uses: SERVICE / CONTAINER (correct?)
```

---

### BL-TEST-001: Test Execution Prerequisites

**Class:** Test failures due to missing prerequisites

**Problem:** Tests run before environment is ready, causing false failures.

```yaml
id: BL-TEST-001
name: Test Execution Prerequisites
class: test_prerequisites
severity: BLOCKING

triggers:
  - Running any test suite
  - Debugging test failures
  - CI pipeline execution

requires:
  step_1:
    action: "Verify database accessible"
    command: "psql $DATABASE_URL -c 'SELECT 1'"
    condition: "Returns 1"
  step_2:
    action: "Verify backend healthy"
    command: "curl -s localhost:8000/health"
    condition: "status == healthy"
  step_3:
    action: "Verify migrations applied"
    command: "alembic current"
    condition: "At expected head"
  step_4:
    action: "Verify test data exists (if needed)"
    check: "Required fixtures present"

forbid:
  - Running tests with unhealthy backend
  - Running tests with pending migrations
  - Running tests without database access
  - Assuming prerequisites are met

violation:
  type: BLOCKING
  message: "BL-TEST-001 VIOLATION: Test prerequisites not verified"
  action: "STOP. Complete prerequisites before testing."

output_required: |
  TEST PREREQUISITES CHECK
  - Database accessible: YES / NO
  - Backend healthy: YES / NO
  - Migrations current: YES / NO
  - Required fixtures: <present / missing>
```

---

### BL-CONSOLE-001: Customer Console Constitution Compliance

**Class:** Console structure deviation / governance violation

**Problem:** Claude proposes console changes that deviate from the frozen v1 constitution without explicit approval.

```yaml
id: BL-CONSOLE-001
name: Customer Console Constitution Compliance
class: console_governance
severity: BLOCKING

triggers:
  - Any work on console.agenticverz.com
  - Any UI structure changes
  - Any sidebar modifications
  - Any domain/subdomain additions
  - Any new page creation for Customer Console
  - Discussion of console navigation
  - Mapping codebase to console structure

requires:
  step_1:
    action: "Load Customer Console Constitution"
    document: "docs/contracts/CUSTOMER_CONSOLE_V1_CONSTITUTION.md"
    verify: "Document exists and is read"
  step_2:
    action: "Verify frozen domains"
    check: "Are only these 5 domains being used?"
    frozen_domains:
      - Overview
      - Activity
      - Incidents
      - Policies
      - Logs
  step_3:
    action: "Check sidebar section placement"
    rule: |
      Core Lenses → Top section
      Connectivity → Middle section
      Administration → Bottom section
  step_4:
    action: "Verify jurisdiction boundaries"
    check: "Is this tenant-scoped only?"
    forbidden: "Cross-tenant data in Customer Console"
  step_5:
    action: "Confirm Claude role constraints"
    rule: "Auditor and mapper, not designer"
    output: "Findings are evidence, not authority"

forbid:
  - Introducing new domains without amendment
  - Renaming frozen domains
  - Merging domains
  - Mixing Customer Console with Founder/Ops Console data
  - Suggesting automation or learned authority
  - Auto-applying structural changes
  - "Improving" without explicit approval
  - Using "system decided" language
  - Cross-tenant intelligence claims

violation:
  type: BLOCKING
  message: "BL-CONSOLE-001 VIOLATION: Console constitution not followed"
  action: "STOP. Verify compliance with CUSTOMER_CONSOLE_V1_CONSTITUTION.md"

output_required: |
  CONSOLE CONSTITUTION CHECK
  - Constitution loaded: YES / NO
  - Frozen domains respected: YES / NO
  - Sidebar structure correct: YES / NO
  - Jurisdiction boundaries maintained: YES / NO
  - Claude role acknowledged: Auditor and mapper, not designer
  - Deviations identified: <list or NONE>
  - Human approval required: YES / NO
```

---

### BL-CONSOLE-002: Console Deviation Protocol

**Class:** Structural deviation without proper flagging

**Problem:** Claude makes console structure suggestions without following the deviation protocol.

```yaml
id: BL-CONSOLE-002
name: Console Deviation Protocol
class: deviation_handling
severity: BLOCKING

triggers:
  - Any proposed deviation from frozen console structure
  - Suggestion to add new domain
  - Suggestion to rename domain
  - Suggestion to merge domains
  - Any structural change recommendation

requires:
  step_1:
    action: "Explicitly identify the deviation"
    output: "What specifically deviates from constitution?"
  step_2:
    action: "Provide clear justification"
    output: "Why is this deviation necessary?"
    evidence: "Codebase evidence supporting the deviation"
  step_3:
    action: "State it will NOT be auto-applied"
    declaration: "This requires human approval before implementation"
  step_4:
    action: "Request explicit approval"
    output: "Propose amendment process if needed"

forbid:
  - Silent deviation (not flagging it)
  - Auto-applying deviations
  - Presenting deviation as recommendation
  - Justifying without evidence
  - Assuming approval

violation:
  type: BLOCKING
  message: "BL-CONSOLE-002 VIOLATION: Deviation not properly flagged"
  action: "STOP. Follow deviation protocol before proposing changes."

output_required: |
  CONSOLE DEVIATION REPORT
  - Deviation identified: <specific item>
  - Justification: <evidence-based reason>
  - Auto-applied: NO (must be NO)
  - Approval required: YES
  - Amendment process: <proposed steps if structural change>
```

---

### BL-CONSOLE-003: Project Scope Enforcement

**Class:** Project scope violation / navigation structure contamination

**Problem:** Claude proposes project-related changes that violate the global scope selector model or attempt to introduce Projects as domains/sidebar items.

```yaml
id: BL-CONSOLE-003
name: Project Scope Enforcement
class: project_scope_violation
severity: BLOCKING

triggers:
  - Any discussion of Project context in Customer Console
  - Any proposal to add Project to navigation
  - Any suggestion affecting project-scoped vs org-scoped data
  - Any cross-project aggregation proposal
  - Any UI change that could affect project selector placement

requires:
  step_1:
    action: "Verify Project Scope rules are loaded"
    document: "docs/contracts/CUSTOMER_CONSOLE_V1_CONSTITUTION.md Section 5.4"
    check: "Project Scope clarification is understood"
  step_2:
    action: "Confirm Project is treated as global scope selector"
    rule: |
      Project selector location: global header
      Project selector NOT in: sidebar
      Project is NOT a domain
  step_3:
    action: "Verify data scope vs structure separation"
    check: |
      Switching Projects changes DATA SCOPE only
      Does NOT change: Domains, Sidebar structure, Topics, Order semantics
  step_4:
    action: "Check for cross-project aggregation"
    rule: "Cross-project aggregation is FORBIDDEN in Customer Console"
  step_5:
    action: "Verify shared resources handling"
    check: |
      Policies: May be ORG-scoped or PROJECT-scoped
      Agents: May be bound to multiple projects
      Executions: Always project-scoped
      Incidents: Attach to executions → always project-scoped

forbid:
  - Proposing Project as a domain
  - Proposing Project as a sidebar item
  - Suggesting project-specific navigation changes
  - Cross-project data exposure in Customer Console
  - Treating Project selector as anything other than global scope filter
  - Aggregating data across projects in Customer Console views

violation:
  type: BLOCKING
  message: "BL-CONSOLE-003 VIOLATION: Project scope rules not followed"
  action: "STOP. Verify Project is treated as global scope selector only."

output_required: |
  PROJECT SCOPE CHECK
  - Project Scope rules loaded: YES / NO
  - Project treated as global selector: YES / NO
  - Project NOT proposed as domain/sidebar: YES / NO
  - Data scope vs structure separation maintained: YES / NO
  - Cross-project aggregation avoided: YES / NO
  - Shared resources correctly scoped: YES / NO
```

---

### BL-FRONTEND-001: Entry Point & Product Boundary Enforcement

**Class:** Frontend architecture violation / entry point contamination

**Problem:** Claude creates or modifies frontend code that violates the 3-layer entry point model or products-first folder structure frozen in PIN-235.

```yaml
id: BL-FRONTEND-001
name: Entry Point & Product Boundary Enforcement
class: frontend_architecture
severity: BLOCKING

triggers:
  - Any change to src/products/*/main.tsx
  - Any change to src/products/*/app/*.tsx
  - Any new product folder creation
  - Any page relocation or rename
  - Any import path changes in products folder
  - Discussion of frontend entry points
  - Creating new frontend components

requires:
  step_1:
    action: "Load PIN-235 freeze points"
    document: "docs/memory-pins/PIN-235-products-first-architecture-migration.md"
    verify: "Freeze points 1-3 are understood"
  step_2:
    action: "Verify 3-layer architecture"
    check: |
      Layer 1: main.tsx = runtime entry (DOM mounting, BrowserRouter)
      Layer 2: AIConsoleApp.tsx = product root (providers, routing, layout)
      Layer 3: pages/* = features (UI, business logic)
  step_3:
    action: "Verify folder structure compliance"
    check: |
      products/{product-name}/
        main.tsx
        app/
        pages/
        account/
        integrations/
  step_4:
    action: "Verify import patterns"
    check: |
      Correct: @ai-console/*, @/*
      Wrong: relative imports like ../../
  step_5:
    action: "Check anti-patterns"
    forbidden:
      - Business logic in main.tsx
      - DOM mounting in product code
      - Reorganizing Orders (O2-O5) into folders
      - Merging account + pages
      - Moving providers into main.tsx
      - Adding global Admin folder
      - Renaming AIConsoleApp

forbid:
  - Adding business logic to main.tsx
  - Adding DOM mounting to product components
  - Creating non-standard product folder structures
  - Using relative imports in products folder
  - Renaming frozen components (AIConsoleApp, etc.)
  - Creating new folder patterns without explicit approval
  - Debating frozen architectural decisions

violation:
  type: BLOCKING
  message: "BL-FRONTEND-001 VIOLATION: Frontend architecture invariant violated"
  action: "STOP. Verify compliance with PIN-235 freeze points."

output_required: |
  FRONTEND ARCHITECTURE CHECK
  - PIN-235 loaded: YES / NO
  - 3-layer separation maintained: YES / NO
  - main.tsx is runtime-only: YES / NO
  - Product root handles providers/routing: YES / NO
  - Folder structure compliant: YES / NO
  - Import patterns use aliases: YES / NO
  - Anti-patterns avoided: YES / NO
```

---

### BL-FRONTEND-002: Dead Click & 500 Error Prevention

**Class:** Frontend integration failure / incomplete deployment

**Problem:** Claude creates frontend changes that result in dead clicks (nav items without routes), 500 errors (missing API endpoints), or broken imports.

```yaml
id: BL-FRONTEND-002
name: Dead Click & 500 Error Prevention
class: frontend_integration
severity: BLOCKING

triggers:
  - Any new page added
  - Any route change
  - Any navigation item added
  - Any API integration added
  - Before any frontend deployment
  - Adding onClick handlers
  - Creating fetch/axios calls

requires:
  step_1:
    action: "Run build verification"
    command: "cd website/aos-console/console && npm run build"
    condition: "Build succeeds without errors"
    reason: "Catches import errors and TypeScript issues"
  step_2:
    action: "Verify route completeness"
    check: |
      For each new page:
      - Route exists in AIConsoleApp.tsx: <Route path=... element=... />
      - Route is accessible: navigation to route renders page
    reason: "Prevents 404 on navigation"
  step_3:
    action: "Verify navigation completeness"
    check: |
      For each nav item:
      - onClick or href is present and valid
      - Corresponding route exists
      - Active state reflects current route
    reason: "Prevents dead clicks"
  step_4:
    action: "Verify API integration"
    check: |
      For each API call:
      - Endpoint exists in backend
      - Error states are handled (try/catch, error UI)
      - Loading states are implemented
    reason: "Prevents 500 errors and white screens"
  step_5:
    action: "Verify import paths"
    check: |
      - All @ai-console/* imports resolve
      - All @/* imports resolve
      - No broken import paths
    reason: "Prevents build failures"

forbid:
  - Deploying without successful build
  - Adding nav items without corresponding routes
  - Adding routes without corresponding page components
  - Creating API calls without error handling
  - Leaving TODO comments in production code
  - Ignoring TypeScript errors
  - Assuming backend endpoints exist without verification

violation:
  type: BLOCKING
  message: "BL-FRONTEND-002 VIOLATION: Frontend integration incomplete"
  action: "STOP. Complete integration checklist before proceeding."

output_required: |
  FRONTEND INTEGRATION CHECK
  - Build succeeds: YES / NO
  - All routes have pages: YES / NO
  - All nav items have routes: YES / NO
  - All API calls have error handling: YES / NO
  - All imports resolve: YES / NO
  - No dead clicks: YES / NO
  - No TODO comments: YES / NO
```

---

### BL-CODE-REG-001: Codebase Registry Supremacy

**Class:** Unregistered code reasoning / purpose inference

**Problem:** Claude reasons about, creates, or modifies code without checking if it's registered in the Codebase Purpose & Authority Registry.

```yaml
id: BL-CODE-REG-001
name: Codebase Registry Supremacy
class: code_registration
severity: BLOCKING

triggers:
  - Creating any new code file
  - Modifying existing code
  - Reasoning about code behavior
  - Refactoring code
  - Analyzing dependencies
  - Suggesting architectural changes

requires:
  step_1:
    action: "Search registry for artifact"
    command: "python scripts/ops/artifact_lookup.py <name>"
    check: "Is artifact registered?"
  step_2:
    action: "If not found, pause and propose registration"
    output: |
      Proposed artifact entry:
      - artifact_id: AOS-XX-XXX-XXX-NNN
      - name: <filename>
      - type: <type>
      - purpose: <description>
      - authority_level: <observe|advise|enforce|mutate>
  step_3:
    action: "If found, verify purpose and authority"
    check: "Does the proposed change align with declared purpose?"
  step_4:
    action: "Create change record if modifying"
    requirement: "All modifications need change records"

forbid:
  - Creating code without proposing registry entry
  - Modifying code without checking registry
  - Reasoning about unregistered code behavior
  - Inferring purpose from filename alone
  - Guessing authority based on behavior
  - "Best-practice" assumptions about code

violation:
  type: BLOCKING
  message: "BL-CODE-REG-001 VIOLATION: Code registry not consulted"
  action: "STOP. Search registry before proceeding."

output_required: |
  CODE REGISTRY CHECK
  - Artifact searched: <name>
  - Registry result: FOUND / NOT FOUND
  - If FOUND:
    - artifact_id: <ID>
    - purpose: <purpose>
    - authority_level: <level>
  - If NOT FOUND:
    - Proposed registration: <details or "pending user approval">
  - Change record required: YES / NO
```

---

### BL-CODE-REG-002: No Silent Semantics

**Class:** Silent purpose inference / authority assumption

**Problem:** Claude silently infers why code exists, what it's allowed to do, or where it belongs without explicit registry information.

```yaml
id: BL-CODE-REG-002
name: No Silent Semantics
class: silent_inference
severity: BLOCKING

triggers:
  - Any reasoning about code purpose
  - Any statement about what code "should" do
  - Any suggestion about code placement
  - Any assumption about code authority
  - Explaining code behavior without registry check

requires:
  step_1:
    action: "Check if purpose is declared in registry"
    command: "python scripts/ops/artifact_lookup.py --id <ID> -v"
    check: "Is purpose field populated?"
  step_2:
    action: "Check if authority is declared"
    check: "Is authority_level field populated?"
  step_3:
    action: "If unclear, stop and ask"
    response: |
      I cannot determine the intended purpose of this code.
      Please clarify:
      - What does this code do? (purpose)
      - What is it allowed to modify? (authority_level)
      - Where does it belong? (product, domain)

forbid:
  - Inferring purpose from behavior
  - Inferring authority from naming conventions
  - Assuming placement from file location
  - "Best practice" recommendations without registry basis
  - "This code probably does X" statements
  - Proceeding with ambiguous semantics

violation:
  type: BLOCKING
  message: "BL-CODE-REG-002 VIOLATION: Purpose inferred without registry"
  action: "STOP. Check registry or ask for clarification."

output_required: |
  SEMANTIC CLARITY CHECK
  - Purpose from registry: <stated or UNKNOWN>
  - Authority from registry: <stated or UNKNOWN>
  - Inference attempted: NO (must be NO)
  - Clarification needed: YES / NO
```

---

### BL-CODE-REG-003: Change Record Before Modification

**Class:** Untracked code changes / evolution without audit

**Problem:** Claude modifies code without creating a change record, making evolution untrackable.

```yaml
id: BL-CODE-REG-003
name: Change Record Before Modification
class: untracked_changes
severity: BLOCKING

triggers:
  - Any code modification
  - Any refactoring
  - Any bug fix
  - Any optimization
  - Any interface change
  - Any dependency update

requires:
  step_1:
    action: "Identify affected artifacts"
    command: "python scripts/ops/artifact_lookup.py <name>"
    output: "List of artifact IDs being modified"
  step_2:
    action: "Create change record"
    location: "docs/codebase-registry/changes/CHANGE-YYYY-NNNN.yaml"
    required_fields:
      - change_id
      - date
      - author
      - change_type
      - purpose
      - scope.artifacts_modified
      - impact (authority_change, behavior_change, interface_change, data_change)
      - risk_level
      - backward_compatibility
      - validation
  step_3:
    action: "Request user approval of change record"
    check: "User confirms purpose and scope"
  step_4:
    action: "Only then proceed with modification"
    condition: "Change record approved"

forbid:
  - Modifying code without change record
  - Creating change records without user approval
  - Bundling unrelated changes in one record
  - Proceeding with "minor" changes without registration
  - Assuming changes are too small to track
  - Retrospective change record creation

violation:
  type: BLOCKING
  message: "BL-CODE-REG-003 VIOLATION: No change record for modification"
  action: "STOP. Create and get approval for change record first."

output_required: |
  CHANGE REGISTRATION CHECK
  - Artifacts affected: <list of IDs>
  - Change record created: YES / NO
  - Change ID: <CHANGE-YYYY-NNNN or PENDING>
  - Purpose stated: <purpose>
  - User approval: OBTAINED / PENDING
  - Modification allowed: YES / NO
```

---

### BL-BOUNDARY-001: Product Boundary Declaration Required

**Class:** Product boundary violation / undeclared ownership

**Problem:** Claude creates or modifies code without declaring product ownership, bucket classification, and failure jurisdiction — allowing boundary confusion to accumulate.

```yaml
id: BL-BOUNDARY-001
name: Product Boundary Declaration Required
class: product_boundary
severity: BLOCKING

triggers:
  - Creating any new code file
  - Creating any new module
  - Proposing any new artifact
  - Discussion of where code should live
  - Architectural decisions about code placement

requires:
  step_1:
    action: "Declare product ownership"
    options:
      - ai-console
      - system-wide
      - product-builder
    reason: "Product determines who owns the artifact"
  step_2:
    action: "Declare bucket classification"
    options:
      - surface (product UI/routes only)
      - adapter (thin translation layer)
      - platform (shared infrastructure)
    reason: "Bucket determines architectural role"
  step_3:
    action: "Declare expected callers"
    output: "List of modules/files that will call this"
    reason: "Callers determine true ownership"
  step_4:
    action: "Declare forbidden callers"
    output: "List of modules/patterns that must NOT call this"
    reason: "Forbidden callers enforce boundaries"
  step_5:
    action: "Declare failure scope"
    output: "What breaks if this is removed?"
    reason: "Failure scope validates classification"

forbid:
  - Creating code without product ownership declaration
  - Creating code without bucket classification
  - Assuming product from filename or directory
  - Proceeding with "we'll figure out ownership later"
  - Inferring callers from code structure

violation:
  type: BLOCKING
  message: "BL-BOUNDARY-001 VIOLATION: Product boundary not declared"
  action: "STOP. Declare product, bucket, callers, and failure scope."

output_required: |
  PRODUCT BOUNDARY DECLARATION
  - Product: ai-console / system-wide / product-builder
  - Bucket: surface / adapter / platform
  - Expected callers: <list>
  - Forbidden callers: <list>
  - Breaks if removed: <list>
  - Must not break: <list>
  - Declaration approved: YES / PENDING
```

---

### BL-BOUNDARY-002: Three Blocking Questions Gate

**Class:** Uncertain ownership / speculative architecture

**Problem:** Claude proceeds with code creation or modification while unable to answer fundamental ownership questions.

```yaml
id: BL-BOUNDARY-002
name: Three Blocking Questions Gate
class: ownership_uncertainty
severity: BLOCKING

triggers:
  - Creating any code artifact
  - Modifying existing code
  - Proposing architectural changes
  - Discussing code placement
  - Reasoning about code dependencies

requires:
  step_1:
    question: "Who calls this in production?"
    acceptable_answers:
      - Specific modules/files (e.g., "guard.py", "AIConsoleApp.tsx")
      - "Nothing" (orphan → reject or archive)
      - Explicit list of callers
    unacceptable_answers:
      - "Not sure"
      - "Later"
      - "Probably"
      - "We'll figure it out"
    on_unacceptable: BLOCK
  step_2:
    question: "What breaks if AI Console is deleted?"
    acceptable_answers:
      - Specific products/features
      - "Nothing" (platform-only)
      - "Only this feature"
    unacceptable_answers:
      - "I don't know"
      - "Everything"
      - "Hard to say"
    on_unacceptable: BLOCK
  step_3:
    question: "Who must NOT depend on this?"
    acceptable_answers:
      - Specific modules/patterns
      - "Workers must not call this"
      - "SDK must not import this"
    unacceptable_answers:
      - "Anyone can use it"
      - "No restrictions"
      - "Not sure yet"
    on_unacceptable: BLOCK

forbid:
  - Proceeding when any question has uncertain answer
  - Answering "probably" to ownership questions
  - Deferring ownership decisions to later
  - Assuming boundary questions are "obvious"

violation:
  type: BLOCKING
  message: "BL-BOUNDARY-002 VIOLATION: Cannot answer blocking questions"
  action: "STOP. All three questions must have acceptable answers."

output_required: |
  BLOCKING QUESTIONS CHECK
  - Q1: Who calls this in production?
    Answer: <specific list or BLOCKED>
  - Q2: What breaks if AI Console is deleted?
    Answer: <specific products or BLOCKED>
  - Q3: Who must NOT depend on this?
    Answer: <specific restrictions or BLOCKED>
  - All questions answered acceptably: YES / NO
  - Proceed allowed: YES / NO
```

---

### BL-BOUNDARY-003: Caller Graph Determines Truth

**Class:** Label-based mislabeling / invocation drift

**Problem:** Claude trusts registry labels instead of actual invocation patterns, allowing boundary violations to persist.

```yaml
id: BL-BOUNDARY-003
name: Caller Graph Determines Truth
class: invocation_drift
severity: BLOCKING

triggers:
  - Validating artifact product ownership
  - Reviewing boundary classification
  - Auditing registry accuracy
  - When label and behavior seem misaligned
  - Before reclassifying artifacts

requires:
  step_1:
    action: "Trace actual callers"
    method: "Search codebase for imports/calls"
    output: "List of files that import or call this artifact"
  step_2:
    action: "Classify callers by surface"
    buckets:
      - console-ui (product pages, components)
      - console-api (product routes)
      - workers (background jobs)
      - sdk (published packages)
      - ops/founder (other consoles)
      - tests (test files)
    output: "Caller classification by surface"
  step_3:
    action: "Apply Non-Console Caller Test"
    rule: |
      If ANY of these call the artifact:
      - workers/*
      - sdk/*
      - ops/* (founder/ops console)
      - External API consumers

      Then artifact is NOT ai-console owned.
    output: "Non-console callers found: YES / NO"
  step_4:
    action: "Compare label vs reality"
    check: "Does registered product match actual callers?"
    on_mismatch: "Flag for reclassification"

forbid:
  - Trusting labels over caller evidence
  - Ignoring non-console callers
  - Assuming "tests don't count" (they reveal real usage)
  - Keeping mislabeled artifacts without flagging

violation:
  type: BLOCKING
  message: "BL-BOUNDARY-003 VIOLATION: Label does not match caller graph"
  action: "STOP. Reclassify artifact based on actual invocation."

output_required: |
  CALLER GRAPH ANALYSIS
  - Artifact: <name>
  - Registry label: <product>
  - Actual callers:
    - Console-UI: <list>
    - Console-API: <list>
    - Workers: <list>
    - SDK: <list>
    - Ops/Founder: <list>
    - Tests: <list>
  - Non-console callers found: YES / NO
  - Label matches reality: YES / NO
  - Reclassification needed: YES / NO
  - If YES: Proposed new label: <product>
```

---

## Rule Application Protocol

### When Rules Trigger

1. Claude detects trigger condition in task
2. Claude MUST complete all `requires` steps
3. Claude MUST NOT perform any `forbid` actions
4. Claude MUST include `output_required` in response

### Violation Handling

- **BLOCKING violations**: Claude must STOP and report
- **WARNING violations**: Claude may proceed with caution

### Adding New Rules

When an incident repeats or a new class is identified:

1. Classify the incident (what class of failure?)
2. Extract the behavior rule (what would have prevented it?)
3. Add rule to this library with unique ID
4. Update validator to check for rule compliance

---

## Rule Index

| ID | Name | Class | Severity |
|----|------|-------|----------|
| BL-ENV-001 | Runtime Sync Before Test | environment_drift | BLOCKING |
| BL-DB-001 | Timestamp Semantics Alignment | timezone_mismatch | BLOCKING |
| BL-AUTH-001 | Auth Contract Enumeration | auth_mismatch | BLOCKING |
| BL-MIG-001 | Migration Head Verification | migration_fork | BLOCKING |
| BL-DOCKER-001 | Service Name Resolution | service_name_mismatch | WARNING |
| BL-TEST-001 | Test Execution Prerequisites | test_prerequisites | BLOCKING |
| BL-CONSOLE-001 | Customer Console Constitution Compliance | console_governance | BLOCKING |
| BL-CONSOLE-002 | Console Deviation Protocol | deviation_handling | BLOCKING |
| BL-CONSOLE-003 | Project Scope Enforcement | project_scope_violation | BLOCKING |
| BL-FRONTEND-001 | Entry Point & Product Boundary Enforcement | frontend_architecture | BLOCKING |
| BL-FRONTEND-002 | Dead Click & 500 Error Prevention | frontend_integration | BLOCKING |
| BL-CODE-REG-001 | Codebase Registry Supremacy | code_registration | BLOCKING |
| BL-CODE-REG-002 | No Silent Semantics | silent_inference | BLOCKING |
| BL-CODE-REG-003 | Change Record Before Modification | untracked_changes | BLOCKING |
| BL-BOUNDARY-001 | Product Boundary Declaration Required | product_boundary | BLOCKING |
| BL-BOUNDARY-002 | Three Blocking Questions Gate | ownership_uncertainty | BLOCKING |
| BL-BOUNDARY-003 | Caller Graph Determines Truth | invocation_drift | BLOCKING |

---

## Incident → Rule Conversion Template

When a new incident occurs:

```yaml
# New Rule Template
id: BL-XXX-NNN
name: <Descriptive Name>
class: <incident_class>
severity: BLOCKING / WARNING

# What was the incident?
incident:
  date: YYYY-MM-DD
  description: <What happened>
  root_cause: <Why it happened>
  time_wasted: <Debugging time>

# What would have prevented it?
prevention:
  trigger: <When should this rule apply?>
  check: <What should be verified?>
  output: <What evidence is required?>

# Structured rule
triggers:
  - <condition 1>
  - <condition 2>

requires:
  - <step 1>
  - <step 2>

forbid:
  - <forbidden action 1>
  - <forbidden action 2>

violation:
  type: BLOCKING
  message: "<ID> VIOLATION: <description>"
  action: "STOP. <what to do>"
```

---

## Related Documents

- `CLAUDE_BOOT_CONTRACT.md` — Session initialization
- `CLAUDE_PRE_CODE_DISCIPLINE.md` — Pre-code task checklist
- `scripts/ops/claude_response_validator.py` — Automated validation
- `docs/LESSONS_ENFORCED.md` — Failure prevention rules
- `docs/contracts/CUSTOMER_CONSOLE_V1_CONSTITUTION.md` — Console governance (v1 frozen)
- `docs/contracts/CODE_EVOLUTION_CONTRACT.md` — Code registration & change tracking
- `docs/contracts/PRODUCT_BOUNDARY_CONTRACT.md` — Product boundary enforcement (pre-build)
- `docs/playbooks/SESSION_PLAYBOOK.yaml` — Session bootstrap and console governance
- `docs/memory-pins/PIN-235-products-first-architecture-migration.md` — Frontend architecture (frozen)
- `docs/memory-pins/PIN-237-codebase-registry-survey.md` — Codebase registry (113 artifacts)
- `docs/memory-pins/PIN-239-product-boundary-enforcement.md` — Product boundary enforcement
- `docs/codebase-registry/` — Artifact registry and change records
- `scripts/ops/artifact_lookup.py` — Registry search tool

---

*This library is machine-enforced. Non-compliant responses will be rejected.*
