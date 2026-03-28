# API Reference

Complete reference for all public classes and methods in aigov-shield, organized by module.

## Core Types

**Module:** `aigov_shield.core.types`

### Enums

#### `GovernanceLayer`
```python
class GovernanceLayer(str, Enum):
    PREVENTION = "prevention"
    ACCOUNTABILITY = "accountability"
    MEASUREMENT = "measurement"
```

#### `NISTFunction`
```python
class NISTFunction(str, Enum):
    GOVERN = "govern"
    MAP = "map"
    MEASURE = "measure"
    MANAGE = "manage"
```

#### `GuardAction`
```python
class GuardAction(Enum):
    BLOCK = "block"
    REDACT = "redact"
    FLAG = "flag"
    PASSTHROUGH = "passthrough"
```

#### `RedactionMode`
```python
class RedactionMode(str, Enum):
    MASK = "mask"
    HASH = "hash"
    PARTIAL = "partial"
    REMOVE = "remove"
```

#### `PIICategory`
```python
class PIICategory(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    NATIONAL_ID = "national_id"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    DATE_OF_BIRTH = "date_of_birth"
    ADDRESS = "address"
    PASSPORT = "passport"
    IBAN = "iban"
```

#### `PrivilegeCategory`
```python
class PrivilegeCategory(str, Enum):
    ATTORNEY_CLIENT = "attorney_client"
    WORK_PRODUCT = "work_product"
    SETTLEMENT = "settlement"
```

#### `BiasCategory`
```python
class BiasCategory(str, Enum):
    GENDER = "gender"
    RACIAL_ETHNIC = "racial_ethnic"
    AGE = "age"
    DISABILITY = "disability"
    SOCIOECONOMIC = "socioeconomic"
```

#### `SensitivityLevel`
```python
class SensitivityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
```

#### `ContentType`
```python
class ContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
```

---

## Prevention Layer

**Module:** `aigov_shield.prevention`

### `GuardResult`

Dataclass returned by all guard checks.

| Field | Type | Description |
|---|---|---|
| `passed` | `bool` | Whether the content passed |
| `action_taken` | `GuardAction` | Action applied |
| `original_text` | `str` | Input text |
| `modified_text` | `str | None` | Modified text (redaction only) |
| `violations` | `list[dict[str, Any]]` | Detected violations |
| `confidence` | `float` | Detection confidence (0.0--1.0) |
| `guard_name` | `str` | Name of the guard |
| `execution_time_ms` | `float` | Execution time in milliseconds |
| `metadata` | `dict[str, Any]` | Additional metadata |

### `BaseGuard`

Abstract base class for all guards.

```python
BaseGuard(name: str, on_violation: GuardAction = GuardAction.BLOCK, confidence_threshold: float = 0.5)
```

**Methods:**

- `check(text: str, context: dict | None = None) -> GuardResult` -- Check text against the guard's rules (abstract).
- `__call__(text: str, context: dict | None = None) -> GuardResult` -- Alias for `check()`.

### `PIIGuard`

```python
PIIGuard(
    on_violation: GuardAction = GuardAction.REDACT,
    confidence_threshold: float = 0.5,
    categories: list[PIICategory] | None = None,
    redaction_mode: RedactionMode = RedactionMode.MASK,
)
```

**Methods:**

- `check(text: str, context: dict | None = None) -> GuardResult` -- Scan text for PII.

### `PrivilegeGuard`

```python
PrivilegeGuard(
    on_violation: GuardAction = GuardAction.BLOCK,
    confidence_threshold: float = 0.5,
    categories: list[PrivilegeCategory] | None = None,
)
```

**Methods:**

- `check(text: str, context: dict | None = None) -> GuardResult` -- Scan text for legally privileged content.

### `ToxicityGuard`

```python
ToxicityGuard(
    on_violation: GuardAction = GuardAction.BLOCK,
    confidence_threshold: float = 0.5,
    categories: list[str] | None = None,
    custom_patterns: dict[str, list[str]] | None = None,
    classifier_fn: Callable[[str], tuple[bool, float]] | None = None,
)
```

**Methods:**

- `check(text: str, context: dict | None = None) -> GuardResult` -- Scan text for toxic content.

### `TopicGuard`

```python
TopicGuard(
    on_violation: GuardAction = GuardAction.BLOCK,
    confidence_threshold: float = 0.5,
    allowed_topics: list[str] | None = None,
    blocked_topics: list[str] | None = None,
    blocked_keywords: dict[str, list[str]] | None = None,
)
```

**Methods:**

- `check(text: str, context: dict | None = None) -> GuardResult` -- Scan text for topical violations.

### `PromptInjectionGuard`

```python
PromptInjectionGuard(
    on_violation: GuardAction = GuardAction.BLOCK,
    confidence_threshold: float = 0.5,
    custom_patterns: list[tuple[str, str, float]] | None = None,
)
```

**Methods:**

- `check(text: str, context: dict | None = None) -> GuardResult` -- Scan text for injection attempts.

### `GuardChain`

```python
GuardChain(
    guards: list[BaseGuard],
    execution_mode: ExecutionMode = ExecutionMode.RUN_ALL,
    priority_threshold: int = 0,
)
```

**Methods:**

- `run(text: str, context: dict | None = None) -> ChainResult` -- Run text through all guards.
- `__call__(text: str, context: dict | None = None) -> ChainResult` -- Alias for `run()`.

### `ChainResult`

Dataclass returned by `GuardChain.run()`.

| Field | Type | Description |
|---|---|---|
| `passed` | `bool` | Whether all guards passed |
| `results` | `list[GuardResult]` | Individual guard results |
| `failed_guards` | `list[str]` | Names of failed guards |
| `total_execution_time_ms` | `float` | Total execution time |
| `execution_mode` | `str` | Execution mode used |
| `metadata` | `dict[str, Any]` | Additional metadata |

**Properties:**

- `modified_text -> str | None` -- Final modified text after all redactions.

### `ExecutionMode`

```python
class ExecutionMode(Enum):
    FAIL_FAST = "fail_fast"
    RUN_ALL = "run_all"
    PRIORITY = "priority"
```

---

## Accountability Layer

**Module:** `aigov_shield.accountability`

### `ChainOfCustody`

```python
ChainOfCustody(storage_backend: str = "memory")
```

**Methods:**

- `add_record(interaction_type: str, content: str, actor: str, model_id: str | None = None, input_hash: str | None = None, documents_referenced: list[str] | None = None, guard_results: list[dict] | None = None, metadata: dict | None = None) -> CustodyRecord` -- Add a record to the chain.
- `verify_chain() -> tuple[bool, list[str]]` -- Verify the integrity of the chain.
- `get_record(record_id: str) -> CustodyRecord | None` -- Retrieve a record by ID.
- `get_chain() -> list[CustodyRecord]` -- Return a copy of the full chain.
- `export_json() -> str` -- Export as JSON.
- `export_jsonl() -> str` -- Export as JSON Lines.
- `export_csv() -> str` -- Export as CSV.
- `__len__() -> int` -- Number of records in the chain.

### `CustodyRecord`

Dataclass representing a single chain record.

| Field | Type | Description |
|---|---|---|
| `record_id` | `str` | UUID v4 identifier |
| `timestamp` | `str` | ISO 8601 timestamp |
| `interaction_type` | `str` | Type of interaction |
| `content_hash` | `str` | SHA-256 hash of content |
| `previous_record_hash` | `str` | Previous record's hash or `"GENESIS"` |
| `actor` | `str` | Actor identifier |
| `model_id` | `str | None` | Model identifier |
| `input_hash` | `str | None` | Input hash |
| `documents_referenced` | `list[str]` | Document IDs |
| `guard_results` | `list[dict]` | Guard results |
| `metadata` | `dict` | Additional metadata |
| `record_hash` | `str` | Computed hash of all fields |

**Methods:**

- `compute_hash() -> str` -- Compute SHA-256 hash of all fields except `record_hash`.
- `to_dict() -> dict` -- Convert to dictionary.

### `EvidenceLogger`

```python
EvidenceLogger(case_id: str, storage: str = "memory")
```

**Methods:**

- `log_retrieval(query: str, documents_retrieved: list[str], retrieval_method: str = "unknown", relevance_scores: list[float] | None = None, metadata: dict | None = None) -> str` -- Log a retrieval event. Returns the record ID.
- `log_generation(prompt: str, response: str, model: str = "unknown", documents_used: list[str] | None = None, guard_results: list[dict] | None = None, confidence: float | None = None, metadata: dict | None = None) -> str` -- Log a generation event. Returns the record ID.
- `log_event(event_type: str, description: str, metadata: dict | None = None) -> str` -- Log a generic event. Returns the record ID.
- `get_record(record_id: str) -> dict | None` -- Retrieve a record by ID.
- `get_records(event_type: str | None = None) -> list[dict]` -- Get records, optionally filtered by type.
- `get_chain() -> ChainOfCustody` -- Return the underlying chain.
- `verify_integrity() -> tuple[bool, list[str]]` -- Verify evidence chain integrity.
- `export(format: str = "json") -> str` -- Export records as `"json"`, `"jsonl"`, or `"csv"`.

### `DocumentTracker`

```python
DocumentTracker()
```

**Methods:**

- `register_document(doc_id: str, path: str, content_hash: str, metadata: dict | None = None) -> TrackedDocument` -- Register a document.
- `get_document(doc_id: str) -> TrackedDocument | None` -- Retrieve a tracked document.
- `record_usage(output_id: str, documents_used: list[str], chunks_used: list[dict] | None = None, metadata: dict | None = None) -> UsageRecord` -- Record document usage.
- `get_provenance(output_id: str) -> dict | None` -- Get provenance chain for an output.
- `get_document_usage(doc_id: str) -> list[str]` -- Get output IDs that used a document.
- `export(format: str = "json") -> str` -- Export tracking data.

### `DecisionRecorder`

```python
DecisionRecorder()
```

**Methods:**

- `record_decision(decision_id: str) -> DecisionContext` -- Create a context manager for recording a decision.
- `export_decision(decision_id: str) -> dict | None` -- Export a decision trail.
- `list_decisions() -> list[str]` -- List all decision IDs.

### `DecisionContext`

Context manager for recording decision steps.

**Methods:**

- `log_step(step_name: str, **kwargs) -> None` -- Log a step with arbitrary data.

### Export Functions

- `export_to_json(records: list[dict]) -> str` -- Export as pretty-printed JSON.
- `export_to_jsonl(records: list[dict]) -> str` -- Export as JSON Lines.
- `export_to_csv(records: list[dict]) -> str` -- Export as CSV with flattened nested dicts.
- `flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict` -- Flatten nested dictionary.

---

## Measurement Layer

**Module:** `aigov_shield.measurement`

### `EvaluationResult`

Dataclass returned by all evaluators.

| Field | Type | Description |
|---|---|---|
| `metric_name` | `str` | Name of the metric |
| `score` | `float` | Score (0.0--1.0) |
| `passed` | `bool` | Whether threshold was met |
| `threshold` | `float` | Pass/fail threshold |
| `details` | `list[dict]` | Per-item breakdown |
| `summary` | `dict` | Aggregate statistics |
| `nist_function` | `str` | NIST AI RMF function |

### `BaseEvaluator`

```python
BaseEvaluator(threshold: float = 0.9)
```

**Methods:**

- `evaluate(data: list[dict[str, str]]) -> EvaluationResult` -- Evaluate a dataset (abstract).

### `PIIEvaluator`

```python
PIIEvaluator(threshold: float = 0.95, categories: list[PIICategory] | None = None)
```

**Methods:**

- `evaluate(data: list[dict[str, str]]) -> EvaluationResult` -- Evaluate PII leakage. Data items must have a `"text"` key.

### `PrivilegeEvaluator`

```python
PrivilegeEvaluator(threshold: float = 0.95, categories: list[PrivilegeCategory] | None = None)
```

**Methods:**

- `evaluate(data: list[dict[str, str]]) -> EvaluationResult` -- Evaluate privilege disclosure. Data items must have a `"text"` key.

### `GroundingEvaluator`

```python
GroundingEvaluator(threshold: float = 0.7, similarity_threshold: float = 0.3)
```

**Methods:**

- `evaluate(data: list[dict[str, str]]) -> EvaluationResult` -- Evaluate factual grounding. Data items must have `"output"` and `"context"` keys.

### `BiasEvaluator`

```python
BiasEvaluator(threshold: float = 0.95, sensitivity: str = "medium")
```

**Methods:**

- `evaluate(data: list[dict[str, str]]) -> EvaluationResult` -- Evaluate demographic bias. Data items must have a `"text"` key.

### `ComplianceScorer`

```python
ComplianceScorer(
    pii_weight: float = 0.25,
    privilege_weight: float = 0.25,
    grounding_weight: float = 0.25,
    bias_weight: float = 0.25,
    pass_threshold: float = 0.7,
)
```

**Methods:**

- `evaluate(data: list[dict[str, str]], context_column: str | None = None) -> dict[str, Any]` -- Run all evaluators and return composite results.

**Return dict keys:** `nist_compliance_score`, `function_scores`, `overall_pass`, `per_function_pass`, `recommendations`, `evaluator_results`.

### `DriftMonitor`

```python
DriftMonitor(alert_threshold: float = 0.1)
```

**Methods:**

- `compare(baseline_results: dict[str, EvaluationResult], current_results: dict[str, EvaluationResult]) -> dict[str, Any]` -- Compare two evaluation runs.

**Return dict keys:** `metrics`, `alerts`, `summary`.

---

## Integrations

**Module:** `aigov_shield.integrations`

### `GovernanceCallbackHandler`

LangChain callback handler. Requires `langchain-core`.

```python
GovernanceCallbackHandler(
    guards: list[BaseGuard] | None = None,
    evidence_logger: EvidenceLogger | None = None,
    chain_of_custody: ChainOfCustody | None = None,
    check_inputs: bool = True,
    check_outputs: bool = True,
)
```

**Properties:**

- `last_results -> list[GuardResult]` -- Results from the most recent guard checks.

### `GovernedOpenAI`

Drop-in OpenAI client wrapper. Requires `openai`.

```python
GovernedOpenAI(
    api_key: str | None = None,
    guards: list[BaseGuard] | None = None,
    custody: ChainOfCustody | None = None,
    evidence_logger: EvidenceLogger | None = None,
    **client_kwargs,
)
```

**Attributes:**

- `chat.completions.create(**kwargs) -> Any` -- Create a governed chat completion.

### `GovernedChatCompletions`

Lower-level governed completions wrapper.

```python
GovernedChatCompletions(
    client: Any,
    guards: list[BaseGuard],
    custody: ChainOfCustody | None = None,
    evidence_logger: EvidenceLogger | None = None,
)
```

**Methods:**

- `create(**kwargs) -> Any` -- Create a chat completion with governance checks.

**Properties:**

- `last_results -> list[GuardResult]` -- Results from the most recent guard checks.

### `GovernanceMiddleware`

FastAPI/Starlette middleware. Requires `starlette`.

```python
GovernanceMiddleware(
    app: Any,
    guards: list[BaseGuard] | None = None,
    check_requests: bool = True,
    check_responses: bool = True,
    custody: ChainOfCustody | None = None,
    evidence_logger: EvidenceLogger | None = None,
    excluded_paths: list[str] | None = None,
)
```

---

## Reporting

**Module:** `aigov_shield.reporting`

### `NISTComplianceReport`

```python
NISTComplianceReport(results: dict[str, Any])
```

**Methods:**

- `save_html(path: str) -> None` -- Save report as HTML.
- `save_json(path: str) -> None` -- Save report as JSON.

### `NISTReportSection`

Dataclass representing a section of the NIST report.

### Report Functions

- `generate_guard_report(results: list[GuardResult]) -> str` -- Generate HTML guard report.
- `save_guard_report(results: list[GuardResult], path: str) -> None` -- Save guard report to file.
- `generate_json_report(results: list[GuardResult]) -> str` -- Generate JSON guard report.
- `save_json_report(results: list[GuardResult], path: str) -> None` -- Save JSON report to file.

---

## CLI

**Entry point:** `aigov-shield`

### Commands

```
aigov-shield guard <text> [--guards pii,privilege,...] [--action block|redact|flag]
aigov-shield evaluate --input <file.jsonl> [--output <file>] [--format json|html]
aigov-shield verify-chain --input <chain.jsonl>
aigov-shield report --input <results.json> --output <report> [--format json|html]
aigov-shield --version
```
