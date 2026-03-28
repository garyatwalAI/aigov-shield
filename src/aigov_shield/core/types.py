"""Shared type definitions and enums for aigov-shield."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Dict


class GovernanceLayer(str, enum.Enum):
    """Governance layer classification.

    Defines the three primary layers of the governance framework.
    """

    PREVENTION = "prevention"
    ACCOUNTABILITY = "accountability"
    MEASUREMENT = "measurement"


class NISTFunction(str, enum.Enum):
    """NIST AI Risk Management Framework functions.

    Maps to the four core functions defined in NIST AI RMF 1.0.
    """

    GOVERN = "govern"
    MAP = "map"
    MEASURE = "measure"
    MANAGE = "manage"


class SensitivityLevel(str, enum.Enum):
    """Data sensitivity classification level."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ContentType(str, enum.Enum):
    """Supported content types for governance processing."""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"


class RedactionMode(str, enum.Enum):
    """Strategy used when redacting sensitive content."""

    MASK = "mask"
    HASH = "hash"
    PARTIAL = "partial"
    REMOVE = "remove"


class PIICategory(str, enum.Enum):
    """Categories of personally identifiable information (PII)."""

    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    NATIONAL_ID = "national_id"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    DATE_OF_BIRTH = "date_of_birth"
    ADDRESS = "address"
    PASSPORT = "passport"
    IBAN = "iban"


class PrivilegeCategory(str, enum.Enum):
    """Categories of legal privilege applicable to content."""

    ATTORNEY_CLIENT = "attorney_client"
    WORK_PRODUCT = "work_product"
    SETTLEMENT = "settlement"


class BiasCategory(str, enum.Enum):
    """Categories of bias evaluated during fairness assessments."""

    GENDER = "gender"
    RACIAL_ETHNIC = "racial_ethnic"
    AGE = "age"
    DISABILITY = "disability"
    SOCIOECONOMIC = "socioeconomic"


@dataclass
class InteractionRecord:
    """A single recorded interaction within the governance system.

    Attributes:
        record_id: Unique identifier for this interaction record.
        timestamp: ISO-8601 timestamp of when the interaction occurred.
        interaction_type: Category of the interaction (e.g., "query", "response").
        actor: Identifier for the entity that initiated the interaction.
        content: The textual content of the interaction.
        metadata: Additional key-value metadata associated with the record.
    """

    record_id: str
    timestamp: str
    interaction_type: str
    actor: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
