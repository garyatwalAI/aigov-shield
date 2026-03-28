"""Legal privilege detection guard.

Detects attorney-client privilege, work product doctrine, and settlement
communication markers in text to prevent inadvertent disclosure of
legally protected content.
"""

from __future__ import annotations

import re
import time
from typing import Any

from aigov_shield.core.types import PrivilegeCategory
from aigov_shield.prevention.base import BaseGuard, GuardAction, GuardResult

# ---------------------------------------------------------------------------
# Category definitions: keywords and compiled regex patterns
# ---------------------------------------------------------------------------

_PRIVILEGE_CATEGORIES: list[dict[str, Any]] = [
    {
        "name": PrivilegeCategory.ATTORNEY_CLIENT,
        "keywords": [
            "attorney-client privilege",
            "legal advice",
            "privileged communication",
            "solicitor-client",
            "legal opinion",
            "client confidentiality",
            "privileged and confidential",
            "seek legal counsel",
            "legal consultation",
            "retain an attorney",
            "communications with counsel",
        ],
        "patterns": [
            re.compile(
                r"this\s+(?:communication|email|memorandum|letter|document)\s+"
                r"is\s+(?:privileged|confidential|protected)",
                re.IGNORECASE,
            ),
            re.compile(
                r"(?:attorney|counsel|solicitor|lawyer|legal\s+team)"
                r".{0,60}"
                r"(?:advise[ds]?|advice|opinion|recommend|instruct)",
                re.IGNORECASE,
            ),
            re.compile(
                r"(?:privilege[ds]?|confidential)"
                r".{0,40}"
                r"(?:communication|discussion|conversation|correspondence)",
                re.IGNORECASE,
            ),
            re.compile(
                r"for\s+the\s+purpose\s+of\s+(?:obtaining|seeking|providing)"
                r".{0,30}"
                r"legal\s+(?:advice|counsel|opinion)",
                re.IGNORECASE,
            ),
            re.compile(
                r"(?:do\s+not|should\s+not|must\s+not)"
                r".{0,30}"
                r"(?:disclose|share|forward|distribute)"
                r".{0,40}"
                r"(?:privileged|confidential)",
                re.IGNORECASE,
            ),
        ],
    },
    {
        "name": PrivilegeCategory.WORK_PRODUCT,
        "keywords": [
            "litigation strategy",
            "case analysis",
            "legal memorandum",
            "trial preparation",
            "work product",
            "litigation hold",
            "case theory",
            "deposition preparation",
            "prepared in anticipation of litigation",
            "legal research memorandum",
            "trial strategy",
        ],
        "patterns": [
            re.compile(
                r"prepared\s+(?:in\s+anticipation\s+of|for\s+purposes\s+of"
                r"|in\s+connection\s+with)"
                r".{0,40}litigation",
                re.IGNORECASE,
            ),
            re.compile(
                r"(?:litigation|trial|case)\s+"
                r"(?:strategy|preparation|theory|analysis|plan)",
                re.IGNORECASE,
            ),
            re.compile(
                r"work\s+product\s+(?:doctrine|protection|privilege)",
                re.IGNORECASE,
            ),
            re.compile(
                r"(?:memorandum|memo|brief|analysis)"
                r".{0,40}"
                r"(?:litigation|trial|deposition|discovery)",
                re.IGNORECASE,
            ),
        ],
    },
    {
        "name": PrivilegeCategory.SETTLEMENT,
        "keywords": [
            "settlement offer",
            "without prejudice",
            "settlement negotiations",
            "mediation brief",
            "compromise proposal",
            "settlement authority",
            "mediation session",
            "settlement conference",
            "settlement demand",
            "Rule 408",
            "FRE 408",
        ],
        "patterns": [
            re.compile(
                r"without\s+prejudice"
                r".{0,60}"
                r"(?:offer|proposal|negotiate|discuss|terms)",
                re.IGNORECASE,
            ),
            re.compile(
                r"settlement\s+(?:offer|proposal|demand|authority|conference|agreement)"
                r".{0,60}"
                r"(?:amount|\$|\u00a3|\u20ac|\d)",
                re.IGNORECASE,
            ),
            re.compile(
                r"(?:mediation|arbitration)"
                r".{0,40}"
                r"(?:brief|statement|submission|session|conference)",
                re.IGNORECASE,
            ),
            re.compile(
                r"Fed\.?\s*R\.?\s*Evid\.?\s*408|Rule\s+408|FRE\s+408",
                re.IGNORECASE,
            ),
        ],
    },
]

# ---------------------------------------------------------------------------
# False-positive exclusion patterns
# ---------------------------------------------------------------------------

_FALSE_POSITIVE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\battorney\s+general\b", re.IGNORECASE),
    re.compile(r"\bdistrict\s+attorney\b", re.IGNORECASE),
    re.compile(
        r"\bsettlement\s+of\s+(?:dust|sediment|particles|soil|land|terrain|ground)\b",
        re.IGNORECASE,
    ),
]

# ---------------------------------------------------------------------------
# Redaction labels per category
# ---------------------------------------------------------------------------

_REDACTION_LABELS: dict[PrivilegeCategory, str] = {
    PrivilegeCategory.ATTORNEY_CLIENT: "[PRIVILEGED \u2014 ATTORNEY-CLIENT]",
    PrivilegeCategory.WORK_PRODUCT: "[PRIVILEGED \u2014 WORK PRODUCT]",
    PrivilegeCategory.SETTLEMENT: "[PRIVILEGED \u2014 SETTLEMENT]",
}


class PrivilegeGuard(BaseGuard):
    """Guard that detects legally privileged content.

    Scans text for markers of attorney-client privilege, work-product
    doctrine, and settlement communications.  When a violation is found
    the guard can block, flag, or redact the content depending on its
    ``on_violation`` setting.

    Args:
        on_violation: Action to take when privileged content is detected.
        confidence_threshold: Minimum confidence to treat a match as a
            real violation.
        categories: Subset of ``PrivilegeCategory`` values to check.
            ``None`` (the default) enables all categories.
    """

    def __init__(
        self,
        on_violation: GuardAction = GuardAction.BLOCK,
        confidence_threshold: float = 0.5,
        categories: list[PrivilegeCategory] | None = None,
    ) -> None:
        super().__init__(
            name="PrivilegeGuard",
            on_violation=on_violation,
            confidence_threshold=confidence_threshold,
        )
        if categories is not None:
            self._enabled_categories: set[PrivilegeCategory] = set(categories)
        else:
            self._enabled_categories = {
                PrivilegeCategory.ATTORNEY_CLIENT,
                PrivilegeCategory.WORK_PRODUCT,
                PrivilegeCategory.SETTLEMENT,
            }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(
        self,
        text: str,
        context: dict[str, Any] | None = None,
    ) -> GuardResult:
        """Scan *text* for legal-privilege markers.

        Args:
            text: The text to analyse.
            context: Optional contextual metadata (unused by this guard
                but accepted to satisfy the ``BaseGuard`` interface).

        Returns:
            A ``GuardResult`` describing the outcome.
        """
        start_time = time.perf_counter()
        text_lower = text.lower()

        # Detect false-positive phrases present in the text.
        false_positive_spans: list[tuple[int, int]] = []
        for fp_pattern in _FALSE_POSITIVE_PATTERNS:
            for m in fp_pattern.finditer(text):
                false_positive_spans.append((m.start(), m.end()))

        violations: list[dict[str, Any]] = []
        category_scores: dict[PrivilegeCategory, float] = {}
        categories_with_patterns: set[PrivilegeCategory] = set()

        for cat_def in _PRIVILEGE_CATEGORIES:
            cat_name: PrivilegeCategory = cat_def["name"]
            if cat_name not in self._enabled_categories:
                continue

            keywords: list[str] = cat_def["keywords"]
            patterns: list[re.Pattern[str]] = cat_def["patterns"]

            # --- keyword matching ---
            keyword_hits: list[str] = []
            for kw in keywords:
                if kw.lower() in text_lower:
                    # Check whether this keyword match overlaps entirely
                    # with a false-positive span.
                    kw_lower = kw.lower()
                    idx = text_lower.find(kw_lower)
                    if idx != -1 and self._is_false_positive_only(
                        idx, idx + len(kw_lower), false_positive_spans
                    ):
                        continue
                    keyword_hits.append(kw)
                    violations.append(
                        {
                            "category": cat_name.value,
                            "matched_text": kw,
                            "match_type": "keyword",
                        }
                    )

            # --- pattern matching ---
            pattern_hits: list[dict[str, Any]] = []
            for pat in patterns:
                for m in pat.finditer(text):
                    if self._is_false_positive_only(m.start(), m.end(), false_positive_spans):
                        continue
                    hit: dict[str, Any] = {
                        "category": cat_name.value,
                        "matched_text": m.group(),
                        "match_type": "pattern",
                        "position": {"start": m.start(), "end": m.end()},
                    }
                    pattern_hits.append(hit)
                    violations.append(hit)

            if pattern_hits:
                categories_with_patterns.add(cat_name)

            # --- per-category confidence ---
            score = self._compute_category_score(
                keyword_count=len(keyword_hits),
                pattern_count=len(pattern_hits),
            )
            if score > 0.0:
                category_scores[cat_name] = score

        # --- overall confidence ---
        confidence = self._compute_overall_confidence(category_scores, categories_with_patterns)

        if confidence >= self.confidence_threshold and violations:
            passed = False
            modified_text: str | None = None
            if self.on_violation == GuardAction.REDACT:
                modified_text = self._redact_text(text, violations)
        else:
            passed = True
            violations = []
            modified_text = None

        return self._make_result(
            text=text,
            passed=passed,
            violations=violations,
            confidence=confidence,
            start_time=start_time,
            modified_text=modified_text,
        )

    # ------------------------------------------------------------------
    # Confidence scoring helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_category_score(
        keyword_count: int,
        pattern_count: int,
    ) -> float:
        """Return a confidence score for a single category.

        Scoring rules:
            - 1 keyword, 0 patterns  -> 0.25
            - 2+ keywords, 0 patterns -> 0.45
            - keyword(s) + pattern(s) -> 0.65
            - 0 keywords, pattern(s)  -> 0.45

        Args:
            keyword_count: Number of keyword matches in the category.
            pattern_count: Number of pattern matches in the category.

        Returns:
            A float in ``[0.0, 1.0]``.
        """
        if keyword_count == 0 and pattern_count == 0:
            return 0.0
        if keyword_count > 0 and pattern_count > 0:
            return 0.65
        if keyword_count >= 2:
            return 0.45
        if keyword_count == 1:
            return 0.25
        # pattern_count > 0, no keywords
        return 0.45

    @staticmethod
    def _compute_overall_confidence(
        category_scores: dict[PrivilegeCategory, float],
        categories_with_patterns: set[PrivilegeCategory],
    ) -> float:
        """Compute the aggregate confidence across all categories.

        Multi-category boosts:
            - 2+ categories triggered          -> at least 0.80
            - 2+ categories with patterns      -> 0.95

        Args:
            category_scores: Per-category confidence values.
            categories_with_patterns: Categories that had regex hits.

        Returns:
            A float in ``[0.0, 1.0]``.
        """
        if not category_scores:
            return 0.0

        active_categories = len(category_scores)
        base = max(category_scores.values())

        if active_categories >= 2:
            base = max(base, 0.80)
            if len(categories_with_patterns) >= 2:
                base = max(base, 0.95)

        return base

    # ------------------------------------------------------------------
    # False-positive helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_false_positive_only(
        start: int,
        end: int,
        fp_spans: list[tuple[int, int]],
    ) -> bool:
        """Return ``True`` if the span is fully covered by false-positive spans.

        Args:
            start: Start offset of the candidate match.
            end: End offset of the candidate match.
            fp_spans: List of (start, end) false-positive spans.

        Returns:
            ``True`` when the candidate is entirely within a
            false-positive span.
        """
        return any(fp_start <= start and end <= fp_end for fp_start, fp_end in fp_spans)

    # ------------------------------------------------------------------
    # Redaction
    # ------------------------------------------------------------------

    def _redact_text(
        self,
        text: str,
        violations: list[dict[str, Any]],
    ) -> str:
        """Produce a redacted copy of *text*.

        Pattern-match violations (which carry position information) are
        replaced by their category redaction label at the matched span.
        Keyword-only violations (no position) trigger replacement of the
        sentence that contains the keyword.

        Replacements are applied from the end of the string toward the
        beginning so that earlier offsets remain valid.

        Args:
            text: Original text.
            violations: List of violation dicts from ``check()``.

        Returns:
            The redacted text.
        """
        result = text

        # Separate violations into positioned (pattern) and un-positioned
        # (keyword-only).
        positioned: list[dict[str, Any]] = []
        keyword_only: list[dict[str, Any]] = []

        for v in violations:
            if "position" in v and v["position"] is not None:
                positioned.append(v)
            elif v.get("match_type") == "keyword":
                keyword_only.append(v)

        # --- Handle positioned violations (descending order) ---
        positioned.sort(key=lambda v: v["position"]["start"], reverse=True)
        replaced_spans: list[tuple[int, int]] = []

        for v in positioned:
            cat = PrivilegeCategory(v["category"])
            label = _REDACTION_LABELS[cat]
            start: int = v["position"]["start"]
            end: int = v["position"]["end"]

            # Skip if this span overlaps with one already replaced.
            if any(s <= start < e or s < end <= e for s, e in replaced_spans):
                continue

            result = result[:start] + label + result[end:]
            replaced_spans.append((start, end))

        # --- Handle keyword-only violations ---
        for v in keyword_only:
            cat = PrivilegeCategory(v["category"])
            label = _REDACTION_LABELS[cat]
            keyword: str = v["matched_text"]

            sentence = self._find_sentence(result, keyword)
            if sentence is not None:
                result = result.replace(sentence, label, 1)

        return result

    @staticmethod
    def _find_sentence(text: str, keyword: str) -> str | None:
        """Locate the sentence in *text* that contains *keyword*.

        A sentence is delimited by ``[.!?]`` followed by whitespace, or
        by the start/end of the string.

        Args:
            text: The full text to search.
            keyword: Keyword to locate (case-insensitive).

        Returns:
            The matched sentence string, or ``None`` if the keyword is
            not found.
        """
        idx = text.lower().find(keyword.lower())
        if idx == -1:
            return None

        # Walk backward to find sentence start.
        start = 0
        for i in range(idx - 1, -1, -1):
            if text[i] in ".!?" and i + 1 < len(text) and text[i + 1] in " \n\r\t":
                start = i + 1
                break

        # Walk forward to find sentence end.
        end = len(text)
        for i in range(idx + len(keyword), len(text)):
            if text[i] in ".!?":
                end = i + 1
                break

        sentence = text[start:end].strip()
        return sentence if sentence else None
