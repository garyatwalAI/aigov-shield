"""Guard chain for composing multiple guards into a pipeline."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from aigov_shield.prevention.base import BaseGuard, GuardAction, GuardResult


class ExecutionMode(Enum):
    """Execution mode for the guard chain.

    Attributes:
        FAIL_FAST: Stop at the first guard failure.
        RUN_ALL: Run all guards and aggregate results.
        PRIORITY: Run guards in priority order, stop at first failure
            at or above the priority threshold.
    """

    FAIL_FAST = "fail_fast"
    RUN_ALL = "run_all"
    PRIORITY = "priority"


@dataclass
class ChainResult:
    """Result of running a guard chain.

    Attributes:
        passed: Whether all guards passed (or none exceeded the failure policy).
        results: Individual GuardResult from each guard that ran.
        failed_guards: Names of guards that failed.
        total_execution_time_ms: Total time for the entire chain.
        execution_mode: The execution mode that was used.
        metadata: Additional metadata about the chain execution.
    """

    passed: bool
    results: list[GuardResult] = field(default_factory=list)
    failed_guards: list[str] = field(default_factory=list)
    total_execution_time_ms: float = 0.0
    execution_mode: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def modified_text(self) -> str | None:
        """Return the final modified text after all redactions.

        Returns the last non-None modified_text from the chain, or None
        if no guard produced a modification.
        """
        for result in reversed(self.results):
            if result.modified_text is not None:
                return result.modified_text
        return None


class GuardChain:
    """Compose multiple guards into a sequential pipeline.

    The chain runs guards in order and applies configurable execution
    policies to determine when to stop and how to aggregate results.

    Args:
        guards: List of guard instances to run in order.
        execution_mode: How to execute the chain (fail_fast, run_all, priority).
        priority_threshold: For PRIORITY mode, the minimum priority level
            (0-based index) at which a failure stops the chain.

    Example:
        >>> chain = GuardChain([
        ...     PIIGuard(on_violation=GuardAction.REDACT),
        ...     PrivilegeGuard(on_violation=GuardAction.BLOCK),
        ...     ToxicityGuard(on_violation=GuardAction.FLAG),
        ... ])
        >>> result = chain.run("Some text to check")
    """

    def __init__(
        self,
        guards: list[BaseGuard],
        execution_mode: ExecutionMode = ExecutionMode.RUN_ALL,
        priority_threshold: int = 0,
    ) -> None:
        self.guards = guards
        self.execution_mode = execution_mode
        self.priority_threshold = priority_threshold

    def run(
        self,
        text: str,
        context: dict[str, Any] | None = None,
    ) -> ChainResult:
        """Run text through all guards in the chain.

        For REDACT actions, the modified text from one guard is passed
        as input to the next guard in the chain.

        Args:
            text: The text to check.
            context: Optional additional context passed to each guard.

        Returns:
            ChainResult with individual results and overall pass/fail.
        """
        start_time = time.perf_counter()
        results: list[GuardResult] = []
        failed_guards: list[str] = []
        current_text = text

        for i, guard in enumerate(self.guards):
            result = guard.check(current_text, context)
            results.append(result)

            if not result.passed:
                failed_guards.append(result.guard_name)

                if result.action_taken == GuardAction.REDACT and result.modified_text:
                    current_text = result.modified_text

                if self._should_stop(i, result):
                    break
            elif result.modified_text:
                current_text = result.modified_text

        elapsed = (time.perf_counter() - start_time) * 1000
        passed = len(failed_guards) == 0

        return ChainResult(
            passed=passed,
            results=results,
            failed_guards=failed_guards,
            total_execution_time_ms=round(elapsed, 3),
            execution_mode=self.execution_mode.value,
        )

    def _should_stop(self, index: int, result: GuardResult) -> bool:
        """Determine whether the chain should stop after a failure.

        Args:
            index: The index of the current guard in the chain.
            result: The result from the current guard.

        Returns:
            True if the chain should stop execution.
        """
        if self.execution_mode == ExecutionMode.FAIL_FAST:
            return True

        if self.execution_mode == ExecutionMode.PRIORITY:
            return index >= self.priority_threshold

        return False

    def __call__(
        self,
        text: str,
        context: dict[str, Any] | None = None,
    ) -> ChainResult:
        """Allow the chain to be called as a function."""
        return self.run(text, context)
