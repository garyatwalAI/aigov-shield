"""Tests for PII evaluator."""

from __future__ import annotations

from aigov_shield.measurement.pii_evaluator import PIIEvaluator


def test_clean_data_high_score():
    evaluator = PIIEvaluator(threshold=0.95)
    data = [
        {"text": "Revenue grew by 15 percent."},
        {"text": "The project is on track."},
    ]
    result = evaluator.evaluate(data)
    assert result.score == 1.0
    assert result.passed is True


def test_pii_data_low_score():
    evaluator = PIIEvaluator(threshold=0.95)
    data = [
        {"text": "Contact john.doe@example.com for details."},
        {"text": "The project is on track."},
    ]
    result = evaluator.evaluate(data)
    assert result.score < 1.0


def test_nist_function():
    evaluator = PIIEvaluator()
    result = evaluator.evaluate([{"text": "clean data"}])
    assert result.nist_function == "MEASURE"


def test_summary_fields():
    evaluator = PIIEvaluator()
    result = evaluator.evaluate([{"text": "test@example.com"}])
    assert "pii_leakage_rate" in result.summary
    assert "pii_count_total" in result.summary
    assert "items_evaluated" in result.summary
    assert "items_with_pii" in result.summary


def test_empty_data():
    evaluator = PIIEvaluator()
    result = evaluator.evaluate([])
    assert result.score == 1.0
    assert result.passed is True
