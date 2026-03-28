"""Tests for LangChain callback handler."""

from __future__ import annotations

from aigov_shield.accountability.chain_of_custody import ChainOfCustody
from aigov_shield.integrations.langchain_callback import GovernanceCallbackHandler
from aigov_shield.prevention import GuardAction, PIIGuard


def test_init():
    guard = PIIGuard(on_violation=GuardAction.FLAG)
    handler = GovernanceCallbackHandler(guards=[guard])
    assert len(handler.guards) == 1


def test_run_guards():
    guard = PIIGuard(on_violation=GuardAction.FLAG)
    handler = GovernanceCallbackHandler(guards=[guard])
    results = handler._run_guards("clean text")
    assert len(results) == 1
    assert results[0].passed is True


def test_on_llm_start_logs_to_custody():
    guard = PIIGuard(on_violation=GuardAction.FLAG)
    custody = ChainOfCustody()
    # Seed the chain so bool(custody) is True (empty chain has __len__==0).
    custody.add_record(interaction_type="init", content="seed", actor="test")
    handler = GovernanceCallbackHandler(guards=[guard], chain_of_custody=custody)
    handler.on_llm_start(serialized={}, prompts=["test prompt"])
    assert len(custody) == 2


def test_last_results_property():
    guard = PIIGuard(on_violation=GuardAction.FLAG)
    handler = GovernanceCallbackHandler(guards=[guard])
    handler.on_llm_start(serialized={}, prompts=["hello world"])
    results = handler.last_results
    assert len(results) == 1
    assert results[0].guard_name == "pii_guard"
