# Layer: L2.1 — Facade (Auth Identity Lane)
# capability_id: CAP-006
"""
Facade for the HOC Identity auth lane.

Aggregates auth routers into a single router bundle for consumption
by app.py. Follows the L2.1 facade contract: imports L2 routers only,
exports router bundles (no endpoints).
"""

from app.hoc.api.auth import ROUTERS as AUTH_ROUTERS

ROUTERS = AUTH_ROUTERS
