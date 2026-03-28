"""Example: Run compliance evaluation on a dataset.

Demonstrates how to evaluate a dataset of AI outputs against
compliance criteria using all four evaluators.
"""

from __future__ import annotations

from aigov_shield.measurement import (
    BiasEvaluator,
    ComplianceScorer,
    GroundingEvaluator,
    PIIEvaluator,
    PrivilegeEvaluator,
)


def main() -> None:
    # Sample dataset of AI outputs
    data = [
        {
            "text": "The policy covers flood damage as described in Section 4.2 of the agreement.",
            "output": "The policy covers flood damage as described in Section 4.2 of the agreement.",
            "context": "Section 4.2: This policy covers flood damage to residential properties.",
        },
        {
            "text": "Your claim for roof repairs has been approved for $12,000.",
            "output": "Your claim for roof repairs has been approved for $12,000.",
            "context": "Roof repair claims up to $15,000 are covered under the standard policy.",
        },
        {
            "text": "Based on the assessment, the property damage is consistent with wind damage.",
            "output": "Based on the assessment, the property damage is consistent with wind damage.",
            "context": "The assessor noted wind damage to the roof and siding.",
        },
    ]

    # Run individual evaluators
    print("Individual Evaluator Results:")
    print("-" * 50)

    pii_eval = PIIEvaluator()
    pii_result = pii_eval.evaluate(data)
    print(f"PII Leakage:     {pii_result.score:.1%} (threshold: {pii_result.threshold:.1%}) {'PASS' if pii_result.passed else 'FAIL'}")

    priv_eval = PrivilegeEvaluator()
    priv_result = priv_eval.evaluate(data)
    print(f"Privilege:       {priv_result.score:.1%} (threshold: {priv_result.threshold:.1%}) {'PASS' if priv_result.passed else 'FAIL'}")

    ground_eval = GroundingEvaluator()
    ground_result = ground_eval.evaluate(data)
    print(f"Grounding:       {ground_result.score:.1%} (threshold: {ground_result.threshold:.1%}) {'PASS' if ground_result.passed else 'FAIL'}")

    bias_eval = BiasEvaluator()
    bias_result = bias_eval.evaluate(data)
    print(f"Bias:            {bias_result.score:.1%} (threshold: {bias_result.threshold:.1%}) {'PASS' if bias_result.passed else 'FAIL'}")

    # Run composite scorer
    print()
    print("Composite NIST Compliance Score:")
    print("-" * 50)

    scorer = ComplianceScorer()
    results = scorer.evaluate(data)

    print(f"Overall Score:   {results['nist_compliance_score']:.1%}")
    print(f"Overall Pass:    {results['overall_pass']}")
    print()
    print("Function Scores:")
    for func, score in results.get("function_scores", {}).items():
        passed = results.get("per_function_pass", {}).get(func, False)
        print(f"  {func:8s}: {score:.1%} {'PASS' if passed else 'FAIL'}")

    if results.get("recommendations"):
        print()
        print("Recommendations:")
        for rec in results["recommendations"]:
            print(f"  - {rec}")


if __name__ == "__main__":
    main()
