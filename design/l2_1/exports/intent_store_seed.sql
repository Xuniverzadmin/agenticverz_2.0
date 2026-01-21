-- AURORA_L2 Intent Store Seed Data
-- Generated: 2026-01-19T18:29:59.664608+00:00
-- Intents: 86
-- NOTE: All intents marked UNREVIEWED per migration policy

-- Clear existing data (optional, comment out if incremental)
-- TRUNCATE aurora_l2_intent_store;

BEGIN;

INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('ACT-LLM-COMP-O1', 'ACTIVITY', 'LLM_RUNS', 'COMPLETED', 'ACTIVITY.LLM_RUNS.COMPLETED', 1, 'L2_1', 'ACT-LLM-COMP-O1', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show how many LLM runs have completed in the selected window.

What it shows:
- Total completed runs count

What it explicitly does NOT show:
- No success/failure split
- No duration
- No cost', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.297709+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('ACT-LLM-COMP-O2', 'ACTIVITY', 'LLM_RUNS', 'COMPLETED', 'ACTIVITY.LLM_RUNS.COMPLETED', 2, 'L2_1', 'ACT-LLM-COMP-O2', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Surface how many completed runs finished successfully.

What it shows:
- Count of successful runs

What it explicitly does NOT show:
- No quality scoring
- No downstream impact
- No policy attribution', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.302559+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('ACT-LLM-COMP-O3', 'ACTIVITY', 'LLM_RUNS', 'COMPLETED', 'ACTIVITY.LLM_RUNS.COMPLETED', 3, 'L2_1', 'ACT-LLM-COMP-O3', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Expose completed runs that ended in failure.

What it shows:
- Count of failed runs (from status breakdown)
- Uses FAILED bucket from summary_by_status

What it explicitly does NOT show:
- No root cause
- No retry controls
- No blame attribution', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.306793+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('ACT-LLM-COMP-O4', 'ACTIVITY', 'LLM_RUNS', 'COMPLETED', 'ACTIVITY.LLM_RUNS.COMPLETED', 4, 'L2_1', 'ACT-LLM-COMP-O4', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Highlight runs that completed but came close to limits.

What it shows:
- Count of completed runs that were near:
- Cost limits
- Time limits
- Token limits

What it explicitly does NOT show:
- No violations
- No enforcement
- No tuning actions', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.311357+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('ACT-LLM-COMP-O5', 'ACTIVITY', 'LLM_RUNS', 'COMPLETED', 'ACTIVITY.LLM_RUNS.COMPLETED', 5, 'L2_1', 'ACT-LLM-COMP-O5', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show runs that ended intentionally before completion.

What it shows:
- Count of aborted or cancelled runs

What it explicitly does NOT show:
- No initiator identity
- No reason codes
- No recovery options', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.315634+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('ACT-LLM-LIVE-O1', 'ACTIVITY', 'LLM_RUNS', 'LIVE', 'ACTIVITY.LLM_RUNS.LIVE', 1, 'L2_1', 'ACT-LLM-LIVE-O1', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show how many LLM runs are currently in progress.

What it shows:
- Total number of live LLM runs

What it explicitly does NOT show:
- No breakdown by model, agent, user, or cost
- No status reasons
- No controls', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.319835+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('ACT-LLM-LIVE-O2', 'ACTIVITY', 'LLM_RUNS', 'LIVE', 'ACTIVITY.LLM_RUNS.LIVE', 2, 'L2_1', 'ACT-LLM-LIVE-O2', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Surface live runs exceeding expected execution time.

What it shows:
- Count of live runs exceeding time threshold (e.g., > X minutes)
- Runs flagged as AT_RISK or VIOLATED for execution time

What it explicitly does NOT show:
- No root cause
- No cost data
- No termination control', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.323778+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('ACT-LLM-LIVE-O3', 'ACTIVITY', 'LLM_RUNS', 'LIVE', 'ACTIVITY.LLM_RUNS.LIVE', 3, 'L2_1', 'ACT-LLM-LIVE-O3', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Highlight live runs that are approaching failure or limits.

What it shows:
- Count of live runs flagged as near-threshold or unstable

What it explicitly does NOT show:
- No policy actions
- No manual override
- No mitigation controls', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.328125+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('ACT-LLM-LIVE-O4', 'ACTIVITY', 'LLM_RUNS', 'LIVE', 'ACTIVITY.LLM_RUNS.LIVE', 4, 'L2_1', 'ACT-LLM-LIVE-O4', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Indicate whether telemetry, logs, and traces are flowing for live runs.

What it shows:
- Percentage or status of live runs emitting evidence

What it explicitly does NOT show:
- No log contents
- No replay
- No export', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.332050+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('ACT-LLM-LIVE-O5', 'ACTIVITY', 'LLM_RUNS', 'LIVE', 'ACTIVITY.LLM_RUNS.LIVE', 5, 'L2_1', 'ACT-LLM-LIVE-O5', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Provide a coarse distribution of live runs by major dimension.

What it shows:
- Distribution by LLM provider, agent, source, risk level, status, or cost
- Dimension selector buttons to switch views (LIVE topic-scoped):
- By Provider → /runs/live/by-dimension?dim=provider_type
- By Source → /runs/live/by-dimension?dim=source
- By Agent → /runs/live/by-dimension?dim=agent_id
- By Risk → /runs/live/by-dimension?dim=risk_level
- By Status → /summary/by-status (future: /summary/live/by-status)
- By Cost → /cost-analysis (future: /cost-analysis/live)
- NOTE: Per Policy TOPIC-SCOPED-ENDPOINT-001, state=LIVE is hardcoded at endpoint

What it explicitly does NOT show:
- No drill-down
- No per-run detail
- No controls', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.336802+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('ACT-LLM-SIG-O1', 'ACTIVITY', 'LLM_RUNS', 'SIGNALS', 'ACTIVITY.LLM_RUNS.SIGNALS', 1, 'L2_1', 'ACT-LLM-SIG-O1', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Surface what is happening right now that matters — the primary attention surface.

What it shows:
- Critical failures
- Critical successes
- Active risk conditions
- Only currently active or very recent signals

What it explicitly does NOT show:
- No historical signals
- No controls or actions
- No policy execution', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.340568+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('ACT-LLM-SIG-O2', 'ACTIVITY', 'LLM_RUNS', 'SIGNALS', 'ACTIVITY.LLM_RUNS.SIGNALS', 2, 'L2_1', 'ACT-LLM-SIG-O2', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Surface runs approaching failure, policy, or cost limits (threshold proximity).

What it shows:
- Token limits nearing breach
- Cost ceilings approaching
- Timeouts nearing SLA breach
- Frequency/rate-limit pressure

What it explicitly does NOT show:
- No actions or mitigations
- No policy controls
- No historical trends', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.345381+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('ACT-LLM-SIG-O3', 'ACTIVITY', 'LLM_RUNS', 'SIGNALS', 'ACTIVITY.LLM_RUNS.SIGNALS', 3, 'L2_1', 'ACT-LLM-SIG-O3', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Surface temporal signals — behavior patterns over time indicating instability.

What it shows:
- Frequent retries
- Latency spikes
- Repeated partial failures
- Flapping success/failure patterns

What it explicitly does NOT show:
- No single-event failures (patterns only)
- No root cause analysis
- No remediation controls', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.349546+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('ACT-LLM-SIG-O4', 'ACTIVITY', 'LLM_RUNS', 'SIGNALS', 'ACTIVITY.LLM_RUNS.SIGNALS', 4, 'L2_1', 'ACT-LLM-SIG-O4', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Surface economic deviations — where money is being lost or saved unexpectedly.

What it shows:
- Cost overruns
- Cost savers (first-class signals)
- Efficiency anomalies
- Unexpected cost spikes or drops

What it explicitly does NOT show:
- No budget controls
- No policy enforcement
- No historical cost trends', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.353926+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('ACT-LLM-SIG-O5', 'ACTIVITY', 'LLM_RUNS', 'SIGNALS', 'ACTIVITY.LLM_RUNS.SIGNALS', 5, 'L2_1', 'ACT-LLM-SIG-O5', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Synthesize attention priority — what to look at first and why.

What it shows:
- Prioritized attention queue combining:
- Severity (O1)
- Proximity (O2)
- Pattern persistence (O3)
- Economic impact (O4)
- Grouping by LLM, Agent, or Human
- Cross-cutting issues

What it explicitly does NOT show:
- No decisions or actions
- No policy execution
- No drill-down details', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.358252+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('INC-EV-ACT-O1', 'INCIDENTS', 'EVENTS', 'ACTIVE', 'INCIDENTS.EVENTS.ACTIVE', 1, 'L2_1', 'INC-EV-ACT-O1', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show the canonical set of currently active incidents.

What it shows:
- Failures (hard policy violation)
- Near-threshold escalations (policy-defined)
- Prevented overruns (policy intervened)
- Governance-triggered halts
- One row = one incident (no aggregation)

What it explicitly does NOT show:
- No trends or interpretation
- No raw signals (those are in Activity)
- No actions or controls', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.362734+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('INC-EV-ACT-O2', 'INCIDENTS', 'EVENTS', 'ACTIVE', 'INCIDENTS.EVENTS.ACTIVE', 2, 'L2_1', 'INC-EV-ACT-O2', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Explain why each incident occurred — cause and trigger classification.

What it shows:
- Triggering condition (cost threshold, token limit, time SLA, policy rule)
- Whether detected after violation or prevented before violation

What it explicitly does NOT show:
- No blame attribution
- No actions or remediation
- No policy editing', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.367368+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('INC-EV-ACT-O3', 'INCIDENTS', 'EVENTS', 'ACTIVE', 'INCIDENTS.EVENTS.ACTIVE', 3, 'L2_1', 'INC-EV-ACT-O3', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show control state — whether each incident is contained or still dangerous.

What it shows:
- Still active / paused / quarantined
- Human override applied or not
- Auto-remediation attempted or not
- Guardrails holding or breached

What it explicitly does NOT show:
- No escalation actions
- No policy changes
- No resolution controls', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.371310+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('INC-EV-ACT-O4', 'INCIDENTS', 'EVENTS', 'ACTIVE', 'INCIDENTS.EVENTS.ACTIVE', 4, 'L2_1', 'INC-EV-ACT-O4', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show impact assessment — actual damage or prevented damage.

What it shows:
- Actual cost incurred
- Cost prevented by policy
- Downtime / latency impact
- Business impact classification (if available)
- Prevented damage is first-class

What it explicitly does NOT show:
- No cost controls
- No budget editing
- No forecasts', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.375665+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('INC-EV-ACT-O5', 'INCIDENTS', 'EVENTS', 'ACTIVE', 'INCIDENTS.EVENTS.ACTIVE', 5, 'L2_1', 'INC-EV-ACT-O5', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Provide attribution and escalation context for each incident.

What it shows:
- Attribution by LLM, Agent, Human, Policy
- Repeated incident marker
- Linked past incidents (if any)
- Escalation eligibility (yes/no)

What it explicitly does NOT show:
- No approval actions
- No policy changes
- No resolution execution', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.379610+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('INC-EV-HIST-O1', 'INCIDENTS', 'EVENTS', 'HISTORICAL', 'INCIDENTS.EVENTS.HISTORICAL', 1, 'L2_1', 'INC-EV-HIST-O1', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show incident volume and trend baseline over time.

What it shows:
- Incident counts by time window (day / week / month)
- Trend direction (rising, flat, declining)
- Aggregates only (no per-incident rows)

What it explicitly does NOT show:
- No individual incidents
- No real-time data
- No controls', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.383564+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('INC-EV-HIST-O2', 'INCIDENTS', 'EVENTS', 'HISTORICAL', 'INCIDENTS.EVENTS.HISTORICAL', 2, 'L2_1', 'INC-EV-HIST-O2', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show incident type distribution over time.

What it shows:
- Failure type distribution (success breach, failure, near-threshold)
- Policy-related vs non-policy
- Cost-related vs performance-related
- Infrastructure vs model vs human-triggered

What it explicitly does NOT show:
- No individual incidents
- No real-time data
- No controls', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.387884+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('INC-EV-HIST-O3', 'INCIDENTS', 'EVENTS', 'HISTORICAL', 'INCIDENTS.EVENTS.HISTORICAL', 3, 'L2_1', 'INC-EV-HIST-O3', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show repeatability and recurrence analysis — which incidents keep coming back.

What it shows:
- Same root cause recurring
- Same policy involved repeatedly
- Same agent / LLM / human role involved
- Short recurrence intervals

What it explicitly does NOT show:
- No blame attribution
- No policy changes
- No actions', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.391142+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('INC-EV-HIST-O4', 'INCIDENTS', 'EVENTS', 'HISTORICAL', 'INCIDENTS.EVENTS.HISTORICAL', 4, 'L2_1', 'INC-EV-HIST-O4', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show cost and impact over time — true economic footprint.

What it shows:
- Total cost incurred
- Total cost prevented (via governance)
- Cost avoided vs cost paid ratio
- Long-term cost trend
- Finalized costs only (no forecasts)

What it explicitly does NOT show:
- No budget controls
- No projections
- No real-time data', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.395192+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('INC-EV-HIST-O5', 'INCIDENTS', 'EVENTS', 'HISTORICAL', 'INCIDENTS.EVENTS.HISTORICAL', 5, 'L2_1', 'INC-EV-HIST-O5', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Surface systemic signals and governance pressure from historical patterns.

What it shows:
- Policies with chronic incident association
- Thresholds consistently too tight or too loose
- Areas where human overrides dominate
- Domains where automation underperforms

What it explicitly does NOT show:
- No policy execution
- No approvals
- No automated actions', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.400041+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('INC-EV-RES-O1', 'INCIDENTS', 'EVENTS', 'RESOLVED', 'INCIDENTS.EVENTS.RESOLVED', 1, 'L2_1', 'INC-EV-RES-O1', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show the canonical list of recently resolved incidents.

What it shows:
- Incidents transitioned from Active → Resolved
- Within the recent window (not long-term history)
- Resolution timestamp mandatory
- Original incident ID preserved

What it explicitly does NOT show:
- No active incidents
- No historical aggregation
- No controls', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.404358+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('INC-EV-RES-O2', 'INCIDENTS', 'EVENTS', 'RESOLVED', 'INCIDENTS.EVENTS.RESOLVED', 2, 'L2_1', 'INC-EV-RES-O2', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show how each incident was resolved — resolution method.

What it shows:
- Automatic recovery
- Policy enforcement succeeded
- Human override
- Manual intervention
- System rollback
- External dependency recovery
- Each incident maps to exactly one primary resolution method

What it explicitly does NOT show:
- No resolution actions
- No policy editing', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.408813+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('INC-EV-RES-O3', 'INCIDENTS', 'EVENTS', 'RESOLVED', 'INCIDENTS.EVENTS.RESOLVED', 3, 'L2_1', 'INC-EV-RES-O3', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show time-to-resolution (TTR) and SLA compliance.

What it shows:
- Detection time
- Resolution time
- Total duration in exception
- SLA classification (within / breached)

What it explicitly does NOT show:
- No contextual judgment
- No policy adjustments
- No controls', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.412949+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('INC-EV-RES-O4', 'INCIDENTS', 'EVENTS', 'RESOLVED', 'INCIDENTS.EVENTS.RESOLVED', 4, 'L2_1', 'INC-EV-RES-O4', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show outcome and impact post-resolution — the final reality.

What it shows:
- Final cost incurred
- Cost prevented
- Residual impact (if any)
- Side effects introduced by resolution

What it explicitly does NOT show:
- No projections
- No forecasts
- No policy controls', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.418630+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('INC-EV-RES-O5', 'INCIDENTS', 'EVENTS', 'RESOLVED', 'INCIDENTS.EVENTS.RESOLVED', 5, 'L2_1', 'INC-EV-RES-O5', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Surface learning and follow-up signals from resolved incidents.

What it shows:
- Policy change suggested (yes/no)
- Recurrence risk (low/medium/high)
- Similar past incidents detected
- Escalate to: Policies / Humans / Engineering backlog

What it explicitly does NOT show:
- No policy edits
- No approvals
- No automated actions', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.423787+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('LOG-REC-AUD-O1', 'LOGS', 'RECORDS', 'AUDIT', 'LOGS.RECORDS.AUDIT', 1, 'L2_1', 'LOG-REC-AUD-O1', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show identity and authentication lifecycle — who accessed and how.', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.427515+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('LOG-REC-AUD-O2', 'LOGS', 'RECORDS', 'AUDIT', 'LOGS.RECORDS.AUDIT', 2, 'L2_1', 'LOG-REC-AUD-O2', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show authorization and access decisions — what each identity was allowed to do.', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.431541+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('LOG-REC-AUD-O3', 'LOGS', 'RECORDS', 'AUDIT', 'LOGS.RECORDS.AUDIT', 3, 'L2_1', 'LOG-REC-AUD-O3', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show trace and log access audit — who viewed, exported, or modified observability data.', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.435753+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('LOG-REC-AUD-O4', 'LOGS', 'RECORDS', 'AUDIT', 'LOGS.RECORDS.AUDIT', 4, 'L2_1', 'LOG-REC-AUD-O4', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show integrity and tamper detection — was any audit data altered or compromised.', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.439262+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('LOG-REC-AUD-O5', 'LOGS', 'RECORDS', 'AUDIT', 'LOGS.RECORDS.AUDIT', 5, 'L2_1', 'LOG-REC-AUD-O5', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show compliance and export record — what audit evidence was produced, shared, or certified.', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.443113+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('LOG-REC-LLM-O1', 'LOGS', 'RECORDS', 'LLM_RUNS', 'LOGS.RECORDS.LLM_RUNS', 1, 'L2_1', 'LOG-REC-LLM-O1', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show the run log envelope — canonical immutable record per run.', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.446738+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('LOG-REC-LLM-O2', 'LOGS', 'RECORDS', 'LLM_RUNS', 'LOGS.RECORDS.LLM_RUNS', 2, 'L2_1', 'LOG-REC-LLM-O2', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show execution trace — step-by-step progression of the run.', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.450459+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('LOG-REC-LLM-O3', 'LOGS', 'RECORDS', 'LLM_RUNS', 'LOGS.RECORDS.LLM_RUNS', 3, 'L2_1', 'LOG-REC-LLM-O3', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show threshold and policy interaction trace — governance footprint per run.', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.453882+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('LOG-REC-LLM-O4', 'LOGS', 'RECORDS', 'LLM_RUNS', 'LOGS.RECORDS.LLM_RUNS', 4, 'L2_1', 'LOG-REC-LLM-O4', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show 60-second incident replay window — what happened around the inflection point.', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.457526+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('LOG-REC-LLM-O5', 'LOGS', 'RECORDS', 'LLM_RUNS', 'LOGS.RECORDS.LLM_RUNS', 5, 'L2_1', 'LOG-REC-LLM-O5', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show audit and export package — legally defensible evidence bundle.', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.461349+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('LOG-REC-SYS-O1', 'LOGS', 'RECORDS', 'SYSTEM_LOGS', 'LOGS.RECORDS.SYSTEM_LOGS', 1, 'L2_1', 'LOG-REC-SYS-O1', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show environment snapshot — baseline state at run start.', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.465436+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('LOG-REC-SYS-O2', 'LOGS', 'RECORDS', 'SYSTEM_LOGS', 'LOGS.RECORDS.SYSTEM_LOGS', 2, 'L2_1', 'LOG-REC-SYS-O2', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show network and bandwidth telemetry — connectivity health during execution.', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.469436+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('LOG-REC-SYS-O3', 'LOGS', 'RECORDS', 'SYSTEM_LOGS', 'LOGS.RECORDS.SYSTEM_LOGS', 3, 'L2_1', 'LOG-REC-SYS-O3', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show infra interrupts and degradation events — what infra did to the run.', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.473917+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('LOG-REC-SYS-O4', 'LOGS', 'RECORDS', 'SYSTEM_LOGS', 'LOGS.RECORDS.SYSTEM_LOGS', 4, 'L2_1', 'LOG-REC-SYS-O4', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show run-aligned infra replay window — infra state at moment of anomaly.', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.477589+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('LOG-REC-SYS-O5', 'LOGS', 'RECORDS', 'SYSTEM_LOGS', 'LOGS.RECORDS.SYSTEM_LOGS', 5, 'L2_1', 'LOG-REC-SYS-O5', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show infra audit and attribution record — who is responsible.', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.481544+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('OVR-SUM-CI-O1', 'OVERVIEW', 'SUMMARY', 'COST_INTELLIGENCE', 'OVERVIEW.SUMMARY.COST_INTELLIGENCE', 1, 'L2_1', 'OVR-SUM-CI-O1', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Give an immediate snapshot of current cost posture without requiring
navigation into Activity or Policies.

What it shows:
- Current spend rate (aggregate)
- Trend indicator (up / flat / down)
- Primary cost driver (top contributor category)

What it explicitly does NOT show:
- No historical charts
- No per-run breakdown
- No policy configuration
- No thresholds or limits editing
- No predictions', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.486190+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('OVR-SUM-CI-O2', 'OVERVIEW', 'SUMMARY', 'COST_INTELLIGENCE', 'OVERVIEW.SUMMARY.COST_INTELLIGENCE', 2, 'L2_1', 'OVR-SUM-CI-O2', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show how total cost is distributed across primary drivers so the user
understands what is consuming money at a glance.

What it shows:
- Cost split by driver category (e.g., model, project, policy bucket)
- Percentage contribution per driver
- Top 1–3 contributors only

What it explicitly does NOT show:
- No per-run or per-request logs
- No time-series charts
- No configuration controls
- No thresholds or alerts
- No forecasts', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.491000+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('OVR-SUM-CI-O3', 'OVERVIEW', 'SUMMARY', 'COST_INTELLIGENCE', 'OVERVIEW.SUMMARY.COST_INTELLIGENCE', 3, 'L2_1', 'OVR-SUM-CI-O3', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Provide a short-horizon view of cost movement so the user can tell
whether spend is trending up, flat, or down.

What it shows:
- Aggregate cost trend over a short window (e.g., last N periods)
- Directional indicator only (↑ ↓ →)
- Relative change, not absolute detail

What it explicitly does NOT show:
- No driver-level breakdown
- No per-run or per-model detail
- No long-term forecasting
- No alerts or policy thresholds
- No controls', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.495156+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('OVR-SUM-CI-O4', 'OVERVIEW', 'SUMMARY', 'COST_INTELLIGENCE', 'OVERVIEW.SUMMARY.COST_INTELLIGENCE', 4, 'L2_1', 'OVR-SUM-CI-O4', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Provide a near-term cost trajectory based on recent behavior,
so the user can anticipate direction without detailed forecasting.

What it shows:
- Near-term projected direction (increase / stable / decrease)
- Confidence band or qualitative confidence (low / medium / high)
- Projection based on recent trend only

What it explicitly does NOT show:
- No long-range forecasts
- No scenario modeling
- No "what-if" controls
- No policy or alert thresholds
- No per-run or per-model detail', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.499954+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('OVR-SUM-DC-O1', 'OVERVIEW', 'SUMMARY', 'DECISIONS', 'OVERVIEW.SUMMARY.DECISIONS', 1, 'L2_1', 'OVR-SUM-DC-O1', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Surface decisions that require explicit human approval or rejection,
without forcing navigation into policies or incidents.

What it shows:
- Count of pending policy approvals
- Count of blocked runs awaiting human override
- Count of escalations requiring approval/reject decision
- Oldest pending decision age (time-based pressure)

What it explicitly does NOT show:
- No execution buttons
- No approval/reject actions
- No policy details
- No explanations or rationale
- No historical decisions', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.504761+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('OVR-SUM-DC-O2', 'OVERVIEW', 'SUMMARY', 'DECISIONS', 'OVERVIEW.SUMMARY.DECISIONS', 2, 'L2_1', 'OVR-SUM-DC-O2', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Provide short-term feedback on recent human decisions so the user
can confirm impact without drilling into other domains.

What it shows:
- Last N decisions taken (approve / reject / override)
- Resulting outcome state (resolved / still pending / failed)
- Time-to-effect (decision → outcome)

What it explicitly does NOT show:
- No ability to re-open or change decisions
- No policy configuration
- No incident details
- No execution controls
- No historical archive beyond recent window', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.509420+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('OVR-SUM-DC-O3', 'OVERVIEW', 'SUMMARY', 'DECISIONS', 'OVERVIEW.SUMMARY.DECISIONS', 3, 'L2_1', 'OVR-SUM-DC-O3', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Identify recurrent human decisions that should become policy —
where humans are acting as rate limiters instead of governance.

What it shows:
- Repeated decision patterns (same condition, same outcome, same actors)
- Frequency × avoided effort × avoided cost ranking
- Cost-overrun overrides approved repeatedly
- Manual allowlist decisions trending up
- Direct links to Policies → Drafts and Limits → Thresholds (pre-filled context)

What it explicitly does NOT show:
- No execution or approval actions
- No policy editing
- No incident details', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.514313+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('OVR-SUM-DC-O4', 'OVERVIEW', 'SUMMARY', 'DECISIONS', 'OVERVIEW.SUMMARY.DECISIONS', 4, 'L2_1', 'OVR-SUM-DC-O4', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show decisions avoided by governance — where the system already removed
decision load successfully, reinforcing trust in automation.

What it shows:
- Auto-prevent counts (decisions not escalated)
- Avoidance attribution: by policy, by limit, by automation
- Trust progression tracking
- Policies that avoided human interventions
- Agents/LLMs now fully governed (no manual touch for N days)

What it explicitly does NOT show:
- No execution controls
- No policy editing
- No approval actions', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.519020+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('OVR-SUM-HL-O1', 'OVERVIEW', 'SUMMARY', 'HIGHLIGHTS', 'OVERVIEW.SUMMARY.HIGHLIGHTS', 1, 'L2_1', 'OVR-SUM-HL-O1', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Provide a single, glanceable snapshot of current system activity so the user
can immediately understand whether the system is calm, active, or stressed.

What it shows:
- Count of currently running LLM executions
- Count of executions completed in the last window (e.g. 15 min)
- Count of executions currently in near-threshold or risk state
- Timestamp of last successful observation update

What it explicitly does NOT show:
- No logs
- No configuration
- No historical charts
- No per-run drilldown
- No policy or cost breakdown', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.523439+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('OVR-SUM-HL-O2', 'OVERVIEW', 'SUMMARY', 'HIGHLIGHTS', 'OVERVIEW.SUMMARY.HIGHLIGHTS', 2, 'L2_1', 'OVR-SUM-HL-O2', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Surface non-ignorable signals that require human attention,
without requiring navigation into domains.

What it shows:
- Count of active incidents (any severity)
- Count of runs currently in near-threshold state
- Count of policy violations prevented by governance
- Highest severity level currently present (if any)

What it explicitly does NOT show:
- No historical incidents
- No explanations
- No root cause
- No controls or actions
- No links or drilldowns', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.528192+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('OVR-SUM-HL-O4', 'OVERVIEW', 'SUMMARY', 'HIGHLIGHTS', 'OVERVIEW.SUMMARY.HIGHLIGHTS', 4, 'L2_1', 'OVR-SUM-HL-O4', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Expose rare but high-impact clusters — low-frequency, high-cost events
invisible in averages.

What it shows:
- Severity-weighted cost/time loss ranking
- Long-tail outliers (top 1-2%)
- Extreme run duration/cost spikes
- Overridden violations with high blast radius
- Impact-ranked clusters by LLM, agent, human, policy

What it explicitly does NOT show:
- No count-based rankings
- No actions or controls
- No policy editing
- No drill-down beyond identification', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.532847+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-GOV-ACT-O1', 'POLICIES', 'GOVERNANCE', 'ACTIVE', 'POLICIES.GOVERNANCE.ACTIVE', 1, 'L2_1', 'POL-GOV-ACT-O1', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show the complete inventory of currently active (enabled + enforced) policies.

What it shows:
- List/count of all active policies
- Grouped by policy type (cost, rate, approval, safety, escalation)
- Grouped by scope (global / domain / agent / LLM / user)
- Grouped by enforcement mode (hard block / soft block / require approval)

What it explicitly does NOT show:
- No impact metrics
- No drafts or proposals
- No historical policies', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.537270+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-GOV-ACT-O2', 'POLICIES', 'GOVERNANCE', 'ACTIVE', 'POLICIES.GOVERNANCE.ACTIVE', 2, 'L2_1', 'POL-GOV-ACT-O2', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show enforcement effectiveness — are policies actually doing anything.

What it shows:
- Per policy: times evaluated, triggered, enforced, bypassed
- Dead policies (never triggered)
- Over-firing policies
- Policies with zero real-world impact

What it explicitly does NOT show:
- No policy editing
- No recommendations
- No draft proposals', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.541505+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-GOV-ACT-O3', 'POLICIES', 'GOVERNANCE', 'ACTIVE', 'POLICIES.GOVERNANCE.ACTIVE', 3, 'L2_1', 'POL-GOV-ACT-O3', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show incident prevention and regulation impact — what policies are preventing or shaping.

What it shows:
- Incidents prevented entirely
- Incidents soft-regulated (slowed, capped, gated)
- Incidents escalated to human decision
- Policy → incident class mapping
- Evidence-backed only (claimed prevention without observation ignored)

What it explicitly does NOT show:
- No policy changes
- No enforcement controls
- No draft proposals', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.546090+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-GOV-ACT-O4', 'POLICIES', 'GOVERNANCE', 'ACTIVE', 'POLICIES.GOVERNANCE.ACTIVE', 4, 'L2_1', 'POL-GOV-ACT-O4', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show cost and performance side effects — what governance is costing us.

What it shows:
- Cost saved by enforcement
- Cost introduced by enforcement (latency, friction, rejects)
- Trade-offs: safety vs throughput, cost vs success rate, automation vs human load
- Numbers only, no value judgment

What it explicitly does NOT show:
- No policy tuning controls
- No recommendations
- No forecasts', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.550311+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-GOV-ACT-O5', 'POLICIES', 'GOVERNANCE', 'ACTIVE', 'POLICIES.GOVERNANCE.ACTIVE', 5, 'L2_1', 'POL-GOV-ACT-O5', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Surface governance stress and decision signals — which policies need review.

What it shows:
- Policies with frequent overrides
- Policies frequently hit near thresholds
- Policies causing cascading blocks
- Policies correlated with user/system friction
- Candidates for adjustment, split, promotion, or decommissioning

What it explicitly does NOT show:
- No policy state changes
- No disabling
- No auto-rewriting', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.554868+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-GOV-DFT-O1', 'POLICIES', 'GOVERNANCE', 'LESSONS', 'POLICIES.GOVERNANCE.LESSONS', 1, 'L2_1', 'POL-GOV-DFT-O1', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show observed governance signals — raw lessons from system behavior.

What it shows:
- Critical failures, critical successes
- Near-threshold runs, frequent temporal breaks
- Cost overruns, cost savers
- High override frequency
- Grouped by LLM, Agent, Human actor, Policy gap type

What it explicitly does NOT show:
- No synthesis or recommendations
- No draft policies yet
- No actions', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.559543+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-GOV-DFT-O2', 'POLICIES', 'GOVERNANCE', 'LESSONS', 'POLICIES.GOVERNANCE.LESSONS', 2, 'L2_1', 'POL-GOV-DFT-O2', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show draft policy candidates — machine-proposed governance rules.

What it shows:
- Auto-generated draft policies
- Each draft linked to evidence (incident IDs, run IDs)
- Observed benefit or risk per draft
- Drafts are non-executable

What it explicitly does NOT show:
- No enforcement
- No activation
- No human bypass', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.564320+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-GOV-DFT-O3', 'POLICIES', 'GOVERNANCE', 'LESSONS', 'POLICIES.GOVERNANCE.LESSONS', 3, 'L2_1', 'POL-GOV-DFT-O3', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show draft justification and impact preview — why each draft exists.

What it shows:
- Problem statement (derived from evidence)
- Expected effect: incidents prevented, costs saved, failures reduced
- Known risks: false positives, reduced throughput, human friction
- Preview based on historical/simulated data only

What it explicitly does NOT show:
- No future predictions beyond evidence
- No black-box proposals
- No enforcement', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.568217+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-GOV-DFT-O4', 'POLICIES', 'GOVERNANCE', 'LESSONS', 'POLICIES.GOVERNANCE.LESSONS', 4, 'L2_1', 'POL-GOV-DFT-O4', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Provide approval and blast radius control for draft policies.

What it shows:
- Scope selection: single LLM, group of LLMs, agent class, human role
- Blast radius: pilot (1 entity), limited (subset), global
- Enforcement mode: observe-only, soft gate, hard block
- Explicit choices only, no defaults

What it explicitly does NOT show:
- No auto-activation
- No silent inheritance', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.571640+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-GOV-DFT-O5', 'POLICIES', 'GOVERNANCE', 'LESSONS', 'POLICIES.GOVERNANCE.LESSONS', 5, 'L2_1', 'POL-GOV-DFT-O5', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show decision outcomes and lifecycle routing after human decides.

What it shows:
- Approved: draft → active policy, moves to Governance → Active
- Rejected: draft archived with reason, signal suppressed
- Deferred: parked for more data, re-evaluated later
- Every draft must end in one of these three states

What it explicitly does NOT show:
- No silent expiration
- No auto-decisions', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.575517+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-GOV-LES-O1', 'POLICIES', 'GOVERNANCE', 'LESSONS', 'POLICIES.GOVERNANCE.LESSONS', 1, 'L2_1', 'POL-GOV-LES-O1', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show lessons learned from system behavior — observed patterns that inform governance.

What it shows:
- Critical failures and their root causes
- Near-threshold runs and recurring patterns
- Cost overruns and cost-saving behaviors
- High override frequency signals
- Grouped by: LLM, Agent, Human actor, Policy gap type
- Evidence links: incident IDs, run IDs, trace IDs

What it explicitly does NOT show:
- No recommendations or synthesis
- No draft policies
- No actions or controls', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.579069+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-GOV-LES-O2', 'POLICIES', 'GOVERNANCE', 'LESSONS', 'POLICIES.GOVERNANCE.LESSONS', 2, 'L2_1', 'POL-GOV-LES-O2', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show draft policy proposals derived from lessons — awaiting human approval or rejection.

What it shows:
- Machine-proposed policy drafts based on observed lessons
- Each proposal linked to source lessons (evidence chain)
- Expected benefit: incidents prevented, costs saved
- Known risks: false positives, friction
- Proposal status: pending, approved, rejected, deferred

What it explicitly does NOT show:
- No auto-activation
- No enforcement
- No silent decisions', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.582103+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-GOV-LES-O3', 'POLICIES', 'GOVERNANCE', 'LESSONS', 'POLICIES.GOVERNANCE.LESSONS', 3, 'L2_1', 'POL-GOV-LES-O3', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, TRUE, NULL, FALSE, FALSE, NULL, TRUE, ARRAY[]::text[], TRUE, ARRAY[]::text[], 'Convert a lesson learned into a draft policy rule.
This action converts observed patterns into actionable policy suggestions.', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.586268+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-GOV-LES-O4', 'POLICIES', 'GOVERNANCE', 'LESSONS', 'POLICIES.GOVERNANCE.LESSONS', 4, 'L2_1', 'POL-GOV-LES-O4', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, TRUE, NULL, FALSE, FALSE, NULL, TRUE, ARRAY[]::text[], TRUE, ARRAY[]::text[], 'Dismiss or defer a lesson learned.
Mark lessons as not actionable or defer for future consideration.', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.590341+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-GOV-LES-O5', 'POLICIES', 'GOVERNANCE', 'LESSONS', 'POLICIES.GOVERNANCE.LESSONS', 5, 'L2_1', 'POL-GOV-LES-O5', NULL, TRUE, FALSE, 'INLINE', TRUE, TRUE, FALSE, NULL, TRUE, TRUE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show lessons history and statistics.
Historical view of all lessons learned, conversions, and dismissals.', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.594619+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-GOV-LIB-O1', 'POLICIES', 'GOVERNANCE', 'POLICY_LIBRARY', 'POLICIES.GOVERNANCE.POLICY_LIBRARY', 1, 'L2_1', 'POL-GOV-LIB-O1', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show the global policy catalog — all policies available from Agenticverz backend.

What it shows:
- Complete list of global policies (cost controls, rate limits, safety guards, etc.)
- Metadata: policy ID, category, default enforcement mode, version, maintainer
- Read-only discovery surface

What it explicitly does NOT show:
- No adoption controls
- No filtering by current usage
- No enforcement', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.599266+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-GOV-LIB-O2', 'POLICIES', 'GOVERNANCE', 'POLICY_LIBRARY', 'POLICIES.GOVERNANCE.POLICY_LIBRARY', 2, 'L2_1', 'POL-GOV-LIB-O2', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show applicability and compatibility matrix — where each policy can be applied.

What it shows:
- Supported targets: LLMs, agents, human executors, run types
- Org-wide applicability
- Mutually exclusive policies, required prerequisites, known incompatibilities

What it explicitly does NOT show:
- No human override at this stage
- No adoption actions', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.603504+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-GOV-LIB-O3', 'POLICIES', 'GOVERNANCE', 'POLICY_LIBRARY', 'POLICIES.GOVERNANCE.POLICY_LIBRARY', 3, 'L2_1', 'POL-GOV-LIB-O3', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show adoption status and current usage — how and where each policy is used.

What it shows:
- Adoption state: not used, used in limited scope, used globally
- Active scopes: specific LLMs, agents, humans, all runs
- Last modified, who approved
- Reflects actual enforcement, not intent

What it explicitly does NOT show:
- No adoption controls
- No proposed changes', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.608120+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-GOV-LIB-O4', 'POLICIES', 'GOVERNANCE', 'POLICY_LIBRARY', 'POLICIES.GOVERNANCE.POLICY_LIBRARY', 4, 'L2_1', 'POL-GOV-LIB-O4', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Provide attach/detach policy controls — human action to adopt or remove policies.

What it shows:
- Attach policy to: single LLM, agent group, human role, all runs
- Detach policy from any scope
- Required inputs: scope selection, enforcement mode, justification (mandatory)
- Every change is auditable

What it explicitly does NOT show:
- No default scope
- No silent inheritance', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.612807+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-GOV-LIB-O5', 'POLICIES', 'GOVERNANCE', 'POLICY_LIBRARY', 'POLICIES.GOVERNANCE.POLICY_LIBRARY', 5, 'L2_1', 'POL-GOV-LIB-O5', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show change impact and audit trail for policy adoption changes.

What it shows:
- Impact preview based on historical runs
- Expected prevented incidents, cost savings
- Known risks
- Audit record: policy, scope before/after, approved by, timestamp
- Rollback option (first-class)

What it explicitly does NOT show:
- No auto-rollback
- No silent changes', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.617100+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-LIM-THR-O1', 'POLICIES', 'LIMITS', 'THRESHOLDS', 'POLICIES.LIMITS.THRESHOLDS', 1, 'L2_1', 'POL-LIM-THR-O1', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show limit policy definition matrix — what limits exist and where they apply.

What it shows:
- Policy ID/Name, limit type (cost/token/rate/time)
- Scope: org/project, LLM(s), agent(s), human executor(s)
- Blast radius: single, group, global
- Status: active, shadow (observe only), disabled

What it explicitly does NOT show:
- No usage metrics
- No violation data', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.621222+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-LIM-THR-O2', 'POLICIES', 'LIMITS', 'THRESHOLDS', 'POLICIES.LIMITS.THRESHOLDS', 2, 'L2_1', 'POL-LIM-THR-O2', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Provide threshold configuration and fine-tuning controls.

What it shows:
- Per policy: hard limit (enforced), soft limit (warn/flag)
- Grace window: time-based, count-based
- Cool-down/reset logic
- Dimensions: by LLM, by agent class, by human role, by time
- Live preview: "At current usage, this would have blocked X runs yesterday"

What it explicitly does NOT show:
- No usage analytics
- No violation history', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.625072+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-LIM-THR-O3', 'POLICIES', 'LIMITS', 'THRESHOLDS', 'POLICIES.LIMITS.THRESHOLDS', 3, 'L2_1', 'POL-LIM-THR-O3', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Set execution thresholds that drive LLM run governance signals.

This is the authoritative input surface for customer-controlled limits.
These params feed the LLMRunThresholdResolver which evaluates runs.

What it shows:
- Max Execution Time (ms): 1000-300000, default 60000
- Max Tokens: 256-200000, default 8192
- Max Cost (USD): 0.01-100.00, default 1.00
- Signal on Failure: toggle, default ON
- Effective defaults shown when empty (grey "Inherited default")
- Yellow badge: "Overrides default"
- Red badge: "Invalid / rejected"

What it enables:
- ACT-LLM-LIVE-O2: Surface live runs exceeding expected execution time
- ACT-LLM-COMP-O3: Expose completed runs that ended in failure

What it explicitly does NOT show:
- No usage analytics
- No violation history
- No live run data', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.629464+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-LIM-THR-O4', 'POLICIES', 'LIMITS', 'THRESHOLDS', 'POLICIES.LIMITS.THRESHOLDS', 4, 'L2_1', 'POL-LIM-THR-O4', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Provide experimentation and what-if simulation capabilities.

What it shows:
- Clone existing policy, modify thresholds
- Run simulation against last 7/30/90 days
- Compare: blocks vs allows, cost saved vs runs blocked
- Comparison view: current policy vs candidate policy
- Experiments do not affect live runs, must be named and scoped

What it explicitly does NOT show:
- No live enforcement
- No production impact', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.633204+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-LIM-THR-O5', 'POLICIES', 'LIMITS', 'THRESHOLDS', 'POLICIES.LIMITS.THRESHOLDS', 5, 'L2_1', 'POL-LIM-THR-O5', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Provide approval, audit, and activation workflow for threshold changes.

What it shows:
- Workflow: draft → review → active
- Optional multi-approver, activation notes required
- Audit log: threshold changes, scope changes, rollbacks, overrides
- Post-activation hooks: auto-link to Usage → O3, Governance → Active

What it explicitly does NOT show:
- No silent activation
- No hidden changes', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.636580+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-LIM-VIO-O1', 'POLICIES', 'LIMITS', 'VIOLATIONS', 'POLICIES.LIMITS.VIOLATIONS', 1, 'L2_1', 'POL-LIM-VIO-O1', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show the violation ledger — immutable record of every limit violation.

What it shows:
- Run ID, timestamp, policy ID, limit type
- Violation mode: hard terminate, temporal fracture, human override
- Actor at violation: LLM, agent, human
- Enforcement state: blocked, allowed (override)
- One row per violation event, overrides do not erase violation

What it explicitly does NOT show:
- No configuration controls
- No policy editing', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.640855+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-LIM-VIO-O2', 'POLICIES', 'LIMITS', 'VIOLATIONS', 'POLICIES.LIMITS.VIOLATIONS', 2, 'L2_1', 'POL-LIM-VIO-O2', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show violation classification and attribution — why and who.

What it shows:
- Aggregations: by limit type, by LLM, by agent, by human, by policy
- Primary trigger: cost overrun, token spike, time breach
- Secondary factor: retry loop, fan-out, poor prompt, downstream latency

What it explicitly does NOT show:
- No policy controls
- No excuses', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.645534+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-LIM-VIO-O3', 'POLICIES', 'LIMITS', 'VIOLATIONS', 'POLICIES.LIMITS.VIOLATIONS', 3, 'L2_1', 'POL-LIM-VIO-O3', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show override and fracture analysis — which violations were ignored or softened.

What it shows:
- Override count, override rate (% of violations)
- Fracture duration (avg/p95), re-entry success rate
- Breakdown: by role, by policy, by urgency tag
- Flags: repeated overrides on same policy, overrides followed by failure

What it explicitly does NOT show:
- No override controls
- No policy editing', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.650085+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-LIM-VIO-O4', 'POLICIES', 'LIMITS', 'VIOLATIONS', 'POLICIES.LIMITS.VIOLATIONS', 4, 'L2_1', 'POL-LIM-VIO-O4', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show loss and impact quantification — what violations actually cost.

What it shows:
- Cost lost, time lost (compute + human wait), productivity lost
- Cost saved (from enforced blocks)
- Views: by LLM, by agent, by human, by policy, by time window
- Saved and lost shown together (no vanity metrics)

What it explicitly does NOT show:
- No policy controls
- No threshold editing', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.654665+00:00', 'INFO');
INSERT INTO aurora_l2_intent_store (panel_id, domain, subdomain, topic, topic_id, order_level, action_layer, panel_name, ranking_dimension, visible_by_default, nav_required, expansion_mode, read_enabled, download_enabled, write_enabled, write_action, replay_enabled, filtering_enabled, selection_mode, activate_enabled, activate_actions, confirmation_required, control_set, notes, review_status, migrated_from, migration_date, compiled_at, binding_status) VALUES ('POL-LIM-VIO-O5', 'POLICIES', 'LIMITS', 'VIOLATIONS', 'POLICIES.LIMITS.VIOLATIONS', 5, 'L2_1', 'POL-LIM-VIO-O5', NULL, TRUE, FALSE, 'INLINE', TRUE, FALSE, FALSE, NULL, TRUE, FALSE, NULL, FALSE, ARRAY[]::text[], FALSE, ARRAY[]::text[], 'Show escalation, evidence, and governance hooks for violations requiring action.

What it shows:
- Triggers: repeated violations, high override density, high loss concentration
- Links to: Governance → Drafts (revision), Governance → Active (review)
- Export: audit logs, evidence bundles (SOC2/internal review)
- This surface escalates, not fixes

What it explicitly does NOT show:
- No editing limits
- No approvals', 'UNREVIEWED', 'CSV', '', '2026-01-19T18:29:59.658993+00:00', 'INFO');

COMMIT;
