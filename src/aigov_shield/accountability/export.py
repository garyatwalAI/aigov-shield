"""Export utilities for accountability records."""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, List


def flatten_dict(
    d: Dict[str, Any],
    parent_key: str = "",
    sep: str = ".",
) -> Dict[str, Any]:
    """Flatten a nested dictionary using dot notation.

    Args:
        d: The dictionary to flatten.
        parent_key: Prefix for keys (used in recursion).
        sep: Separator between parent and child keys.

    Returns:
        A flat dictionary with dot-separated keys for nested values.
    """
    items: List[tuple[str, Any]] = []
    for key, value in d.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep=sep).items())
        else:
            items.append((new_key, value))
    return dict(items)


def export_to_json(records: List[Dict[str, Any]]) -> str:
    """Export records as pretty-printed JSON.

    Args:
        records: List of record dictionaries.

    Returns:
        Pretty-printed JSON string.
    """
    return json.dumps(records, indent=2)


def export_to_jsonl(records: List[Dict[str, Any]]) -> str:
    """Export records as JSON Lines (one JSON object per line).

    Args:
        records: List of record dictionaries.

    Returns:
        JSONL string.
    """
    lines = [json.dumps(record) for record in records]
    return "\n".join(lines)


def export_to_csv(records: List[Dict[str, Any]]) -> str:
    """Export records as CSV with flattened nested dictionaries.

    Args:
        records: List of record dictionaries.

    Returns:
        CSV string with headers derived from the first record.
    """
    if not records:
        return ""

    flat_records = [flatten_dict(record) for record in records]

    # Collect all fieldnames across all records for consistent columns.
    fieldnames: List[str] = []
    seen: set[str] = set()
    for flat in flat_records:
        for key in flat:
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)

    output = io.StringIO()
    writer = csv.DictWriter(
        output, fieldnames=fieldnames, extrasaction="ignore"
    )
    writer.writeheader()
    for flat in flat_records:
        row: Dict[str, Any] = {}
        for key in fieldnames:
            value = flat.get(key, "")
            if isinstance(value, (list, dict)):
                row[key] = json.dumps(value)
            else:
                row[key] = value
        writer.writerow(row)
    return output.getvalue()
