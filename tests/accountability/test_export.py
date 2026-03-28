"""Tests for export utilities."""

from __future__ import annotations

import json

from aigov_shield.accountability.export import (
    export_to_csv,
    export_to_json,
    export_to_jsonl,
    flatten_dict,
)


def test_export_to_json():
    records = [{"a": 1}, {"a": 2}]
    result = export_to_json(records)
    parsed = json.loads(result)
    assert parsed == records
    assert "\n" in result  # pretty-printed


def test_export_to_jsonl():
    records = [{"a": 1}, {"b": 2}]
    result = export_to_jsonl(records)
    lines = result.strip().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0]) == {"a": 1}
    assert json.loads(lines[1]) == {"b": 2}


def test_export_to_csv():
    records = [{"name": "alice", "score": 10}, {"name": "bob", "score": 20}]
    result = export_to_csv(records)
    lines = result.strip().split("\n")
    assert len(lines) == 3  # header + 2 rows
    assert "name" in lines[0]
    assert "score" in lines[0]


def test_flatten_dict():
    nested = {"a": {"b": {"c": 1}}, "d": 2}
    flat = flatten_dict(nested)
    assert flat == {"a.b.c": 1, "d": 2}


def test_empty_records():
    assert export_to_json([]) == "[]"
    assert export_to_jsonl([]) == ""
    assert export_to_csv([]) == ""
