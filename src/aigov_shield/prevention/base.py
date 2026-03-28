"""Base classes and types for the prevention layer."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GuardAction(Enum):
    """Action to take when a guard detects a violation."""

    BLOCK = "block"
    REDACT = "redact"
    FLAG = "flag"
    PASSTHROUGH = "passthrough"


@dataclass
class GuardResult:
    """Result of a guard check."""

    passed: bool
    action_taken: GuardAction
    original_text: str
    modified_text: str | None = None
    violations: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    guard_name: str = ""
    execution_time_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseGuard(ABC):
    """Base class for all prevention guards.

    All guards implement the check() method which analyses text and returns
    a GuardResult indicating whether the text passes the guard's rules.

    Args:
        name: Human-readable name for this guard instance.
        on_violation: Action to take when a violation is detected.
        confidence_threshold: Minimum confidence score to consider a detection valid.
    """

    def __init__(
        self,
        name: str,
        on_violation: GuardAction = GuardAction.BLOCK,
        confidence_threshold: float = 0.5,
    ) -> None:
        self.name = name
        self.on_violation = on_violation
        self.confidence_threshold = confidence_threshold

    @abstractmethod
    def check(self, text: str, context: dict[str, Any] | None = None) -> GuardResult:
        """Check text against the guard's rules.

        Args:
            text: The text to check.
            context: Optional additional context for the check.

        Returns:
            GuardResult with the check outcome.
        """
        ...

    def __call__(self, text: str, context: dict[str, Any] | None = None) -> GuardResult:
        """Allow guards to be called as functions."""
        return self.check(text, context)

    def _make_result(
        self,
        text: str,
        passed: bool,
        violations: list[dict[str, Any]],
        confidence: float,
        start_time: float,
        modified_text: str | None = None,
    ) -> GuardResult:
        """Helper to construct a GuardResult with timing info.

        Args:
            text: The original text.
            passed: Whether the text passed the check.
            violations: List of detected violations.
            confidence: Confidence score for the detection.
            start_time: Time when the check started (from time.perf_counter()).
            modified_text: Modified text if redaction was applied.

        Returns:
            A populated GuardResult.
        """
        elapsed = (time.perf_counter() - start_time) * 1000
        action = GuardAction.PASSTHROUGH if passed else self.on_violation
        return GuardResult(
            passed=passed,
            action_taken=action,
            original_text=text,
            modified_text=modified_text,
            violations=violations,
            confidence=confidence,
            guard_name=self.name,
            execution_time_ms=round(elapsed, 3),
        )
