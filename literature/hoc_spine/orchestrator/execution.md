# execution.py

**Path:** `backend/app/hoc/hoc_spine/orchestrator/lifecycle/drivers/execution.py`  
**Layer:** L4 — HOC Spine (Orchestrator)  
**Component:** Orchestrator

---

## Placement Card

```
File:            execution.py
Lives in:        orchestrator/
Role:            Orchestrator
Inbound:         IngestHandler, IndexHandler, ClassifyHandler
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Module: execution
Violations:      none
```

## Purpose

Module: execution
Purpose: Real execution implementations for knowledge plane lifecycle stages.

Wires:
    - Source: ConnectorRegistry for data source access
    - Target: Internal storage for processed data

Contains:
    - DataIngestionExecutor (GAP-159): Real data ingestion from connectors
    - IndexingExecutor (GAP-160): Real embedding generation and indexing
    - ClassificationExecutor (GAP-161): Real PII detection and classification

Acceptance Criteria:
    - AC-159-01: Data read via ConnectorRegistry
    - AC-159-02: Supports HTTP, SQL, File connector types
    - AC-159-03: Progress reported via JobProgressTracker
    - AC-159-04: Failures captured with retry support
    - AC-160-01: Embeddings generated for text content
    - AC-160-02: Vectors stored in VectorConnector
    - AC-160-03: Metadata indexed for search
    - AC-161-01: PII patterns detected
    - AC-161-02: Sensitivity levels assigned
    - AC-161-03: Classification evidence emitted

## Import Analysis

Pure stdlib — no application imports.

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `get_ingestion_executor() -> DataIngestionExecutor`

Get or create the singleton DataIngestionExecutor.

### `get_indexing_executor() -> IndexingExecutor`

Get or create the singleton IndexingExecutor.

### `get_classification_executor() -> ClassificationExecutor`

Get or create the singleton ClassificationExecutor.

### `reset_executors() -> None`

Reset all singletons (for testing).

## Classes

### `IngestionSourceType(str, Enum)`

Types of data sources for ingestion.

### `IngestionBatch`

A batch of ingested records.

#### Methods

- `__post_init__()` — _No docstring._

### `IngestionResult`

Result of data ingestion operation.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary.

### `DataIngestionExecutor`

Real data ingestion executor (GAP-159).

Reads data from configured connectors and prepares it for indexing.

Supported source types:
- HTTP: REST API endpoints via HttpConnectorService
- SQL: Database queries via SqlGatewayService
- FILE: File storage via FileConnector
- VECTOR: Existing vector stores via VectorConnector

#### Methods

- `__init__(batch_size: int, max_records: int, max_bytes: int)` — Initialize the ingestion executor.
- `async execute(plane_id: str, tenant_id: str, config: Dict[str, Any], progress_callback: Optional[callable]) -> IngestionResult` — Execute data ingestion from configured source.
- `async _get_connector(connector_id: Optional[str], tenant_id: str) -> Optional[Any]` — Get connector from registry.
- `async _ingest_from_http(plane_id: str, connector: Any, config: Dict[str, Any], progress_callback: Optional[callable]) -> IngestionResult` — Ingest data from HTTP connector.
- `async _ingest_from_sql(plane_id: str, connector: Any, config: Dict[str, Any], progress_callback: Optional[callable]) -> IngestionResult` — Ingest data from SQL connector.
- `async _ingest_from_file(plane_id: str, connector: Any, config: Dict[str, Any], progress_callback: Optional[callable]) -> IngestionResult` — Ingest data from file connector.
- `async _ingest_from_vector(plane_id: str, connector: Any, config: Dict[str, Any], progress_callback: Optional[callable]) -> IngestionResult` — Ingest metadata from existing vector store.
- `async _simulate_ingestion(plane_id: str, config: Dict[str, Any], progress_callback: Optional[callable]) -> IngestionResult` — Simulate ingestion for testing when no connector configured.

### `IndexingResult`

Result of indexing operation.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary.

### `IndexingExecutor`

Real indexing executor (GAP-160).

Generates embeddings and stores vectors for search.

Features:
- Text chunking for long documents
- Embedding generation (via configured provider)
- Vector upsert to VectorConnector
- Metadata indexing for filtering

#### Methods

- `__init__(chunk_size: int, chunk_overlap: int, embedding_dimension: int, batch_size: int)` — Initialize the indexing executor.
- `async execute(plane_id: str, tenant_id: str, ingestion_batches: List[IngestionBatch], config: Dict[str, Any], progress_callback: Optional[callable]) -> IndexingResult` — Execute indexing on ingested data.
- `async _get_vector_connector(connector_id: Optional[str], tenant_id: str) -> Optional[Any]` — Get vector connector from registry.
- `_extract_documents(batches: List[IngestionBatch]) -> List[Dict[str, Any]]` — Extract text documents from ingestion batches.
- `_chunk_documents(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]` — Split documents into chunks for embedding.
- `async _generate_embeddings(chunks: List[Dict[str, Any]], provider: str, progress_callback: Optional[callable]) -> List[Dict[str, Any]]` — Generate embeddings for chunks.
- `_simulate_embedding(text: str) -> List[float]` — Generate a simulated embedding (deterministic).
- `async _call_embedding_api(text: str, provider: str) -> List[float]` — Call embedding API (placeholder for real implementation).

### `SensitivityLevel(str, Enum)`

Data sensitivity levels.

### `PIIType(str, Enum)`

Types of PII detected.

### `PIIDetection`

A detected PII instance.

### `ClassificationResult`

Result of classification operation.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary.

### `ClassificationExecutor`

Real classification executor (GAP-161).

Analyzes data for:
- PII detection (emails, phones, SSNs, etc.)
- Sensitivity classification
- Content categorization

Features:
- Regex-based PII detection
- Configurable sensitivity thresholds
- Category inference from content

#### Methods

- `__init__(sample_size: int, pii_threshold: int)` — Initialize the classification executor.
- `async execute(plane_id: str, tenant_id: str, ingestion_batches: List[IngestionBatch], progress_callback: Optional[callable]) -> ClassificationResult` — Execute classification on ingested data.
- `_sample_records(batches: List[IngestionBatch]) -> List[Tuple[str, str]]` — Sample records for analysis.
- `_detect_pii(samples: List[Tuple[str, str]]) -> List[PIIDetection]` — Detect PII in sampled content.
- `_redact(value: str) -> str` — Partially redact a value for safe display.
- `_detect_categories(samples: List[Tuple[str, str]]) -> List[str]` — Detect content categories from samples.
- `_determine_sensitivity(pii_detections: List[PIIDetection], categories: List[str]) -> SensitivityLevel` — Determine sensitivity level based on analysis.

## Domain Usage

**Callers:** IngestHandler, IndexHandler, ClassifyHandler

## Export Contract

```yaml
exports:
  functions:
    - name: get_ingestion_executor
      signature: "get_ingestion_executor() -> DataIngestionExecutor"
      consumers: ["orchestrator"]
    - name: get_indexing_executor
      signature: "get_indexing_executor() -> IndexingExecutor"
      consumers: ["orchestrator"]
    - name: get_classification_executor
      signature: "get_classification_executor() -> ClassificationExecutor"
      consumers: ["orchestrator"]
    - name: reset_executors
      signature: "reset_executors() -> None"
      consumers: ["orchestrator"]
  classes:
    - name: IngestionSourceType
      methods: []
      consumers: ["orchestrator"]
    - name: IngestionBatch
      methods:
      consumers: ["orchestrator"]
    - name: IngestionResult
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: DataIngestionExecutor
      methods:
        - execute
      consumers: ["orchestrator"]
    - name: IndexingResult
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: IndexingExecutor
      methods:
        - execute
      consumers: ["orchestrator"]
    - name: SensitivityLevel
      methods: []
      consumers: ["orchestrator"]
    - name: PIIType
      methods: []
      consumers: ["orchestrator"]
    - name: PIIDetection
      methods: []
      consumers: ["orchestrator"]
    - name: ClassificationResult
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: ClassificationExecutor
      methods:
        - execute
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc.api.*"
    - "hoc_spine.adapters.*"
  forbidden_inbound:
  actual_imports:
    spine_internal: []
    l7_model: []
    external: []
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

