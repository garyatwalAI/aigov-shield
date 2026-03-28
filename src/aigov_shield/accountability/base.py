"""Base classes for the accountability layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseAuditLogger(ABC):
    """Base class for all audit loggers.

    Args:
        logger_name: Human-readable name for this logger.
        case_id: Optional case or session identifier.
    """

    def __init__(self, logger_name: str, case_id: str | None = None) -> None:
        self.logger_name = logger_name
        self.case_id = case_id

    @abstractmethod
    def log(self, event_type: str, data: dict[str, Any]) -> str:
        """Log an event and return its record ID."""
        ...

    @abstractmethod
    def get_record(self, record_id: str) -> dict[str, Any] | None:
        """Retrieve a record by its ID."""
        ...

    @abstractmethod
    def export(self, format: str = "json") -> str:
        """Export all records in the specified format."""
        ...
