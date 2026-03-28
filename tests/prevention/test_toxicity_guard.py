"""Tests for the ToxicityGuard."""

from __future__ import annotations

from aigov_shield.prevention import GuardAction, ToxicityGuard


def test_clean_text_passes(toxicity_guard, sample_clean_text):
    """Normal text should pass without triggering toxicity detection."""
    result = toxicity_guard.check(sample_clean_text)
    assert result.passed is True
    assert result.violations == []
    assert result.action_taken == GuardAction.PASSTHROUGH


def test_threat_detection(toxicity_guard):
    """'I will kill you' should be detected as a threat."""
    result = toxicity_guard.check("I will kill you if you don't comply.")
    assert result.passed is False
    categories = {v["category"] for v in result.violations}
    assert "threats" in categories


def test_hate_speech_detection(toxicity_guard):
    """Clearly hateful content should be detected."""
    result = toxicity_guard.check(
        "They are subhuman, an inferior race, and deserve ethnic cleansing."
    )
    assert result.passed is False
    categories = {v["category"] for v in result.violations}
    assert "hate_speech" in categories


def test_self_harm_always_flagged():
    """Self-harm content should get FLAG action regardless of on_violation setting."""
    guard = ToxicityGuard(on_violation=GuardAction.BLOCK, confidence_threshold=0.0)
    result = guard.check("I want to kill myself.")
    assert result.passed is False
    assert result.action_taken == GuardAction.FLAG


def test_self_harm_human_review():
    """Self-harm result should have metadata['requires_human_review'] = True."""
    guard = ToxicityGuard(on_violation=GuardAction.BLOCK, confidence_threshold=0.0)
    result = guard.check("I want to kill myself.")
    assert result.metadata.get("requires_human_review") is True


def test_custom_patterns():
    """User-provided custom patterns should work."""
    guard = ToxicityGuard(
        on_violation=GuardAction.BLOCK,
        custom_patterns={"threats": ["i will sue you"]},
        confidence_threshold=0.0,
    )
    result = guard.check("I will sue you for everything you have.")
    assert result.passed is False
    matched = [v["matched_text"] for v in result.violations]
    assert "i will sue you" in matched


def test_empty_input_passes(toxicity_guard):
    """Empty string should pass the guard."""
    result = toxicity_guard.check("")
    assert result.passed is True
    assert result.violations == []


def test_regex_threat_pattern(toxicity_guard):
    """Complex threat regex should match 'I'm going to hurt them'."""
    result = toxicity_guard.check("I'm going to hurt them badly.")
    assert result.passed is False
    regex_violations = [v for v in result.violations if v.get("detection_type") == "regex"]
    assert len(regex_violations) >= 1


def test_multiple_categories_high_confidence(toxicity_guard):
    """Multiple toxic indicators should produce higher confidence."""
    result_single = toxicity_guard.check("You're worthless.")
    result_multi = toxicity_guard.check("I will kill you. You're worthless. You disgust me.")
    # Multiple hits should produce equal or higher confidence.
    assert result_multi.confidence >= result_single.confidence
