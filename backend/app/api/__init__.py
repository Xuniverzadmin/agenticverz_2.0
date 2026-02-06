# TOMBSTONE_EXPIRY: 2026-03-04
# DEPRECATED: All routers migrated to app/hoc/api/
# Do not add new code here. See PIN-526.
#
# This package is FROZEN and scheduled for deletion.
# All L2 API routers have been migrated to:
#   - app/hoc/api/cus/* (customer-facing)
#   - app/hoc/api/fdr/* (founder-facing)
#
# Legacy imports continue to work via app.api.X
# but new code should import from app.hoc.api.*

"""
Legacy API Package - DEPRECATED

WARNING: This package is deprecated (PIN-526).
All routers have been migrated to app/hoc/api/.
This package will be deleted after TOMBSTONE_EXPIRY.

Migration:
  - Customer APIs: app/hoc/api/cus/{domain}/
  - Founder APIs: app/hoc/api/fdr/{domain}/
"""
