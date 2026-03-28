"""HTML report generation for guard and evaluation results."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def generate_guard_report(
    results: list[dict[str, Any]],
    title: str = "Guard Results Report",
) -> str:
    """Generate an HTML report from guard check results.

    Args:
        results: List of guard result dictionaries.
        title: Report title.

    Returns:
        HTML string of the report.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    rows = ""
    for i, result in enumerate(results):
        passed = result.get("passed", False)
        color = "#27ae60" if passed else "#e74c3c"
        status = "PASS" if passed else "FAIL"
        rows += (
            f"<tr>"
            f"<td>{i + 1}</td>"
            f"<td>{result.get('guard_name', 'unknown')}</td>"
            f'<td style="color:{color};font-weight:bold">{status}</td>'
            f"<td>{result.get('action_taken', '')}</td>"
            f"<td>{result.get('confidence', 0):.2%}</td>"
            f"<td>{result.get('execution_time_ms', 0):.1f}ms</td>"
            f"<td>{len(result.get('violations', []))}</td>"
            f"</tr>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
               padding: 2rem; background: #f5f5f5; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ color: #2c3e50; }}
        .meta {{ color: #7f8c8d; margin-bottom: 1.5rem; }}
        table {{ width: 100%; border-collapse: collapse; background: white;
                 border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        th, td {{ padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid #ecf0f1; }}
        th {{ background: #2c3e50; color: white; }}
        tr:hover {{ background: #f8f9fa; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p class="meta">Generated: {timestamp} | Total checks: {len(results)}</p>
        <table>
            <tr><th>#</th><th>Guard</th><th>Status</th><th>Action</th>
                <th>Confidence</th><th>Time</th><th>Violations</th></tr>
            {rows}
        </table>
    </div>
</body>
</html>"""


def save_guard_report(
    results: list[dict[str, Any]],
    path: str,
    title: str = "Guard Results Report",
) -> None:
    """Generate and save an HTML guard report.

    Args:
        results: List of guard result dictionaries.
        path: Output file path.
        title: Report title.
    """
    html = generate_guard_report(results, title)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
