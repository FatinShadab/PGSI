"""
Validation helpers for pgsi_analyzer.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd

from ..platform.detection import detect_platform, is_linux_intel
from .errors import PlatformError, AnalysisError, ConfigurationError


def validate_file_path(path: Path | str, must_exist: bool = True) -> Path:
    """Ensure a path is a Path and (optionally) exists."""
    p = Path(path)
    if must_exist and not p.exists():
        raise ConfigurationError(f"File not found: {p}")
    return p


def validate_dataframe(df: pd.DataFrame, required_columns: Sequence[str]) -> None:
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        raise AnalysisError(f"Missing required columns: {missing}")


def validate_weights(alpha: float, beta: float, gamma: float) -> None:
    total = alpha + beta + gamma
    if abs(total - 1.0) > 1e-6:
        raise AnalysisError(f"Weights must sum to 1.0; got {total:.6f}")


def validate_platform(require_linux_intel: bool = False) -> None:
    platform = detect_platform()
    if require_linux_intel and not is_linux_intel():
        raise PlatformError(
            f"Linux x86_64 required for hardware measurement. Current platform: {platform}"
        )


def require_columns(df: pd.DataFrame, columns: Iterable[str]) -> None:
    """Alias for validate_dataframe for convenience."""
    validate_dataframe(df, list(columns))

