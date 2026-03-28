"""Tests for evidence logger implementation."""

from __future__ import annotations

import json

from aigov_shield.accountability.evidence_logger import EvidenceLogger


def test_log_retrieval():
    logger = EvidenceLogger(case_id="CASE-001")
    rid = logger.log_retrieval(query="search", documents_retrieved=["doc1"])
    record = logger.get_record(rid)
    assert record is not None
    assert record["event_type"] == "retrieval"


def test_log_generation():
    logger = EvidenceLogger(case_id="CASE-001")
    rid = logger.log_generation(prompt="hello", response="world", model="gpt-4")
    record = logger.get_record(rid)
    assert record is not None
    assert record["event_type"] == "generation"
    assert record["data"]["prompt"] == "hello"
    assert record["data"]["response"] == "world"
    assert record["data"]["model"] == "gpt-4"


def test_log_event():
    logger = EvidenceLogger(case_id="CASE-001")
    rid = logger.log_event(event_type="custom", description="something happened")
    record = logger.get_record(rid)
    assert record is not None
    assert record["event_type"] == "custom"


def test_get_records_by_type():
    logger = EvidenceLogger(case_id="CASE-001")
    logger.log_event(event_type="alpha", description="a")
    logger.log_event(event_type="beta", description="b")
    logger.log_event(event_type="alpha", description="c")
    results = logger.get_records(event_type="alpha")
    assert len(results) == 2
    assert all(r["event_type"] == "alpha" for r in results)


def test_verify_integrity():
    logger = EvidenceLogger(case_id="CASE-001")
    logger.log_event(event_type="test", description="ok")
    valid, errors = logger.verify_integrity()
    assert valid is True
    assert errors == []


def test_export_json():
    logger = EvidenceLogger(case_id="CASE-001")
    logger.log_event(event_type="test", description="ok")
    data = json.loads(logger.export("json"))
    assert isinstance(data, list)
    assert len(data) == 1


def test_case_id_stored():
    logger = EvidenceLogger(case_id="CASE-XYZ")
    rid = logger.log_event(event_type="test", description="ok")
    record = logger.get_record(rid)
    assert record["case_id"] == "CASE-XYZ"
