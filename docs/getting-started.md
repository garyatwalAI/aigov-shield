# Getting Started

This guide walks through installing aigov-shield and using each of the three governance layers.

## 1. Installation

Install the core package:

```bash
pip install aigov-shield
```

Install with all optional integration dependencies:

```bash
pip install aigov-shield[all]
```

Or install specific extras as needed:

```bash
pip install aigov-shield[langchain]   # LangChain callback handler
pip install aigov-shield[openai]      # OpenAI governed wrapper
pip install aigov-shield[fastapi]     # FastAPI middleware
```

### Requirements

- Python 3.10 or later
- No required external dependencies for the core package

## 2. Running Your First Guard

Guards are the building blocks of the prevention layer. Each guard inspects text and returns a `GuardResult`.

```python
from aigov_shield.prevention import PIIGuard, GuardAction

# Create a guard that redacts PII
guard = PIIGuard(on_violation=GuardAction.REDACT)

# Check some text
result = guard.check("Send payment to john@example.com, card 4111111111111111")

print(f"Passed: {result.passed}")           # False
print(f"Action: {result.action_taken}")     # GuardAction.REDACT
print(f"Output: {result.modified_text}")    # "Send payment to [EMAIL], card [CREDIT_CARD]"
print(f"Violations: {len(result.violations)}")  # 2
```

### Composing Multiple Guards

Use `GuardChain` to run multiple guards in sequence:

```python
from aigov_shield.prevention import (
    PIIGuard, PrivilegeGuard, ToxicityGuard,
    GuardChain, GuardAction, ExecutionMode,
)

chain = GuardChain(
    guards=[
        PIIGuard(on_violation=GuardAction.REDACT),
        PrivilegeGuard(on_violation=GuardAction.BLOCK),
        ToxicityGuard(on_violation=GuardAction.FLAG),
    ],
    execution_mode=ExecutionMode.RUN_ALL,
)

result = chain.run("Contact john@example.com about the settlement offer of $500,000.")

print(f"Overall passed: {result.passed}")
print(f"Failed guards: {result.failed_guards}")
print(f"Modified text: {result.modified_text}")
```

## 3. Setting Up Audit Logging

The accountability layer creates tamper-evident records for every interaction.

```python
from aigov_shield.accountability import ChainOfCustody, EvidenceLogger

# Option A: Direct chain of custody
custody = ChainOfCustody()
custody.add_record(
    interaction_type="query",
    content="What is the settlement amount?",
    actor="user",
)
custody.add_record(
    interaction_type="response",
    content="The settlement amount is $250,000.",
    actor="system",
    model_id="gpt-4",
)

# Verify the chain has not been tampered with
valid, errors = custody.verify_chain()
print(f"Chain valid: {valid}")  # True

# Option B: Evidence logger (higher-level API)
logger = EvidenceLogger(case_id="CASE-2026-001")
logger.log_retrieval(
    query="settlement amount",
    documents_retrieved=["doc-001", "doc-002"],
    retrieval_method="vector_search",
)
logger.log_generation(
    prompt="What is the settlement amount?",
    response="The settlement amount is $250,000.",
    model="gpt-4",
    documents_used=["doc-001"],
)

# Export the evidence trail
print(logger.export(format="json"))
```

## 4. Running Compliance Evaluation

The measurement layer evaluates batches of outputs against compliance criteria.

```python
from aigov_shield.measurement import ComplianceScorer

# Prepare your dataset -- each item needs at least a "text" field
data = [
    {
        "text": "The report shows quarterly growth of 15%.",
        "context": "The quarterly financial report indicates growth of 15%.",
        "output": "The report shows quarterly growth of 15%.",
    },
    {
        "text": "Contact support at help@company.com for assistance.",
        "context": "Our support team is available during business hours.",
        "output": "Contact support at help@company.com for assistance.",
    },
]

scorer = ComplianceScorer()
results = scorer.evaluate(data)

print(f"NIST Compliance Score: {results['nist_compliance_score']:.1%}")
print(f"Overall Pass: {results['overall_pass']}")
print(f"Function Scores: {results['function_scores']}")
print(f"Recommendations: {results['recommendations']}")
```

### Using Individual Evaluators

You can also run evaluators independently:

```python
from aigov_shield.measurement import PIIEvaluator, BiasEvaluator

pii_eval = PIIEvaluator(threshold=0.95)
pii_result = pii_eval.evaluate([
    {"text": "No PII here."},
    {"text": "Email: john@example.com"},
])
print(f"PII Score: {pii_result.score:.1%}")
print(f"Leakage Rate: {pii_result.summary['pii_leakage_rate']:.1%}")

bias_eval = BiasEvaluator(sensitivity="high")
bias_result = bias_eval.evaluate([
    {"text": "All candidates were evaluated on their qualifications."},
])
print(f"Bias Score: {bias_result.score:.1%}")
```

## 5. Generating a Report

Use the CLI to generate NIST compliance reports:

```bash
# Evaluate a dataset and save results
aigov-shield evaluate --input data.jsonl --output results.json

# Generate an HTML report from results
aigov-shield report --input results.json --output report.html --format html
```

Or generate reports programmatically:

```python
from aigov_shield.measurement import ComplianceScorer
from aigov_shield.reporting import NISTComplianceReport

scorer = ComplianceScorer()
results = scorer.evaluate(data)

report = NISTComplianceReport(results)
report.save_html("compliance_report.html")
report.save_json("compliance_report.json")
```

## Next Steps

- [Prevention Guide](prevention-guide.md) -- Detailed configuration for each guard
- [Accountability Guide](accountability-guide.md) -- Full audit trail setup
- [Measurement Guide](measurement-guide.md) -- Evaluator configuration and drift monitoring
- [Integrations](integrations.md) -- LangChain, OpenAI, and FastAPI setup
- [NIST Alignment](nist-alignment.md) -- Detailed NIST AI RMF mapping
- [API Reference](api-reference.md) -- Complete API documentation
