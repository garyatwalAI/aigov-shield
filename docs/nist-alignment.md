# NIST AI RMF Alignment

aigov-shield is designed around the NIST AI Risk Management Framework (AI RMF 1.0). This document explains how each component maps to the four core NIST functions: GOVERN, MAP, MEASURE, and MANAGE.

## NIST AI RMF Overview

The NIST AI RMF defines four core functions for managing AI risk:

| Function | Purpose |
|---|---|
| **GOVERN** | Establish and maintain governance structures, policies, and accountability mechanisms |
| **MAP** | Identify and document AI system context, capabilities, and impacts |
| **MEASURE** | Quantify and track AI risks, performance, and trustworthiness |
| **MANAGE** | Allocate resources and take actions to address identified risks |

## Component Mapping

### GOVERN Function

The GOVERN function is about establishing accountability and oversight structures. aigov-shield maps three components to this function:

#### ChainOfCustody (Accountability Layer)

**NIST Alignment:** GOVERN 1.1 -- Legal and regulatory requirements are identified. GOVERN 1.5 -- Ongoing monitoring is in place.

The chain of custody provides a tamper-evident audit trail that satisfies regulatory requirements for record-keeping. Each record is cryptographically linked to the previous record, allowing independent verification of the entire chain.

```python
from aigov_shield.accountability import ChainOfCustody

custody = ChainOfCustody()
custody.add_record(interaction_type="query", content="user input", actor="system")

# Verify the chain at any time
valid, errors = custody.verify_chain()
```

#### EvidenceLogger (Accountability Layer)

**NIST Alignment:** GOVERN 1.2 -- Trustworthy AI characteristics are identified. GOVERN 6.1 -- Policies and procedures are in place for AI system accountability.

The evidence logger creates structured, litigation-ready records that capture retrievals, generations, and governance events. These records satisfy evidentiary requirements for legal proceedings.

#### DecisionRecorder (Accountability Layer)

**NIST Alignment:** GOVERN 1.4 -- Organizational practices promote transparency. GOVERN 6.2 -- Mechanisms are in place for accountability.

The decision recorder captures explainable decision trails, documenting every step in the decision process with timestamps and data. This supports transparency and explainability requirements.

#### ComplianceScorer (Measurement Layer)

**NIST Alignment:** GOVERN 5.1 -- Organizational policies address AI risks. GOVERN 5.2 -- Mechanisms for compliance are established.

The composite compliance score aggregates all evaluator results into a single governance metric, providing an executive-level view of compliance posture.

### MAP Function

The MAP function is about understanding the AI system and its context. aigov-shield maps two components to this function:

#### DocumentTracker (Accountability Layer)

**NIST Alignment:** MAP 1.1 -- Intended purposes and context of use are documented. MAP 3.4 -- Risks from third-party data are assessed.

The document tracker establishes provenance by registering source documents and tracking which outputs used which sources. This maps the relationship between inputs and outputs, a core MAP function.

```python
from aigov_shield.accountability import DocumentTracker

tracker = DocumentTracker()
tracker.register_document(doc_id="doc-001", path="/data/source.pdf", content_hash="sha256-...")
tracker.record_usage(output_id="out-001", documents_used=["doc-001"])
provenance = tracker.get_provenance("out-001")
```

#### GroundingEvaluator (Measurement Layer)

**NIST Alignment:** MAP 2.3 -- Scientific integrity of the AI system is assessed. MAP 3.5 -- System outputs are compared to ground truth.

The grounding evaluator measures whether outputs are factually grounded in source material, directly assessing the relationship between system outputs and their supporting evidence.

### MEASURE Function

The MEASURE function is about quantifying AI risks. aigov-shield maps four components to this function:

#### PIIEvaluator

**NIST Alignment:** MEASURE 2.5 -- Privacy risks are assessed. MEASURE 2.6 -- Privacy-related metrics are tracked.

Quantifies the PII leakage rate across outputs, providing a measurable privacy risk metric.

```python
from aigov_shield.measurement import PIIEvaluator

evaluator = PIIEvaluator(threshold=0.95)
result = evaluator.evaluate([{"text": "output text here"}])
print(f"PII Leakage Rate: {result.summary['pii_leakage_rate']:.1%}")
```

#### PrivilegeEvaluator

**NIST Alignment:** MEASURE 2.5 -- Confidentiality risks are assessed. MEASURE 2.7 -- Security risks are quantified.

Measures the rate of privileged content disclosure, tracking a critical security metric for legal environments.

#### BiasEvaluator

**NIST Alignment:** MEASURE 2.6 -- Fairness metrics are tracked. MEASURE 2.11 -- Bias is identified and measured.

Detects demographic bias across five dimensions (gender, racial/ethnic, age, disability, socioeconomic), quantifying fairness risks.

#### DriftMonitor

**NIST Alignment:** MEASURE 3.2 -- AI system performance is monitored over time. MEASURE 3.3 -- Feedback from monitoring informs risk management.

Compares compliance metrics between evaluation runs to detect degradation, supporting continuous monitoring requirements.

### MANAGE Function

The MANAGE function is about taking action to address risks. aigov-shield maps five components to this function:

#### PrivilegeGuard (Prevention Layer)

**NIST Alignment:** MANAGE 2.2 -- Mechanisms to mitigate identified risks are implemented. MANAGE 4.1 -- Responses to identified risks are deployed.

Prevents disclosure of legally privileged content by actively blocking or redacting privileged communications before they reach end users.

#### PIIGuard (Prevention Layer)

**NIST Alignment:** MANAGE 2.2 -- Privacy protections are implemented. MANAGE 4.1 -- Data protection mechanisms are deployed.

Prevents PII leakage by detecting and redacting personally identifiable information in real time.

#### ToxicityGuard (Prevention Layer)

**NIST Alignment:** MANAGE 2.2 -- Safety mechanisms are implemented. MANAGE 4.1 -- Harmful content filters are deployed.

Prevents harmful content (hate speech, threats, harassment) from reaching end users through active detection and blocking.

#### TopicGuard (Prevention Layer)

**NIST Alignment:** MANAGE 2.4 -- AI system behavior is constrained to intended use. MANAGE 4.2 -- Boundaries on system behavior are enforced.

Enforces topical boundaries to keep the system operating within its intended domain, preventing unauthorized advice or off-topic outputs.

#### PromptInjectionGuard (Prevention Layer)

**NIST Alignment:** MANAGE 2.3 -- Security controls are implemented. MANAGE 4.1 -- Adversarial attack mitigations are deployed.

Prevents prompt injection attacks that could compromise system behavior, addressing adversarial robustness requirements.

## Complete Mapping Table

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

## ComplianceScorer NIST Function Scores

When using `ComplianceScorer`, results include scores mapped to each NIST function:

| Function | Score Calculation | Components |
|---|---|---|
| GOVERN | Weighted composite of all evaluators | All evaluators |
| MAP | Grounding evaluator score | GroundingEvaluator |
| MEASURE | Average of PII and bias scores | PIIEvaluator, BiasEvaluator |
| MANAGE | Privilege evaluator score | PrivilegeEvaluator |

```python
from aigov_shield.measurement import ComplianceScorer

scorer = ComplianceScorer()
results = scorer.evaluate(data)

for function, score in results["function_scores"].items():
    status = "PASS" if results["per_function_pass"][function] else "FAIL"
    print(f"  {function}: {score:.1%} [{status}]")
```
