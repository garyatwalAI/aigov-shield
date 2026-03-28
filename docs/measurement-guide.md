# Measurement Guide

The measurement layer evaluates datasets of outputs against compliance criteria and tracks whether governance posture is improving or degrading over time.

## Core Concepts

Every evaluator extends `BaseEvaluator` and implements the `evaluate()` method, which accepts a list of dictionaries and returns an `EvaluationResult`.

### EvaluationResult

| Field | Type | Description |
|---|---|---|
| `metric_name` | `str` | Name of the metric |
| `score` | `float` | Score from 0.0 to 1.0 (higher is better) |
| `passed` | `bool` | Whether the score meets the threshold |
| `threshold` | `float` | The pass/fail threshold |
| `details` | `list[dict]` | Per-item breakdown |
| `summary` | `dict` | Aggregate statistics |
| `nist_function` | `str` | NIST AI RMF function this maps to |

## PIIEvaluator

Measures PII leakage rate across a dataset of outputs. Uses `PIIGuard` internally to scan each item.

### Configuration

```python
from aigov_shield.measurement import PIIEvaluator
from aigov_shield.core.types import PIICategory

# Default: 95% threshold, all PII categories
evaluator = PIIEvaluator()

# Custom threshold and categories
evaluator = PIIEvaluator(
    threshold=0.99,
    categories=[PIICategory.EMAIL, PIICategory.SSN, PIICategory.CREDIT_CARD],
)
```

### Usage

```python
data = [
    {"text": "No PII in this output."},
    {"text": "Contact john@example.com for details."},
    {"text": "Call 555-123-4567 to confirm."},
    {"text": "Clean output with no personal data."},
]

result = evaluator.evaluate(data)

print(f"Score: {result.score:.1%}")                          # 50.0%
print(f"Passed: {result.passed}")                            # False
print(f"Leakage Rate: {result.summary['pii_leakage_rate']:.1%}")  # 50.0%
print(f"Total PII Found: {result.summary['pii_count_total']}")
print(f"By Category: {result.summary['pii_by_category']}")
```

### Summary Fields

| Field | Description |
|---|---|
| `pii_leakage_rate` | Fraction of items containing PII |
| `pii_count_total` | Total number of PII instances found |
| `pii_by_category` | Count of PII by category |
| `items_evaluated` | Total items evaluated |
| `items_with_pii` | Number of items containing PII |

## PrivilegeEvaluator

Measures the rate of privileged content disclosure across outputs. Uses `PrivilegeGuard` internally.

### Configuration

```python
from aigov_shield.measurement import PrivilegeEvaluator
from aigov_shield.core.types import PrivilegeCategory

evaluator = PrivilegeEvaluator(
    threshold=0.95,
    categories=[PrivilegeCategory.ATTORNEY_CLIENT, PrivilegeCategory.SETTLEMENT],
)
```

### Usage

```python
data = [
    {"text": "The project timeline is on track."},
    {"text": "This communication is privileged and confidential. Our attorney advises caution."},
]

result = evaluator.evaluate(data)

print(f"Score: {result.score:.1%}")
print(f"Disclosure Rate: {result.summary['privilege_disclosure_rate']:.1%}")
print(f"Average Confidence: {result.summary['average_confidence']:.2f}")
```

### Summary Fields

| Field | Description |
|---|---|
| `privilege_disclosure_rate` | Fraction of items containing privileged content |
| `privilege_by_category` | Count by privilege category |
| `average_confidence` | Average detection confidence |
| `items_evaluated` | Total items evaluated |
| `items_with_privilege` | Number of items with privileged content |

## GroundingEvaluator

Measures factual grounding by comparing each sentence in an output against a reference context using token-level Jaccard similarity.

### Configuration

```python
from aigov_shield.measurement import GroundingEvaluator

# Default: 70% threshold, 0.3 similarity threshold
evaluator = GroundingEvaluator()

# Stricter grounding requirements
evaluator = GroundingEvaluator(
    threshold=0.9,
    similarity_threshold=0.5,
)
```

### Data Format

The grounding evaluator expects `"output"` and `"context"` fields (not `"text"`):

```python
data = [
    {
        "output": "Revenue grew 15% in Q3 driven by new product launches.",
        "context": "Q3 results show 15% revenue growth attributed to new product launches in the consumer segment.",
    },
    {
        "output": "The company plans to expand to Mars by 2027.",
        "context": "The company announced plans to expand to three new domestic markets.",
    },
]

result = evaluator.evaluate(data)

print(f"Grounding Score: {result.score:.1%}")
print(f"Hallucination Rate: {result.summary['hallucination_rate']:.1%}")
print(f"Total Claims: {result.summary['total_claims']}")
print(f"Grounded Claims: {result.summary['grounded_claims']}")
```

### How It Works

1. Each output is split into sentences.
2. Sentences with fewer than 5 words are filtered out.
3. Each remaining sentence is tokenized and compared to the context using Jaccard similarity.
4. Sentences with similarity below the threshold are classified as ungrounded.
5. The grounding score is the fraction of grounded sentences.

### Summary Fields

| Field | Description |
|---|---|
| `grounding_score` | Average grounding score across items |
| `hallucination_rate` | 1.0 minus the grounding score |
| `total_claims` | Total sentences evaluated |
| `grounded_claims` | Number of grounded sentences |
| `ungrounded_claims` | List of ungrounded sentence texts |

## BiasEvaluator

Detects demographic bias across five dimensions using keyword matching with configurable sensitivity levels.

### Bias Dimensions

| Dimension | Example Indicators |
|---|---|
| Gender | Gender stereotypes, role assumptions |
| Racial/Ethnic | Ethnic stereotypes, racial profiling language |
| Age | Age-based generalizations |
| Disability | Ableist language, stereotypes |
| Socioeconomic | Class-based stereotypes |

### Configuration

```python
from aigov_shield.measurement import BiasEvaluator

# Default: medium sensitivity, 95% threshold
evaluator = BiasEvaluator()

# High sensitivity (more indicators, more detections)
evaluator = BiasEvaluator(sensitivity="high")

# Low sensitivity (only the most obvious indicators)
evaluator = BiasEvaluator(sensitivity="low")
```

### Usage

```python
data = [
    {"text": "All candidates were evaluated based on qualifications and experience."},
    {"text": "She should stay home instead of pursuing a career."},
]

result = evaluator.evaluate(data)

print(f"Bias Score: {result.score:.1%}")
print(f"Flagged Items: {result.summary['flagged_items']}")
print(f"By Dimension: {result.summary['bias_by_dimension']}")
```

### Sensitivity Levels

| Level | Behavior |
|---|---|
| `low` | Uses only the 3 most obvious indicators per category |
| `medium` | Uses the full default indicator set |
| `high` | Adds additional subtle indicators to each category |

## ComplianceScorer

Combines all evaluators into a single NIST AI RMF-aligned composite score.

### Configuration

```python
from aigov_shield.measurement import ComplianceScorer

# Default: equal weights, 70% pass threshold
scorer = ComplianceScorer()

# Custom weights
scorer = ComplianceScorer(
    pii_weight=0.30,
    privilege_weight=0.30,
    grounding_weight=0.20,
    bias_weight=0.20,
    pass_threshold=0.80,
)
```

### Usage

```python
data = [
    {
        "text": "The quarterly report shows steady growth.",
        "context": "Q3 financial results indicate steady growth across all segments.",
        "output": "The quarterly report shows steady growth.",
    },
]

results = scorer.evaluate(data)

print(f"NIST Compliance Score: {results['nist_compliance_score']:.1%}")
print(f"Overall Pass: {results['overall_pass']}")
print(f"Function Scores: {results['function_scores']}")
# {'GOVERN': 0.95, 'MAP': 1.0, 'MEASURE': 0.95, 'MANAGE': 1.0}
print(f"Recommendations: {results['recommendations']}")
```

### Output Structure

| Key | Description |
|---|---|
| `nist_compliance_score` | Weighted composite score |
| `function_scores` | Per-NIST-function scores (GOVERN, MAP, MEASURE, MANAGE) |
| `overall_pass` | Whether the composite score meets the threshold |
| `per_function_pass` | Pass/fail per NIST function |
| `recommendations` | Actionable improvement recommendations |
| `evaluator_results` | Individual EvaluationResult objects |

### NIST Function Score Mapping

| Function | Calculation |
|---|---|
| GOVERN | Composite compliance score |
| MAP | Grounding evaluator score |
| MEASURE | Average of PII and bias scores |
| MANAGE | Privilege evaluator score |

## DriftMonitor

Compares compliance metrics between two evaluation runs to detect improvement, degradation, or stability.

### Configuration

```python
from aigov_shield.measurement import DriftMonitor

# Default: 10% alert threshold
monitor = DriftMonitor()

# More sensitive to changes
monitor = DriftMonitor(alert_threshold=0.05)
```

### Usage

```python
from aigov_shield.measurement import PIIEvaluator, BiasEvaluator, DriftMonitor

pii_eval = PIIEvaluator()
bias_eval = BiasEvaluator()

# Baseline evaluation
baseline_data = [{"text": "Clean output."}, {"text": "Another clean output."}]
baseline = {
    "pii": pii_eval.evaluate(baseline_data),
    "bias": bias_eval.evaluate(baseline_data),
}

# Current evaluation
current_data = [{"text": "Email john@example.com."}, {"text": "Clean output."}]
current = {
    "pii": pii_eval.evaluate(current_data),
    "bias": bias_eval.evaluate(current_data),
}

monitor = DriftMonitor(alert_threshold=0.1)
drift = monitor.compare(baseline, current)

print(f"Metrics: {drift['metrics']}")
print(f"Alerts: {drift['alerts']}")
print(f"Summary: {drift['summary']}")
# {'improved': 0, 'degraded': 1, 'stable': 1}
```

### Output Structure

| Key | Description |
|---|---|
| `metrics` | Per-metric details (baseline, current, delta, status) |
| `alerts` | List of alert strings for degraded metrics |
| `summary` | Count of improved, degraded, and stable metrics |

### Metric Status

| Status | Meaning |
|---|---|
| `improved` | Delta exceeds alert threshold (positive) |
| `degraded` | Delta exceeds alert threshold (negative) |
| `stable` | Delta within alert threshold |

## Best Practices

1. **Evaluate regularly.** Run compliance evaluation on a regular schedule (daily or weekly) to track trends.

2. **Use DriftMonitor to catch regressions.** Compare each evaluation against the previous run to detect degradation early.

3. **Adjust weights for your domain.** A legal application should weight privilege higher; a healthcare application should weight PII higher.

4. **Set thresholds based on regulatory requirements.** Different industries have different acceptable leakage rates.

5. **Include grounding context.** Always provide source context for grounding evaluation to get meaningful hallucination rates.

6. **Use high sensitivity for bias in regulated domains.** Financial services and healthcare should use `sensitivity="high"` for bias evaluation.
