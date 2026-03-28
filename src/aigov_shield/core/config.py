"""Global configuration management for aigov-shield."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class GovernanceConfig:
    """Central configuration for the aigov-shield governance framework.

    Attributes:
        default_action: Default action when a guard triggers (e.g., "block").
        confidence_threshold: Minimum confidence score to act on a detection.
        enable_logging: Whether governance event logging is enabled.
        log_level: Logging verbosity level.
        storage_backend: Backend used for persisting governance data.
        storage_path: Filesystem path for file-based storage backends.
        metadata: Arbitrary additional configuration metadata.
    """

    default_action: str = "block"
    confidence_threshold: float = 0.5
    enable_logging: bool = True
    log_level: str = "INFO"
    storage_backend: str = "memory"
    storage_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GovernanceConfig:
        """Create a GovernanceConfig from a dictionary.

        Args:
            data: Dictionary containing configuration key-value pairs.
                  Unknown keys are silently ignored.

        Returns:
            A new GovernanceConfig instance.
        """
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)

    @classmethod
    def from_env(cls) -> GovernanceConfig:
        """Create a GovernanceConfig from environment variables.

        Reads environment variables prefixed with ``AIGOV_SHIELD_`` and maps
        them to configuration fields. For example,
        ``AIGOV_SHIELD_CONFIDENCE_THRESHOLD`` maps to ``confidence_threshold``.

        Returns:
            A new GovernanceConfig populated from the environment.
        """
        prefix = "AIGOV_SHIELD_"
        data: dict[str, Any] = {}

        env_mapping: dict[str, type] = {
            "DEFAULT_ACTION": str,
            "CONFIDENCE_THRESHOLD": float,
            "ENABLE_LOGGING": bool,
            "LOG_LEVEL": str,
            "STORAGE_BACKEND": str,
            "STORAGE_PATH": str,
        }

        for env_suffix, cast_type in env_mapping.items():
            env_var = f"{prefix}{env_suffix}"
            value = os.environ.get(env_var)
            if value is not None:
                field_name = env_suffix.lower()
                if cast_type is bool:
                    data[field_name] = value.lower() in ("true", "1", "yes")
                elif cast_type is float:
                    data[field_name] = float(value)
                else:
                    data[field_name] = value

        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        """Serialize this configuration to a plain dictionary.

        Returns:
            Dictionary representation of all configuration fields.
        """
        return asdict(self)
