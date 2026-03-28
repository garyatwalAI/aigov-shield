# Integrations

aigov-shield provides drop-in integrations for LangChain, OpenAI, and FastAPI. Each integration automatically applies guards, maintains audit trails, and logs evidence.

## LangChain

The `GovernanceCallbackHandler` integrates with LangChain's callback system to automatically govern all LLM interactions.

### Installation

```bash
pip install aigov-shield[langchain]
```

### Basic Setup

```python
from aigov_shield.integrations import GovernanceCallbackHandler
from aigov_shield.prevention import PIIGuard, PrivilegeGuard, GuardAction

handler = GovernanceCallbackHandler(
    guards=[
        PIIGuard(on_violation=GuardAction.FLAG),
        PrivilegeGuard(on_violation=GuardAction.FLAG),
    ],
)

# Use with any LangChain LLM
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4", callbacks=[handler])
response = llm.invoke("Summarize the settlement terms.")

# Check guard results
for result in handler.last_results:
    print(f"{result.guard_name}: {'PASS' if result.passed else 'FAIL'}")
```

### With Evidence Logging

```python
from aigov_shield.integrations import GovernanceCallbackHandler
from aigov_shield.prevention import PIIGuard, PrivilegeGuard, GuardAction
from aigov_shield.accountability import ChainOfCustody, EvidenceLogger

custody = ChainOfCustody()
logger = EvidenceLogger(case_id="CASE-2026-001")

handler = GovernanceCallbackHandler(
    guards=[
        PIIGuard(on_violation=GuardAction.FLAG),
        PrivilegeGuard(on_violation=GuardAction.FLAG),
    ],
    evidence_logger=logger,
    chain_of_custody=custody,
    check_inputs=True,
    check_outputs=True,
)
```

### Configuration Options

| Parameter | Type | Default | Description |
|---|---|---|---|
| `guards` | `list[BaseGuard]` | `[]` | Guards to run on inputs and outputs |
| `evidence_logger` | `EvidenceLogger` | `None` | Logger for litigation-ready evidence |
| `chain_of_custody` | `ChainOfCustody` | `None` | Chain of custody for audit trails |
| `check_inputs` | `bool` | `True` | Whether to check LLM inputs |
| `check_outputs` | `bool` | `True` | Whether to check LLM outputs |

### Supported Callbacks

The handler responds to the following LangChain lifecycle events:

| Event | Behavior |
|---|---|
| `on_llm_start` | Runs guards on input prompts |
| `on_llm_end` | Runs guards on LLM output |
| `on_llm_error` | Logs errors to evidence logger |
| `on_chain_start` | Logs chain inputs to custody |
| `on_chain_end` | Logs chain outputs to custody |
| `on_tool_start` | Logs tool usage to custody |
| `on_retriever_end` | Logs document retrieval to evidence logger |

### With RAG Chains

The callback handler automatically tracks document retrieval when used with LangChain retrieval chains:

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4", callbacks=[handler])

# When used with a retriever, on_retriever_end logs all retrieved documents
# to the evidence logger with document IDs and retrieval method
```

## OpenAI

The `GovernedOpenAI` wrapper provides a drop-in replacement for the OpenAI client with automatic governance.

### Installation

```bash
pip install aigov-shield[openai]
```

### Basic Setup

```python
from aigov_shield.integrations import GovernedOpenAI
from aigov_shield.prevention import PIIGuard, PrivilegeGuard, GuardAction

client = GovernedOpenAI(
    api_key="sk-...",
    guards=[
        PIIGuard(on_violation=GuardAction.FLAG),
        PrivilegeGuard(on_violation=GuardAction.BLOCK),
    ],
)

# Use exactly like the standard OpenAI client
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello, how can I help?"}],
)
```

### With Audit Trail

```python
from aigov_shield.integrations import GovernedOpenAI
from aigov_shield.prevention import PIIGuard, PrivilegeGuard, GuardAction
from aigov_shield.accountability import ChainOfCustody, EvidenceLogger

custody = ChainOfCustody()
logger = EvidenceLogger(case_id="CASE-2026-001")

client = GovernedOpenAI(
    api_key="sk-...",
    guards=[
        PIIGuard(on_violation=GuardAction.REDACT),
        PrivilegeGuard(on_violation=GuardAction.BLOCK),
    ],
    custody=custody,
    evidence_logger=logger,
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Summarize the case."}],
)

# Both input and output are logged to the custody chain and evidence logger
valid, errors = custody.verify_chain()
print(f"Chain valid: {valid}, Records: {len(custody)}")
```

### Blocking Behavior

When a guard with `BLOCK` action detects a violation in the input, `GovernedOpenAI` raises a `ValueError` before the API call is made:

```python
from aigov_shield.integrations import GovernedOpenAI
from aigov_shield.prevention import PrivilegeGuard, GuardAction

client = GovernedOpenAI(
    api_key="sk-...",
    guards=[PrivilegeGuard(on_violation=GuardAction.BLOCK)],
)

try:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Share the privileged settlement terms."}],
    )
except ValueError as e:
    print(f"Blocked: {e}")
```

### Configuration Options

| Parameter | Type | Default | Description |
|---|---|---|---|
| `api_key` | `str` | `None` | OpenAI API key |
| `guards` | `list[BaseGuard]` | `[]` | Guards to apply |
| `custody` | `ChainOfCustody` | `None` | Chain of custody |
| `evidence_logger` | `EvidenceLogger` | `None` | Evidence logger |
| `**client_kwargs` | | | Additional OpenAI client arguments |

### GovernedChatCompletions

For more control, you can use `GovernedChatCompletions` directly with an existing OpenAI client:

```python
from openai import OpenAI
from aigov_shield.integrations import GovernedChatCompletions
from aigov_shield.prevention import PIIGuard

client = OpenAI(api_key="sk-...")
governed = GovernedChatCompletions(
    client=client,
    guards=[PIIGuard()],
)

response = governed.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}],
)
```

## FastAPI

The `GovernanceMiddleware` integrates with FastAPI/Starlette to apply governance checks at the API level.

### Installation

```bash
pip install aigov-shield[fastapi]
```

### Basic Setup

```python
from fastapi import FastAPI
from aigov_shield.integrations import GovernanceMiddleware
from aigov_shield.prevention import PIIGuard, PrivilegeGuard, GuardAction

app = FastAPI()

app.add_middleware(
    GovernanceMiddleware,
    guards=[
        PIIGuard(on_violation=GuardAction.BLOCK),
        PrivilegeGuard(on_violation=GuardAction.BLOCK),
    ],
)

@app.post("/chat")
async def chat(message: dict):
    return {"response": "Hello!"}
```

### With Audit Trail

```python
from fastapi import FastAPI
from aigov_shield.integrations import GovernanceMiddleware
from aigov_shield.prevention import PIIGuard, PrivilegeGuard, GuardAction
from aigov_shield.accountability import ChainOfCustody, EvidenceLogger

custody = ChainOfCustody()
logger = EvidenceLogger(case_id="API-SESSION-001")

app = FastAPI()
app.add_middleware(
    GovernanceMiddleware,
    guards=[
        PIIGuard(on_violation=GuardAction.BLOCK),
        PrivilegeGuard(on_violation=GuardAction.BLOCK),
    ],
    custody=custody,
    evidence_logger=logger,
    check_requests=True,
    check_responses=True,
    excluded_paths=["/health", "/docs", "/openapi.json"],
)
```

### Blocking Behavior

When a guard with `BLOCK` action detects a violation in the request body, the middleware returns a 422 response:

```json
{
    "error": "governance_violation",
    "guard": "pii_guard",
    "violations": 2,
    "execution_time_ms": 1.234
}
```

### Configuration Options

| Parameter | Type | Default | Description |
|---|---|---|---|
| `guards` | `list[BaseGuard]` | `[]` | Guards to run on request/response bodies |
| `check_requests` | `bool` | `True` | Whether to check request bodies |
| `check_responses` | `bool` | `True` | Whether to check response bodies |
| `custody` | `ChainOfCustody` | `None` | Chain of custody |
| `evidence_logger` | `EvidenceLogger` | `None` | Evidence logger |
| `excluded_paths` | `list[str]` | `[]` | URL paths to skip governance checks |

### Excluding Paths

Use `excluded_paths` to skip governance checks on health checks, documentation, and other non-sensitive endpoints:

```python
app.add_middleware(
    GovernanceMiddleware,
    guards=[PIIGuard()],
    excluded_paths=["/health", "/metrics", "/docs", "/openapi.json"],
)
```

## Integration Patterns

### End-to-End Governance

Combine all three layers with an integration for comprehensive governance:

```python
from aigov_shield.prevention import PIIGuard, PrivilegeGuard, GuardAction
from aigov_shield.accountability import ChainOfCustody, EvidenceLogger
from aigov_shield.measurement import ComplianceScorer
from aigov_shield.integrations import GovernedOpenAI

# Set up accountability
custody = ChainOfCustody()
logger = EvidenceLogger(case_id="SESSION-001")

# Set up governed client
client = GovernedOpenAI(
    api_key="sk-...",
    guards=[
        PIIGuard(on_violation=GuardAction.REDACT),
        PrivilegeGuard(on_violation=GuardAction.BLOCK),
    ],
    custody=custody,
    evidence_logger=logger,
)

# Use the client for all interactions
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Summarize the case."}],
)

# Periodically evaluate compliance
scorer = ComplianceScorer()
# ... collect outputs and evaluate
```
