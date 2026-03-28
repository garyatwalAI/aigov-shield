"""Prompt injection detection guard.

Detects prompt injection attempts across five attack categories
(instruction override, role switching, system prompt extraction,
delimiter injection, and encoding attacks) using compiled
regular-expression patterns with per-category severity scores.
"""

from __future__ import annotations

import re
import time
from typing import Any

from aigov_shield.prevention.base import BaseGuard, GuardAction, GuardResult

# ---------------------------------------------------------------------------
# Compiled injection patterns: (category, pattern, severity)
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS: list[tuple[str, re.Pattern[str], float]] = [
    # -- instruction_override (severity 0.9) ---------------------------------
    (
        "instruction_override",
        re.compile(
            r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+"
            r"(?:instructions|prompts|directives|rules)",
            re.IGNORECASE,
        ),
        0.9,
    ),
    (
        "instruction_override",
        re.compile(
            r"disregard\s+(?:all\s+)?(?:previous|prior|your)\s+"
            r"(?:instructions|programming|rules)",
            re.IGNORECASE,
        ),
        0.9,
    ),
    (
        "instruction_override",
        re.compile(
            r"forget\s+(?:all\s+)?(?:your|previous|prior)\s+"
            r"(?:instructions|rules|programming)",
            re.IGNORECASE,
        ),
        0.9,
    ),
    # -- role_switching (severity 0.7) ---------------------------------------
    (
        "role_switching",
        re.compile(
            r"you\s+are\s+now\s+(?:a|an|the)\s+",
            re.IGNORECASE,
        ),
        0.7,
    ),
    (
        "role_switching",
        re.compile(
            r"act\s+as\s+(?:a|an|if\s+you\s+were)\s+",
            re.IGNORECASE,
        ),
        0.7,
    ),
    (
        "role_switching",
        re.compile(
            r"pretend\s+(?:to\s+be|you\s+are)\s+",
            re.IGNORECASE,
        ),
        0.7,
    ),
    (
        "role_switching",
        re.compile(
            r"from\s+now\s+on\s+you\s+(?:are|will|must|should)\s+",
            re.IGNORECASE,
        ),
        0.7,
    ),
    # -- system_prompt_extraction (severity 0.85) ----------------------------
    (
        "system_prompt_extraction",
        re.compile(
            r"(?:repeat|show|display|reveal|print|output)\s+"
            r"(?:your\s+)?(?:system\s+)?(?:prompt|instructions|programming|rules)",
            re.IGNORECASE,
        ),
        0.85,
    ),
    (
        "system_prompt_extraction",
        re.compile(
            r"what\s+(?:are|is)\s+your\s+(?:system\s+)?"
            r"(?:prompt|instructions|rules|programming)",
            re.IGNORECASE,
        ),
        0.85,
    ),
    (
        "system_prompt_extraction",
        re.compile(
            r"(?:tell|show)\s+me\s+your\s+(?:initial|system|original)\s+"
            r"(?:prompt|instructions|message)",
            re.IGNORECASE,
        ),
        0.85,
    ),
    # -- delimiter_injection (severity 0.95) ---------------------------------
    (
        "delimiter_injection",
        re.compile(
            r"```\s*(?:system|assistant|user)\s*\n",
            re.IGNORECASE,
        ),
        0.95,
    ),
    (
        "delimiter_injection",
        re.compile(
            r"<\|(?:im_start|im_end|system|endoftext)\|>",
            re.IGNORECASE,
        ),
        0.95,
    ),
    (
        "delimiter_injection",
        re.compile(
            r"\[INST\]|\[/INST\]|<<SYS>>|<</SYS>>",
            re.IGNORECASE,
        ),
        0.95,
    ),
    # -- encoding_attack (severity 0.6) --------------------------------------
    (
        "encoding_attack",
        re.compile(
            r"(?:base64|rot13|hex)\s*(?:decode|encode|of)\s*:?\s*",
            re.IGNORECASE,
        ),
        0.6,
    ),
    (
        "encoding_attack",
        re.compile(
            r"decode\s+(?:this|the\s+following)\s*:?\s*[A-Za-z0-9+/=]{20,}",
            re.IGNORECASE,
        ),
        0.6,
    ),
]


class PromptInjectionGuard(BaseGuard):
    """Guard that detects prompt injection attempts.

    Scans text against a library of compiled regular-expression patterns
    grouped into five attack categories.  Each pattern carries a severity
    score; the overall detection confidence equals the maximum severity
    among all matched patterns.

    Args:
        on_violation: Action to take when an injection attempt is
            detected.
        confidence_threshold: Minimum confidence to treat a detection as
            a real violation.
        custom_patterns: Optional list of ``(category, pattern_string,
            severity)`` tuples.  These are compiled and appended to the
            built-in pattern list.
    """

    def __init__(
        self,
        on_violation: GuardAction = GuardAction.BLOCK,
        confidence_threshold: float = 0.5,
        custom_patterns: list[tuple[str, str, float]] | None = None,
    ) -> None:
        super().__init__(
            name="prompt_injection_guard",
            on_violation=on_violation,
            confidence_threshold=confidence_threshold,
        )
        self._patterns: list[tuple[str, re.Pattern[str], float]] = list(_INJECTION_PATTERNS)
        if custom_patterns:
            for category, pattern_str, severity in custom_patterns:
                compiled = re.compile(pattern_str, re.IGNORECASE)
                self._patterns.append((category, compiled, severity))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(
        self,
        text: str,
        context: dict[str, Any] | None = None,
    ) -> GuardResult:
        """Scan *text* for prompt injection attempts and return a ``GuardResult``.

        Args:
            text: The input string to scan.
            context: Optional metadata (unused by this guard but accepted
                for interface compatibility).

        Returns:
            A ``GuardResult`` describing what was found.
        """
        start_time = time.perf_counter()

        violations: list[dict[str, Any]] = []
        max_severity = 0.0

        for category, pattern, severity in self._patterns:
            match = pattern.search(text)
            if match:
                violations.append(
                    {
                        "category": category,
                        "matched_text": match.group(0),
                        "severity": severity,
                    }
                )
                if severity > max_severity:
                    max_severity = severity

        confidence = max_severity
        passed = not violations or confidence < self.confidence_threshold

        return self._make_result(
            text=text,
            passed=passed,
            violations=violations,
            confidence=confidence,
            start_time=start_time,
        )
