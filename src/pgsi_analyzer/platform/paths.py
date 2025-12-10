"""
Path resolution utilities for cross-platform compatibility.

This module provides functions to resolve paths in a platform-independent
manner using pathlib.Path, with support for environment variable overrides.
"""

import os
from pathlib import Path
from typing import Optional


def get_user_data_dir() -> Path:
    """
    Get platform-specific user data directory for pgsi_analyzer.

    Returns:
        Path to user data directory:
        - Windows: %APPDATA%/pgsi_analyzer
        - Linux/macOS: ~/.local/share/pgsi_analyzer

    Examples:
        >>> get_user_data_dir()
        WindowsPath('C:/Users/User/AppData/Roaming/pgsi_analyzer')
        PosixPath('/home/user/.local/share/pgsi_analyzer')
    """
    if os.name == "nt":  # Windows
        base = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif os.name == "posix":  # Linux/macOS
        base = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    else:
        base = Path.home()
    
    return base / "pgsi_analyzer"


def resolve_data_path(base: Optional[Path] = None) -> Path:
    """
    Resolve data directory path with environment variable support.

    Checks PGSI_ANALYZER_DATA_DIR environment variable first, then falls back
    to the user data directory.

    Args:
        base: Optional base path. If provided, returns this path directly.

    Returns:
        Path to data directory

    Examples:
        >>> resolve_data_path()
        WindowsPath('C:/Users/User/AppData/Roaming/pgsi_analyzer/data')
        
        >>> import os
        >>> os.environ['PGSI_ANALYZER_DATA_DIR'] = '/custom/path'
        >>> resolve_data_path()
        PosixPath('/custom/path')
    """
    if base:
        return Path(base)
    
    env_path = os.getenv("PGSI_ANALYZER_DATA_DIR")
    if env_path:
        return Path(env_path)
    
    return get_user_data_dir() / "data"


def resolve_benchmark_path(algorithm: str, method: str) -> Path:
    """
    Resolve benchmark file path with environment variable support.

    Checks PGSI_ANALYZER_BENCHMARKS_DIR environment variable first, then
    falls back to current directory.

    Args:
        algorithm: Algorithm name (e.g., 'binary-trees', 'fasta')
        method: Execution method (e.g., 'cpython', 'pypy', 'cython')

    Returns:
        Path to benchmark directory

    Examples:
        >>> resolve_benchmark_path('binary-trees', 'cpython')
        PosixPath('./binary-trees/cpython')
        
        >>> import os
        >>> os.environ['PGSI_ANALYZER_BENCHMARKS_DIR'] = '/benchmarks'
        >>> resolve_benchmark_path('fasta', 'pypy')
        PosixPath('/benchmarks/fasta/pypy')
    """
    base = Path(os.getenv("PGSI_ANALYZER_BENCHMARKS_DIR", "."))
    return base / algorithm / method

