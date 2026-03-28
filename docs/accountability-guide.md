# Accountability Guide

The accountability layer creates tamper-evident records of every interaction, designed for regulated environments where audit trails must withstand legal scrutiny.

## Chain of Custody

`ChainOfCustody` is the foundation of the accountability layer. It maintains a hash-linked chain of records where each record contains a SHA-256 hash of its content and a reference to the previous record's hash.

### Creating a Chain

```python
from aigov_shield.accountability import ChainOfCustody

custody = ChainOfCustody()
```

### Adding Records

```python
record = custody.add_record(
    interaction_type="query",
    content="What is the settlement amount?",
    actor="user",
)

record = custody.add_record(
    interaction_type="response",
    content="The settlement amount is $250,000.",
    actor="system",
    model_id="gpt-4",
    documents_referenced=["doc-001", "doc-002"],
    guard_results=[
        {"guard": "pii_guard", "passed": True, "confidence": 0.0},
    ],
    metadata={"session_id": "sess-123"},
)
```

### Interaction Types

Common interaction types include:

| Type | Description |
|---|---|
| `query` | User or system query |
| `response` | System response |
| `document_retrieval` | Document retrieval event |
| `guard_check` | Guard check event |

### CustodyRecord Fields

| Field | Type | Description |
|---|---|---|
| `record_id` | `str` | UUID v4 identifier |
| `timestamp` | `str` | ISO 8601 timestamp (UTC) |
| `interaction_type` | `str` | Type of interaction |
| `content_hash` | `str` | SHA-256 hash of the content |
| `previous_record_hash` | `str` | Hash of the previous record, or `"GENESIS"` |
| `actor` | `str` | Identifier of the acting entity |
| `model_id` | `str or None` | Model identifier |
| `input_hash` | `str or None` | Hash of the input |
| `documents_referenced` | `list[str]` | Referenced document IDs |
| `guard_results` | `list[dict]` | Guard check results |
| `metadata` | `dict` | Additional metadata |
| `record_hash` | `str` | Computed hash of all fields |

### Verifying Chain Integrity

```python
valid, errors = custody.verify_chain()

if valid:
    print(f"Chain verified: {len(custody)} records, all hashes valid.")
else:
    print(f"Chain INVALID: {len(errors)} error(s) found:")
    for error in errors:
        print(f"  - {error}")
```

Verification checks two things for each record:
1. The `record_hash` matches a recomputed hash of all other fields
2. The `previous_record_hash` matches the preceding record's hash (or is `"GENESIS"` for the first record)

### Retrieving Records

```python
# Get a specific record by ID
record = custody.get_record("some-uuid-here")

# Get all records
all_records = custody.get_chain()
```

### Exporting

```python
# Export as JSON
json_str = custody.export_json()

# Export as JSON Lines
jsonl_str = custody.export_jsonl()

# Export as CSV
csv_str = custody.export_csv()
```

## Evidence Logger

`EvidenceLogger` provides a higher-level API for creating litigation-ready evidence records. Each logged event is backed by a tamper-evident chain of custody.

### Creating a Logger

```python
from aigov_shield.accountability import EvidenceLogger

logger = EvidenceLogger(case_id="CASE-2026-001")
```

### Logging Retrievals

```python
record_id = logger.log_retrieval(
    query="settlement amount case 456",
    documents_retrieved=["doc-001", "doc-002", "doc-003"],
    retrieval_method="vector_search",
    relevance_scores=[0.95, 0.87, 0.72],
    metadata={"search_index": "litigation_docs"},
)
```

### Logging Generations

```python
record_id = logger.log_generation(
    prompt="Summarize the settlement terms from doc-001.",
    response="The settlement terms include a payment of $250,000...",
    model="gpt-4",
    documents_used=["doc-001"],
    guard_results=[
        {"guard": "pii_guard", "passed": True},
        {"guard": "privilege_guard", "passed": False},
    ],
    confidence=0.92,
)
```

### Logging Generic Events

```python
record_id = logger.log_event(
    event_type="user_action",
    description="User approved the redacted response for delivery.",
    metadata={"approved_by": "reviewer-42"},
)
```

### Retrieving and Filtering Records

```python
# Get all records
all_records = logger.get_records()

# Filter by event type
retrievals = logger.get_records(event_type="retrieval")
generations = logger.get_records(event_type="generation")

# Get a specific record
record = logger.get_record(record_id)
```

### Verifying Integrity

```python
valid, errors = logger.verify_integrity()
```

### Exporting Evidence

```python
json_output = logger.export(format="json")
jsonl_output = logger.export(format="jsonl")
csv_output = logger.export(format="csv")
```

## Document Tracker

`DocumentTracker` registers documents and tracks which outputs used which source documents, establishing provenance from output back to source.

### Registering Documents

```python
from aigov_shield.accountability import DocumentTracker

tracker = DocumentTracker()

doc = tracker.register_document(
    doc_id="doc-001",
    path="/data/contracts/settlement_agreement.pdf",
    content_hash="sha256-abc123...",
    metadata={"type": "contract", "date": "2026-01-15"},
)
```

### Recording Usage

```python
usage = tracker.record_usage(
    output_id="output-001",
    documents_used=["doc-001", "doc-002"],
    chunks_used=[
        {
            "doc_id": "doc-001",
            "page": 3,
            "start_char": 150,
            "end_char": 450,
            "chunk_text": "The settlement amount shall be...",
        },
        {
            "doc_id": "doc-002",
            "page": 1,
            "start_char": 0,
            "end_char": 200,
        },
    ],
    metadata={"model": "gpt-4"},
)
```

### Querying Provenance

```python
# Get full provenance chain for an output
provenance = tracker.get_provenance("output-001")
# Returns: {
#     "output_id": "output-001",
#     "timestamp": "...",
#     "documents": [...],
#     "chunks": [...],
#     "metadata": {...},
# }

# Find all outputs that used a specific document
output_ids = tracker.get_document_usage("doc-001")
```

### Exporting Tracking Data

```python
json_output = tracker.export(format="json")
jsonl_output = tracker.export(format="jsonl")
csv_output = tracker.export(format="csv")
```

## Decision Recorder

`DecisionRecorder` captures decision trails as a series of named steps with timestamps, providing explainability for governance decisions.

### Recording a Decision

```python
from aigov_shield.accountability import DecisionRecorder

recorder = DecisionRecorder()

# Use as a context manager for automatic timing
with recorder.record_decision("decision-001") as ctx:
    ctx.log_step("input_received", query="What is the settlement?")
    ctx.log_step("documents_retrieved", doc_count=3, method="vector_search")
    ctx.log_step("guard_check", guards_run=2, all_passed=True)
    ctx.log_step("response_generated", model="gpt-4", confidence=0.92)
    ctx.log_step("response_delivered", redacted=False)
```

### Exporting Decision Trails

```python
trail = recorder.export_decision("decision-001")
# Returns: {
#     "decision_id": "decision-001",
#     "started_at": "...",
#     "completed_at": "...",
#     "steps": [
#         {"step_name": "input_received", "timestamp": "...", "data": {...}},
#         ...
#     ],
#     "metadata": {},
# }

# List all recorded decisions
decision_ids = recorder.list_decisions()
```

## Export Utilities

The `aigov_shield.accountability` module includes standalone export functions:

```python
from aigov_shield.accountability import export_to_json, export_to_jsonl, export_to_csv, flatten_dict

records = [{"key": "value", "nested": {"a": 1}}]

json_str = export_to_json(records)    # Pretty-printed JSON
jsonl_str = export_to_jsonl(records)  # One JSON object per line
csv_str = export_to_csv(records)      # CSV with flattened nested dicts

# flatten_dict is useful for preparing nested data for CSV
flat = flatten_dict({"a": {"b": {"c": 1}}})
# {"a.b.c": 1}
```

## Best Practices

1. **Create one ChainOfCustody per session or case.** This keeps chains manageable and allows per-case verification.

2. **Always record both inputs and outputs.** A complete audit trail requires recording what went in and what came out.

3. **Include guard results in custody records.** This ties prevention checks to the audit trail for complete traceability.

4. **Use EvidenceLogger for litigation workflows.** It provides structured logging tailored to legal evidence requirements.

5. **Verify chain integrity periodically.** Run `verify_chain()` at the end of each session and before exporting evidence.

6. **Export in JSONL for large chains.** JSONL is more efficient for large chains and supports streaming.
