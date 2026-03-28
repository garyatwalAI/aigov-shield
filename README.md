[![PyPI version](https://img.shields.io/pypi/v/aigov-shield)](https://pypi.org/project/aigov-shield/)
[![Python versions](https://img.shields.io/pypi/pyversions/aigov-shield)](https://pypi.org/project/aigov-shield/)
[![Tests](https://img.shields.io/github/actions/workflow/status/garyatwalAI/aigov-shield/ci.yml?label=tests)](https://github.com/garyatwalAI/aigov-shield/actions)
[![License](https://img.shields.io/github/license/garyatwalAI/aigov-shield)](https://github.com/garyatwalAI/aigov-shield/blob/main/LICENSE)

# aigov-shield

Production-ready AI governance infrastructure for regulated industries -- prevention, accountability, and measurement in a single framework.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     aigov-shield                            │
├─────────────────────────────────────────────────────────────┤
│  LAYER 1: PREVENTION          Runtime Guardrails            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ Privilege │ │   PII    │ │ Toxicity │ │ Injection│      │
│  │  Guard   │ │  Guard   │ │  Guard   │ │  Guard   │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
├─────────────────────────────────────────────────────────────┤
│  LAYER 2: ACCOUNTABILITY      Evidence & Audit Trails       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ Chain of │ │ Evidence │ │ Document │ │ Decision │      │
│  │ Custody  │ │  Logger  │ │ Tracker  │ │ Recorder │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
├─────────────────────────────────────────────────────────────┤
│  LAYER 3: MEASUREMENT         Compliance Metrics            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │   PII    │ │Privilege │ │Grounding │ │   Bias   │      │
│  │Evaluator │ │Evaluator │ │Evaluator │ │Evaluator │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Installation

```bash
pip install aigov-shield
```

Install with all optional dependencies (LangChain, OpenAI, FastAPI):

```bash
pip install aigov-shield[all]
```

Or install specific extras:

```bash
pip install aigov-shield[langchain]
pip install aigov-shield[openai]
pip install aigov-shield[fastapi]
```

## Quick Start

```python
from aigov_shield.prevention import PIIGuard, PrivilegeGuard, GuardChain, GuardAction
from aigov_shield.accountability import ChainOfCustody, EvidenceLogger
from aigov_shield.measurement import ComplianceScorer

# Layer 1: Prevention
chain = GuardChain([
    PIIGuard(on_violation=GuardAction.REDACT),
    PrivilegeGuard(on_violation=GuardAction.BLOCK),
])
result = chain.run("Contact john@example.com for the settlement offer of $500,000.")

# Layer 2: Accountability
custody = ChainOfCustody()
custody.add_record(interaction_type="query", content="user query", actor="system")

# Layer 3: Measurement
scorer = ComplianceScorer()
scores = scorer.evaluate([{"text": "Safe output with no PII.", "context": "source doc", "output": "Safe output with no PII."}])
print(f"Compliance Score: {scores['nist_compliance_score']:.1%}")
```

## Features

### Prevention Guards

Runtime guardrails that check content before it reaches end users. Guards detect and optionally block, redact, or flag non-compliant content.

```python
from aigov_shield.prevention import PIIGuard, GuardAction

guard = PIIGuard(on_violation=GuardAction.REDACT)
result = guard.check("Email me at john@example.com")
print(result.modified_text)  # "Email me at [EMAIL]"
```

Available guards:
- **PIIGuard** -- Detects and redacts 10 categories of PII (email, phone, SSN, credit card, etc.)
- **PrivilegeGuard** -- Detects attorney-client privilege, work product, and settlement communications
- **ToxicityGuard** -- Detects hate speech, threats, self-harm, harassment, and explicit content
- **TopicGuard** -- Enforces topical boundaries with allowed/blocked topic lists
- **PromptInjectionGuard** -- Detects prompt injection attacks across 5 attack categories

### Accountability & Audit

Tamper-evident audit trails that create defensible records of every interaction.

```python
from aigov_shield.accountability import ChainOfCustody

custody = ChainOfCustody()
custody.add_record(
    interaction_type="query",
    content="What is the settlement amount?",
    actor="user",
)
custody.add_record(
    interaction_type="response",
    content="The settlement amount is [REDACTED].",
    actor="system",
)

# Verify chain integrity
valid, errors = custody.verify_chain()
print(f"Chain valid: {valid}")
```

Components:
- **ChainOfCustody** -- Hash-linked tamper-evident audit chain
- **EvidenceLogger** -- Litigation-ready structured evidence logging
- **DocumentTracker** -- Document provenance and usage tracking
- **DecisionRecorder** -- Explainable decision trail recording

### Compliance Measurement

Quantify compliance across multiple dimensions with NIST AI RMF-aligned scoring.

```python
from aigov_shield.measurement import ComplianceScorer

scorer = ComplianceScorer()
results = scorer.evaluate([
    {"text": "Contact john@example.com for details.", "context": "source doc", "output": "Contact john@example.com for details."},
])
print(f"Score: {results['nist_compliance_score']:.1%}")
print(f"Pass: {results['overall_pass']}")
```

Evaluators:
- **PIIEvaluator** -- Measures PII leakage rate across outputs
- **PrivilegeEvaluator** -- Measures privileged content disclosure rate
- **GroundingEvaluator** -- Measures hallucination rate via Jaccard similarity
- **BiasEvaluator** -- Detects demographic bias across 5 dimensions
- **ComplianceScorer** -- Weighted composite NIST compliance score
- **DriftMonitor** -- Tracks compliance drift between evaluation runs

## NIST AI RMF Alignment

| Layer | Component | NIST Function | Purpose |
|---|---|---|---|
| Prevention | PrivilegeGuard | MANAGE | Prevents privileged communication disclosure |
| Prevention | PIIGuard | MANAGE | Prevents PII leakage |
| Prevention | ToxicityGuard | MANAGE | Prevents harmful content |
| Prevention | TopicGuard | MANAGE | Enforces topical boundaries |
| Prevention | PromptInjectionGuard | MANAGE | Prevents prompt injection |
| Accountability | ChainOfCustody | GOVERN | Tamper-evident audit trail |
| Accountability | EvidenceLogger | GOVERN | Structured evidence logging |
| Accountability | DocumentTracker | MAP | Document provenance tracking |
| Accountability | DecisionRecorder | GOVERN | Decision point recording |
| Measurement | PIIEvaluator | MEASURE | PII leakage rate |
| Measurement | PrivilegeEvaluator | MEASURE | Privilege disclosure rate |
| Measurement | GroundingEvaluator | MAP | Hallucination rate |
| Measurement | BiasEvaluator | MEASURE | Demographic bias |
| Measurement | ComplianceScorer | GOVERN | Composite compliance score |
| Measurement | DriftMonitor | MEASURE | Compliance drift detection |

## Integrations

### LangChain

```python
from aigov_shield.integrations import GovernanceCallbackHandler
from aigov_shield.prevention import PIIGuard, PrivilegeGuard

handler = GovernanceCallbackHandler(
    guards=[PIIGuard(), PrivilegeGuard()],
)
# Pass to any LangChain LLM or chain as a callback
```

### OpenAI

```python
from aigov_shield.integrations import GovernedOpenAI
from aigov_shield.prevention import PIIGuard

client = GovernedOpenAI(
    api_key="sk-...",
    guards=[PIIGuard()],
)
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}],
)
```

### FastAPI

```python
from fastapi import FastAPI
from aigov_shield.integrations import GovernanceMiddleware
from aigov_shield.prevention import PIIGuard

app = FastAPI()
app.add_middleware(
    GovernanceMiddleware,
    guards=[PIIGuard()],
)
```

## Use Cases

- **Legal / Litigation Support** -- Prevent disclosure of privileged communications, maintain tamper-evident audit trails for e-discovery
- **Insurance Claims** -- Redact PII from claims processing outputs, track document provenance for regulatory compliance
- **Financial Services** -- Enforce topical boundaries to prevent unauthorized financial advice, measure compliance drift over time
- **Healthcare Compliance** -- Detect and redact protected health information, generate NIST-aligned compliance reports

## CLI

```bash
# Run guards on text
aigov-shield guard "Contact john@example.com for the settlement offer" --guards pii,privilege

# Evaluate a dataset
aigov-shield evaluate --input data.jsonl --output report.json

# Verify a chain of custody
aigov-shield verify-chain --input chain.jsonl

# Generate a NIST compliance report
aigov-shield report --input results.json --output report.html --format html
```

## Documentation

- [Architecture](docs/architecture.md)
- [Getting Started](docs/getting-started.md)
- [Prevention Guide](docs/prevention-guide.md)
- [Accountability Guide](docs/accountability-guide.md)
- [Measurement Guide](docs/measurement-guide.md)
- [NIST Alignment](docs/nist-alignment.md)
- [Integrations](docs/integrations.md)
- [API Reference](docs/api-reference.md)

## Contributing

Contributions are welcome. Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to get started.

## License

Apache 2.0. See [LICENSE](LICENSE) for details.

## Citation

```bibtex
@software{aigov_shield,
  title = {aigov-shield: AI Governance Infrastructure for Regulated Industries},
  author = {Atwal, Gary},
  year = {2026},
  url = {https://github.com/garyatwalAI/aigov-shield},
  license = {Apache-2.0}
}
```
