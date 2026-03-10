"""
Custom exception hierarchy for pgsi_analyzer.
"""


class PGSIAnalyzerError(Exception):
    """Base exception for all pgsi_analyzer errors."""


class MeasurementError(PGSIAnalyzerError):
    """Raised for measurement-related failures (energy/time)."""


class AnalysisError(PGSIAnalyzerError):
    """Raised for analysis/data processing failures."""


class PlatformError(PGSIAnalyzerError):
    """Raised when the current platform is unsupported or misconfigured."""


class ConfigurationError(PGSIAnalyzerError):
    """Raised for configuration or missing resource issues."""


class AuditError(PGSIAnalyzerError):
    """Raised when audit validation fails (e.g. data in unregistered directory/method)."""

