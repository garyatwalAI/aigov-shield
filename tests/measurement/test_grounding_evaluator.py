"""Tests for grounding evaluator."""

from __future__ import annotations

from aigov_shield.measurement.grounding_evaluator import GroundingEvaluator


def test_grounded_output():
    evaluator = GroundingEvaluator(threshold=0.5)
    data = [
        {
            "output": "The company reported strong revenue growth last quarter.",
            "context": "The company reported strong revenue growth last quarter driven by new products.",
        },
    ]
    result = evaluator.evaluate(data)
    assert result.score >= 0.5


def test_ungrounded_output():
    evaluator = GroundingEvaluator(threshold=0.5)
    data = [
        {
            "output": "Aliens have been discovered living on Mars since last year.",
            "context": "The quarterly earnings report showed a 10 percent increase in profit margins.",
        },
    ]
    result = evaluator.evaluate(data)
    assert result.score < 0.5


def test_short_sentences_skipped():
    evaluator = GroundingEvaluator(threshold=0.5)
    data = [
        {
            "output": "Yes. No. Maybe. Okay sure.",
            "context": "Completely unrelated context about finance.",
        },
    ]
    result = evaluator.evaluate(data)
    # Short sentences (< 5 words) are skipped, so score defaults to 1.0
    assert result.score == 1.0


def test_nist_function():
    evaluator = GroundingEvaluator()
    result = evaluator.evaluate([{"output": "test output here", "context": "test"}])
    assert result.nist_function == "MAP"
