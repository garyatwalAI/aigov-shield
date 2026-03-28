"""Example: Generate a NIST AI RMF compliance report.

Demonstrates generating HTML and JSON compliance reports
from evaluation results.
"""

from __future__ import annotations

from aigov_shield.measurement import ComplianceScorer
from aigov_shield.reporting import NISTComplianceReport


def main() -> None:
    # Evaluate a sample dataset
    data = [
        {
            "text": "The insurance policy covers flood damage under Section 4.2.",
            "output": "The insurance policy covers flood damage under Section 4.2.",
            "context": "Section 4.2 of the policy covers residential flood damage.",
        },
        {
            "text": "Your claim has been processed and approved.",
            "output": "Your claim has been processed and approved.",
            "context": "Claims meeting all requirements are approved automatically.",
        },
    ]

    scorer = ComplianceScorer()
    results = scorer.evaluate(data)

    # Generate reports
    report = NISTComplianceReport(
        evaluation_results=results,
        title="Q1 2026 AI Governance Compliance Report",
        organization="Example Insurance Corp",
    )

    # Save as JSON
    report.save_json("nist_compliance_report.json")
    print("JSON report saved to nist_compliance_report.json")

    # Save as HTML
    report.save_html("nist_compliance_report.html")
    print("HTML report saved to nist_compliance_report.html")

    # Print summary
    report_data = report.to_dict()
    print(f"\nOverall Score: {report_data['overall_score']:.1%}")
    print(f"Overall Pass: {report_data['overall_pass']}")
    for section in report_data["sections"]:
        print(f"  {section['function']}: {section['score']:.1%} ({'PASS' if section['passed'] else 'FAIL'})")


if __name__ == "__main__":
    main()
