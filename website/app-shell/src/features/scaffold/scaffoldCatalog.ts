/**
 * PR Scaffold Catalog for /page/<domain>/<subpage>
 *
 * Layer: L1 — Product Experience (UI)
 * Product: ai-console
 * Role: Contract-first metadata for stagetest scaffold surfaces.
 * Source: PR1-PR10 facade addendum contracts.
 */

export interface ScaffoldSlice {
  pr: string;
  domain: string;
  subpage: string;
  title: string;
  facadePath: string;
  query?: Record<string, string>;
  probeHeaders?: Record<string, string>;
  contractDoc: string;
  preflightReferencePath?: string;
  legacyReferencePath?: string;
}

export const SCAFFOLD_SLICES: ScaffoldSlice[] = [
  {
    pr: 'PR1',
    domain: 'activity',
    subpage: 'runs-live',
    title: 'Activity Runs Live',
    facadePath: '/hoc/api/cus/activity/runs',
    query: { topic: 'live', limit: '50', offset: '0' },
    contractDoc: 'backend/app/hoc/docs/architecture/usecases/PR1_RUNS_FACADE_CONTRACT_ADDENDUM_2026-02-16.md',
    preflightReferencePath: '/precus/activity/runs?state=LIVE',
    legacyReferencePath: '/api/v1/runtime/activity/runs?state=LIVE',
  },
  {
    pr: 'PR1',
    domain: 'activity',
    subpage: 'runs-completed',
    title: 'Activity Runs Completed',
    facadePath: '/hoc/api/cus/activity/runs',
    query: { topic: 'completed', limit: '50', offset: '0' },
    contractDoc: 'backend/app/hoc/docs/architecture/usecases/PR1_RUNS_FACADE_CONTRACT_ADDENDUM_2026-02-16.md',
    preflightReferencePath: '/precus/activity/runs?state=COMPLETED',
    legacyReferencePath: '/api/v1/runtime/activity/runs?state=COMPLETED',
  },
  {
    pr: 'PR2',
    domain: 'incidents',
    subpage: 'events-active',
    title: 'Incidents Active',
    facadePath: '/hoc/api/cus/incidents/list',
    query: { topic: 'active', limit: '50', offset: '0' },
    contractDoc: 'backend/app/hoc/docs/architecture/usecases/PR2_INCIDENTS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md',
    preflightReferencePath: '/precus/incidents/events/active',
  },
  {
    pr: 'PR2',
    domain: 'incidents',
    subpage: 'events-resolved',
    title: 'Incidents Resolved',
    facadePath: '/hoc/api/cus/incidents/list',
    query: { topic: 'resolved', limit: '50', offset: '0' },
    contractDoc: 'backend/app/hoc/docs/architecture/usecases/PR2_INCIDENTS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md',
    preflightReferencePath: '/precus/incidents/events/resolved',
  },
  {
    pr: 'PR2',
    domain: 'incidents',
    subpage: 'events-historical',
    title: 'Incidents Historical',
    facadePath: '/hoc/api/cus/incidents/list',
    query: { topic: 'historical', limit: '50', offset: '0' },
    contractDoc: 'backend/app/hoc/docs/architecture/usecases/PR2_INCIDENTS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md',
    preflightReferencePath: '/precus/incidents/events/history',
  },
  {
    pr: 'PR3',
    domain: 'policies',
    subpage: 'governance-active',
    title: 'Policies Governance Active',
    facadePath: '/hoc/api/cus/policies/list',
    query: { topic: 'active', limit: '50', offset: '0' },
    contractDoc: 'backend/app/hoc/docs/architecture/usecases/PR3_POLICIES_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md',
    preflightReferencePath: '/precus/policies/governance/active',
  },
  {
    pr: 'PR3',
    domain: 'policies',
    subpage: 'governance-retired',
    title: 'Policies Governance Retired',
    facadePath: '/hoc/api/cus/policies/list',
    query: { topic: 'retired', limit: '50', offset: '0' },
    contractDoc: 'backend/app/hoc/docs/architecture/usecases/PR3_POLICIES_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md',
    preflightReferencePath: '/precus/policies/governance/library',
  },
  {
    pr: 'PR4',
    domain: 'policies',
    subpage: 'limits-all',
    title: 'Controls Limits All',
    facadePath: '/hoc/api/cus/controls/list',
    query: { topic: 'all', limit: '50', offset: '0' },
    contractDoc: 'backend/app/hoc/docs/architecture/usecases/PR4_CONTROLS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md',
    preflightReferencePath: '/precus/policies/limits/controls',
  },
  {
    pr: 'PR4',
    domain: 'policies',
    subpage: 'limits-enabled',
    title: 'Controls Limits Enabled',
    facadePath: '/hoc/api/cus/controls/list',
    query: { topic: 'enabled', limit: '50', offset: '0' },
    contractDoc: 'backend/app/hoc/docs/architecture/usecases/PR4_CONTROLS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md',
  },
  {
    pr: 'PR4',
    domain: 'policies',
    subpage: 'limits-disabled',
    title: 'Controls Limits Disabled',
    facadePath: '/hoc/api/cus/controls/list',
    query: { topic: 'disabled', limit: '50', offset: '0' },
    contractDoc: 'backend/app/hoc/docs/architecture/usecases/PR4_CONTROLS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md',
  },
  {
    pr: 'PR4',
    domain: 'policies',
    subpage: 'limits-auto',
    title: 'Controls Limits Auto',
    facadePath: '/hoc/api/cus/controls/list',
    query: { topic: 'auto', limit: '50', offset: '0' },
    contractDoc: 'backend/app/hoc/docs/architecture/usecases/PR4_CONTROLS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md',
  },
  {
    pr: 'PR5',
    domain: 'logs',
    subpage: 'records-llm-runs',
    title: 'Logs Records LLM Runs',
    facadePath: '/hoc/api/cus/logs/list',
    query: { topic: 'llm_runs', limit: '50', offset: '0' },
    contractDoc: 'backend/app/hoc/docs/architecture/usecases/PR5_LOGS_REPLAY_FEED_FACADE_CONTRACT_ADDENDUM_2026-02-16.md',
    preflightReferencePath: '/precus/logs/records/llm-runs',
  },
  {
    pr: 'PR5',
    domain: 'logs',
    subpage: 'records-system',
    title: 'Logs Records System',
    facadePath: '/hoc/api/cus/logs/list',
    query: { topic: 'system_records', limit: '50', offset: '0' },
    contractDoc: 'backend/app/hoc/docs/architecture/usecases/PR5_LOGS_REPLAY_FEED_FACADE_CONTRACT_ADDENDUM_2026-02-16.md',
    preflightReferencePath: '/precus/logs/records/system',
  },
  {
    pr: 'PR6',
    domain: 'overview',
    subpage: 'highlights',
    title: 'Overview Highlights',
    facadePath: '/hoc/api/cus/overview/highlights',
    query: { limit: '50', offset: '0' },
    contractDoc: 'backend/app/hoc/docs/architecture/usecases/PR6_OVERVIEW_HIGHLIGHTS_FACADE_CONTRACT_ADDENDUM_2026-02-16.md',
    preflightReferencePath: '/precus/overview',
  },
  {
    pr: 'PR7',
    domain: 'analytics',
    subpage: 'usage',
    title: 'Analytics Usage',
    facadePath: '/hoc/api/cus/analytics/statistics/usage',
    query: { resolution: 'day', scope: 'org', limit: '50', offset: '0' },
    contractDoc: 'backend/app/hoc/docs/architecture/usecases/PR7_ANALYTICS_USAGE_FACADE_CONTRACT_ADDENDUM_2026-02-16.md',
    preflightReferencePath: '/precus/analytics/statistics/usage',
  },
  {
    pr: 'PR8',
    domain: 'connectivity',
    subpage: 'integrations',
    title: 'Connectivity Integrations',
    facadePath: '/hoc/api/cus/integrations/list',
    query: { limit: '50', offset: '0' },
    contractDoc: 'backend/app/hoc/docs/architecture/usecases/PR8_INTEGRATIONS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md',
    preflightReferencePath: '/precus/connectivity',
  },
  {
    pr: 'PR9',
    domain: 'connectivity',
    subpage: 'api-keys',
    title: 'Connectivity API Keys',
    facadePath: '/hoc/api/cus/api_keys/list',
    query: { limit: '50', offset: '0' },
    contractDoc: 'backend/app/hoc/docs/architecture/usecases/PR9_API_KEYS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md',
    preflightReferencePath: '/precus/connectivity',
  },
  {
    pr: 'PR10',
    domain: 'account',
    subpage: 'team-members',
    title: 'Account Team Members',
    facadePath: '/hoc/api/cus/account/users/list',
    query: { limit: '50', offset: '0' },
    contractDoc: 'backend/app/hoc/docs/architecture/usecases/PR10_ACCOUNT_USERS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md',
    preflightReferencePath: '/precus/account',
  },
];

export function getSlice(domain: string | undefined, subpage: string | undefined): ScaffoldSlice | undefined {
  if (!domain || !subpage) {
    return undefined;
  }
  return SCAFFOLD_SLICES.find((item) => item.domain === domain && item.subpage === subpage);
}

export function buildRequestPath(slice: ScaffoldSlice): string {
  const params = new URLSearchParams(slice.query ?? {});
  const query = params.toString();
  return query ? `${slice.facadePath}?${query}` : slice.facadePath;
}
