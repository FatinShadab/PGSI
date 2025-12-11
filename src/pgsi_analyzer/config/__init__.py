"""
Configuration module for pgsi_analyzer.

Provides access to default benchmark parameters and config path helpers.
"""
from pathlib import Path
from typing import Dict, Any

from .defaults import DEFAULT_PARAMS, get_default_params
from ..platform.paths import resolve_data_path


def resolve_config_path(*parts: str) -> Path:
    """
    Resolve a configuration-related path under the pgsi_analyzer data directory.
    This is a thin wrapper around platform.paths.resolve_data_path.
    """
    base = resolve_data_path()
    return base.joinpath(*parts)


__all__ = [
    "DEFAULT_PARAMS",
    "get_default_params",
    "resolve_config_path",
]

# Backwards-compatibility alias for legacy callers that referenced __default__
__default__: Dict[str, Any] = DEFAULT_PARAMS

