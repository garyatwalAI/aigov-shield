"""Decision recording for explainable decision trails."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class DecisionStep:
    """A single step in a decision trail.

    Attributes:
        step_name: Name of this decision step.
        timestamp: ISO 8601 timestamp when the step was recorded.
        data: Arbitrary data associated with this step.
    """

    step_name: str
    timestamp: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionTrail:
    """A complete decision trail consisting of multiple steps.

    Attributes:
        decision_id: Unique identifier for this decision.
        started_at: ISO 8601 timestamp when the decision began.
        completed_at: ISO 8601 timestamp when the decision ended, or ``None``
            if still in progress.
        steps: Ordered list of decision steps.
        metadata: Additional metadata.
    """

    decision_id: str
    started_at: str
    completed_at: str | None = None
    steps: list[DecisionStep] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class DecisionContext:
    """Context manager for recording steps within a decision.

    Args:
        decision_id: Identifier for the decision being recorded.
        recorder: The parent ``DecisionRecorder`` instance.
    """

    def __init__(self, decision_id: str, recorder: DecisionRecorder) -> None:
        self._decision_id = decision_id
        self._recorder = recorder

    def log_step(self, step_name: str, **kwargs: Any) -> None:
        """Log a step in the decision trail.

        Args:
            step_name: Name of the step.
            **kwargs: Arbitrary key-value data for this step.
        """
        trail = self._recorder._decisions.get(self._decision_id)
        if trail is None:
            return
        step = DecisionStep(
            step_name=step_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=dict(kwargs),
        )
        trail.steps.append(step)

    def __enter__(self) -> DecisionContext:
        trail = self._recorder._decisions.get(self._decision_id)
        if trail is not None:
            trail.started_at = datetime.now(timezone.utc).isoformat()
        return self

    def __exit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: Any | None,
    ) -> None:
        trail = self._recorder._decisions.get(self._decision_id)
        if trail is not None:
            trail.completed_at = datetime.now(timezone.utc).isoformat()


class DecisionRecorder:
    """Records decision trails for explainability and auditing."""

    def __init__(self) -> None:
        self._decisions: dict[str, DecisionTrail] = {}

    def record_decision(self, decision_id: str) -> DecisionContext:
        """Create a context manager for recording a decision trail.

        Args:
            decision_id: Unique identifier for the decision.

        Returns:
            A ``DecisionContext`` that can be used as a context manager.
        """
        trail = DecisionTrail(
            decision_id=decision_id,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        self._decisions[decision_id] = trail
        return DecisionContext(decision_id=decision_id, recorder=self)

    def export_decision(self, decision_id: str) -> dict[str, Any] | None:
        """Export a single decision trail as a dictionary.

        Args:
            decision_id: The decision identifier.

        Returns:
            Dictionary representation of the decision trail, or ``None`` if
            not found.
        """
        trail = self._decisions.get(decision_id)
        if trail is None:
            return None
        return {
            "decision_id": trail.decision_id,
            "started_at": trail.started_at,
            "completed_at": trail.completed_at,
            "steps": [
                {
                    "step_name": step.step_name,
                    "timestamp": step.timestamp,
                    "data": step.data,
                }
                for step in trail.steps
            ],
            "metadata": trail.metadata,
        }

    def list_decisions(self) -> list[str]:
        """List all recorded decision IDs.

        Returns:
            List of decision identifiers.
        """
        return list(self._decisions.keys())
