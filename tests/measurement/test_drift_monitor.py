"""Tests for drift monitor."""

from __future__ import annotations

from aigov_shield.measurement.base import EvaluationResult
from aigov_shield.measurement.drift_monitor import DriftMonitor


def _make_result(score: float) -> EvaluationResult:
    return EvaluationResult(
        metric_name="test",
        score=score,
        passed=score >= 0.7,
        threshold=0.7,
    )


def test_no_drift():
    monitor = DriftMonitor(alert_threshold=0.1)
    baseline = {"metric_a": _make_result(0.8)}
    current = {"metric_a": _make_result(0.8)}
    result = monitor.compare(baseline, current)
    assert result["metrics"]["metric_a"]["status"] == "stable"


def test_improvement():
    monitor = DriftMonitor(alert_threshold=0.1)
    baseline = {"metric_a": _make_result(0.6)}
    current = {"metric_a": _make_result(0.9)}
    result = monitor.compare(baseline, current)
    assert result["metrics"]["metric_a"]["status"] == "improved"


def test_degradation():
    monitor = DriftMonitor(alert_threshold=0.1)
    baseline = {"metric_a": _make_result(0.9)}
    current = {"metric_a": _make_result(0.5)}
    result = monitor.compare(baseline, current)
    assert result["metrics"]["metric_a"]["status"] == "degraded"
    assert len(result["alerts"]) == 1


def test_alert_threshold():
    monitor = DriftMonitor(alert_threshold=0.5)
    baseline = {"metric_a": _make_result(0.8)}
    current = {"metric_a": _make_result(0.6)}
    result = monitor.compare(baseline, current)
    # Delta of -0.2 is within threshold of 0.5, so stable
    assert result["metrics"]["metric_a"]["status"] == "stable"
    assert len(result["alerts"]) == 0
