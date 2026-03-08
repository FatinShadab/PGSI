"""
Utilities module for shared helper functions.

This module provides validation, error handling, and other utility functions
used throughout the package.
"""

from .validation import (
    validate_file_path,
    validate_dataframe,
    validate_weights,
    validate_platform,
    require_columns,
)
from .errors import (
    PGSIAnalyzerError,
    MeasurementError,
    AnalysisError,
    PlatformError,
    ConfigurationError,
    AuditError,
)

__all__ = [
    "validate_file_path",
    "validate_dataframe",
    "validate_weights",
    "validate_platform",
    "require_columns",
    "PGSIAnalyzerError",
    "MeasurementError",
    "AnalysisError",
    "PlatformError",
    "ConfigurationError",
    "AuditError",
]

