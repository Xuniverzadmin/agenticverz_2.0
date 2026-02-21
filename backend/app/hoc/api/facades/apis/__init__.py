# Layer: L2.1 — Facade (APIs Publication Lane)
# capability_id: CAP-011
"""
Facade for the APIs publication lane.

Aggregates publication routers (ledger + swagger views) into a single
router bundle for consumption by app.py.
"""

from app.hoc.api.apis.cus_publication import router as CUS_PUBLICATION_ROUTER

ROUTERS = [CUS_PUBLICATION_ROUTER]
