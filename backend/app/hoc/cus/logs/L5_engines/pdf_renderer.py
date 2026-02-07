# Layer: L5 — Domain Engine
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Render export bundles to PDF format
# Callers: api/incidents.py
# Allowed Imports: L7 models, external libs
# Forbidden Imports: L1, L2, L3, L4
# Reference: BACKEND_REMEDIATION_PLAN.md GAP-004, GAP-005

"""
PDF Renderer Engine

Renders export bundles to PDF format for compliance exports,
executive debriefs, and evidence documentation.

Key Responsibilities:
1. Render EvidenceBundle to detailed PDF
2. Render SOC2Bundle with control attestations
3. Render ExecutiveDebriefBundle for leadership

Uses reportlab for PDF generation (same library as evidence_report.py).
"""

from __future__ import annotations

import io
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

if TYPE_CHECKING:
    from app.models.export_bundles import (
        EvidenceBundle,
        ExecutiveDebriefBundle,
        SOC2Bundle,
    )

logger = logging.getLogger("nova.hoc.logs.pdf_renderer")


class PDFRenderer:
    """Render export bundles to PDF format."""

    # Color palette
    PRIMARY_COLOR = colors.HexColor("#1a365d")
    SECONDARY_COLOR = colors.HexColor("#2b6cb0")
    ACCENT_COLOR = colors.HexColor("#e53e3e")
    LIGHT_GRAY = colors.HexColor("#f7fafc")
    BORDER_COLOR = colors.HexColor("#e2e8f0")

    def __init__(self):
        """Initialize PDF renderer with styles."""
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self) -> None:
        """Configure custom paragraph styles."""
        # Title style
        self.styles.add(
            ParagraphStyle(
                "CustomTitle",
                parent=self.styles["Title"],
                fontSize=24,
                textColor=self.PRIMARY_COLOR,
                spaceAfter=20,
                alignment=TA_CENTER,
            )
        )

        # Subtitle style
        self.styles.add(
            ParagraphStyle(
                "CustomSubtitle",
                parent=self.styles["Normal"],
                fontSize=14,
                textColor=self.SECONDARY_COLOR,
                spaceAfter=12,
            )
        )

        # Section header style
        self.styles.add(
            ParagraphStyle(
                "SectionHeader",
                parent=self.styles["Heading2"],
                fontSize=14,
                textColor=self.PRIMARY_COLOR,
                spaceBefore=16,
                spaceAfter=8,
                borderPadding=4,
            )
        )

        # Body text style
        self.styles.add(
            ParagraphStyle(
                "BodyText",
                parent=self.styles["Normal"],
                fontSize=10,
                leading=14,
                spaceAfter=8,
            )
        )

        # Alert text style
        self.styles.add(
            ParagraphStyle(
                "AlertText",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=self.ACCENT_COLOR,
                fontName="Helvetica-Bold",
            )
        )

    def render_evidence_pdf(self, bundle: EvidenceBundle) -> bytes:
        """
        Render evidence bundle to PDF bytes.

        Args:
            bundle: EvidenceBundle to render

        Returns:
            PDF as bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        story = []

        # Cover page
        story.extend(self._build_evidence_cover(bundle))
        story.append(PageBreak())

        # Summary section
        story.extend(self._build_evidence_summary(bundle))

        # Trace timeline
        if bundle.steps:
            story.append(PageBreak())
            story.extend(self._build_trace_timeline(bundle))

        # Policy context
        story.append(PageBreak())
        story.extend(self._build_policy_section(bundle))

        # Integrity verification
        story.extend(self._build_integrity_section(bundle))

        doc.build(story)
        buffer.seek(0)

        logger.info(
            "evidence_pdf_rendered",
            extra={
                "bundle_id": bundle.bundle_id,
                "page_estimate": len(story) // 10,
            },
        )

        return buffer.getvalue()

    def render_soc2_pdf(self, bundle: SOC2Bundle) -> bytes:
        """
        Render SOC2 bundle to PDF with attestation.

        Args:
            bundle: SOC2Bundle to render

        Returns:
            PDF as bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        story = []

        # Cover page with SOC2 branding
        story.extend(self._build_soc2_cover(bundle))
        story.append(PageBreak())

        # Control mappings
        story.extend(self._build_control_mappings(bundle))
        story.append(PageBreak())

        # Attestation statement
        story.extend(self._build_attestation(bundle))
        story.append(PageBreak())

        # Evidence summary (from base bundle)
        story.extend(self._build_evidence_summary(bundle))

        # Trace timeline
        if bundle.steps:
            story.append(PageBreak())
            story.extend(self._build_trace_timeline(bundle))

        doc.build(story)
        buffer.seek(0)

        logger.info(
            "soc2_pdf_rendered",
            extra={
                "bundle_id": bundle.bundle_id,
                "controls_count": len(bundle.control_mappings),
            },
        )

        return buffer.getvalue()

    def render_executive_debrief_pdf(self, bundle: ExecutiveDebriefBundle) -> bytes:
        """
        Render executive debrief to PDF.

        Args:
            bundle: ExecutiveDebriefBundle to render

        Returns:
            PDF as bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        story = []

        # Cover page
        story.extend(self._build_exec_cover(bundle))
        story.append(PageBreak())

        # Executive summary
        story.extend(self._build_exec_summary(bundle))

        # Recommendations
        story.extend(self._build_recommendations(bundle))

        # Key metrics
        story.extend(self._build_exec_metrics(bundle))

        doc.build(story)
        buffer.seek(0)

        logger.info(
            "executive_debrief_pdf_rendered",
            extra={
                "bundle_id": bundle.bundle_id,
                "risk_level": bundle.risk_level,
            },
        )

        return buffer.getvalue()

    # =========================================================================
    # Evidence PDF Builders
    # =========================================================================

    def _build_evidence_cover(self, bundle: EvidenceBundle) -> list:
        """Build evidence cover page."""
        story = []
        story.append(Spacer(1, 2 * inch))
        story.append(Paragraph("EVIDENCE BUNDLE", self.styles["CustomTitle"]))
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph(f"Bundle ID: {bundle.bundle_id}", self.styles["CustomSubtitle"]))
        story.append(Paragraph(f"Incident ID: {bundle.incident_id or 'N/A'}", self.styles["CustomSubtitle"]))
        story.append(Paragraph(f"Run ID: {bundle.run_id}", self.styles["CustomSubtitle"]))
        story.append(Spacer(1, inch))
        story.append(
            Paragraph(
                f"Generated: {bundle.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                self.styles["BodyText"],
            )
        )
        story.append(Paragraph(f"Exported by: {bundle.exported_by}", self.styles["BodyText"]))
        if bundle.export_reason:
            story.append(Paragraph(f"Reason: {bundle.export_reason}", self.styles["BodyText"]))
        return story

    def _build_evidence_summary(self, bundle: EvidenceBundle) -> list:
        """Build evidence summary section."""
        story = []
        story.append(Paragraph("Evidence Summary", self.styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=self.BORDER_COLOR))
        story.append(Spacer(1, 0.2 * inch))

        # Summary table
        data = [
            ["Run ID", bundle.run_id],
            ["Trace ID", bundle.trace_id],
            ["Tenant ID", bundle.tenant_id],
            ["Total Steps", str(bundle.total_steps)],
            ["Total Tokens", f"{bundle.total_tokens:,}"],
            ["Total Cost", f"${bundle.total_cost_cents / 100:.2f}"],
            ["Duration", f"{bundle.total_duration_ms / 1000:.2f}s"],
            ["Termination Reason", bundle.termination_reason or "N/A"],
        ]

        if bundle.violation_step_index is not None:
            data.append(["Violation Step", str(bundle.violation_step_index)])

        table = Table(data, colWidths=[2 * inch, 4 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), self.LIGHT_GRAY),
                    ("TEXTCOLOR", (0, 0), (0, -1), self.PRIMARY_COLOR),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, self.BORDER_COLOR),
                ]
            )
        )
        story.append(table)
        return story

    def _build_trace_timeline(self, bundle: EvidenceBundle) -> list:
        """Build trace timeline section."""
        story = []
        story.append(Paragraph("Execution Timeline", self.styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=self.BORDER_COLOR))
        story.append(Spacer(1, 0.2 * inch))

        # Timeline table header
        data = [["Step", "Timestamp", "Type", "Tokens", "Status"]]

        for step in bundle.steps[:50]:  # Limit to 50 steps
            status_text = step.status.upper()
            if step.is_inflection:
                status_text = "VIOLATION"

            data.append(
                [
                    str(step.step_index),
                    step.timestamp.strftime("%H:%M:%S.%f")[:-3],
                    step.step_type[:20],
                    str(step.tokens),
                    status_text,
                ]
            )

        table = Table(data, colWidths=[0.6 * inch, 1.2 * inch, 1.8 * inch, 0.8 * inch, 1.2 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), self.PRIMARY_COLOR),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, self.BORDER_COLOR),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ]
            )
        )
        story.append(table)

        if len(bundle.steps) > 50:
            story.append(Spacer(1, 0.1 * inch))
            story.append(
                Paragraph(
                    f"(Showing first 50 of {len(bundle.steps)} steps)",
                    self.styles["BodyText"],
                )
            )

        return story

    def _build_policy_section(self, bundle: EvidenceBundle) -> list:
        """Build policy context section."""
        story = []
        story.append(Paragraph("Policy Context", self.styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=self.BORDER_COLOR))
        story.append(Spacer(1, 0.2 * inch))

        ctx = bundle.policy_context
        data = [
            ["Policy Snapshot ID", ctx.policy_snapshot_id],
            ["Violated Policy ID", ctx.violated_policy_id or "None"],
            ["Violated Policy Name", ctx.violated_policy_name or "None"],
            ["Violation Type", ctx.violation_type or "None"],
            ["Threshold Value", ctx.threshold_value or "N/A"],
            ["Actual Value", ctx.actual_value or "N/A"],
        ]

        table = Table(data, colWidths=[2 * inch, 4 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), self.LIGHT_GRAY),
                    ("TEXTCOLOR", (0, 0), (0, -1), self.PRIMARY_COLOR),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, self.BORDER_COLOR),
                ]
            )
        )
        story.append(table)
        return story

    def _build_integrity_section(self, bundle: EvidenceBundle) -> list:
        """Build integrity verification section."""
        story = []
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph("Integrity Verification", self.styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=self.BORDER_COLOR))
        story.append(Spacer(1, 0.2 * inch))

        story.append(
            Paragraph(
                f"Content Hash (SHA256): {bundle.content_hash or 'Not computed'}",
                self.styles["BodyText"],
            )
        )
        story.append(
            Paragraph(
                "This hash can be used to verify the integrity of this evidence bundle.",
                self.styles["BodyText"],
            )
        )
        return story

    # =========================================================================
    # SOC2 PDF Builders
    # =========================================================================

    def _build_soc2_cover(self, bundle: SOC2Bundle) -> list:
        """Build SOC2 cover page."""
        story = []
        story.append(Spacer(1, 2 * inch))
        story.append(Paragraph("SOC 2 COMPLIANCE REPORT", self.styles["CustomTitle"]))
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("Trust Services Criteria Evidence", self.styles["CustomSubtitle"]))
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph(f"Bundle ID: {bundle.bundle_id}", self.styles["CustomSubtitle"]))
        story.append(Paragraph(f"Incident ID: {bundle.incident_id or 'N/A'}", self.styles["CustomSubtitle"]))
        story.append(Spacer(1, inch))

        # Compliance period
        if bundle.compliance_period_start and bundle.compliance_period_end:
            story.append(
                Paragraph(
                    f"Compliance Period: {bundle.compliance_period_start.strftime('%Y-%m-%d')} "
                    f"to {bundle.compliance_period_end.strftime('%Y-%m-%d')}",
                    self.styles["BodyText"],
                )
            )

        story.append(
            Paragraph(
                f"Generated: {bundle.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                self.styles["BodyText"],
            )
        )
        return story

    def _build_control_mappings(self, bundle: SOC2Bundle) -> list:
        """Build SOC2 control mappings section."""
        story = []
        story.append(Paragraph("Trust Services Criteria Mappings", self.styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=self.BORDER_COLOR))
        story.append(Spacer(1, 0.2 * inch))

        for control in bundle.control_mappings:
            story.append(
                Paragraph(
                    f"<b>{control.control_id}: {control.control_name}</b>",
                    self.styles["CustomSubtitle"],
                )
            )
            story.append(Paragraph(control.control_description, self.styles["BodyText"]))
            story.append(
                Paragraph(
                    f"<b>Evidence:</b> {control.evidence_provided}",
                    self.styles["BodyText"],
                )
            )
            story.append(
                Paragraph(
                    f"<b>Status:</b> {control.compliance_status}",
                    self.styles["BodyText"],
                )
            )
            story.append(Spacer(1, 0.2 * inch))

        return story

    def _build_attestation(self, bundle: SOC2Bundle) -> list:
        """Build attestation statement section."""
        story = []
        story.append(Paragraph("Attestation Statement", self.styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=self.BORDER_COLOR))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(bundle.attestation_statement, self.styles["BodyText"]))

        if bundle.auditor_notes:
            story.append(Spacer(1, 0.3 * inch))
            story.append(Paragraph("Auditor Notes", self.styles["CustomSubtitle"]))
            story.append(Paragraph(bundle.auditor_notes, self.styles["BodyText"]))

        return story

    # =========================================================================
    # Executive Debrief PDF Builders
    # =========================================================================

    def _build_exec_cover(self, bundle: ExecutiveDebriefBundle) -> list:
        """Build executive debrief cover page."""
        story = []
        story.append(Spacer(1, 2 * inch))
        story.append(Paragraph("EXECUTIVE BRIEFING", self.styles["CustomTitle"]))
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("AI Governance Incident Summary", self.styles["CustomSubtitle"]))
        story.append(Spacer(1, 0.5 * inch))

        # Risk level indicator
        risk_color = self.ACCENT_COLOR if bundle.risk_level == "high" else self.SECONDARY_COLOR
        story.append(
            Paragraph(
                f"Risk Level: <font color='{risk_color.hexval()}'><b>{bundle.risk_level.upper()}</b></font>",
                self.styles["CustomSubtitle"],
            )
        )

        story.append(Spacer(1, inch))
        story.append(
            Paragraph(
                f"Generated: {bundle.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                self.styles["BodyText"],
            )
        )
        if bundle.prepared_for:
            story.append(Paragraph(f"Prepared for: {bundle.prepared_for}", self.styles["BodyText"]))
        story.append(Paragraph(f"Prepared by: {bundle.prepared_by}", self.styles["BodyText"]))
        story.append(Paragraph(f"Classification: {bundle.classification}", self.styles["BodyText"]))
        return story

    def _build_exec_summary(self, bundle: ExecutiveDebriefBundle) -> list:
        """Build executive summary section."""
        story = []
        story.append(Paragraph("Incident Summary", self.styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=self.BORDER_COLOR))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(bundle.incident_summary, self.styles["BodyText"]))

        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("Business Impact", self.styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=self.BORDER_COLOR))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(bundle.business_impact, self.styles["BodyText"]))

        # Key facts table
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("Key Facts", self.styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=self.BORDER_COLOR))
        story.append(Spacer(1, 0.2 * inch))

        data = [
            ["Incident ID", bundle.incident_id],
            ["Policy Violated", bundle.policy_violated],
            ["Violation Time", bundle.violation_time.strftime("%Y-%m-%d %H:%M:%S UTC")],
            ["Detection Time", bundle.detection_time.strftime("%Y-%m-%d %H:%M:%S UTC")],
            ["Remediation Status", bundle.remediation_status.upper()],
        ]

        table = Table(data, colWidths=[2 * inch, 4 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), self.LIGHT_GRAY),
                    ("TEXTCOLOR", (0, 0), (0, -1), self.PRIMARY_COLOR),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, self.BORDER_COLOR),
                ]
            )
        )
        story.append(table)
        return story

    def _build_recommendations(self, bundle: ExecutiveDebriefBundle) -> list:
        """Build recommendations section."""
        story = []
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("Recommended Actions", self.styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=self.BORDER_COLOR))
        story.append(Spacer(1, 0.2 * inch))

        for i, action in enumerate(bundle.recommended_actions, 1):
            story.append(Paragraph(f"{i}. {action}", self.styles["BodyText"]))

        return story

    def _build_exec_metrics(self, bundle: ExecutiveDebriefBundle) -> list:
        """Build executive metrics section."""
        story = []
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("Key Metrics", self.styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=self.BORDER_COLOR))
        story.append(Spacer(1, 0.2 * inch))

        data = [
            ["Time to Detect", f"{bundle.time_to_detect_seconds}s"],
            ["Cost Incurred", f"${bundle.cost_incurred_cents / 100:.2f}"],
        ]

        if bundle.time_to_contain_seconds:
            data.append(["Time to Contain", f"{bundle.time_to_contain_seconds}s"])

        if bundle.cost_prevented_cents:
            data.append(["Cost Prevented (Est.)", f"${bundle.cost_prevented_cents / 100:.2f}"])

        table = Table(data, colWidths=[2 * inch, 2 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), self.LIGHT_GRAY),
                    ("TEXTCOLOR", (0, 0), (0, -1), self.PRIMARY_COLOR),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, self.BORDER_COLOR),
                ]
            )
        )
        story.append(table)
        return story


# Singleton instance
_pdf_renderer: Optional[PDFRenderer] = None


def get_pdf_renderer() -> PDFRenderer:
    """Get or create PDFRenderer singleton."""
    global _pdf_renderer
    if _pdf_renderer is None:
        _pdf_renderer = PDFRenderer()
    return _pdf_renderer
