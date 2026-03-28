# Architecture

aigov-shield is structured around three independent but composable layers. Each layer addresses a distinct governance concern and maps directly to functions defined in the NIST AI Risk Management Framework (AI RMF 1.0).

## Design Philosophy

1. **Prevention stops bad outputs in real time.** Guards inspect content before it reaches end users, blocking, redacting, or flagging violations as they occur.

2. **Accountability creates defensible records.** Every interaction is recorded in a tamper-evident chain of custody so that the full history of inputs, outputs, and decisions can be independently verified.

3. **Measurement quantifies compliance over time.** Evaluators score datasets against compliance criteria and track whether governance posture is improving or degrading.

4. **Each layer is independent but composable.** You can adopt any single layer without the others, or combine all three for end-to-end governance coverage.

5. **The three layers map to NIST AI RMF functions.** Prevention maps to MANAGE, accountability maps to GOVERN, and measurement maps to MEASURE and MAP.

## Three-Layer Architecture

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

## Layer 1: Prevention

The prevention layer provides runtime guardrails that inspect text content and take immediate action when violations are detected. All guards extend `BaseGuard` and implement the `check()` method, which accepts a text string and returns a `GuardResult`.

**Guards can be configured with one of four violation actions:**

| Action | Behavior |
|---|---|
| `BLOCK` | Reject the content entirely |
| `REDACT` | Replace sensitive content with placeholders |
| `FLAG` | Allow the content but mark it for review |
| `PASSTHROUGH` | Allow the content without modification |

Guards can be composed into a `GuardChain` that runs them in sequence. The chain supports three execution modes:

- **FAIL_FAST** -- Stop at the first guard failure
- **RUN_ALL** -- Run all guards and aggregate results
- **PRIORITY** -- Run guards in priority order, stop at a configurable threshold

When a guard in REDACT mode modifies text, the modified text is passed forward to the next guard in the chain.

## Layer 2: Accountability

The accountability layer produces tamper-evident records of every interaction. It is designed for regulated environments where audit trails must withstand legal scrutiny.

**ChainOfCustody** is the foundation. Each record contains a SHA-256 hash of its content plus a reference to the previous record's hash, forming a linked chain. Tampering with any record breaks the chain, and `verify_chain()` detects this.

**EvidenceLogger** builds on top of ChainOfCustody to provide structured logging for retrievals, generations, and generic events. Each log entry is backed by a custody record.

**DocumentTracker** registers documents and tracks which outputs used which source documents. This establishes provenance from output back to source.

**DecisionRecorder** captures decision trails as a series of named steps with timestamps, providing explainability for governance decisions.

## Layer 3: Measurement

The measurement layer evaluates datasets of outputs against compliance criteria. Each evaluator extends `BaseEvaluator` and returns an `EvaluationResult` with a score between 0.0 and 1.0.

**ComplianceScorer** orchestrates all evaluators and produces a weighted composite score mapped to NIST AI RMF functions:

- **GOVERN** -- Overall composite compliance score
- **MAP** -- Factual grounding score (hallucination detection)
- **MEASURE** -- Average of PII and bias scores
- **MANAGE** -- Privilege disclosure score

**DriftMonitor** compares two evaluation runs and classifies each metric as improved, degraded, or stable. Metrics that degrade beyond the alert threshold trigger alerts.

## How the Layers Interact

The layers are designed to work independently or together. A typical end-to-end flow looks like this:

```
User Input
    |
    v
[Layer 1: Prevention]
    |-- GuardChain runs PIIGuard, PrivilegeGuard, ToxicityGuard
    |-- Violations are blocked/redacted/flagged
    |-- GuardResults are captured
    |
    v
[Layer 2: Accountability]
    |-- ChainOfCustody records the interaction
    |-- EvidenceLogger logs the guard results
    |-- DocumentTracker records which documents were used
    |-- DecisionRecorder captures the decision trail
    |
    v
[Layer 3: Measurement]  (periodic / batch)
    |-- ComplianceScorer evaluates accumulated outputs
    |-- DriftMonitor compares against baseline
    |-- NIST compliance reports are generated
    |
    v
Compliance Dashboard / Audit Export
```

Prevention operates in real time on every request. Accountability records are created alongside prevention checks. Measurement runs periodically over batches of outputs to produce aggregate compliance scores.

## NIST AI RMF Mapping

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

## Module Structure

```
src/aigov_shield/
    core/           # Shared types, config, exceptions, registry
    prevention/     # Layer 1: Runtime guards
    accountability/ # Layer 2: Audit trails and evidence
    measurement/    # Layer 3: Compliance evaluators
    reporting/      # NIST reports, HTML reports, JSON exports
    integrations/   # LangChain, OpenAI, FastAPI adapters
    cli/            # Command-line interface
```
