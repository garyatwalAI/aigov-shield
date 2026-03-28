"""Tests for chain of custody implementation."""

from __future__ import annotations

import json

from aigov_shield.accountability.chain_of_custody import ChainOfCustody, CustodyRecord


def test_add_record():
    chain = ChainOfCustody()
    record = chain.add_record(interaction_type="query", content="hello", actor="user")
    assert isinstance(record, CustodyRecord)
    assert len(record.record_id) == 36  # UUID v4
    assert record.record_hash != ""


def test_chain_linking():
    chain = ChainOfCustody()
    r1 = chain.add_record(interaction_type="query", content="a", actor="u")
    r2 = chain.add_record(interaction_type="response", content="b", actor="u")
    assert r2.previous_record_hash == r1.record_hash


def test_genesis_record():
    chain = ChainOfCustody()
    r = chain.add_record(interaction_type="query", content="first", actor="u")
    assert r.previous_record_hash == "GENESIS"


def test_verify_chain_valid():
    chain = ChainOfCustody()
    chain.add_record(interaction_type="query", content="a", actor="u")
    chain.add_record(interaction_type="response", content="b", actor="u")
    valid, errors = chain.verify_chain()
    assert valid is True
    assert errors == []


def test_verify_chain_tampered():
    chain = ChainOfCustody()
    chain.add_record(interaction_type="query", content="a", actor="u")
    chain.add_record(interaction_type="response", content="b", actor="u")
    chain._chain[0].content_hash = "tampered"
    valid, errors = chain.verify_chain()
    assert valid is False
    assert len(errors) > 0


def test_chain_length():
    chain = ChainOfCustody()
    assert len(chain) == 0
    chain.add_record(interaction_type="query", content="a", actor="u")
    chain.add_record(interaction_type="response", content="b", actor="u")
    assert len(chain) == 2


def test_export_json():
    chain = ChainOfCustody()
    chain.add_record(interaction_type="query", content="a", actor="u")
    data = json.loads(chain.export_json())
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["interaction_type"] == "query"


def test_export_jsonl():
    chain = ChainOfCustody()
    chain.add_record(interaction_type="query", content="a", actor="u")
    chain.add_record(interaction_type="response", content="b", actor="u")
    lines = chain.export_jsonl().strip().split("\n")
    assert len(lines) == 2
    for line in lines:
        parsed = json.loads(line)
        assert "record_id" in parsed


def test_export_csv():
    chain = ChainOfCustody()
    chain.add_record(interaction_type="query", content="a", actor="u")
    csv_str = chain.export_csv()
    lines = csv_str.strip().split("\n")
    assert len(lines) >= 2  # header + data
    assert "record_id" in lines[0]


def test_get_record():
    chain = ChainOfCustody()
    r = chain.add_record(interaction_type="query", content="a", actor="u")
    found = chain.get_record(r.record_id)
    assert found is not None
    assert found.record_id == r.record_id


def test_get_record_not_found():
    chain = ChainOfCustody()
    assert chain.get_record("nonexistent-id") is None


def test_empty_chain_valid():
    chain = ChainOfCustody()
    valid, errors = chain.verify_chain()
    assert valid is True
    assert errors == []
