# CUS Domain Ledger: activity

**Generated:** 2026-02-21T07:54:56.667404+00:00
**Total endpoints:** 21
**Unique method+path:** 20

| Method | Path | Operation | Summary |
|--------|------|-----------|---------|
| GET | /hoc/api/cus/activity/attention-queue | get_attention_queue | Get attention queue (SIG-O5). READ-ONLY from v_runs_o2. |
| GET | /hoc/api/cus/activity/completed | list_completed_runs | List COMPLETED runs with policy context. |
| GET | /hoc/api/cus/activity/cost-analysis | get_cost_analysis | Analyze cost anomalies (SIG-O4). READ-ONLY from runs table. |
| GET | /hoc/api/cus/activity/live | list_live_runs | List LIVE runs with policy context. |
| GET | /hoc/api/cus/activity/metrics | get_activity_metrics | Get aggregated activity metrics (V2). |
| GET | /hoc/api/cus/activity/patterns | get_patterns | Detect instability patterns (SIG-O3). READ-ONLY from aos_tra |
| GET | /hoc/api/cus/activity/risk-signals | get_risk_signals | Returns aggregated risk signal counts. |
| GET | /hoc/api/cus/activity/runs | list_runs | List runs with unified query filters. READ-ONLY from v_runs_ |
| GET | /hoc/api/cus/activity/runs | list_runs_facade |  |
| GET | /hoc/api/cus/activity/runs/by-dimension | get_runs_by_dimension | [INTERNAL] Get runs grouped by dimension with optional state |
| GET | /hoc/api/cus/activity/runs/completed/by-dimension | get_completed_runs_by_dimension | Get COMPLETED runs grouped by dimension. State=COMPLETED is  |
| GET | /hoc/api/cus/activity/runs/live/by-dimension | get_live_runs_by_dimension | Get LIVE runs grouped by dimension. State=LIVE is hardcoded. |
| GET | /hoc/api/cus/activity/runs/{run_id} | get_run_detail | Get run detail (O3). Tenant isolation enforced. |
| GET | /hoc/api/cus/activity/runs/{run_id}/evidence | get_run_evidence | Get run evidence (O4). Preflight console only. |
| GET | /hoc/api/cus/activity/runs/{run_id}/proof | get_run_proof | Get run proof (O5). Preflight console only. |
| GET | /hoc/api/cus/activity/signals | list_signals | List activity signals (V2 projection). |
| POST | /hoc/api/cus/activity/signals/{signal_fingerprint}/ack | acknowledge_signal | Acknowledge a signal. |
| POST | /hoc/api/cus/activity/signals/{signal_fingerprint}/suppress | suppress_signal | Suppress a signal temporarily. |
| GET | /hoc/api/cus/activity/summary/by-status | get_summary_by_status | Get run summary by status (COMP-O3). READ-ONLY from v_runs_o |
| GET | /hoc/api/cus/activity/threshold-signals | get_threshold_signals | Get threshold proximity signals (V2). |
| GET | /hoc/api/cus/runs | list_runs | List runs for the current tenant. |
