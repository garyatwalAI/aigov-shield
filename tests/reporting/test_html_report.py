"""Tests for HTML report generation."""

from __future__ import annotations

from aigov_shield.reporting.html_report import generate_guard_report, save_guard_report


def test_generate_guard_report():
    results = [
        {
            "guard_name": "pii_guard",
            "passed": True,
            "action_taken": "passthrough",
            "confidence": 0.0,
            "execution_time_ms": 1.5,
            "violations": [],
        },
    ]
    html = generate_guard_report(results)
    assert "<table>" in html
    assert "pii_guard" in html
    assert "<!DOCTYPE html>" in html


def test_save_guard_report(tmp_path):
    results = [
        {
            "guard_name": "pii_guard",
            "passed": True,
            "action_taken": "passthrough",
            "confidence": 0.0,
            "execution_time_ms": 1.0,
            "violations": [],
        },
    ]
    path = str(tmp_path / "report.html")
    save_guard_report(results, path)
    with open(path, encoding="utf-8") as f:
        html = f.read()
    assert "pii_guard" in html


def test_empty_results():
    html = generate_guard_report([])
    assert "<table>" in html
    assert "Total checks: 0" in html
