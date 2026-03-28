"""Base classes for the measurement layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvaluationResult:
    """Result of evaluating a dataset against compliance criteria.

    Attributes:
        metric_name: Name of the metric being measured.
        score: Score from 0.0 to 1.0.
        passed: Whether the score meets the threshold.
        threshold: The threshold used for pass/fail determination.
        details: Per-item breakdown of the evaluation.
        summary: Aggregate statistics.
        nist_function: Which NIST AI RMF function this maps to.
    """

    metric_name: str
    score: float
    passed: bool
    threshold: float
    details: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    nist_function: str = ""


class BaseEvaluator(ABC):
    """Base class for all compliance evaluators.

    Args:
        threshold: The minimum score required to pass (0.0 to 1.0).
    """

    def __init__(self, threshold: float = 0.9) -> None:
        self.threshold = threshold

    @abstractmethod
    def evaluate(self, data: list[dict[str, str]]) -> EvaluationResult:
        """Evaluate a dataset of AI outputs against compliance criteria.

        Args:
            data: List of dicts, each representing one AI output to evaluate.

        Returns:
            EvaluationResult with scores and details.
        """
        ...
