# Layer: L6 — Driver
# AUDIENCE: FOUNDER
# Role: Data access layer for ops incident service

from typing import List, Optional
from sqlalchemy import select
from sqlmodel import Session

# TODO: Import required models
# from app.models.incidents import YourModel


class OpsIncidentServiceReadService:
    """
    Pure data access - no business logic.

    Extracted from: ops_incident_service.py
    DB operations found: 2
    """

    def __init__(self, session: Session):
        self.session = session

    # TODO: Extract DB operations from original file
    # Example patterns to extract:
    # result = session.execute(

    # def get_by_id(self, id: str) -> Optional[YourModel]:
    #     stmt = select(YourModel).where(YourModel.id == id)
    #     return self.session.execute(stmt).scalar_one_or_none()

    # def get_by_tenant(self, tenant_id: str) -> List[YourModel]:
    #     stmt = select(YourModel).where(YourModel.tenant_id == tenant_id)
    #     return self.session.execute(stmt).scalars().all()
