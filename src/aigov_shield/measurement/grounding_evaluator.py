"""Factual grounding evaluator for the measurement layer."""

from __future__ import annotations

import re
import string
from typing import Any

from aigov_shield.measurement.base import BaseEvaluator, EvaluationResult


class GroundingEvaluator(BaseEvaluator):
    """Measures factual grounding using token-level Jaccard similarity.

    Compares each sentence in an AI output against the provided reference
    context to determine whether the output is grounded in factual source
    material.

    Args:
        threshold: Minimum average grounding score required to pass.
        similarity_threshold: Minimum Jaccard similarity for a sentence
            to be considered grounded.
    """

    _SENTENCE_SPLIT_PATTERN: re.Pattern[str] = re.compile(r"(?<=[\.\!\?])\s+|\n+")

    def __init__(
        self,
        threshold: float = 0.7,
        similarity_threshold: float = 0.3,
    ) -> None:
        super().__init__(threshold=threshold)
        self.similarity_threshold = similarity_threshold

    def evaluate(self, data: list[dict[str, str]]) -> EvaluationResult:
        """Evaluate factual grounding across the provided dataset.

        Each item in *data* must contain an ``"output"`` key (the AI-generated
        text) and a ``"context"`` key (the reference source material).

        Args:
            data: List of dicts with ``"output"`` and ``"context"`` fields.

        Returns:
            An ``EvaluationResult`` with metric name
            ``"factual_grounding"``.
        """
        total_items = len(data)
        if total_items == 0:
            return EvaluationResult(
                metric_name="factual_grounding",
                score=1.0,
                passed=True,
                threshold=self.threshold,
                details=[],
                summary={
                    "grounding_score": 1.0,
                    "hallucination_rate": 0.0,
                    "total_claims": 0,
                    "grounded_claims": 0,
                    "ungrounded_claims": [],
                },
                nist_function="MAP",
            )

        details: list[dict[str, Any]] = []
        total_grounding_score = 0.0
        total_claims = 0
        total_grounded = 0
        all_ungrounded: list[str] = []

        for idx, item in enumerate(data):
            output_text = item.get("output", "")
            context_text = item.get("context", "")

            sentences = self._split_sentences(output_text)
            # Filter to sentences with 5+ words.
            meaningful_sentences = [s for s in sentences if len(s.split()) >= 5]

            if not meaningful_sentences:
                details.append(
                    {
                        "item_index": idx,
                        "grounding_score": 1.0,
                        "grounded_sentences": 0,
                        "ungrounded_sentences": 0,
                        "ungrounded_text": [],
                    }
                )
                total_grounding_score += 1.0
                continue

            context_tokens = self._tokenize(context_text)
            grounded_count = 0
            ungrounded_text: list[str] = []

            for sentence in meaningful_sentences:
                sentence_tokens = self._tokenize(sentence)
                similarity = self._jaccard_similarity(
                    sentence_tokens,
                    context_tokens,
                )
                if similarity >= self.similarity_threshold:
                    grounded_count += 1
                else:
                    ungrounded_text.append(sentence)

            ungrounded_count = len(meaningful_sentences) - grounded_count
            item_score = grounded_count / len(meaningful_sentences)

            total_claims += len(meaningful_sentences)
            total_grounded += grounded_count
            total_grounding_score += item_score
            all_ungrounded.extend(ungrounded_text)

            details.append(
                {
                    "item_index": idx,
                    "grounding_score": item_score,
                    "grounded_sentences": grounded_count,
                    "ungrounded_sentences": ungrounded_count,
                    "ungrounded_text": ungrounded_text,
                }
            )

        score = total_grounding_score / total_items
        passed = score >= self.threshold

        return EvaluationResult(
            metric_name="factual_grounding",
            score=score,
            passed=passed,
            threshold=self.threshold,
            details=details,
            summary={
                "grounding_score": score,
                "hallucination_rate": 1.0 - score,
                "total_claims": total_claims,
                "grounded_claims": total_grounded,
                "ungrounded_claims": all_ungrounded,
            },
            nist_function="MAP",
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences using common delimiters.

        Args:
            text: The text to split.

        Returns:
            A list of non-empty sentence strings.
        """
        parts = self._SENTENCE_SPLIT_PATTERN.split(text)
        return [p.strip() for p in parts if p.strip()]

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        """Tokenize text by lowercasing, splitting on whitespace, and
        stripping punctuation.

        Args:
            text: The text to tokenize.

        Returns:
            A set of lowercase token strings.
        """
        translator = str.maketrans("", "", string.punctuation)
        words = text.lower().split()
        return {w.translate(translator) for w in words if w.translate(translator)}

    @staticmethod
    def _jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
        """Compute Jaccard similarity between two token sets.

        Args:
            set_a: First set of tokens.
            set_b: Second set of tokens.

        Returns:
            A float in ``[0.0, 1.0]``.  Returns 0.0 if both sets are empty.
        """
        if not set_a and not set_b:
            return 0.0
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union)
