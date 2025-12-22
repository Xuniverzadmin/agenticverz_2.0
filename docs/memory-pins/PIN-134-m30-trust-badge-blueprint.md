# PIN-134: M30 Trust Badge Blueprint

**Status:** SPECIFICATION
**Category:** Milestone / Enterprise / Trust & Compliance
**Created:** 2025-12-22
**Related PINs:** PIN-128 (Master Plan), PIN-133 (M29 Quality Score), PIN-132 (M28 Unified Console)

---

## Executive Summary

M30 adds **Customer-Facing Trust Badges** - embeddable widgets and verification pages that showcase AI governance metrics to end-users. This is a **CONDITIONAL** milestone for enterprise upsells requiring public proof of AI safety.

**Key Deliverables:**
1. Embeddable Trust Badge Widget (JavaScript snippet)
2. Public Verification Page (verifiable certificate)
3. Trust Report Generator (PDF/HTML)
4. Trust Score Aggregator (combines all pillars)
5. Badge Configuration Console

**Duration:** 1 week
**Risk:** LOW (aggregation of existing data)
**Dependencies:** M28 Unified Console, M29 Quality Score (optional), M22-M27 pillars

---

## Architecture Overview

```
                      TRUST BADGE SYSTEM
                      ==================

   ┌─────────────────────────────────────────────────────────────┐
   │                    DATA AGGREGATION LAYER                   │
   │                                                             │
   │   M26 Cost      M22/M23      M29 Quality    M17/M18        │
   │   Intelligence   Guard       Score          CARE           │
   │       │            │            │              │            │
   │       ▼            ▼            ▼              ▼            │
   │   ┌─────────────────────────────────────────────────┐      │
   │   │           TRUST SCORE AGGREGATOR               │      │
   │   │                                                 │      │
   │   │   Cost       Safety      Accuracy    Response   │      │
   │   │   Efficiency Incidents   Score       Time       │      │
   │   │   ────────   ─────────   ────────    ────────   │      │
   │   │   $0.08/int  0 in 30d    94.2%       <2s avg    │      │
   │   └─────────────────────────────────────────────────┘      │
   └─────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
   ┌─────────────────────────────────────────────────────────────┐
   │                    TRUST BADGE SERVICE                      │
   │                                                             │
   │   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  │
   │   │ Badge Widget  │  │ Verification  │  │ Trust Report  │  │
   │   │ (Embeddable)  │  │ Page (Public) │  │ Generator     │  │
   │   └───────────────┘  └───────────────┘  └───────────────┘  │
   │                                                             │
   │   ┌─────────────────────────────────────────────────────┐  │
   │   │              CERTIFICATE SERVICE (M23)              │  │
   │   │              Cryptographic Signing                  │  │
   │   └─────────────────────────────────────────────────────┘  │
   └─────────────────────────────────────────────────────────────┘
                             │
                             ▼
   ┌─────────────────────────────────────────────────────────────┐
   │                    PUBLIC ENDPOINTS                         │
   │                                                             │
   │   GET /trust/badge/{tenant_id}           → SVG/HTML badge   │
   │   GET /trust/verify/{certificate_id}     → Verification UI  │
   │   GET /trust/report/{tenant_id}          → PDF/HTML report  │
   │   GET /trust/metrics/{tenant_id}         → JSON metrics     │
   │                                                             │
   └─────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### 1. Trust Score Aggregator

#### Score Computation

```python
# backend/app/trust/aggregator.py

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from enum import Enum


class TrustLevel(str, Enum):
    """Trust badge levels based on aggregate score."""
    PLATINUM = "platinum"  # 95%+ on all metrics
    GOLD = "gold"          # 85%+ on all metrics
    SILVER = "silver"      # 75%+ on all metrics
    BRONZE = "bronze"      # 60%+ on all metrics
    UNRATED = "unrated"    # Insufficient data


@dataclass
class TrustMetrics:
    """Aggregated trust metrics from all pillars."""

    tenant_id: str
    period_days: int = 30

    # Cost Pillar (M26)
    avg_cost_per_interaction: float = 0.0
    cost_budget_utilization: float = 0.0  # % of budget used
    cost_anomalies_detected: int = 0

    # Safety Pillar (M22/M23)
    safety_incidents: int = 0
    incidents_resolved: int = 0
    avg_incident_resolution_time_hours: float = 0.0
    killswitch_activations: int = 0

    # Quality Pillar (M29) - Optional
    accuracy_score: Optional[float] = None
    relevance_score: Optional[float] = None
    safety_score: Optional[float] = None
    hallucinations_detected: int = 0

    # Performance Pillar
    avg_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    uptime_percentage: float = 100.0
    total_requests: int = 0
    successful_requests: int = 0

    # Governance Pillar (M19)
    policies_active: int = 0
    policy_violations: int = 0
    policy_compliance_rate: float = 100.0

    # Computed at aggregation time
    computed_at: datetime = None

    def __post_init__(self):
        if self.computed_at is None:
            self.computed_at = datetime.now(timezone.utc)


class TrustScoreAggregator:
    """Aggregates metrics from all pillars into trust score."""

    # Weights for overall trust score
    WEIGHTS = {
        "safety": 0.35,       # Safety is most important
        "quality": 0.25,      # Accuracy matters
        "performance": 0.20,  # Speed matters
        "governance": 0.15,   # Policy compliance
        "cost": 0.05,         # Cost efficiency (minor weight)
    }

    async def compute_trust_metrics(
        self,
        tenant_id: str,
        period_days: int = 30,
    ) -> TrustMetrics:
        """Aggregate metrics from all pillars."""

        metrics = TrustMetrics(
            tenant_id=tenant_id,
            period_days=period_days,
        )

        # Fetch from Cost pillar (M26)
        cost_data = await self._get_cost_metrics(tenant_id, period_days)
        metrics.avg_cost_per_interaction = cost_data.get("avg_cost", 0.0)
        metrics.cost_budget_utilization = cost_data.get("budget_util", 0.0)
        metrics.cost_anomalies_detected = cost_data.get("anomalies", 0)

        # Fetch from Safety pillar (M22/M23)
        safety_data = await self._get_safety_metrics(tenant_id, period_days)
        metrics.safety_incidents = safety_data.get("incidents", 0)
        metrics.incidents_resolved = safety_data.get("resolved", 0)
        metrics.killswitch_activations = safety_data.get("killswitch", 0)

        # Fetch from Quality pillar (M29) - optional
        quality_data = await self._get_quality_metrics(tenant_id, period_days)
        if quality_data:
            metrics.accuracy_score = quality_data.get("accuracy")
            metrics.relevance_score = quality_data.get("relevance")
            metrics.safety_score = quality_data.get("safety")
            metrics.hallucinations_detected = quality_data.get("hallucinations", 0)

        # Fetch Performance metrics
        perf_data = await self._get_performance_metrics(tenant_id, period_days)
        metrics.avg_response_time_ms = perf_data.get("avg_latency", 0.0)
        metrics.p99_response_time_ms = perf_data.get("p99_latency", 0.0)
        metrics.uptime_percentage = perf_data.get("uptime", 100.0)
        metrics.total_requests = perf_data.get("total", 0)
        metrics.successful_requests = perf_data.get("success", 0)

        # Fetch from Governance pillar (M19)
        gov_data = await self._get_governance_metrics(tenant_id, period_days)
        metrics.policies_active = gov_data.get("active", 0)
        metrics.policy_violations = gov_data.get("violations", 0)
        metrics.policy_compliance_rate = gov_data.get("compliance", 100.0)

        return metrics

    def compute_trust_score(self, metrics: TrustMetrics) -> dict:
        """Compute weighted trust score from metrics."""

        scores = {}

        # Safety score (0 incidents = 100%)
        if metrics.safety_incidents == 0:
            scores["safety"] = 1.0
        else:
            # Penalize based on unresolved incidents
            unresolved = metrics.safety_incidents - metrics.incidents_resolved
            scores["safety"] = max(0.0, 1.0 - (unresolved * 0.1))

        # Quality score (average of accuracy, relevance, safety)
        if metrics.accuracy_score is not None:
            quality_components = [
                metrics.accuracy_score or 0.0,
                metrics.relevance_score or 0.0,
                metrics.safety_score or 0.0,
            ]
            scores["quality"] = sum(quality_components) / len(quality_components)
        else:
            # No quality data, use neutral score
            scores["quality"] = 0.8

        # Performance score
        if metrics.total_requests > 0:
            success_rate = metrics.successful_requests / metrics.total_requests
            latency_score = 1.0 if metrics.avg_response_time_ms < 2000 else 0.5
            scores["performance"] = (success_rate + latency_score + metrics.uptime_percentage / 100) / 3
        else:
            scores["performance"] = 0.8

        # Governance score
        scores["governance"] = metrics.policy_compliance_rate / 100

        # Cost score (budget efficiency)
        if metrics.cost_budget_utilization <= 1.0:
            scores["cost"] = 1.0 - (metrics.cost_anomalies_detected * 0.1)
        else:
            scores["cost"] = max(0.0, 1.0 - (metrics.cost_budget_utilization - 1.0))

        # Compute weighted average
        overall = sum(
            scores[k] * self.WEIGHTS[k]
            for k in self.WEIGHTS
            if k in scores
        )

        # Determine trust level
        min_score = min(scores.values())
        if min_score >= 0.95:
            level = TrustLevel.PLATINUM
        elif min_score >= 0.85:
            level = TrustLevel.GOLD
        elif min_score >= 0.75:
            level = TrustLevel.SILVER
        elif min_score >= 0.60:
            level = TrustLevel.BRONZE
        else:
            level = TrustLevel.UNRATED

        return {
            "overall_score": overall,
            "level": level.value,
            "component_scores": scores,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }

    def compute_trust_level(self, score: float) -> TrustLevel:
        """Determine trust badge level from score."""
        if score >= 0.95:
            return TrustLevel.PLATINUM
        elif score >= 0.85:
            return TrustLevel.GOLD
        elif score >= 0.75:
            return TrustLevel.SILVER
        elif score >= 0.60:
            return TrustLevel.BRONZE
        else:
            return TrustLevel.UNRATED
```

---

### 2. Trust Badge Widget

#### Embeddable JavaScript Snippet

```html
<!-- Customer embeds this in their website -->
<div id="agenticverz-trust-badge" data-tenant="tenant_abc123"></div>
<script src="https://cdn.agenticverz.com/trust-badge.js" async></script>
```

#### Badge JavaScript SDK

```typescript
// cdn/trust-badge.js

(function() {
  'use strict';

  const API_BASE = 'https://api.agenticverz.com';
  const BADGE_STYLES = {
    platinum: { bg: '#E5E4E2', accent: '#B4B4B4', icon: '🛡️' },
    gold: { bg: '#FFD700', accent: '#B8860B', icon: '🛡️' },
    silver: { bg: '#C0C0C0', accent: '#808080', icon: '🛡️' },
    bronze: { bg: '#CD7F32', accent: '#8B4513', icon: '🛡️' },
    unrated: { bg: '#E0E0E0', accent: '#999999', icon: '?' },
  };

  interface TrustBadgeData {
    tenant_id: string;
    level: string;
    overall_score: number;
    metrics: {
      accuracy?: string;
      safety_incidents: number;
      avg_cost: string;
      avg_response_time: string;
    };
    certificate_id: string;
    valid_until: string;
  }

  class TrustBadge {
    private container: HTMLElement;
    private tenantId: string;

    constructor(container: HTMLElement) {
      this.container = container;
      this.tenantId = container.dataset.tenant || '';
      this.init();
    }

    async init() {
      if (!this.tenantId) {
        this.renderError('Missing tenant ID');
        return;
      }

      try {
        const data = await this.fetchBadgeData();
        this.render(data);
      } catch (error) {
        this.renderError('Failed to load badge');
      }
    }

    async fetchBadgeData(): Promise<TrustBadgeData> {
      const response = await fetch(
        `${API_BASE}/trust/badge/${this.tenantId}?format=json`
      );
      if (!response.ok) throw new Error('Badge fetch failed');
      return response.json();
    }

    render(data: TrustBadgeData) {
      const style = BADGE_STYLES[data.level] || BADGE_STYLES.unrated;
      const verifyUrl = `${API_BASE}/trust/verify/${data.certificate_id}`;

      this.container.innerHTML = `
        <div class="agenticverz-badge" style="
          font-family: system-ui, -apple-system, sans-serif;
          border: 2px solid ${style.accent};
          border-radius: 12px;
          padding: 16px;
          background: linear-gradient(135deg, ${style.bg}22, ${style.bg}44);
          max-width: 320px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        ">
          <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
            <span style="font-size: 32px;">${style.icon}</span>
            <div>
              <div style="font-weight: 600; font-size: 14px; color: #333;">
                Protected by Agenticverz
              </div>
              <div style="font-size: 12px; color: #666; text-transform: uppercase;">
                ${data.level} Verified
              </div>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px;">
            ${data.metrics.accuracy ? `
              <div style="display: flex; align-items: center; gap: 4px;">
                <span style="color: #22c55e;">✓</span>
                <span>${data.metrics.accuracy} Accuracy</span>
              </div>
            ` : ''}
            <div style="display: flex; align-items: center; gap: 4px;">
              <span style="color: #22c55e;">✓</span>
              <span>${data.metrics.safety_incidents} Safety Incidents</span>
            </div>
            <div style="display: flex; align-items: center; gap: 4px;">
              <span style="color: #22c55e;">✓</span>
              <span>${data.metrics.avg_cost}/interaction</span>
            </div>
            <div style="display: flex; align-items: center; gap: 4px;">
              <span style="color: #22c55e;">✓</span>
              <span>${data.metrics.avg_response_time} avg response</span>
            </div>
          </div>

          <div style="margin-top: 12px; display: flex; gap: 8px;">
            <a href="${verifyUrl}" target="_blank" style="
              font-size: 11px;
              color: ${style.accent};
              text-decoration: none;
            ">Verify Certificate →</a>
          </div>
        </div>
      `;
    }

    renderError(message: string) {
      this.container.innerHTML = `
        <div style="color: #999; font-size: 12px; padding: 8px;">
          ${message}
        </div>
      `;
    }
  }

  // Auto-initialize badges
  document.addEventListener('DOMContentLoaded', () => {
    const containers = document.querySelectorAll('[id="agenticverz-trust-badge"]');
    containers.forEach(el => new TrustBadge(el as HTMLElement));
  });

  // Expose for manual initialization
  (window as any).AgenticverzTrustBadge = TrustBadge;
})();
```

---

### 3. Public Verification Page

#### Verification Endpoint

```python
# backend/app/api/trust.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/trust", tags=["trust"])


@router.get("/verify/{certificate_id}", response_class=HTMLResponse)
async def verify_certificate_page(certificate_id: str):
    """
    Public verification page for trust certificates.

    Returns an HTML page that displays:
    - Certificate validity
    - Trust metrics snapshot
    - Verification QR code
    - Download options
    """
    # Fetch and verify certificate
    cert_service = get_certificate_service()
    trust_service = get_trust_service()

    try:
        certificate = await trust_service.get_trust_certificate(certificate_id)
        verification = cert_service.verify_certificate(certificate)
    except Exception:
        raise HTTPException(status_code=404, detail="Certificate not found")

    # Build verification page
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Agenticverz Trust Verification</title>
        <style>
            * {{ box-sizing: border-box; }}
            body {{
                font-family: system-ui, -apple-system, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
            }}
            .card {{
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 500px;
                width: 100%;
                padding: 32px;
            }}
            .header {{
                text-align: center;
                margin-bottom: 24px;
            }}
            .logo {{ font-size: 48px; margin-bottom: 8px; }}
            .title {{ font-size: 24px; font-weight: 600; color: #333; }}
            .subtitle {{ font-size: 14px; color: #666; }}
            .status {{
                background: {'#22c55e' if verification['valid'] else '#ef4444'};
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                text-align: center;
                margin: 20px 0;
                font-weight: 600;
            }}
            .metrics {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 16px;
                margin: 24px 0;
            }}
            .metric {{
                background: #f8f9fa;
                border-radius: 8px;
                padding: 16px;
            }}
            .metric-label {{ font-size: 12px; color: #666; }}
            .metric-value {{ font-size: 20px; font-weight: 600; color: #333; }}
            .details {{
                font-size: 12px;
                color: #666;
                border-top: 1px solid #eee;
                padding-top: 16px;
                margin-top: 16px;
            }}
            .detail-row {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 8px;
            }}
            .actions {{
                display: flex;
                gap: 12px;
                margin-top: 24px;
            }}
            .btn {{
                flex: 1;
                padding: 12px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                text-align: center;
                text-decoration: none;
            }}
            .btn-primary {{
                background: #667eea;
                color: white;
            }}
            .btn-secondary {{
                background: #f0f0f0;
                color: #333;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                <div class="logo">🛡️</div>
                <div class="title">Trust Certificate</div>
                <div class="subtitle">Verified by Agenticverz</div>
            </div>

            <div class="status">
                {'✓ Certificate Valid' if verification['valid'] else '✗ Certificate Invalid'}
            </div>

            <div class="metrics">
                <div class="metric">
                    <div class="metric-label">Accuracy Score</div>
                    <div class="metric-value">{certificate.payload.get('accuracy', 'N/A')}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Safety Incidents</div>
                    <div class="metric-value">{certificate.payload.get('safety_incidents', 0)}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Avg Cost</div>
                    <div class="metric-value">${certificate.payload.get('avg_cost', '0.00')}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Response Time</div>
                    <div class="metric-value">{certificate.payload.get('response_time', '<2s')}</div>
                </div>
            </div>

            <div class="details">
                <div class="detail-row">
                    <span>Certificate ID</span>
                    <span>{certificate_id[:16]}...</span>
                </div>
                <div class="detail-row">
                    <span>Issued</span>
                    <span>{verification['issued_at'][:10]}</span>
                </div>
                <div class="detail-row">
                    <span>Valid Until</span>
                    <span>{verification['valid_until'][:10]}</span>
                </div>
                <div class="detail-row">
                    <span>Trust Level</span>
                    <span style="text-transform: uppercase;">{certificate.payload.get('level', 'N/A')}</span>
                </div>
            </div>

            <div class="actions">
                <a href="/trust/report/{certificate.payload.tenant_id}" class="btn btn-primary">
                    View Full Report
                </a>
                <a href="/trust/badge/{certificate.payload.tenant_id}?format=pdf" class="btn btn-secondary">
                    Download PDF
                </a>
            </div>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html)
```

---

### 4. Trust Report Generator

#### Report Model

```python
# backend/app/trust/report.py

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from enum import Enum


class ReportFormat(str, Enum):
    HTML = "html"
    PDF = "pdf"
    JSON = "json"


@dataclass
class TrustReportSection:
    """A section of the trust report."""
    title: str
    score: float  # 0.0-1.0
    status: str   # "excellent", "good", "warning", "critical"
    metrics: dict
    highlights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class TrustReport:
    """Complete trust report for a tenant."""

    tenant_id: str
    tenant_name: str
    report_id: str
    generated_at: datetime

    # Period
    period_start: datetime
    period_end: datetime
    period_days: int

    # Overall
    overall_score: float
    trust_level: str
    certificate_id: str

    # Sections
    safety_section: TrustReportSection
    quality_section: Optional[TrustReportSection]
    performance_section: TrustReportSection
    governance_section: TrustReportSection
    cost_section: TrustReportSection

    # Summary
    executive_summary: str
    key_achievements: List[str] = field(default_factory=list)
    areas_for_improvement: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "tenant_name": self.tenant_name,
            "report_id": self.report_id,
            "generated_at": self.generated_at.isoformat(),
            "period": {
                "start": self.period_start.isoformat(),
                "end": self.period_end.isoformat(),
                "days": self.period_days,
            },
            "overall": {
                "score": self.overall_score,
                "level": self.trust_level,
                "certificate_id": self.certificate_id,
            },
            "sections": {
                "safety": self._section_to_dict(self.safety_section),
                "quality": self._section_to_dict(self.quality_section) if self.quality_section else None,
                "performance": self._section_to_dict(self.performance_section),
                "governance": self._section_to_dict(self.governance_section),
                "cost": self._section_to_dict(self.cost_section),
            },
            "summary": {
                "executive": self.executive_summary,
                "achievements": self.key_achievements,
                "improvements": self.areas_for_improvement,
            },
        }

    def _section_to_dict(self, section: TrustReportSection) -> dict:
        return {
            "title": section.title,
            "score": section.score,
            "status": section.status,
            "metrics": section.metrics,
            "highlights": section.highlights,
            "recommendations": section.recommendations,
        }


class TrustReportGenerator:
    """Generates trust reports in various formats."""

    async def generate(
        self,
        tenant_id: str,
        period_days: int = 30,
        format: ReportFormat = ReportFormat.HTML,
    ) -> str:
        """Generate trust report."""

        # Aggregate metrics
        aggregator = TrustScoreAggregator()
        metrics = await aggregator.compute_trust_metrics(tenant_id, period_days)
        score_data = aggregator.compute_trust_score(metrics)

        # Build report sections
        report = await self._build_report(tenant_id, metrics, score_data, period_days)

        # Render in requested format
        if format == ReportFormat.JSON:
            return json.dumps(report.to_dict(), indent=2)
        elif format == ReportFormat.HTML:
            return self._render_html(report)
        elif format == ReportFormat.PDF:
            return self._render_pdf(report)

    async def _build_report(
        self,
        tenant_id: str,
        metrics: TrustMetrics,
        score_data: dict,
        period_days: int,
    ) -> TrustReport:
        """Build complete trust report."""

        now = datetime.now(timezone.utc)

        # Safety section
        safety_section = TrustReportSection(
            title="Safety & Incident Management",
            score=score_data["component_scores"]["safety"],
            status=self._score_to_status(score_data["component_scores"]["safety"]),
            metrics={
                "total_incidents": metrics.safety_incidents,
                "incidents_resolved": metrics.incidents_resolved,
                "killswitch_activations": metrics.killswitch_activations,
            },
            highlights=[
                f"Zero safety incidents in last {period_days} days"
            ] if metrics.safety_incidents == 0 else [],
            recommendations=[
                "Review unresolved incidents"
            ] if metrics.safety_incidents > metrics.incidents_resolved else [],
        )

        # Quality section (optional)
        quality_section = None
        if metrics.accuracy_score is not None:
            quality_section = TrustReportSection(
                title="AI Quality & Accuracy",
                score=score_data["component_scores"]["quality"],
                status=self._score_to_status(score_data["component_scores"]["quality"]),
                metrics={
                    "accuracy_score": metrics.accuracy_score,
                    "relevance_score": metrics.relevance_score,
                    "safety_score": metrics.safety_score,
                    "hallucinations_detected": metrics.hallucinations_detected,
                },
                highlights=[
                    f"{metrics.accuracy_score * 100:.1f}% accuracy achieved"
                ] if metrics.accuracy_score >= 0.9 else [],
            )

        # Performance section
        performance_section = TrustReportSection(
            title="Performance & Reliability",
            score=score_data["component_scores"]["performance"],
            status=self._score_to_status(score_data["component_scores"]["performance"]),
            metrics={
                "avg_response_time_ms": metrics.avg_response_time_ms,
                "p99_response_time_ms": metrics.p99_response_time_ms,
                "uptime_percentage": metrics.uptime_percentage,
                "total_requests": metrics.total_requests,
                "success_rate": (
                    metrics.successful_requests / metrics.total_requests * 100
                    if metrics.total_requests > 0 else 100
                ),
            },
            highlights=[
                f"{metrics.uptime_percentage:.2f}% uptime maintained"
            ],
        )

        # Governance section
        governance_section = TrustReportSection(
            title="Policy Governance",
            score=score_data["component_scores"]["governance"],
            status=self._score_to_status(score_data["component_scores"]["governance"]),
            metrics={
                "policies_active": metrics.policies_active,
                "policy_violations": metrics.policy_violations,
                "compliance_rate": metrics.policy_compliance_rate,
            },
            highlights=[
                f"{metrics.policies_active} active policies enforced"
            ],
        )

        # Cost section
        cost_section = TrustReportSection(
            title="Cost Efficiency",
            score=score_data["component_scores"]["cost"],
            status=self._score_to_status(score_data["component_scores"]["cost"]),
            metrics={
                "avg_cost_per_interaction": metrics.avg_cost_per_interaction,
                "budget_utilization": metrics.cost_budget_utilization,
                "anomalies_detected": metrics.cost_anomalies_detected,
            },
            highlights=[
                f"${metrics.avg_cost_per_interaction:.3f} average cost per interaction"
            ],
        )

        # Build executive summary
        executive_summary = self._generate_executive_summary(
            score_data, metrics, period_days
        )

        return TrustReport(
            tenant_id=tenant_id,
            tenant_name="Tenant",  # Would fetch from tenant service
            report_id=str(uuid.uuid4()),
            generated_at=now,
            period_start=now - timedelta(days=period_days),
            period_end=now,
            period_days=period_days,
            overall_score=score_data["overall_score"],
            trust_level=score_data["level"],
            certificate_id=str(uuid.uuid4()),  # Would create actual cert
            safety_section=safety_section,
            quality_section=quality_section,
            performance_section=performance_section,
            governance_section=governance_section,
            cost_section=cost_section,
            executive_summary=executive_summary,
            key_achievements=self._extract_achievements(metrics, score_data),
            areas_for_improvement=self._extract_improvements(metrics, score_data),
        )

    def _score_to_status(self, score: float) -> str:
        if score >= 0.95:
            return "excellent"
        elif score >= 0.80:
            return "good"
        elif score >= 0.60:
            return "warning"
        else:
            return "critical"
```

---

### 5. Database Migration (047)

```python
# backend/alembic/versions/047_m30_trust_badge.py

"""M30 Trust Badge - Trust certificates and badge configurations

Revision ID: 047_m30_trust
Revises: 046_m29_quality
Create Date: 2025-XX-XX
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "047_m30_trust"
down_revision = "046_m29_quality"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Trust certificates table
    op.create_table(
        "trust_certificates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),

        # Certificate data
        sa.Column("certificate_type", sa.String(50), nullable=False),  # trust_badge, report
        sa.Column("trust_level", sa.String(20), nullable=False),  # platinum, gold, silver, bronze
        sa.Column("overall_score", sa.Float, nullable=False),

        # Component scores
        sa.Column("safety_score", sa.Float, nullable=True),
        sa.Column("quality_score", sa.Float, nullable=True),
        sa.Column("performance_score", sa.Float, nullable=True),
        sa.Column("governance_score", sa.Float, nullable=True),
        sa.Column("cost_score", sa.Float, nullable=True),

        # Metrics snapshot
        sa.Column("metrics_snapshot", postgresql.JSONB, nullable=False),

        # Validity
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_revoked", sa.Boolean, default=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revocation_reason", sa.Text, nullable=True),

        # Signature
        sa.Column("signature", sa.String(128), nullable=False),
        sa.Column("signature_algorithm", sa.String(50), default="HMAC-SHA256"),

        # Period
        sa.Column("period_days", sa.Integer, default=30),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),

        sa.Index("ix_trust_certificates_tenant_valid", "tenant_id", "valid_until"),
        sa.Index("ix_trust_certificates_level", "trust_level"),
    )

    # 2. Badge configurations table
    op.create_table(
        "badge_configurations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, unique=True),

        # Badge settings
        sa.Column("badge_enabled", sa.Boolean, default=True),
        sa.Column("badge_style", sa.String(50), default="default"),  # default, compact, minimal
        sa.Column("show_accuracy", sa.Boolean, default=True),
        sa.Column("show_safety", sa.Boolean, default=True),
        sa.Column("show_cost", sa.Boolean, default=True),
        sa.Column("show_response_time", sa.Boolean, default=True),

        # Branding (enterprise)
        sa.Column("custom_logo_url", sa.String(500), nullable=True),
        sa.Column("custom_colors", postgresql.JSONB, nullable=True),
        sa.Column("white_label", sa.Boolean, default=False),

        # Allowed domains (CORS)
        sa.Column("allowed_domains", postgresql.ARRAY(sa.String(200)), default=[]),

        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 3. Badge access logs (for analytics)
    op.create_table(
        "badge_access_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column("certificate_id", postgresql.UUID(as_uuid=True), nullable=True),

        # Access details
        sa.Column("access_type", sa.String(50), nullable=False),  # badge_view, verify, report_download
        sa.Column("referrer_domain", sa.String(200), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),

        # Timestamps
        sa.Column("accessed_at", sa.DateTime(timezone=True), nullable=False),

        sa.Index("ix_badge_access_tenant_time", "tenant_id", "accessed_at"),
    )

    # 4. Trust reports table
    op.create_table(
        "trust_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column("certificate_id", postgresql.UUID(as_uuid=True), nullable=False),

        # Report content
        sa.Column("report_format", sa.String(20), nullable=False),  # html, pdf, json
        sa.Column("report_content", sa.Text, nullable=True),  # For HTML/JSON
        sa.Column("report_blob", sa.LargeBinary, nullable=True),  # For PDF

        # Period
        sa.Column("period_days", sa.Integer, nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),

        # Timestamps
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),

        sa.Index("ix_trust_reports_tenant_generated", "tenant_id", "generated_at"),
    )


def downgrade():
    op.drop_table("trust_reports")
    op.drop_table("badge_access_logs")
    op.drop_table("badge_configurations")
    op.drop_table("trust_certificates")
```

---

### 6. API Endpoints

```python
# backend/app/api/trust.py

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/trust", tags=["trust"])


# === Badge Endpoints ===

@router.get("/badge/{tenant_id}")
async def get_trust_badge(
    tenant_id: str,
    format: str = Query("html", enum=["html", "svg", "json", "js"]),
):
    """
    Get embeddable trust badge for a tenant.

    Formats:
    - html: Complete HTML widget
    - svg: Vector badge image
    - json: Raw badge data
    - js: JavaScript snippet
    """
    trust_service = get_trust_service()
    badge_data = await trust_service.get_badge_data(tenant_id)

    if format == "json":
        return badge_data
    elif format == "svg":
        svg = trust_service.render_badge_svg(badge_data)
        return Response(content=svg, media_type="image/svg+xml")
    elif format == "js":
        js = trust_service.render_badge_js(tenant_id)
        return Response(content=js, media_type="application/javascript")
    else:
        html = trust_service.render_badge_html(badge_data)
        return HTMLResponse(content=html)


@router.get("/metrics/{tenant_id}")
async def get_trust_metrics(
    tenant_id: str,
    period_days: int = Query(30, ge=1, le=365),
):
    """Get raw trust metrics for a tenant."""
    aggregator = TrustScoreAggregator()
    metrics = await aggregator.compute_trust_metrics(tenant_id, period_days)
    score = aggregator.compute_trust_score(metrics)

    return {
        "tenant_id": tenant_id,
        "period_days": period_days,
        "overall_score": score["overall_score"],
        "trust_level": score["level"],
        "component_scores": score["component_scores"],
        "metrics": {
            "safety": {
                "incidents": metrics.safety_incidents,
                "resolved": metrics.incidents_resolved,
                "killswitch_activations": metrics.killswitch_activations,
            },
            "quality": {
                "accuracy": metrics.accuracy_score,
                "relevance": metrics.relevance_score,
                "safety": metrics.safety_score,
            } if metrics.accuracy_score else None,
            "performance": {
                "avg_response_time_ms": metrics.avg_response_time_ms,
                "uptime_percentage": metrics.uptime_percentage,
                "success_rate": (
                    metrics.successful_requests / metrics.total_requests
                    if metrics.total_requests > 0 else 1.0
                ),
            },
            "governance": {
                "policies_active": metrics.policies_active,
                "compliance_rate": metrics.policy_compliance_rate,
            },
            "cost": {
                "avg_cost_per_interaction": metrics.avg_cost_per_interaction,
                "budget_utilization": metrics.cost_budget_utilization,
            },
        },
        "computed_at": score["computed_at"],
    }


# === Verification Endpoints ===

@router.get("/verify/{certificate_id}", response_class=HTMLResponse)
async def verify_certificate_page(certificate_id: str):
    """Public verification page for trust certificates."""
    # Implementation shown in section 3
    pass


@router.get("/verify/{certificate_id}/json")
async def verify_certificate_json(certificate_id: str):
    """API verification of trust certificate."""
    trust_service = get_trust_service()

    try:
        certificate = await trust_service.get_certificate(certificate_id)
        verification = trust_service.verify_certificate(certificate)
    except Exception:
        raise HTTPException(status_code=404, detail="Certificate not found")

    return verification


# === Report Endpoints ===

@router.get("/report/{tenant_id}")
async def get_trust_report(
    tenant_id: str,
    period_days: int = Query(30, ge=1, le=365),
    format: str = Query("html", enum=["html", "pdf", "json"]),
):
    """Generate trust report for a tenant."""
    generator = TrustReportGenerator()
    report = await generator.generate(
        tenant_id=tenant_id,
        period_days=period_days,
        format=ReportFormat(format),
    )

    if format == "pdf":
        return StreamingResponse(
            io.BytesIO(report),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=trust-report-{tenant_id}.pdf"
            }
        )
    elif format == "json":
        return Response(content=report, media_type="application/json")
    else:
        return HTMLResponse(content=report)


# === Configuration Endpoints (Authenticated) ===

class BadgeConfigUpdate(BaseModel):
    badge_enabled: Optional[bool] = None
    badge_style: Optional[str] = None
    show_accuracy: Optional[bool] = None
    show_safety: Optional[bool] = None
    show_cost: Optional[bool] = None
    show_response_time: Optional[bool] = None
    allowed_domains: Optional[List[str]] = None


@router.get("/config/{tenant_id}")
async def get_badge_config(tenant_id: str):
    """Get badge configuration for tenant."""
    trust_service = get_trust_service()
    config = await trust_service.get_badge_config(tenant_id)
    return config


@router.patch("/config/{tenant_id}")
async def update_badge_config(tenant_id: str, update: BadgeConfigUpdate):
    """Update badge configuration."""
    trust_service = get_trust_service()
    config = await trust_service.update_badge_config(tenant_id, update.dict(exclude_none=True))
    return config
```

---

### 7. Console UI Components

#### Badge Configuration Page

```typescript
// website/aos-console/console/src/pages/trust/BadgeConfigPage.tsx

export const BadgeConfigPage: React.FC = () => {
  const { config, updateConfig } = useBadgeConfig();
  const { metrics } = useTrustMetrics();

  return (
    <div className="badge-config-page">
      <h1>Trust Badge Configuration</h1>

      {/* Preview */}
      <Card>
        <CardHeader>Badge Preview</CardHeader>
        <CardContent>
          <TrustBadgePreview config={config} metrics={metrics} />
        </CardContent>
      </Card>

      {/* Settings */}
      <Card>
        <CardHeader>Display Settings</CardHeader>
        <CardContent>
          <FormGroup>
            <Toggle
              label="Enable Badge"
              checked={config.badge_enabled}
              onChange={(v) => updateConfig({ badge_enabled: v })}
            />
          </FormGroup>

          <FormGroup>
            <Label>Badge Style</Label>
            <Select
              value={config.badge_style}
              onChange={(v) => updateConfig({ badge_style: v })}
              options={[
                { value: "default", label: "Default" },
                { value: "compact", label: "Compact" },
                { value: "minimal", label: "Minimal" },
              ]}
            />
          </FormGroup>

          <FormGroup>
            <Label>Metrics to Display</Label>
            <CheckboxGroup>
              <Checkbox
                label="Accuracy Score"
                checked={config.show_accuracy}
                onChange={(v) => updateConfig({ show_accuracy: v })}
              />
              <Checkbox
                label="Safety Incidents"
                checked={config.show_safety}
                onChange={(v) => updateConfig({ show_safety: v })}
              />
              <Checkbox
                label="Average Cost"
                checked={config.show_cost}
                onChange={(v) => updateConfig({ show_cost: v })}
              />
              <Checkbox
                label="Response Time"
                checked={config.show_response_time}
                onChange={(v) => updateConfig({ show_response_time: v })}
              />
            </CheckboxGroup>
          </FormGroup>
        </CardContent>
      </Card>

      {/* Embed Code */}
      <Card>
        <CardHeader>Embed Code</CardHeader>
        <CardContent>
          <CodeBlock language="html">
            {`<div id="agenticverz-trust-badge" data-tenant="${config.tenant_id}"></div>
<script src="https://cdn.agenticverz.com/trust-badge.js" async></script>`}
          </CodeBlock>
          <Button onClick={copyToClipboard}>Copy Code</Button>
        </CardContent>
      </Card>

      {/* Allowed Domains */}
      <Card>
        <CardHeader>Allowed Domains (CORS)</CardHeader>
        <CardContent>
          <DomainList
            domains={config.allowed_domains}
            onAdd={(d) => updateConfig({
              allowed_domains: [...config.allowed_domains, d]
            })}
            onRemove={(d) => updateConfig({
              allowed_domains: config.allowed_domains.filter(x => x !== d)
            })}
          />
        </CardContent>
      </Card>
    </div>
  );
};
```

---

## Integration with M28 Control Center

### Add Trust View to Control Center

```typescript
// Update M28 TopNavBar with Trust view
const views = [
  { id: "cost", label: "Cost", icon: DollarSign },
  { id: "incident", label: "Incident", icon: AlertTriangle },
  { id: "self-heal", label: "Self-Heal", icon: RefreshCw },
  { id: "governance", label: "Governance", icon: Shield },
  { id: "quality", label: "Quality", icon: CheckCircle },
  { id: "trust", label: "Trust Badge", icon: Award },  // NEW
];
```

### Trust Summary in Metrics Strip

```typescript
// Add to MetricsStrip
<MetricsStrip>
  <Metric label="Active Incidents" value={3} />
  <Metric label="Recovery Suggestions" value={12} />
  <Metric label="Policies Active" value={47} />
  <Metric label="Cost This Month" value="$4,847 / $5,000" />
  <Metric label="Quality Score" value="94.2%" trend="+1.3%" />
  <Metric
    label="Trust Level"
    value={<TrustLevelBadge level="gold" />}  // NEW
  />
</MetricsStrip>
```

---

## Implementation Plan

### Phase 1: Trust Aggregator (2 days)

| Day | Task | Output |
|-----|------|--------|
| 1 | Trust metrics aggregator | `TrustScoreAggregator` class |
| 1 | Trust level computation | Level determination logic |
| 2 | Migration 047 | Database tables |
| 2 | Trust certificate service | Extends M23 certificate service |

### Phase 2: Badge System (3 days)

| Day | Task | Output |
|-----|------|--------|
| 3 | Badge API endpoints | `/trust/badge/*` routes |
| 3 | Badge JavaScript SDK | CDN-hosted widget |
| 4 | Verification page | Public `/trust/verify/*` page |
| 4 | SVG badge rendering | Vector badge generation |
| 5 | Badge configuration API | Config CRUD endpoints |
| 5 | Badge analytics logging | Access tracking |

### Phase 3: Reports & Console (2 days)

| Day | Task | Output |
|-----|------|--------|
| 6 | Trust report generator | HTML/PDF/JSON reports |
| 6 | Report API endpoints | `/trust/report/*` routes |
| 7 | Console configuration page | Badge config UI |
| 7 | M28 integration | Add Trust view to Control Center |

---

## CDN Deployment

### Badge Script Hosting

```yaml
# cloudflare/trust-badge-worker.js

// Deploy to cdn.agenticverz.com/trust-badge.js
export default {
  async fetch(request, env) {
    // Serve minified badge script
    const script = await env.BADGE_BUCKET.get('trust-badge.min.js');

    return new Response(script.body, {
      headers: {
        'Content-Type': 'application/javascript',
        'Cache-Control': 'public, max-age=3600',
        'Access-Control-Allow-Origin': '*',
      },
    });
  },
};
```

---

## Security Considerations

### 1. Certificate Signing

```python
# Certificates use HMAC-SHA256 with environment secret
# Same infrastructure as M23 certificates
CERTIFICATE_SECRET = os.getenv("CERTIFICATE_SECRET")

# Signature verification prevents tampering
signature = hmac.new(
    CERTIFICATE_SECRET.encode(),
    payload.canonical_json().encode(),
    hashlib.sha256
).hexdigest()
```

### 2. Domain Allowlist (CORS)

```python
# Only serve badge to configured domains
@router.get("/badge/{tenant_id}")
async def get_badge(tenant_id: str, request: Request):
    config = await get_badge_config(tenant_id)

    origin = request.headers.get("Origin", "")
    if origin and not any(
        allowed in origin for allowed in config.allowed_domains
    ):
        raise HTTPException(403, "Domain not allowed")
```

### 3. Rate Limiting

```python
# Rate limit badge endpoints to prevent abuse
@router.get("/badge/{tenant_id}")
@rate_limit(limit=1000, window=60)  # 1000/minute
async def get_badge(tenant_id: str):
    pass
```

---

## Activation Criteria

**M30 is CONDITIONAL.** Only implement when:

1. **Enterprise deal requires** public proof of AI governance
2. **Customer needs** embeddable trust widget for their website
3. **Regulatory/compliance** demands third-party verification

**Evidence to collect:**
- Enterprise RFP requiring trust certification
- Customer request for embeddable badge
- Compliance audit requiring public verification

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Badge embed rate | 20% of tenants | tenants_with_badge / total_tenants |
| Verification page visits | 100/month/tenant | badge_access_logs |
| Report downloads | 10/month/tenant | report_downloads |
| Trust level distribution | 50% Gold+ | certificates by level |

---

## Related Documentation

- PIN-128: Master Plan M25-M30
- PIN-133: M29 Quality Score Blueprint
- PIN-132: M28 Unified Console Blueprint
- M23: Certificate Service (existing infrastructure)
- M26: Cost Intelligence (cost metrics)
- M22/M23: Guard Console (safety metrics)

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-22 | Created PIN-134 M30 Trust Badge Blueprint |
