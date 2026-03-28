"""Tests for the PIIGuard."""

from __future__ import annotations

import pytest

from aigov_shield.core.types import PIICategory, RedactionMode
from aigov_shield.prevention import GuardAction, PIIGuard


def test_clean_text_passes(pii_guard, sample_clean_text):
    """Text without PII should pass the guard."""
    result = pii_guard.check(sample_clean_text)
    assert result.passed is True
    assert result.violations == []
    assert result.action_taken == GuardAction.PASSTHROUGH


def test_email_detection(pii_guard):
    """An email address should be detected."""
    result = pii_guard.check("Send to user@example.com please.")
    assert result.passed is False
    categories = [v["category"] for v in result.violations]
    assert "email" in categories


def test_phone_detection_us(pii_guard):
    """A US phone number should be detected."""
    result = pii_guard.check("Call me at 555-123-4567.")
    assert result.passed is False
    categories = [v["category"] for v in result.violations]
    assert "phone" in categories


def test_phone_detection_uk(pii_guard):
    """A UK international phone number should be detected."""
    result = pii_guard.check("Reach me at +44 7911 123456.")
    assert result.passed is False
    categories = [v["category"] for v in result.violations]
    assert "phone" in categories


def test_ssn_detection(pii_guard):
    """A valid SSN pattern should be detected."""
    result = pii_guard.check("SSN: 123-45-6789")
    assert result.passed is False
    categories = [v["category"] for v in result.violations]
    assert "ssn" in categories


def test_ssn_invalid_area(pii_guard):
    """SSN with area number 000 should NOT be detected (invalid)."""
    result = pii_guard.check("SSN: 000-12-3456")
    ssn_violations = [v for v in result.violations if v["category"] == "ssn"]
    assert len(ssn_violations) == 0


def test_credit_card_detection(pii_guard):
    """A valid Visa card number (passes Luhn) should be detected."""
    result = pii_guard.check("Card: 4111111111111111")
    assert result.passed is False
    categories = [v["category"] for v in result.violations]
    assert "credit_card" in categories


def test_credit_card_luhn_fail(pii_guard):
    """An invalid credit card number (fails Luhn) should NOT be detected."""
    result = pii_guard.check("Card: 4111111111111112")
    cc_violations = [v for v in result.violations if v["category"] == "credit_card"]
    assert len(cc_violations) == 0


def test_ip_address_detection(pii_guard):
    """An IPv4 address should be detected."""
    result = pii_guard.check("Server is at 192.168.1.1 on the local network.")
    assert result.passed is False
    categories = [v["category"] for v in result.violations]
    assert "ip_address" in categories


def test_iban_detection(pii_guard):
    """An IBAN should be detected."""
    result = pii_guard.check("Transfer to GB29 NWBK 6016 1331 9268 19.")
    assert result.passed is False
    categories = [v["category"] for v in result.violations]
    assert "iban" in categories


def test_dob_detection(pii_guard):
    """A date of birth should be detected."""
    result = pii_guard.check("DOB: 01/15/1990")
    assert result.passed is False
    categories = [v["category"] for v in result.violations]
    assert "date_of_birth" in categories


def test_address_detection(pii_guard):
    """A street address should be detected."""
    result = pii_guard.check("Ship to 123 Main Street in Springfield.")
    assert result.passed is False
    categories = [v["category"] for v in result.violations]
    assert "address" in categories


def test_redaction_mask_mode():
    """Detected PII should be replaced with category tags like '[EMAIL]', '[SSN]'."""
    guard = PIIGuard(
        on_violation=GuardAction.REDACT,
        redaction_mode=RedactionMode.MASK,
    )
    result = guard.check("Email: user@example.com SSN: 123-45-6789")
    assert result.modified_text is not None
    assert "[EMAIL]" in result.modified_text
    assert "[SSN]" in result.modified_text
    assert "user@example.com" not in result.modified_text


def test_redaction_hash_mode():
    """PII should be replaced with a SHA-256 hash prefix."""
    guard = PIIGuard(
        on_violation=GuardAction.REDACT,
        redaction_mode=RedactionMode.HASH,
    )
    result = guard.check("Email: user@example.com")
    assert result.modified_text is not None
    assert "user@example.com" not in result.modified_text
    # Hash mode produces a 16-char hex string.
    assert "[EMAIL]" not in result.modified_text


def test_redaction_partial_mode():
    """Email should show partial redaction like 'u***@example.com'."""
    guard = PIIGuard(
        on_violation=GuardAction.REDACT,
        redaction_mode=RedactionMode.PARTIAL,
    )
    result = guard.check("Email: user@example.com")
    assert result.modified_text is not None
    assert "u***@example.com" in result.modified_text


def test_multiple_pii_types(pii_guard, sample_pii_text):
    """Text with multiple PII types should detect all of them."""
    result = pii_guard.check(sample_pii_text)
    assert result.passed is False
    categories = {v["category"] for v in result.violations}
    assert "email" in categories
    assert "phone" in categories
    assert "ssn" in categories


def test_empty_input(pii_guard):
    """Empty string should pass the guard."""
    result = pii_guard.check("")
    assert result.passed is True
    assert result.violations == []


def test_category_filtering():
    """Only detecting EMAIL category should skip SSN."""
    guard = PIIGuard(
        on_violation=GuardAction.BLOCK,
        categories=[PIICategory.EMAIL],
    )
    result = guard.check("Email: user@example.com SSN: 123-45-6789")
    categories = [v["category"] for v in result.violations]
    assert "email" in categories
    assert "ssn" not in categories


def test_confidence_scaling(pii_guard):
    """More PII items should produce higher confidence than fewer."""
    result_one = pii_guard.check("Email: user@example.com")
    result_many = pii_guard.check(
        "Email: user@example.com Phone: 555-123-4567 "
        "SSN: 123-45-6789 DOB: 01/15/1990"
    )
    assert result_many.confidence >= result_one.confidence
