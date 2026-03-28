"""NIST AI RMF compliance report generator."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class NISTReportSection:
    """A section of the NIST compliance report.

    Attributes:
        function_name: NIST AI RMF function name (GOVERN, MAP, MEASURE, MANAGE).
        score: Compliance score for this function (0.0 to 1.0).
        passed: Whether this function meets the threshold.
        details: Detailed breakdown of metrics within this function.
        recommendations: Actionable recommendations for improvement.
    """

    function_name: str
    score: float
    passed: bool
    details: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class NISTComplianceReport:
    """Generate NIST AI RMF-aligned compliance reports.

    Produces structured reports in HTML and JSON formats, mapping
    evaluation results to the four NIST AI RMF functions.

    Args:
        evaluation_results: Results from ComplianceScorer.evaluate().
        title: Report title.
        organization: Organization name for the report header.

    Example:
        >>> report = NISTComplianceReport(evaluation_results)
        >>> report.save_html("compliance_report.html")
        >>> report.save_json("compliance_report.json")
    """

    def __init__(
        self,
        evaluation_results: dict[str, Any],
        title: str = "NIST AI RMF Compliance Report",
        organization: str = "",
    ) -> None:
        self.results = evaluation_results
        self.title = title
        self.organization = organization
        self.generated_at = datetime.now(timezone.utc).isoformat()
        self._sections = self._build_sections()

    def _build_sections(self) -> list[NISTReportSection]:
        """Build report sections from evaluation results."""
        sections = []
        function_scores = self.results.get("function_scores", {})
        per_function_pass = self.results.get("per_function_pass", {})
        recommendations = self.results.get("recommendations", [])
        evaluator_results = self.results.get("evaluator_results", {})

        nist_functions = ["GOVERN", "MAP", "MEASURE", "MANAGE"]

        # Map evaluators to NIST functions
        function_evaluators = {
            "GOVERN": ["compliance_score"],
            "MAP": ["factual_grounding"],
            "MEASURE": ["pii_leakage", "demographic_bias"],
            "MANAGE": ["privilege_disclosure"],
        }

        for func in nist_functions:
            score = function_scores.get(func, 0.0)
            passed = per_function_pass.get(func, False)

            details = []
            for eval_name in function_evaluators.get(func, []):
                if eval_name in evaluator_results:
                    eval_result = evaluator_results[eval_name]
                    details.append(
                        {
                            "metric": eval_name,
                            "score": eval_result.score
                            if hasattr(eval_result, "score")
                            else eval_result.get("score", 0),
                            "passed": eval_result.passed
                            if hasattr(eval_result, "passed")
                            else eval_result.get("passed", False),
                        }
                    )

            func_recs = [r for r in recommendations if func.lower() in r.lower()] or []

            sections.append(
                NISTReportSection(
                    function_name=func,
                    score=score,
                    passed=passed,
                    details=details,
                    recommendations=func_recs,
                )
            )

        return sections

    def to_dict(self) -> dict[str, Any]:
        """Convert the report to a dictionary."""
        return {
            "title": self.title,
            "organization": self.organization,
            "generated_at": self.generated_at,
            "overall_score": self.results.get("nist_compliance_score", 0.0),
            "overall_pass": self.results.get("overall_pass", False),
            "sections": [
                {
                    "function": s.function_name,
                    "score": s.score,
                    "passed": s.passed,
                    "details": s.details,
                    "recommendations": s.recommendations,
                }
                for s in self._sections
            ],
            "recommendations": self.results.get("recommendations", []),
        }

    def save_json(self, path: str) -> None:
        """Save the report as JSON.

        Args:
            path: File path for the JSON output.
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

    def save_html(self, path: str) -> None:
        """Save the report as an HTML file.

        Generates a self-contained HTML document with inline CSS styling.
        No external JavaScript or CSS dependencies.

        Args:
            path: File path for the HTML output.
        """
        html = self._render_html()
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

    def _render_html(self) -> str:
        """Render the full HTML report."""
        overall_score = self.results.get("nist_compliance_score", 0.0)
        overall_pass = self.results.get("overall_pass", False)
        status_color = "#27ae60" if overall_pass else "#e74c3c"
        status_text = "PASS" if overall_pass else "FAIL"

        sections_html = ""
        for section in self._sections:
            sec_color = "#27ae60" if section.passed else "#e74c3c"
            sec_status = "PASS" if section.passed else "FAIL"
            bar_width = max(int(section.score * 100), 1)

            details_rows = ""
            for detail in section.details:
                d_color = "#27ae60" if detail.get("passed") else "#e74c3c"
                details_rows += (
                    f"<tr><td>{detail.get('metric', '')}</td>"
                    f"<td>{detail.get('score', 0):.2%}</td>"
                    f'<td style="color:{d_color}">{"PASS" if detail.get("passed") else "FAIL"}</td></tr>'
                )

            recs_html = ""
            if section.recommendations:
                recs_items = "".join(f"<li>{r}</li>" for r in section.recommendations)
                recs_html = f"<ul>{recs_items}</ul>"

            sections_html += f"""
            <div class="section">
                <h2>{section.function_name}
                    <span class="badge" style="background:{sec_color}">{sec_status}</span>
                </h2>
                <div class="score-bar">
                    <div class="score-fill" style="width:{bar_width}%;background:{sec_color}">
                        {section.score:.1%}
                    </div>
                </div>
                {"<table><tr><th>Metric</th><th>Score</th><th>Status</th></tr>" + details_rows + "</table>" if details_rows else ""}
                {recs_html}
            </div>
            """

        all_recs = self.results.get("recommendations", [])
        recs_section = ""
        if all_recs:
            recs_items = "".join(f"<li>{r}</li>" for r in all_recs)
            recs_section = (
                f'<div class="section"><h2>Recommendations</h2><ol>{recs_items}</ol></div>'
            )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               background: #f5f5f5; color: #333; line-height: 1.6; padding: 2rem; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ color: #2c3e50; margin-bottom: 0.5rem; }}
        .subtitle {{ color: #7f8c8d; margin-bottom: 2rem; }}
        .summary {{ background: white; border-radius: 8px; padding: 2rem;
                    margin-bottom: 2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .overall-score {{ font-size: 3rem; font-weight: bold; color: {status_color}; }}
        .badge {{ display: inline-block; padding: 0.2rem 0.8rem; border-radius: 4px;
                  color: white; font-size: 0.85rem; font-weight: bold; vertical-align: middle; }}
        .section {{ background: white; border-radius: 8px; padding: 1.5rem;
                    margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .section h2 {{ color: #2c3e50; margin-bottom: 1rem; }}
        .score-bar {{ background: #ecf0f1; border-radius: 4px; height: 28px;
                      margin-bottom: 1rem; overflow: hidden; }}
        .score-fill {{ height: 100%; border-radius: 4px; color: white;
                       text-align: center; line-height: 28px; font-weight: bold;
                       font-size: 0.85rem; min-width: 3rem; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 1rem; }}
        th, td {{ padding: 0.6rem 1rem; text-align: left; border-bottom: 1px solid #ecf0f1; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        ul, ol {{ padding-left: 1.5rem; }}
        li {{ margin-bottom: 0.3rem; }}
        .footer {{ text-align: center; color: #95a5a6; margin-top: 2rem; font-size: 0.85rem; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{self.title}</h1>
        <p class="subtitle">{self.organization + " | " if self.organization else ""}Generated: {self.generated_at}</p>

        <div class="summary">
            <h2>Executive Summary</h2>
            <div class="overall-score">{overall_score:.1%}</div>
            <p>Overall Compliance Status: <span class="badge" style="background:{status_color}">{status_text}</span></p>
        </div>

        {sections_html}
        {recs_section}

        <div class="footer">
            <p>Generated by aigov-shield | NIST AI Risk Management Framework Alignment</p>
        </div>
    </div>
</body>
</html>"""
