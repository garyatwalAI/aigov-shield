"""Evidence logger for litigation-ready audit trails."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from aigov_shield.accountability.chain_of_custody import ChainOfCustody


class EvidenceLogger:
    """Logger that produces litigation-ready evidence records.

    Each logged event is backed by a tamper-evident chain of custody so that
    the integrity of the audit trail can be independently verified.

    Args:
        case_id: Identifier for the case or session.
        storage: Storage backend identifier. Currently only ``"memory"``
            is supported.
    """

    def __init__(self, case_id: str, storage: str = "memory") -> None:
        self.case_id = case_id
        self.records: List[Dict[str, Any]] = []
        self._chain = ChainOfCustody(storage_backend=storage)

    def log_retrieval(
        self,
        query: str,
        documents_retrieved: List[str],
        retrieval_method: str = "unknown",
        relevance_scores: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Log a document retrieval event.

        Args:
            query: The query that triggered the retrieval.
            documents_retrieved: List of retrieved document identifiers.
            retrieval_method: Method used for retrieval.
            relevance_scores: Optional relevance scores for each document.
            metadata: Additional metadata.

        Returns:
            The record ID of the newly created record.
        """
        record_id = str(uuid4())
        data: Dict[str, Any] = {
            "query": query,
            "documents_retrieved": documents_retrieved,
            "retrieval_method": retrieval_method,
            "relevance_scores": relevance_scores,
        }
        record: Dict[str, Any] = {
            "record_id": record_id,
            "case_id": self.case_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "retrieval",
            "data": data,
        }
        if metadata:
            record["data"]["metadata"] = metadata

        self.records.append(record)
        self._chain.add_record(
            interaction_type="document_retrieval",
            content=json.dumps(data, sort_keys=True),
            actor=self.case_id,
            documents_referenced=documents_retrieved,
            metadata=metadata or {},
        )
        return record_id

    def log_generation(
        self,
        prompt: str,
        response: str,
        model: str = "unknown",
        documents_used: Optional[List[str]] = None,
        guard_results: Optional[List[Dict[str, Any]]] = None,
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Log a generation event.

        Args:
            prompt: The prompt submitted.
            response: The generated response.
            model: Model identifier.
            documents_used: Document identifiers used in generation.
            guard_results: Results from guard checks.
            confidence: Optional confidence score.
            metadata: Additional metadata.

        Returns:
            The record ID of the newly created record.
        """
        record_id = str(uuid4())
        data: Dict[str, Any] = {
            "prompt": prompt,
            "response": response,
            "model": model,
            "documents_used": documents_used or [],
            "guard_results": guard_results or [],
            "confidence": confidence,
        }
        record: Dict[str, Any] = {
            "record_id": record_id,
            "case_id": self.case_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "generation",
            "data": data,
        }
        if metadata:
            record["data"]["metadata"] = metadata

        self.records.append(record)
        self._chain.add_record(
            interaction_type="response",
            content=json.dumps(data, sort_keys=True),
            actor=self.case_id,
            model_id=model,
            documents_referenced=documents_used or [],
            guard_results=guard_results or [],
            metadata=metadata or {},
        )
        return record_id

    def log_event(
        self,
        event_type: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Log a generic event.

        Args:
            event_type: Type of event.
            description: Human-readable description.
            metadata: Additional metadata.

        Returns:
            The record ID of the newly created record.
        """
        record_id = str(uuid4())
        data: Dict[str, Any] = {
            "description": description,
        }
        record: Dict[str, Any] = {
            "record_id": record_id,
            "case_id": self.case_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "data": data,
        }
        if metadata:
            record["data"]["metadata"] = metadata

        self.records.append(record)
        self._chain.add_record(
            interaction_type=event_type,
            content=json.dumps(data, sort_keys=True),
            actor=self.case_id,
            metadata=metadata or {},
        )
        return record_id

    def get_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a record by its ID.

        Args:
            record_id: The UUID of the record.

        Returns:
            The matching record dictionary, or ``None`` if not found.
        """
        for record in self.records:
            if record["record_id"] == record_id:
                return record
        return None

    def get_records(
        self, event_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve records, optionally filtered by event type.

        Args:
            event_type: If provided, only records of this type are returned.

        Returns:
            List of matching record dictionaries.
        """
        if event_type is None:
            return list(self.records)
        return [r for r in self.records if r["event_type"] == event_type]

    def get_chain(self) -> ChainOfCustody:
        """Return the underlying chain of custody.

        Returns:
            The internal ``ChainOfCustody`` instance.
        """
        return self._chain

    def verify_integrity(self) -> Tuple[bool, List[str]]:
        """Verify the integrity of the evidence chain.

        Returns:
            A tuple of ``(valid, errors)``.
        """
        return self._chain.verify_chain()

    def export(self, format: str = "json") -> str:
        """Export all records in the specified format.

        Args:
            format: One of ``"json"``, ``"jsonl"``, or ``"csv"``.

        Returns:
            Serialized string of all records.

        Raises:
            ValueError: If the format is not supported.
        """
        from aigov_shield.accountability.export import (
            export_to_csv,
            export_to_json,
            export_to_jsonl,
        )

        if format == "json":
            return export_to_json(self.records)
        elif format == "jsonl":
            return export_to_jsonl(self.records)
        elif format == "csv":
            return export_to_csv(self.records)
        else:
            raise ValueError(f"Unsupported export format: {format!r}")
