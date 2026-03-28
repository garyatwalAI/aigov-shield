"""Tests for the TopicGuard."""

from __future__ import annotations

from aigov_shield.prevention import GuardAction, TopicGuard


def test_allowed_topic_passes(topic_guard, sample_clean_text):
    """On-topic text (no blocked keywords) should pass the guard."""
    result = topic_guard.check(sample_clean_text)
    assert result.passed is True
    assert result.violations == []


def test_blocked_topic_fails(topic_guard):
    """Medical advice text should fail when medical_advice is blocked."""
    text = "Based on your symptoms indicate a diagnosis of flu. You should take ibuprofen."
    result = topic_guard.check(text)
    assert result.passed is False
    topics = [v["topic"] for v in result.violations]
    assert "medical_advice" in topics


def test_no_topics_configured_passes():
    """With no topics configured, everything should pass."""
    guard = TopicGuard(on_violation=GuardAction.BLOCK)
    result = guard.check("This is about diagnosis and medication dosage.")
    assert result.passed is True


def test_custom_blocked_keywords():
    """Custom blocked keywords should work for detection."""
    guard = TopicGuard(
        on_violation=GuardAction.BLOCK,
        blocked_topics=["weapons"],
        blocked_keywords={"weapons": ["firearm", "ammunition", "explosive"]},
        confidence_threshold=0.0,
    )
    result = guard.check("We need to discuss the ammunition supply.")
    assert result.passed is False
    topics = [v["topic"] for v in result.violations]
    assert "weapons" in topics


def test_empty_input_passes(topic_guard):
    """Empty string should pass the guard."""
    result = topic_guard.check("")
    assert result.passed is True
    assert result.violations == []


def test_multiple_blocked_hits_confidence():
    """More keyword hits should produce higher confidence."""
    guard = TopicGuard(
        on_violation=GuardAction.BLOCK,
        blocked_topics=["medical_advice"],
        confidence_threshold=0.0,
    )
    result_one = guard.check("The diagnosis was clear.")
    result_many = guard.check(
        "The diagnosis led to a prescription for medication. "
        "The dosage was adjusted based on symptoms indicate improvement."
    )
    assert result_many.confidence >= result_one.confidence
