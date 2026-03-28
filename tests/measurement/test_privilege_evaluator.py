"""Tests for privilege evaluator."""

from __future__ import annotations

from aigov_shield.measurement.privilege_evaluator import PrivilegeEvaluator


def test_clean_data():
    evaluator = PrivilegeEvaluator(threshold=0.95)
    data = [
        {"text": "Revenue grew by 15 percent."},
        {"text": "The project is on track."},
    ]
    result = evaluator.evaluate(data)
    assert result.score == 1.0
    assert result.passed is True


def test_privilege_data():
    evaluator = PrivilegeEvaluator(threshold=0.95)
    data = [
        {"text": "This is privileged and confidential attorney-client communication."},
        {"text": "The project is on track."},
    ]
    result = evaluator.evaluate(data)
    assert result.score < 1.0


def test_nist_function():
    evaluator = PrivilegeEvaluator()
    result = evaluator.evaluate([{"text": "clean data"}])
    assert result.nist_function == "MANAGE"
