"""Compliance drift monitoring between evaluation runs."""

from __future__ import annotations

from typing import Any, Dict, List

from aigov_shield.measurement.base import EvaluationResult


class DriftMonitor:
    """Compare compliance metrics between two evaluation runs.

    Detects whether individual metrics have improved, degraded, or remained
    stable relative to a baseline evaluation.

    Args:
        alert_threshold: Minimum absolute score change required to classify
            a metric as improved or degraded.
    """

    def __init__(self, alert_threshold: float = 0.1) -> None:
        self.alert_threshold = alert_threshold

    def compare(
        self,
        baseline_results: Dict[str, EvaluationResult],
        current_results: Dict[str, EvaluationResult],
    ) -> Dict[str, Any]:
        """Compare baseline and current evaluation results.

        Only metrics present in both *baseline_results* and
        *current_results* are compared.

        Args:
            baseline_results: Mapping of metric name to its baseline
                ``EvaluationResult``.
            current_results: Mapping of metric name to its current
                ``EvaluationResult``.

        Returns:
            A dict with per-metric deltas, alerts for degraded metrics,
            and a status summary.
        """
        metrics: Dict[str, Dict[str, Any]] = {}
        alerts: List[str] = []
        improved_count = 0
        degraded_count = 0
        stable_count = 0

        common_keys = set(baseline_results.keys()) & set(current_results.keys())

        for metric_name in sorted(common_keys):
            baseline = baseline_results[metric_name]
            current = current_results[metric_name]
            delta = current.score - baseline.score

            if delta > self.alert_threshold:
                status = "improved"
                improved_count += 1
            elif delta < -self.alert_threshold:
                status = "degraded"
                degraded_count += 1
                alerts.append(
                    f"{metric_name} degraded by {abs(delta):.3f} "
                    f"(from {baseline.score:.3f} to {current.score:.3f})."
                )
            else:
                status = "stable"
                stable_count += 1

            metrics[metric_name] = {
                "baseline": baseline.score,
                "current": current.score,
                "delta": delta,
                "status": status,
            }

        return {
            "metrics": metrics,
            "alerts": alerts,
            "summary": {
                "improved": improved_count,
                "degraded": degraded_count,
                "stable": stable_count,
            },
        }
