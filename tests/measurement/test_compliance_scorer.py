"""Tests for compliance scorer."""

from __future__ import annotations

from aigov_shield.measurement.compliance_scorer import ComplianceScorer


def test_evaluate_returns_required_keys():
    scorer = ComplianceScorer()
    data = [{"text": "Clean text with no issues.", "context": "Clean context."}]
    result = scorer.evaluate(data)
    assert "nist_compliance_score" in result
    assert "function_scores" in result
    assert "overall_pass" in result
    assert "recommendations" in result
    assert "evaluator_results" in result


def test_clean_data_passes():
    scorer = ComplianceScorer(pass_threshold=0.5)
    data = [
        {"text": "Revenue grew by 15 percent.", "context": "Revenue grew by 15 percent."},
        {"text": "The project is on track.", "context": "The project is on track."},
    ]
    result = scorer.evaluate(data)
    assert result["overall_pass"] is True


def test_overall_structure():
    scorer = ComplianceScorer()
    data = [{"text": "Some text.", "context": "Some context."}]
    result = scorer.evaluate(data)
    fs = result["function_scores"]
    assert "GOVERN" in fs
    assert "MAP" in fs
    assert "MEASURE" in fs
    assert "MANAGE" in fs
