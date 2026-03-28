"""Tests for document tracker implementation."""

from __future__ import annotations

import json

from aigov_shield.accountability.document_tracker import (
    DocumentTracker,
    TrackedDocument,
)


def test_register_document():
    tracker = DocumentTracker()
    doc = tracker.register_document(doc_id="doc-1", path="/data/file.pdf", content_hash="abc123")
    assert isinstance(doc, TrackedDocument)
    assert doc.doc_id == "doc-1"
    assert doc.path == "/data/file.pdf"
    assert doc.content_hash == "abc123"


def test_record_usage():
    tracker = DocumentTracker()
    tracker.register_document(doc_id="doc-1", path="/a.pdf", content_hash="h1")
    usage = tracker.record_usage(output_id="out-1", documents_used=["doc-1"])
    assert usage.output_id == "out-1"
    assert "doc-1" in usage.documents_used


def test_get_provenance():
    tracker = DocumentTracker()
    tracker.register_document(doc_id="doc-1", path="/a.pdf", content_hash="h1")
    tracker.record_usage(output_id="out-1", documents_used=["doc-1"])
    prov = tracker.get_provenance("out-1")
    assert prov is not None
    assert prov["output_id"] == "out-1"
    assert len(prov["documents"]) == 1
    assert prov["documents"][0]["doc_id"] == "doc-1"


def test_get_document_usage():
    tracker = DocumentTracker()
    tracker.register_document(doc_id="doc-1", path="/a.pdf", content_hash="h1")
    tracker.record_usage(output_id="out-1", documents_used=["doc-1"])
    tracker.record_usage(output_id="out-2", documents_used=["doc-1"])
    outputs = tracker.get_document_usage("doc-1")
    assert "out-1" in outputs
    assert "out-2" in outputs


def test_unknown_document():
    tracker = DocumentTracker()
    assert tracker.get_document("no-such-doc") is None


def test_export():
    tracker = DocumentTracker()
    tracker.register_document(doc_id="doc-1", path="/a.pdf", content_hash="h1")
    tracker.record_usage(output_id="out-1", documents_used=["doc-1"])
    data = json.loads(tracker.export("json"))
    assert isinstance(data, list)
    assert len(data) == 2  # one document + one usage
