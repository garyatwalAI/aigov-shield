"""PII detection and redaction guard.

Detects and optionally redacts ten categories of personally identifiable
information (PII) using compiled regular-expression patterns and validation
heuristics such as the Luhn algorithm for credit-card numbers.
"""

from __future__ import annotations

import hashlib
import re
import time
from typing import Any, Dict, List, Optional

from aigov_shield.core.types import PIICategory, RedactionMode
from aigov_shield.prevention.base import BaseGuard, GuardAction, GuardResult

# ---------------------------------------------------------------------------
# Module-level compiled regex patterns
# ---------------------------------------------------------------------------

_EMAIL_PATTERN: re.Pattern[str] = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
)

_PHONE_PATTERN: re.Pattern[str] = re.compile(
    r"(?:"
    r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"  # US
    r"|\+44\s?\d{4}\s?\d{6}"  # UK international
    r"|07\d{3}\s?\d{6}"  # UK local
    r"|\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}"  # International
    r")"
)

_SSN_PATTERN: re.Pattern[str] = re.compile(
    r"\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b"
)

_NATIONAL_ID_PATTERN: re.Pattern[str] = re.compile(
    r"\b[A-CEGHJ-PR-TW-Z]{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-D]\b"
)

_CREDIT_CARD_PATTERN: re.Pattern[str] = re.compile(
    r"\b(?:4\d{3}|5[1-5]\d{2}|3[47]\d{2}|6(?:011|5\d{2}))"
    r"\d?\s?[-\s]?\d{4}\s?[-\s]?\d{4}\s?[-\s]?\d{1,4}\b"
)

_IPV4_PATTERN: re.Pattern[str] = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)

_IPV6_PATTERN: re.Pattern[str] = re.compile(
    r"\b(?:"
    r"(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}"
    r"|(?:[0-9a-fA-F]{1,4}:){1,7}:"
    r"|::(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}"
    r"|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}"
    r")\b",
    re.IGNORECASE,
)

_DOB_PATTERN: re.Pattern[str] = re.compile(
    r"(?:DOB|date\s+of\s+birth|born\s+on|birthday)"
    r"\s*:?\s*"
    r"(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
    re.IGNORECASE,
)

_ADDRESS_PATTERN: re.Pattern[str] = re.compile(
    r"\b\d{1,6}\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s+"
    r"(?:Avenue|Ave|Street|St|Road|Rd|Boulevard|Blvd|Drive|Dr|"
    r"Lane|Ln|Court|Ct|Way|Circle|Cir|Terrace|Ter|Place|Pl)\b"
)

_PASSPORT_PATTERN: re.Pattern[str] = re.compile(
    r"(?:passport\s*(?:no|number|#|num)?\.?\s*:?\s*)(\d{9})\b",
    re.IGNORECASE,
)

_IBAN_PATTERN: re.Pattern[str] = re.compile(
    r"\b[A-Z]{2}\d{2}\s?[A-Z0-9]{4}\s?(?:[A-Z0-9]{4}\s?){1,7}[A-Z0-9]{1,4}\b"
)

_PII_PATTERNS: Dict[PIICategory, List[re.Pattern[str]]] = {
    PIICategory.EMAIL: [_EMAIL_PATTERN],
    PIICategory.PHONE: [_PHONE_PATTERN],
    PIICategory.SSN: [_SSN_PATTERN],
    PIICategory.NATIONAL_ID: [_NATIONAL_ID_PATTERN],
    PIICategory.CREDIT_CARD: [_CREDIT_CARD_PATTERN],
    PIICategory.IP_ADDRESS: [_IPV4_PATTERN, _IPV6_PATTERN],
    PIICategory.DATE_OF_BIRTH: [_DOB_PATTERN],
    PIICategory.ADDRESS: [_ADDRESS_PATTERN],
    PIICategory.PASSPORT: [_PASSPORT_PATTERN],
    PIICategory.IBAN: [_IBAN_PATTERN],
}

# Map each category to the placeholder tag used during MASK redaction.
_CATEGORY_TAGS: Dict[PIICategory, str] = {
    PIICategory.EMAIL: "[EMAIL]",
    PIICategory.PHONE: "[PHONE]",
    PIICategory.SSN: "[SSN]",
    PIICategory.NATIONAL_ID: "[NATIONAL_ID]",
    PIICategory.CREDIT_CARD: "[CREDIT_CARD]",
    PIICategory.IP_ADDRESS: "[IP_ADDRESS]",
    PIICategory.DATE_OF_BIRTH: "[DATE_OF_BIRTH]",
    PIICategory.ADDRESS: "[ADDRESS]",
    PIICategory.PASSPORT: "[PASSPORT]",
    PIICategory.IBAN: "[IBAN]",
}


class PIIGuard(BaseGuard):
    """Guard that detects and redacts personally identifiable information.

    Scans text for ten categories of PII using compiled regular-expression
    patterns.  When a violation is found the guard can block, flag, redact,
    or pass through the content depending on the configured action.

    Args:
        on_violation: Action to take when PII is detected.
        confidence_threshold: Minimum confidence to treat a detection as a
            real violation.
        categories: Subset of ``PIICategory`` values to scan for.  Defaults
            to all categories when ``None``.
        redaction_mode: Strategy used when ``on_violation`` is
            ``GuardAction.REDACT``.
    """

    def __init__(
        self,
        on_violation: GuardAction = GuardAction.REDACT,
        confidence_threshold: float = 0.5,
        categories: Optional[List[PIICategory]] = None,
        redaction_mode: RedactionMode = RedactionMode.MASK,
    ) -> None:
        super().__init__(
            name="pii_guard",
            on_violation=on_violation,
            confidence_threshold=confidence_threshold,
        )
        self.redaction_mode = redaction_mode
        self.categories: List[PIICategory] = (
            categories if categories is not None else list(PIICategory)
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> GuardResult:
        """Scan *text* for PII and return a ``GuardResult``.

        Args:
            text: The input string to scan.
            context: Optional metadata (unused by this guard but accepted
                for interface compatibility).

        Returns:
            A ``GuardResult`` describing what was found and any redacted
            output.
        """
        start_time = time.perf_counter()
        violations: List[Dict[str, Any]] = []

        for category in self.categories:
            patterns = _PII_PATTERNS.get(category, [])
            for pattern in patterns:
                for match in pattern.finditer(text):
                    # Some patterns use a capturing group (e.g. DOB,
                    # PASSPORT).  Prefer the first group when present.
                    if match.lastindex:
                        matched_text = match.group(1)
                        start = match.start(1)
                        end = match.end(1)
                    else:
                        matched_text = match.group(0)
                        start = match.start(0)
                        end = match.end(0)

                    # Credit-card numbers must pass the Luhn check.
                    if category is PIICategory.CREDIT_CARD:
                        digits_only = re.sub(r"[\s\-]", "", matched_text)
                        if not PIIGuard._luhn_check(digits_only):
                            continue

                    violations.append(
                        {
                            "category": category.value,
                            "matched_text": matched_text,
                            "start": start,
                            "end": end,
                        }
                    )

        # Determine confidence based on the number of matches.
        match_count = len(violations)
        if match_count == 0:
            confidence = 0.0
        elif match_count == 1:
            confidence = 0.5
        elif match_count <= 3:
            confidence = 0.7
        else:
            confidence = 0.9

        passed = True
        modified_text: Optional[str] = None

        if violations and confidence >= self.confidence_threshold:
            passed = False
            if self.on_violation is GuardAction.REDACT:
                modified_text = self._redact_text(text, violations)

        return self._make_result(
            text=text,
            passed=passed,
            violations=violations,
            confidence=confidence,
            start_time=start_time,
            modified_text=modified_text,
        )

    # ------------------------------------------------------------------
    # Redaction helpers
    # ------------------------------------------------------------------

    def _redact_text(
        self,
        text: str,
        violations: List[Dict[str, Any]],
    ) -> str:
        """Apply redaction to *text* based on *self.redaction_mode*.

        Violations are processed from the end of the string toward the
        beginning so that earlier character offsets remain valid after each
        replacement.

        Args:
            text: The original text.
            violations: Detected PII matches with positional information.

        Returns:
            The text with PII replaced according to the active redaction
            mode.
        """
        sorted_violations = sorted(
            violations, key=lambda v: v["start"], reverse=True
        )

        for violation in sorted_violations:
            start: int = violation["start"]
            end: int = violation["end"]
            matched: str = violation["matched_text"]
            category = PIICategory(violation["category"])

            replacement = self._replacement_for(category, matched)
            text = text[:start] + replacement + text[end:]

        return text

    def _replacement_for(self, category: PIICategory, matched: str) -> str:
        """Return the replacement string for a single PII match.

        Args:
            category: The PII category that was detected.
            matched: The literal text that was matched.

        Returns:
            A replacement string determined by ``self.redaction_mode``.
        """
        if self.redaction_mode is RedactionMode.MASK:
            return _CATEGORY_TAGS.get(category, "[PII]")

        if self.redaction_mode is RedactionMode.HASH:
            digest = hashlib.sha256(matched.encode("utf-8")).hexdigest()[:16]
            return digest

        if self.redaction_mode is RedactionMode.PARTIAL:
            return self._partial_redact(category, matched)

        # RedactionMode.REMOVE
        return ""

    @staticmethod
    def _partial_redact(category: PIICategory, matched: str) -> str:
        """Produce a partially redacted version of *matched*.

        Args:
            category: The PII category.
            matched: The original matched text.

        Returns:
            A string with most characters hidden but enough visible to
            identify the record.
        """
        if category is PIICategory.EMAIL:
            parts = matched.split("@", 1)
            if len(parts) == 2:
                return parts[0][0] + "***@" + parts[1]
            return matched[0] + "***"

        if category is PIICategory.PHONE:
            digits = re.sub(r"\D", "", matched)
            last_four = digits[-4:] if len(digits) >= 4 else digits
            return "***-***-" + last_four

        if category is PIICategory.SSN:
            last_four = matched[-4:]
            return "***-**-" + last_four

        if category is PIICategory.CREDIT_CARD:
            digits = re.sub(r"\D", "", matched)
            last_four = digits[-4:] if len(digits) >= 4 else digits
            return "****-****-****-" + last_four

        # Generic partial: show first and last character only.
        if len(matched) >= 2:
            return matched[0] + "***" + matched[-1]
        return "***"

    # ------------------------------------------------------------------
    # Validation utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _luhn_check(number: str) -> bool:
        """Validate a numeric string using the Luhn algorithm.

        Args:
            number: A string of digits (spaces and hyphens should already
                be stripped).

        Returns:
            ``True`` if the number passes the Luhn check.
        """
        if not number.isdigit():
            return False

        total = 0
        reverse_digits = number[::-1]
        for idx, char in enumerate(reverse_digits):
            digit = int(char)
            if idx % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            total += digit

        return total % 10 == 0
