"""Chain of custody implementation for tamper-evident audit trails."""

from __future__ import annotations

import csv
import dataclasses
import hashlib
import io
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from aigov_shield.core.exceptions import ChainIntegrityError


@dataclass
class CustodyRecord:
    """A single record in the chain of custody.

    Attributes:
        record_id: Unique identifier for this record (UUID v4).
        timestamp: ISO 8601 timestamp with timezone.
        interaction_type: Type of interaction recorded.
        content_hash: SHA-256 hash of the content.
        previous_record_hash: Hash of the previous record, or ``"GENESIS"``
            for the first record.
        actor: Identifier for the actor that produced this record.
        model_id: Optional model identifier.
        input_hash: Optional SHA-256 hash of the input.
        documents_referenced: List of document identifiers referenced.
        guard_results: List of guard check results.
        metadata: Additional metadata.
        record_hash: Computed hash of all other fields.
    """

    record_id: str
    timestamp: str
    interaction_type: str
    content_hash: str
    previous_record_hash: str
    actor: str
    model_id: Optional[str] = None
    input_hash: Optional[str] = None
    documents_referenced: List[str] = field(default_factory=list)
    guard_results: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    record_hash: str = ""

    def compute_hash(self) -> str:
        """Compute a SHA-256 hash of all fields except ``record_hash``.

        Returns:
            Hex digest of the computed hash.
        """
        hash_data: Dict[str, Any] = {
            "record_id": self.record_id,
            "timestamp": self.timestamp,
            "interaction_type": self.interaction_type,
            "content_hash": self.content_hash,
            "previous_record_hash": self.previous_record_hash,
            "actor": self.actor,
            "model_id": self.model_id,
            "input_hash": self.input_hash,
            "documents_referenced": self.documents_referenced,
            "guard_results": self.guard_results,
            "metadata": self.metadata,
        }
        serialized = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the record to a plain dictionary.

        Returns:
            Dictionary representation of the record.
        """
        return dataclasses.asdict(self)


class ChainOfCustody:
    """Tamper-evident chain of custody for audit records.

    Args:
        storage_backend: Storage backend identifier. Currently only
            ``"memory"`` is supported.
    """

    def __init__(self, storage_backend: str = "memory") -> None:
        self._chain: List[CustodyRecord] = []
        self.storage_backend = storage_backend

    def add_record(
        self,
        interaction_type: str,
        content: str,
        actor: str,
        model_id: Optional[str] = None,
        input_hash: Optional[str] = None,
        documents_referenced: Optional[List[str]] = None,
        guard_results: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CustodyRecord:
        """Add a new record to the chain.

        Args:
            interaction_type: Type of interaction (e.g. ``"query"``,
                ``"response"``, ``"document_retrieval"``, ``"guard_check"``).
            content: Raw content to hash.
            actor: Identifier of the actor.
            model_id: Optional model identifier.
            input_hash: Optional hash of the input.
            documents_referenced: Document identifiers referenced.
            guard_results: Guard check results.
            metadata: Additional metadata.

        Returns:
            The newly created custody record.
        """
        previous_record_hash = (
            self._chain[-1].record_hash if self._chain else "GENESIS"
        )
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        record = CustodyRecord(
            record_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            interaction_type=interaction_type,
            content_hash=content_hash,
            previous_record_hash=previous_record_hash,
            actor=actor,
            model_id=model_id,
            input_hash=input_hash,
            documents_referenced=documents_referenced or [],
            guard_results=guard_results or [],
            metadata=metadata or {},
        )
        record.record_hash = record.compute_hash()
        self._chain.append(record)
        return record

    def verify_chain(self) -> Tuple[bool, List[str]]:
        """Verify the integrity of the entire chain.

        Returns:
            A tuple of ``(valid, errors)`` where *valid* is ``True`` when the
            chain is intact and *errors* is a list of human-readable error
            descriptions.
        """
        errors: List[str] = []

        for idx, record in enumerate(self._chain):
            # Verify record hash matches recomputed hash.
            expected_hash = record.compute_hash()
            if record.record_hash != expected_hash:
                errors.append(
                    f"Record {idx} ({record.record_id}): record_hash mismatch. "
                    f"Expected {expected_hash}, got {record.record_hash}."
                )

            # Verify previous_record_hash linkage.
            if idx == 0:
                if record.previous_record_hash != "GENESIS":
                    errors.append(
                        f"Record 0 ({record.record_id}): "
                        f"previous_record_hash should be 'GENESIS', "
                        f"got '{record.previous_record_hash}'."
                    )
            else:
                expected_previous = self._chain[idx - 1].record_hash
                if record.previous_record_hash != expected_previous:
                    errors.append(
                        f"Record {idx} ({record.record_id}): "
                        f"previous_record_hash mismatch. Expected "
                        f"{expected_previous}, got "
                        f"{record.previous_record_hash}."
                    )

        return (len(errors) == 0, errors)

    def get_record(self, record_id: str) -> Optional[CustodyRecord]:
        """Retrieve a record by its ID.

        Args:
            record_id: The UUID of the record.

        Returns:
            The matching record, or ``None`` if not found.
        """
        for record in self._chain:
            if record.record_id == record_id:
                return record
        return None

    def get_chain(self) -> List[CustodyRecord]:
        """Return a copy of the full chain.

        Returns:
            List of all custody records.
        """
        return list(self._chain)

    def __len__(self) -> int:
        return len(self._chain)

    def export_json(self) -> str:
        """Export all records as a pretty-printed JSON array.

        Returns:
            JSON string.
        """
        return json.dumps(
            [record.to_dict() for record in self._chain], indent=2
        )

    def export_jsonl(self) -> str:
        """Export all records as JSON Lines (one JSON object per line).

        Returns:
            JSONL string.
        """
        lines = [json.dumps(record.to_dict()) for record in self._chain]
        return "\n".join(lines)

    def export_csv(self) -> str:
        """Export all records as CSV.

        Returns:
            CSV string with headers.
        """
        if not self._chain:
            return ""

        records = [record.to_dict() for record in self._chain]
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(records[0].keys()))
        writer.writeheader()
        for record in records:
            # Serialize complex values to JSON strings for CSV.
            row: Dict[str, Any] = {}
            for key, value in record.items():
                if isinstance(value, (list, dict)):
                    row[key] = json.dumps(value)
                else:
                    row[key] = value
            writer.writerow(row)
        return output.getvalue()
