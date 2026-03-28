"""Quick start example demonstrating all three governance layers."""

from __future__ import annotations

from aigov_shield.prevention import PIIGuard, PrivilegeGuard, GuardChain, GuardAction
from aigov_shield.accountability import ChainOfCustody, EvidenceLogger
from aigov_shield.measurement import ComplianceScorer


def main() -> None:
    # Layer 1: Prevention - Guard against PII and privilege leakage
    print("=" * 60)
    print("LAYER 1: PREVENTION")
    print("=" * 60)

    chain = GuardChain([
        PIIGuard(on_violation=GuardAction.REDACT),
        PrivilegeGuard(on_violation=GuardAction.FLAG),
    ])

    text = "Contact John at john.doe@example.com. His SSN is 123-45-6789."
    result = chain.run(text)

    print(f"Input:    {text}")
    print(f"Passed:   {result.passed}")
    print(f"Modified: {result.modified_text}")
    print(f"Failed guards: {result.failed_guards}")
    print()

    # Layer 2: Accountability - Create tamper-evident audit trail
    print("=" * 60)
    print("LAYER 2: ACCOUNTABILITY")
    print("=" * 60)

    custody = ChainOfCustody()

    custody.add_record(
        interaction_type="query",
        content="Summarise the insurance policy for flood damage.",
        actor="user",
    )
    custody.add_record(
        interaction_type="response",
        content="The policy covers flood damage under Section 4.2...",
        actor="llm",
        model_id="gpt-4",
        guard_results=[{"guard": "pii_guard", "passed": True}],
    )

    valid, errors = custody.verify_chain()
    print(f"Chain length: {len(custody)}")
    print(f"Chain valid:  {valid}")
    print(f"Errors:       {errors}")
    print()

    # Layer 3: Measurement - Evaluate compliance
    print("=" * 60)
    print("LAYER 3: MEASUREMENT")
    print("=" * 60)

    data = [
        {"text": "The policy covers flood damage under Section 4.2.", "context": "Section 4.2 covers flood damage claims.", "output": "The policy covers flood damage under Section 4.2."},
        {"text": "Your claim has been approved for processing.", "context": "Claims are processed within 30 days.", "output": "Your claim has been approved for processing."},
        {"text": "Please review the attached documentation.", "context": "Documentation must be reviewed before approval.", "output": "Please review the attached documentation."},
    ]

    scorer = ComplianceScorer()
    results = scorer.evaluate(data)

    print(f"NIST Compliance Score: {results['nist_compliance_score']:.1%}")
    print(f"Overall Pass: {results['overall_pass']}")
    print(f"Function Scores:")
    for func, score in results.get('function_scores', {}).items():
        print(f"  {func}: {score:.1%}")


if __name__ == "__main__":
    main()
