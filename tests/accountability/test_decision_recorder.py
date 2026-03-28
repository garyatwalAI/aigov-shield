"""Tests for decision recorder implementation."""

from __future__ import annotations

from aigov_shield.accountability.decision_recorder import DecisionRecorder


def test_record_decision_context_manager():
    recorder = DecisionRecorder()
    with recorder.record_decision("d-1") as ctx:
        ctx.log_step("step-a", key="value")
    exported = recorder.export_decision("d-1")
    assert exported is not None
    assert exported["started_at"] is not None
    assert exported["completed_at"] is not None


def test_log_step():
    recorder = DecisionRecorder()
    with recorder.record_decision("d-1") as ctx:
        ctx.log_step("gather_data", source="db")
        ctx.log_step("analyze", score=0.9)
    exported = recorder.export_decision("d-1")
    assert len(exported["steps"]) == 2
    assert exported["steps"][0]["step_name"] == "gather_data"
    assert exported["steps"][0]["data"]["source"] == "db"


def test_export_decision():
    recorder = DecisionRecorder()
    with recorder.record_decision("d-1") as ctx:
        ctx.log_step("s1")
    result = recorder.export_decision("d-1")
    assert "decision_id" in result
    assert "steps" in result
    assert result["decision_id"] == "d-1"


def test_list_decisions():
    recorder = DecisionRecorder()
    recorder.record_decision("d-1")
    recorder.record_decision("d-2")
    ids = recorder.list_decisions()
    assert "d-1" in ids
    assert "d-2" in ids


def test_unknown_decision():
    recorder = DecisionRecorder()
    assert recorder.export_decision("no-such-id") is None
