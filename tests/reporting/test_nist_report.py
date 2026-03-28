"""Tests for NIST compliance report."""

from __future__ import annotations

import json

from aigov_shield.reporting.nist_report import NISTComplianceReport


def _sample_results():
    return {
        "nist_compliance_score": 0.85,
        "overall_pass": True,
        "function_scores": {
            "GOVERN": 0.85,
            "MAP": 0.80,
            "MEASURE": 0.90,
            "MANAGE": 0.85,
        },
        "per_function_pass": {
            "GOVERN": True,
            "MAP": True,
            "MEASURE": True,
            "MANAGE": True,
        },
        "recommendations": ["All compliance metrics are within acceptable thresholds."],
        "evaluator_results": {},
    }


def test_report_creation():
    report = NISTComplianceReport(_sample_results(), title="Test Report")
    assert report.title == "Test Report"
    assert report.generated_at is not None


def test_to_dict():
    report = NISTComplianceReport(_sample_results())
    d = report.to_dict()
    assert "title" in d
    assert "overall_score" in d
    assert "overall_pass" in d
    assert "sections" in d
    assert "recommendations" in d


def test_save_json(tmp_path):
    report = NISTComplianceReport(_sample_results())
    path = str(tmp_path / "report.json")
    report.save_json(path)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert data["overall_score"] == 0.85


def test_save_html(tmp_path):
    report = NISTComplianceReport(_sample_results(), title="HTML Test")
    path = str(tmp_path / "report.html")
    report.save_html(path)
    with open(path, encoding="utf-8") as f:
        html = f.read()
    assert "HTML Test" in html
    assert "<!DOCTYPE html>" in html
