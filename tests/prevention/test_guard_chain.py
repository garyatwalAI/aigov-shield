"""Tests for the GuardChain."""

from __future__ import annotations

from aigov_shield.prevention import (
    ExecutionMode,
    GuardAction,
    GuardChain,
    PIIGuard,
    PrivilegeGuard,
    ToxicityGuard,
)


def test_all_pass(sample_clean_text):
    """Clean text should pass all guards in the chain."""
    chain = GuardChain(
        guards=[
            PIIGuard(on_violation=GuardAction.BLOCK),
            ToxicityGuard(on_violation=GuardAction.BLOCK),
        ],
        execution_mode=ExecutionMode.RUN_ALL,
    )
    result = chain.run(sample_clean_text)
    assert result.passed is True
    assert result.failed_guards == []
    assert len(result.results) == 2


def test_fail_fast_stops_early(sample_pii_text):
    """With fail_fast, chain stops at first failure; remaining guards do not run."""
    chain = GuardChain(
        guards=[
            PIIGuard(on_violation=GuardAction.BLOCK),
            ToxicityGuard(on_violation=GuardAction.BLOCK),
            PrivilegeGuard(on_violation=GuardAction.BLOCK),
        ],
        execution_mode=ExecutionMode.FAIL_FAST,
    )
    result = chain.run(sample_pii_text)
    assert result.passed is False
    # PII guard should fail first, so only 1 result should be present.
    assert len(result.results) == 1
    assert result.failed_guards == ["pii_guard"]


def test_run_all_continues(sample_pii_text):
    """With run_all, all guards run even after a failure."""
    chain = GuardChain(
        guards=[
            PIIGuard(on_violation=GuardAction.BLOCK),
            ToxicityGuard(on_violation=GuardAction.BLOCK),
        ],
        execution_mode=ExecutionMode.RUN_ALL,
    )
    result = chain.run(sample_pii_text)
    # All guards should have run regardless of earlier failures.
    assert len(result.results) == 2


def test_redaction_passes_through():
    """PII guard redacts text, then the next guard sees the redacted version."""
    chain = GuardChain(
        guards=[
            PIIGuard(on_violation=GuardAction.REDACT),
            PrivilegeGuard(on_violation=GuardAction.BLOCK),
        ],
        execution_mode=ExecutionMode.RUN_ALL,
    )
    text = "Contact john@example.com for the attorney-client privilege matter."
    result = chain.run(text)

    # The PII guard should have redacted the email.
    pii_result = result.results[0]
    assert pii_result.modified_text is not None
    assert "john@example.com" not in pii_result.modified_text

    # The privilege guard should have received the redacted text.
    priv_result = result.results[1]
    assert "john@example.com" not in priv_result.original_text


def test_chain_result_properties(sample_clean_text):
    """ChainResult should have correct passed, failed_guards, and execution_mode."""
    chain = GuardChain(
        guards=[PIIGuard(on_violation=GuardAction.BLOCK)],
        execution_mode=ExecutionMode.RUN_ALL,
    )
    result = chain.run(sample_clean_text)
    assert result.passed is True
    assert result.failed_guards == []
    assert result.execution_mode == "run_all"
    assert result.total_execution_time_ms > 0


def test_empty_chain(sample_clean_text):
    """Chain with no guards should pass."""
    chain = GuardChain(guards=[], execution_mode=ExecutionMode.RUN_ALL)
    result = chain.run(sample_clean_text)
    assert result.passed is True
    assert result.results == []
    assert result.failed_guards == []


def test_callable_interface(sample_clean_text):
    """Chain should be callable via __call__."""
    chain = GuardChain(
        guards=[PIIGuard(on_violation=GuardAction.BLOCK)],
        execution_mode=ExecutionMode.RUN_ALL,
    )
    result = chain(sample_clean_text)
    assert result.passed is True


def test_multiple_failures():
    """Chain with multiple failing guards should report all failures."""
    text = "I will kill you. Contact john@example.com."
    chain = GuardChain(
        guards=[
            PIIGuard(on_violation=GuardAction.BLOCK),
            ToxicityGuard(on_violation=GuardAction.BLOCK),
        ],
        execution_mode=ExecutionMode.RUN_ALL,
    )
    result = chain.run(text)
    assert result.passed is False
    assert len(result.failed_guards) == 2
    assert "pii_guard" in result.failed_guards
    assert "toxicity_guard" in result.failed_guards


def test_modified_text_property():
    """ChainResult.modified_text should return the last redacted version."""
    chain = GuardChain(
        guards=[
            PIIGuard(on_violation=GuardAction.REDACT),
            ToxicityGuard(on_violation=GuardAction.BLOCK),
        ],
        execution_mode=ExecutionMode.RUN_ALL,
    )
    text = "Email is user@example.com and the report is clean."
    result = chain.run(text)
    assert result.modified_text is not None
    assert "user@example.com" not in result.modified_text
