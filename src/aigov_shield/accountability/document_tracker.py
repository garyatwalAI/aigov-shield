"""Document tracking and provenance for accountability."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from aigov_shield.accountability.export import (
    export_to_csv,
    export_to_json,
    export_to_jsonl,
)


@dataclass
class TrackedDocument:
    """A document registered for tracking.

    Attributes:
        doc_id: Unique document identifier.
        path: File path or URI of the document.
        content_hash: SHA-256 hash of the document content.
        registered_at: ISO 8601 timestamp of registration.
        metadata: Additional metadata.
    """

    doc_id: str
    path: str
    content_hash: str
    registered_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChunkReference:
    """A reference to a specific chunk within a document.

    Attributes:
        doc_id: Identifier of the parent document.
        page: Optional page number.
        start_char: Optional starting character offset.
        end_char: Optional ending character offset.
        chunk_text: Optional text of the chunk.
    """

    doc_id: str
    page: Optional[int] = None
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    chunk_text: Optional[str] = None


@dataclass
class UsageRecord:
    """A record of document usage in an output.

    Attributes:
        output_id: Identifier of the output that used documents.
        timestamp: ISO 8601 timestamp of usage.
        documents_used: List of document identifiers used.
        chunks_used: List of chunk references used.
        metadata: Additional metadata.
    """

    output_id: str
    timestamp: str
    documents_used: List[str]
    chunks_used: List[ChunkReference]
    metadata: Dict[str, Any] = field(default_factory=dict)


class DocumentTracker:
    """Tracks document registration and usage for provenance auditing."""

    def __init__(self) -> None:
        self._documents: Dict[str, TrackedDocument] = {}
        self._usage_records: Dict[str, UsageRecord] = {}

    def register_document(
        self,
        doc_id: str,
        path: str,
        content_hash: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TrackedDocument:
        """Register a document for tracking.

        Args:
            doc_id: Unique document identifier.
            path: File path or URI of the document.
            content_hash: SHA-256 hash of the document content.
            metadata: Additional metadata.

        Returns:
            The newly registered tracked document.
        """
        doc = TrackedDocument(
            doc_id=doc_id,
            path=path,
            content_hash=content_hash,
            registered_at=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        )
        self._documents[doc_id] = doc
        return doc

    def get_document(self, doc_id: str) -> Optional[TrackedDocument]:
        """Retrieve a tracked document by its ID.

        Args:
            doc_id: The document identifier.

        Returns:
            The tracked document, or ``None`` if not found.
        """
        return self._documents.get(doc_id)

    def record_usage(
        self,
        output_id: str,
        documents_used: List[str],
        chunks_used: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UsageRecord:
        """Record that an output used specific documents and chunks.

        Args:
            output_id: Identifier for the output.
            documents_used: List of document identifiers used.
            chunks_used: Optional list of chunk reference dictionaries. Each
                dictionary should contain at minimum a ``"doc_id"`` key.
            metadata: Additional metadata.

        Returns:
            The newly created usage record.
        """
        chunk_refs: List[ChunkReference] = []
        if chunks_used:
            for chunk in chunks_used:
                chunk_refs.append(
                    ChunkReference(
                        doc_id=chunk.get("doc_id", ""),
                        page=chunk.get("page"),
                        start_char=chunk.get("start_char"),
                        end_char=chunk.get("end_char"),
                        chunk_text=chunk.get("chunk_text"),
                    )
                )

        usage = UsageRecord(
            output_id=output_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            documents_used=documents_used,
            chunks_used=chunk_refs,
            metadata=metadata or {},
        )
        self._usage_records[output_id] = usage
        return usage

    def get_provenance(self, output_id: str) -> Optional[Dict[str, Any]]:
        """Get the full provenance chain for an output.

        Traces from the output back through chunks to source documents and
        their content hashes.

        Args:
            output_id: Identifier of the output.

        Returns:
            A dictionary describing the provenance chain, or ``None`` if the
            output has no usage record.
        """
        usage = self._usage_records.get(output_id)
        if usage is None:
            return None

        documents: List[Dict[str, Any]] = []
        for doc_id in usage.documents_used:
            doc = self._documents.get(doc_id)
            if doc:
                documents.append({
                    "doc_id": doc.doc_id,
                    "path": doc.path,
                    "content_hash": doc.content_hash,
                    "registered_at": doc.registered_at,
                    "metadata": doc.metadata,
                })

        chunks: List[Dict[str, Any]] = []
        for chunk in usage.chunks_used:
            chunk_info: Dict[str, Any] = {"doc_id": chunk.doc_id}
            if chunk.page is not None:
                chunk_info["page"] = chunk.page
            if chunk.start_char is not None:
                chunk_info["start_char"] = chunk.start_char
            if chunk.end_char is not None:
                chunk_info["end_char"] = chunk.end_char
            if chunk.chunk_text is not None:
                chunk_info["chunk_text"] = chunk.chunk_text
            chunks.append(chunk_info)

        return {
            "output_id": output_id,
            "timestamp": usage.timestamp,
            "documents": documents,
            "chunks": chunks,
            "metadata": usage.metadata,
        }

    def get_document_usage(self, doc_id: str) -> List[str]:
        """Get all output IDs that used a specific document.

        Args:
            doc_id: The document identifier.

        Returns:
            List of output identifiers that referenced this document.
        """
        output_ids: List[str] = []
        for output_id, usage in self._usage_records.items():
            if doc_id in usage.documents_used:
                output_ids.append(output_id)
        return output_ids

    def export(self, format: str = "json") -> str:
        """Export all tracked documents and usage records.

        Args:
            format: One of ``"json"``, ``"jsonl"``, or ``"csv"``.

        Returns:
            Serialized string of all tracking data.

        Raises:
            ValueError: If the format is not supported.
        """
        records: List[Dict[str, Any]] = []

        for doc in self._documents.values():
            records.append({
                "type": "document",
                "doc_id": doc.doc_id,
                "path": doc.path,
                "content_hash": doc.content_hash,
                "registered_at": doc.registered_at,
                "metadata": doc.metadata,
            })

        for usage in self._usage_records.values():
            chunks_serialized: List[Dict[str, Any]] = []
            for chunk in usage.chunks_used:
                chunk_dict: Dict[str, Any] = {"doc_id": chunk.doc_id}
                if chunk.page is not None:
                    chunk_dict["page"] = chunk.page
                if chunk.start_char is not None:
                    chunk_dict["start_char"] = chunk.start_char
                if chunk.end_char is not None:
                    chunk_dict["end_char"] = chunk.end_char
                if chunk.chunk_text is not None:
                    chunk_dict["chunk_text"] = chunk.chunk_text
                chunks_serialized.append(chunk_dict)

            records.append({
                "type": "usage",
                "output_id": usage.output_id,
                "timestamp": usage.timestamp,
                "documents_used": usage.documents_used,
                "chunks_used": chunks_serialized,
                "metadata": usage.metadata,
            })

        if format == "json":
            return export_to_json(records)
        elif format == "jsonl":
            return export_to_jsonl(records)
        elif format == "csv":
            return export_to_csv(records)
        else:
            raise ValueError(f"Unsupported export format: {format!r}")
