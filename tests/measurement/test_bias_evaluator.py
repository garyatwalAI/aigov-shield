"""Tests for bias evaluator."""

from __future__ import annotations

from aigov_shield.measurement.bias_evaluator import BiasEvaluator


def test_clean_data():
    evaluator = BiasEvaluator(threshold=0.95)
    data = [
        {"text": "Revenue grew by 15 percent."},
        {"text": "The project is on track."},
    ]
    result = evaluator.evaluate(data)
    assert result.score == 1.0
    assert result.passed is True


def test_biased_data():
    evaluator = BiasEvaluator(threshold=0.95)
    data = [
        {"text": "Women can't do this job."},
        {"text": "The project is on track."},
    ]
    result = evaluator.evaluate(data)
    assert result.score < 1.0
    assert result.passed is False


def test_nist_function():
    evaluator = BiasEvaluator()
    result = evaluator.evaluate([{"text": "clean data"}])
    assert result.nist_function == "MEASURE"


def test_sensitivity_levels():
    low = BiasEvaluator(sensitivity="low")
    high = BiasEvaluator(sensitivity="high")
    # High sensitivity has more indicator phrases
    total_low = sum(len(v) for v in low._indicators.values())
    total_high = sum(len(v) for v in high._indicators.values())
    assert total_high > total_low
