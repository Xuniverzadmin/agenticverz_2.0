"""
C2 Prediction API (Minimal, Advisory-Only)

This is a CANARY implementation, not a system.
Purpose: Prove predictions can exist without influencing truth.

Scenarios:
- C2-T1: Incident Risk
- C2-T2: Spend Spike
- C2-T3: Policy Drift (HIGH-RISK, strictest semantic constraints)

C2 Contract:
- All predictions are advisory (I-C2-1)
- Predictions expire and are disposable (I-C2-5)
- No control path influence (I-C2-2)
- No truth mutation (I-C2-3)
- Replay is blind to predictions (I-C2-4)

C2-T2 Rules (Spend Spike):
- No schema changes
- No derived metrics (store raw values only)
- No cache layer (DB only)

C2-T3 Rules (Policy Drift) — STRICTEST SEMANTIC CONSTRAINTS:
- No schema changes
- No derived metrics or pattern computation
- No cache layer (DB only)
- MANDATORY advisory language: "observed", "may indicate", "similarity"
- FORBIDDEN language: "violation", "will violate", "non-compliant", "risk"
- Zero enforcement influence (no blocking, throttling, incidents)

Reference: PIN-222
"""

from datetime import datetime, timedelta, timezone
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.db import get_session
from app.models.prediction import PredictionEvent

router = APIRouter(prefix="/api/v1/c2/predictions", tags=["predictions", "c2"])


def get_db():
    """Get database session."""
    return next(get_session())


@router.post("/incident-risk")
def create_incident_risk_prediction(
    tenant_id: str = Query(..., description="Tenant ID"),
    subject_type: str = Query(..., description="Subject type (tenant, worker, run)"),
    subject_id: str = Query(..., description="Subject identifier"),
    confidence_score: float = Query(..., ge=0.0, le=1.0, description="Confidence 0-1"),
    db: Session = Depends(get_db),
):
    """
    Create ONE advisory prediction for incident risk.

    This is C2-T1: minimal implementation, no generalization.
    Purpose: Prove predictions can be created without side effects.
    """
    prediction_id = uuid4()
    now = datetime.now(timezone.utc)

    p = PredictionEvent(
        id=prediction_id,
        tenant_id=tenant_id,
        prediction_type="incident_risk",
        subject_type=subject_type,
        subject_id=subject_id,
        confidence_score=confidence_score,
        prediction_value={"risk_level": "elevated" if confidence_score > 0.5 else "normal"},
        contributing_factors=[],
        is_advisory=True,  # ALWAYS TRUE (I-C2-1, enforced by DB CHECK)
        created_at=now,
        expires_at=now + timedelta(minutes=30),
        notes="C2-T1 minimal advisory prediction",
    )

    db.add(p)
    db.commit()
    db.refresh(p)

    return {
        "prediction_id": str(p.id),
        "advisory": True,
        "expires_at": p.expires_at.isoformat(),
    }


@router.get("")
def list_predictions(
    subject_type: str = Query(..., description="Subject type"),
    subject_id: str = Query(..., description="Subject identifier"),
    db: Session = Depends(get_db),
) -> List[dict]:
    """
    List non-expired predictions for a subject.

    O4-ready surface (API exists, UI doesn't).
    Expired predictions are invisible.
    """
    now = datetime.now(timezone.utc)

    rows = (
        db.query(PredictionEvent)
        .filter(
            PredictionEvent.subject_type == subject_type,
            PredictionEvent.subject_id == subject_id,
            PredictionEvent.expires_at > now,
        )
        .all()
    )

    return [
        {
            "prediction_id": str(r.id),
            "prediction_type": r.prediction_type,
            "confidence_score": r.confidence_score,
            "advisory": True,  # Always true
            "expires_at": r.expires_at.isoformat() if r.expires_at else None,
        }
        for r in rows
    ]


@router.post("/spend-spike")
def create_spend_spike_prediction(
    subject_type: str = Query(..., description="Subject type (tenant, workflow, agent)"),
    subject_id: str = Query(..., description="Subject identifier"),
    confidence_score: float = Query(..., ge=0.0, le=1.0, description="Confidence 0-1"),
    projected_spend: float = Query(..., ge=0.0, description="Projected spend (raw value)"),
    baseline_spend: float = Query(..., ge=0.0, description="Baseline spend (raw value)"),
    db: Session = Depends(get_db),
):
    """
    Create ONE advisory prediction for spend spike.

    C2-T2: minimal implementation, no enforcement.
    Purpose: Prove spend predictions can exist without influencing behavior.

    Rules:
    - No derived metrics computed here (no spike_ratio)
    - Raw values only in prediction_value
    - No schema changes from T1
    """
    prediction_id = uuid4()
    now = datetime.now(timezone.utc)

    # Use subject_id as tenant_id for spend predictions
    # (spend is inherently tenant-scoped)
    tenant_id = subject_id if subject_type == "tenant" else f"{subject_type}:{subject_id}"

    p = PredictionEvent(
        id=prediction_id,
        tenant_id=tenant_id,
        prediction_type="spend_spike",
        subject_type=subject_type,
        subject_id=subject_id,
        confidence_score=confidence_score,
        # Raw values only - no derived metrics
        prediction_value={
            "projected_spend": projected_spend,
            "baseline_spend": baseline_spend,
        },
        contributing_factors=[],
        is_advisory=True,  # ALWAYS TRUE (I-C2-1, enforced by DB CHECK)
        created_at=now,
        expires_at=now + timedelta(minutes=30),
        notes="C2-T2 spend spike advisory",
    )

    db.add(p)
    db.commit()
    db.refresh(p)

    return {
        "prediction_id": str(p.id),
        "prediction_type": "spend_spike",
        "advisory": True,
        "expires_at": p.expires_at.isoformat(),
    }


@router.post("/policy-drift")
def create_policy_drift_prediction(
    subject_type: str = Query(..., description="Subject type (tenant, workflow, agent)"),
    subject_id: str = Query(..., description="Subject identifier"),
    confidence_score: float = Query(..., ge=0.0, le=1.0, description="Confidence 0-1"),
    observed_pattern: str = Query(..., description="Raw observation (no computation)"),
    reference_policy_type: str = Query(None, description="Policy type observed (optional)"),
    db: Session = Depends(get_db),
):
    """
    Create ONE advisory prediction for policy drift observation.

    C2-T3: minimal implementation, STRICTEST semantic constraints.
    Purpose: Prove policy observations can exist without influencing enforcement.

    SEMANTIC RULES (D1 - NON-NEGOTIABLE):
    - Language MUST be advisory: "observed", "may indicate", "similarity"
    - Language MUST NOT imply: "violation", "will violate", "non-compliant"
    - This prediction has ZERO enforcement influence
    - No blocking, throttling, or incident creation

    Rules:
    - No derived metrics or pattern computation
    - Raw observation only in prediction_value
    - No schema changes from T1/T2
    """
    prediction_id = uuid4()
    now = datetime.now(timezone.utc)

    # Use subject_id as tenant_id for policy observations
    tenant_id = subject_id if subject_type == "tenant" else f"{subject_type}:{subject_id}"

    p = PredictionEvent(
        id=prediction_id,
        tenant_id=tenant_id,
        prediction_type="policy_drift",
        subject_type=subject_type,
        subject_id=subject_id,
        confidence_score=confidence_score,
        # Raw observation only - no derived metrics, no pattern scoring
        prediction_value={
            "observed_pattern": observed_pattern,
            "reference_policy_type": reference_policy_type,
        },
        contributing_factors=[],
        is_advisory=True,  # ALWAYS TRUE (I-C2-1, enforced by DB CHECK)
        created_at=now,
        expires_at=now + timedelta(minutes=30),
        # D1-compliant language: "advisory observation", not "drift detected"
        notes="C2-T3 advisory observation (may indicate similarity to past patterns)",
    )

    db.add(p)
    db.commit()
    db.refresh(p)

    return {
        "prediction_id": str(p.id),
        "prediction_type": "policy_drift",
        "advisory": True,
        "observation_note": "This is an advisory observation only",
        "expires_at": p.expires_at.isoformat(),
    }
