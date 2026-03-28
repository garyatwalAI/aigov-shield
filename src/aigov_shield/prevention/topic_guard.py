"""Topical boundary enforcement guard.

Ensures generated or incoming text stays within configured topical
boundaries by checking for blocked-topic keywords and, optionally,
verifying that the text relates to an allowed set of topics.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from aigov_shield.prevention.base import BaseGuard, GuardAction, GuardResult

# ---------------------------------------------------------------------------
# Default blocked-topic keyword lists
# ---------------------------------------------------------------------------

_DEFAULT_BLOCKED_KEYWORDS: Dict[str, List[str]] = {
    "medical_advice": [
        "diagnosis",
        "prescription",
        "dosage",
        "medication",
        "symptoms indicate",
        "you should take",
        "medical treatment",
    ],
    "financial_advice": [
        "invest in",
        "buy stock",
        "financial advice",
        "guaranteed returns",
        "trading strategy",
    ],
    "legal_advice": [
        "legal advice",
        "you should sue",
        "file a lawsuit",
        "legal recommendation",
    ],
}


class TopicGuard(BaseGuard):
    """Guard that enforces topical boundaries on text content.

    When *blocked_topics* is provided together with *blocked_keywords*,
    any text containing keywords from a blocked topic triggers a
    violation.  When *allowed_topics* is provided, text that does not
    appear to relate to any allowed topic is flagged.

    Args:
        on_violation: Action to take when an off-topic violation is
            detected.
        confidence_threshold: Minimum confidence to treat a detection as
            a real violation.
        allowed_topics: Optional list of topic names that are permitted.
            When supplied, text that does not match any allowed topic is
            flagged.
        blocked_topics: Optional list of topic names that are forbidden.
            Keywords for each topic are looked up in *blocked_keywords*.
        blocked_keywords: Mapping of topic names to keyword lists.
            Defaults to a built-in set covering medical, financial, and
            legal advice topics when ``None``.
    """

    def __init__(
        self,
        on_violation: GuardAction = GuardAction.BLOCK,
        confidence_threshold: float = 0.5,
        allowed_topics: Optional[List[str]] = None,
        blocked_topics: Optional[List[str]] = None,
        blocked_keywords: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        super().__init__(
            name="topic_guard",
            on_violation=on_violation,
            confidence_threshold=confidence_threshold,
        )
        self.allowed_topics: Optional[List[str]] = allowed_topics
        self.blocked_topics: Optional[List[str]] = blocked_topics
        self.blocked_keywords: Dict[str, List[str]] = (
            blocked_keywords
            if blocked_keywords is not None
            else dict(_DEFAULT_BLOCKED_KEYWORDS)
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> GuardResult:
        """Scan *text* for topical violations and return a ``GuardResult``.

        Args:
            text: The input string to scan.
            context: Optional metadata (unused by this guard but accepted
                for interface compatibility).

        Returns:
            A ``GuardResult`` describing what was found.
        """
        start_time = time.perf_counter()
        text_lower = text.lower()

        violations: List[Dict[str, Any]] = []
        total_hits = 0

        # -- Check blocked topics -------------------------------------------
        if self.blocked_topics is not None:
            for topic in self.blocked_topics:
                keywords = self.blocked_keywords.get(topic, [])
                matched_keywords: List[str] = [
                    kw for kw in keywords if kw.lower() in text_lower
                ]
                if matched_keywords:
                    violations.append(
                        {
                            "topic": topic,
                            "matched_keywords": matched_keywords,
                            "detection_type": "blocked_topic",
                        }
                    )
                    total_hits += len(matched_keywords)

        # -- Check allowed topics -------------------------------------------
        if self.allowed_topics is not None:
            topic_matched = False
            for topic in self.allowed_topics:
                # Use the topic name itself as a keyword for simple matching.
                keywords = self.blocked_keywords.get(topic, [topic.lower()])
                if any(kw.lower() in text_lower for kw in keywords):
                    topic_matched = True
                    break
            if not topic_matched:
                violations.append(
                    {
                        "topic": "off_topic",
                        "matched_keywords": [],
                        "detection_type": "not_in_allowed_topics",
                    }
                )
                # Treat an off-topic miss as a single hit for confidence.
                total_hits = max(total_hits, 1)

        # -- Compute confidence ---------------------------------------------
        if total_hits >= 3:
            confidence = 0.8
        elif total_hits == 2:
            confidence = 0.6
        elif total_hits == 1:
            confidence = 0.4
        else:
            confidence = 0.0

        passed = not violations or confidence < self.confidence_threshold

        return self._make_result(
            text=text,
            passed=passed,
            violations=violations,
            confidence=confidence,
            start_time=start_time,
        )
