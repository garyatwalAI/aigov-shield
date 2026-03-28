"""Pattern-based toxicity detection guard.

Detects toxic content across five categories (hate speech, threats,
sexually explicit material, self-harm, and harassment) using keyword
matching, compiled regular expressions, and an optional external
classifier hook.
"""

from __future__ import annotations

import re
import time
from typing import Any, Callable

from aigov_shield.prevention.base import BaseGuard, GuardAction, GuardResult

# ---------------------------------------------------------------------------
# Keyword patterns by category
# ---------------------------------------------------------------------------

_TOXICITY_PATTERNS: dict[str, list[str]] = {
    "hate_speech": [
        "kill all",
        "exterminate",
        "subhuman",
        "inferior race",
        "go back to your country",
        "ethnic cleansing",
        "death to all",
        "they should be wiped out",
        "vermin people",
        "purge them",
    ],
    "threats": [
        "i will kill you",
        "i'm going to hurt you",
        "you will pay for this",
        "watch your back",
        "i'll destroy you",
        "death threat",
        "bomb threat",
        "i will find you",
    ],
    "sexually_explicit": [
        "explicit sexual",
        "pornographic content",
        "sexually explicit material",
        "graphic sexual act",
        "sexual exploitation",
    ],
    "self_harm": [
        "kill myself",
        "end my life",
        "suicide method",
        "how to self-harm",
        "want to die",
        "cut myself",
    ],
    "harassment": [
        "you're worthless",
        "nobody likes you",
        "you're stupid",
        "you disgust me",
        "loser",
        "pathetic excuse",
    ],
}

# ---------------------------------------------------------------------------
# Compiled regex patterns for advanced detection
# ---------------------------------------------------------------------------

_TOXICITY_REGEX: list[tuple[str, re.Pattern[str]]] = [
    (
        "threats",
        re.compile(
            r"(?:i\s+will|i'm\s+going\s+to|gonna)\s+"
            r"(?:kill|hurt|destroy|find|hunt)\s+"
            r"(?:you|them|him|her)",
            re.IGNORECASE,
        ),
    ),
    (
        "hate_speech",
        re.compile(
            r"(?:should\s+be|deserve\s+to\s+be)\s+"
            r"(?:killed|shot|hanged|beaten|eliminated)",
            re.IGNORECASE,
        ),
    ),
]


class ToxicityGuard(BaseGuard):
    """Guard that detects toxic content via keywords, regex, and an optional classifier.

    Scans input text for five toxicity categories.  Detection confidence
    scales with the number of keyword and regex hits.  When self-harm
    content is detected the action is always ``GuardAction.FLAG`` and the
    result metadata includes ``requires_human_review = True``.

    Args:
        on_violation: Action to take when toxic content is detected.
        confidence_threshold: Minimum confidence to treat a detection as
            a real violation.
        categories: Subset of category names to scan.  Defaults to all
            categories when ``None``.
        custom_patterns: Additional keyword patterns keyed by category
            name.  Merged with the built-in patterns.
        classifier_fn: Optional callable that accepts a string and returns
            a ``(is_toxic, confidence)`` tuple.  When provided its result
            is incorporated into the final confidence score.
    """

    def __init__(
        self,
        on_violation: GuardAction = GuardAction.BLOCK,
        confidence_threshold: float = 0.5,
        categories: list[str] | None = None,
        custom_patterns: dict[str, list[str]] | None = None,
        classifier_fn: Callable[[str], tuple[bool, float]] | None = None,
    ) -> None:
        super().__init__(
            name="toxicity_guard",
            on_violation=on_violation,
            confidence_threshold=confidence_threshold,
        )
        self.categories: list[str] = (
            categories if categories is not None else list(_TOXICITY_PATTERNS.keys())
        )
        self.custom_patterns: dict[str, list[str]] = custom_patterns or {}
        self.classifier_fn = classifier_fn

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_patterns_for_category(self, category: str) -> list[str]:
        """Return the merged keyword list for *category*.

        Args:
            category: Toxicity category name.

        Returns:
            Combined list of built-in and custom keywords.
        """
        builtin = _TOXICITY_PATTERNS.get(category, [])
        custom = self.custom_patterns.get(category, [])
        return builtin + custom

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(
        self,
        text: str,
        context: dict[str, Any] | None = None,
    ) -> GuardResult:
        """Scan *text* for toxic content and return a ``GuardResult``.

        Args:
            text: The input string to scan.
            context: Optional metadata (unused by this guard but accepted
                for interface compatibility).

        Returns:
            A ``GuardResult`` describing what was found.
        """
        start_time = time.perf_counter()
        text_lower = text.lower()

        violations: list[dict[str, Any]] = []
        keyword_hit_count = 0
        regex_matched = False
        classifier_matched = False
        self_harm_detected = False

        # -- Keyword matching ------------------------------------------------
        for category in self.categories:
            keywords = self._get_patterns_for_category(category)
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    violations.append(
                        {
                            "category": category,
                            "matched_text": keyword,
                            "detection_type": "keyword",
                        }
                    )
                    keyword_hit_count += 1
                    if category == "self_harm":
                        self_harm_detected = True

        # -- Regex matching --------------------------------------------------
        for category, pattern in _TOXICITY_REGEX:
            if category not in self.categories:
                continue
            match = pattern.search(text)
            if match:
                violations.append(
                    {
                        "category": category,
                        "matched_text": match.group(0),
                        "detection_type": "regex",
                    }
                )
                regex_matched = True

        # -- Optional classifier ---------------------------------------------
        if self.classifier_fn is not None:
            is_toxic, clf_confidence = self.classifier_fn(text)
            if is_toxic:
                violations.append(
                    {
                        "category": "classifier",
                        "matched_text": "",
                        "detection_type": "classifier",
                        "classifier_confidence": clf_confidence,
                    }
                )
                classifier_matched = True

        # -- Compute confidence ----------------------------------------------
        if regex_matched or classifier_matched:
            confidence = 0.9
        elif keyword_hit_count >= 3:
            confidence = 0.7
        elif keyword_hit_count == 2:
            confidence = 0.5
        elif keyword_hit_count == 1:
            confidence = 0.3
        else:
            confidence = 0.0

        # -- Determine pass / fail -------------------------------------------
        passed = not violations or confidence < self.confidence_threshold

        result = self._make_result(
            text=text,
            passed=passed,
            violations=violations,
            confidence=confidence,
            start_time=start_time,
        )

        # -- Self-harm override: always FLAG with human-review note ----------
        if self_harm_detected and not passed:
            result.action_taken = GuardAction.FLAG
            result.metadata["requires_human_review"] = True

        return result
