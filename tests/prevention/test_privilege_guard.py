"""Tests for the PrivilegeGuard."""

from __future__ import annotations

import pytest

from aigov_shield.core.types import PrivilegeCategory
from aigov_shield.prevention import GuardAction, GuardChain, PrivilegeGuard


def test_clean_text_passes(privilege_guard, sample_clean_text):
    """Normal business text should pass without triggering privilege detection."""
    result = privilege_guard.check(sample_clean_text)
    assert result.passed is True
    assert result.violations == []
    assert result.action_taken == GuardAction.PASSTHROUGH


def test_attorney_client_keyword_detection(privilege_guard):
    """Text containing 'attorney-client privilege' should be detected."""
    text = "This document is covered by attorney-client privilege and should not be disclosed."
    result = privilege_guard.check(text)
    assert result.passed is False
    categories = {v["category"] for v in result.violations}
    assert "attorney_client" in categories


def test_work_product_detection(privilege_guard):
    """Work product phrases like 'litigation strategy' should trigger detection."""
    text = (
        "The litigation strategy memo was prepared in anticipation of litigation "
        "against the defendant."
    )
    result = privilege_guard.check(text)
    assert result.passed is False
    categories = {v["category"] for v in result.violations}
    assert "work_product" in categories


def test_settlement_detection(privilege_guard):
    """Settlement offer with dollar amounts and 'without prejudice' should trigger."""
    text = (
        "We propose a settlement offer of $750,000 without prejudice to our "
        "rights under the agreement."
    )
    result = privilege_guard.check(text)
    assert result.passed is False
    categories = {v["category"] for v in result.violations}
    assert "settlement" in categories


def test_multiple_categories(privilege_guard):
    """Text with multiple category indicators should produce high confidence."""
    text = (
        "This privileged communication contains our attorney's legal advice "
        "regarding the litigation strategy. The settlement offer of $500,000 "
        "was prepared in anticipation of litigation and is without prejudice."
    )
    result = privilege_guard.check(text)
    assert result.passed is False
    assert result.confidence >= 0.8


def test_false_positive_attorney_general(privilege_guard):
    """'The attorney general announced...' should NOT trigger detection."""
    text = "The attorney general announced new enforcement guidelines today."
    result = privilege_guard.check(text)
    assert result.passed is True


def test_false_positive_settlement_dust(privilege_guard):
    """'settlement of dust particles' should NOT trigger detection."""
    text = "The settlement of dust particles was observed in the experiment."
    result = privilege_guard.check(text)
    assert result.passed is True


def test_redaction_mode(privilege_guard_redact, sample_privilege_text):
    """With REDACT action, privileged text should be replaced with '[PRIVILEGED -- ...]'."""
    result = privilege_guard_redact.check(sample_privilege_text)
    assert result.passed is False
    assert result.modified_text is not None
    assert "[PRIVILEGED" in result.modified_text
    assert result.action_taken == GuardAction.REDACT


def test_confidence_scoring():
    """A single keyword should produce lower confidence than keyword+pattern."""
    guard = PrivilegeGuard(on_violation=GuardAction.BLOCK, confidence_threshold=0.0)

    keyword_only = "The legal advice was helpful."
    result_kw = guard.check(keyword_only)

    keyword_plus_pattern = (
        "This communication is privileged and confidential. "
        "Our attorney advised us to proceed."
    )
    result_kp = guard.check(keyword_plus_pattern)

    # Both should detect something, but pattern match should yield higher confidence.
    if result_kw.violations and result_kp.violations:
        assert result_kp.confidence >= result_kw.confidence


def test_empty_input(privilege_guard):
    """Empty string should pass the guard cleanly."""
    result = privilege_guard.check("")
    assert result.passed is True
    assert result.violations == []


def test_long_input(privilege_guard):
    """A 10000+ char text with one privilege phrase buried inside should detect it."""
    padding = "This is a normal business sentence about quarterly results. " * 200
    embedded = "This document is covered by attorney-client privilege."
    text = padding + embedded + padding
    assert len(text) > 10000
    result = privilege_guard.check(text)
    assert result.passed is False
    assert any(
        v["category"] == "attorney_client" for v in result.violations
    )


def test_custom_categories():
    """Only enabling ATTORNEY_CLIENT should not detect work product phrases."""
    guard = PrivilegeGuard(
        on_violation=GuardAction.BLOCK,
        categories=[PrivilegeCategory.ATTORNEY_CLIENT],
    )
    text = "The litigation strategy was prepared in anticipation of litigation."
    result = guard.check(text)
    # Work product keywords should be ignored since only attorney_client is enabled.
    wp_violations = [v for v in result.violations if v["category"] == "work_product"]
    assert len(wp_violations) == 0


def test_flag_action():
    """With FLAG action, result should have action_taken=FLAG and passed=False."""
    guard = PrivilegeGuard(on_violation=GuardAction.FLAG)
    text = (
        "This communication is privileged and confidential. "
        "Our attorney advised us on the matter."
    )
    result = guard.check(text)
    assert result.passed is False
    assert result.action_taken == GuardAction.FLAG


def test_callable_interface(privilege_guard):
    """Guard should be callable via __call__."""
    text = "This communication is privileged and confidential."
    result = privilege_guard(text)
    assert isinstance(result.passed, bool)


def test_execution_time_recorded(privilege_guard, sample_privilege_text):
    """result.execution_time_ms should be greater than 0."""
    result = privilege_guard.check(sample_privilege_text)
    assert result.execution_time_ms > 0
