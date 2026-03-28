"""Custom exception hierarchy for aigov-shield."""


class AIGovShieldError(Exception):
    """Base exception for all aigov-shield errors."""


class ConfigurationError(AIGovShieldError):
    """Raised when configuration is invalid or missing."""


class GuardError(AIGovShieldError):
    """Raised when a governance guard encounters an error."""


class GuardChainError(GuardError):
    """Raised when an error occurs within a guard chain."""


class AccountabilityError(AIGovShieldError):
    """Raised when an accountability operation fails."""


class ChainIntegrityError(AccountabilityError):
    """Raised when the integrity of an audit chain is compromised."""


class MeasurementError(AIGovShieldError):
    """Raised when a measurement or evaluation operation fails."""


class ExportError(AIGovShieldError):
    """Raised when exporting data or reports fails."""


class IntegrationError(AIGovShieldError):
    """Raised when a framework integration encounters an error."""


class RegistryError(AIGovShieldError):
    """Raised when a component registry lookup or registration fails."""
