# Layer: L4 — Domain Engines
# Product: system-wide
# Reference: GAP-055 (CustomerDataSource model)
"""
Customer Data Source Services (GAP-055)

Provides models and services for customer-owned data sources
including configuration, status tracking, and access management.

This module provides:
    - CustomerDataSource: Data source model
    - DataSourceConfig: Configuration model
    - DataSourceRegistry: Service for managing data sources
    - Helper functions for quick access
"""

from app.services.datasources.datasource_model import (
    CustomerDataSource,
    DataSourceConfig,
    DataSourceError,
    DataSourceRegistry,
    DataSourceStatus,
    DataSourceType,
    create_datasource,
    get_datasource,
    get_datasource_registry,
    list_datasources,
)

__all__ = [
    "CustomerDataSource",
    "DataSourceConfig",
    "DataSourceError",
    "DataSourceRegistry",
    "DataSourceStatus",
    "DataSourceType",
    "create_datasource",
    "get_datasource",
    "get_datasource_registry",
    "list_datasources",
]
