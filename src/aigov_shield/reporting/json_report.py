"""Machine-readable JSON report generation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


def generate_json_report(
    evaluation_results: dict[str, Any],
    guard_results: list[dict[str, Any]] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate a structured JSON report from evaluation and guard results.

    Args:
        evaluation_results: Results from compliance evaluation.
        guard_results: Optional list of guard check results.
        metadata: Optional additional metadata.

    Returns:
        Dictionary suitable for JSON serialization.
    """
    report: dict[str, Any] = {
        "report_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evaluation": evaluation_results,
    }

    if guard_results is not None:
        report["guard_results"] = guard_results

    if metadata is not None:
        report["metadata"] = metadata

    return report


def save_json_report(
    evaluation_results: dict[str, Any],
    path: str,
    guard_results: list[dict[str, Any]] | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Generate and save a JSON report to file.

    Args:
        evaluation_results: Results from compliance evaluation.
        path: Output file path.
        guard_results: Optional list of guard check results.
        metadata: Optional additional metadata.
    """
    report = generate_json_report(evaluation_results, guard_results, metadata)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
