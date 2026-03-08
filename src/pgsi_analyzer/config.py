"""
Configuration module for pgsi-analyzer.

Handles loading of tool paths (Python, PyPy, C compiler) from multiple sources:
1. CLI arguments (highest priority)
2. Environment variables
3. .env file
4. Defaults (system PATH detection)

Environment Variables:
    PGSI_PYPY_PATH: Path to PyPy executable
    PGSI_CC_PATH: Path to C compiler (gcc/cl.exe)
    PGSI_PYTHON_PATH: Path to Python interpreter for benchmarks
    PGSI_RUNS: Number of measurement runs per benchmark (set by executor when invoking subprocesses)
"""

import os
import sys
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False


@dataclass
class ToolPaths:
    """
    Container for tool executable paths.
    
    Attributes:
        python: Path to Python interpreter (default: sys.executable)
        pypy: Path to PyPy executable (None if not configured/found)
        c_compiler: Path to C compiler (None if not configured/found)
    """
    python: Path
    pypy: Optional[Path] = None
    c_compiler: Optional[Path] = None


# Default parameters per algorithm for benchmarks (test_n = measurement runs when PGSI_RUNS not set).
# Benchmark scripts use DEFAULT_PARAMS[algorithm] for test_n and other algorithm-specific params.
DEFAULT_PARAMS: dict = {
    "binary-trees": {"test_n": 50, "depth": 10},
    "fannkuch_redux": {"test_n": 50, "n": 7},
    "fasta": {"test_n": 50, "k": 3, "query_sequence": "", "target_sequence": ""},
    "hanoi": {"test_n": 50, "n": 15},
    "K_Nucleotide": {"test_n": 50, "k": 2, "nucleotide_sequence_file": ""},
    "knn": {"test_n": 50, "num_samples": 1000, "num_features": 10, "k": 5},
    "mandelbrot": {"test_n": 50, "width": 1000, "height": 1000, "max_iter": 100, "x_min": -2.5, "x_max": 1.0, "y_min": -1.25, "y_max": 1.25},
    "nbody": {
        "test_n": 50,
        "G": 6.674e-11,
        "bodies": [
            {"mass": 1.0, "position": [0.0, 0.0, 0.0], "velocity": [0.0, 0.0, 0.0]},
            {"mass": 1.0, "position": [1.0, 0.0, 0.0], "velocity": [0.0, 0.0, 0.0]},
        ],
        "dt": 0.01,
        "time_steps": 100,
    },
    "n-queens": {"test_n": 50, "n": 12},
    "pi_digits": {"test_n": 50, "iterations": 1000},
    "regex_redux": {"test_n": 50, "file_path": ""},
    "reverse_complement": {"test_n": 50, "dna_sequence": ""},
    "sieve": {"test_n": 50, "n": 1000},
    "spectral-norm": {"test_n": 50, "matrix": [], "iterations": 10},
    "strassen": {"test_n": 50, "A": [[0]], "B": [[0]]},
}


def get_measurement_runs(algorithm: str) -> int:
    """
    Return the number of measurement runs for benchmark decorators.
    When the executor runs benchmark subprocesses, it sets PGSI_RUNS in the environment;
    that value is the source of truth. Otherwise fall back to DEFAULT_PARAMS[algorithm]["test_n"] or 50.
    """
    default = 50
    try:
        if algorithm in DEFAULT_PARAMS and isinstance(DEFAULT_PARAMS[algorithm].get("test_n"), (int, float)):
            default = int(DEFAULT_PARAMS[algorithm]["test_n"])
    except (TypeError, KeyError):
        pass
    return int(os.environ.get("PGSI_RUNS", default))


def _find_pypy_default() -> Optional[Path]:
    """
    Find PyPy executable on system PATH.
    
    Returns:
        Path to PyPy executable if found, None otherwise
    """
    for pypy_cmd in ["pypy3", "pypy", "pypy3.11", "pypy3.10", "pypy3.9"]:
        pypy_path = shutil.which(pypy_cmd)
        if pypy_path:
            return Path(pypy_path)
    return None


def _find_c_compiler_default() -> Optional[Path]:
    """
    Find C compiler on system PATH.
    
    Returns:
        Path to C compiler (gcc/cl.exe) if found, None otherwise
    """
    import platform
    
    if platform.system() == "Windows":
        # Try cl.exe first (MSVC), then gcc
        for compiler in ["cl.exe", "gcc"]:
            compiler_path = shutil.which(compiler)
            if compiler_path:
                return Path(compiler_path)
    else:
        # Linux/macOS: try gcc, then cc
        for compiler in ["gcc", "cc"]:
            compiler_path = shutil.which(compiler)
            if compiler_path:
                return Path(compiler_path)
    
    return None


def _resolve_path(path_str: Optional[str]) -> Optional[Path]:
    """
    Resolve a path string to a Path object, checking if it exists.
    
    Args:
        path_str: Path string or None
        
    Returns:
        Path object if valid and exists, None otherwise
    """
    if not path_str:
        return None
    
    path = Path(path_str)
    
    # If it's an absolute path, check if it exists
    if path.is_absolute():
        if path.exists():
            return path
        return None
    
    # If it's a command name, try to find it on PATH
    resolved = shutil.which(str(path))
    if resolved:
        return Path(resolved)
    
    # Try as relative path from current directory
    if path.exists():
        return path.resolve()
    
    return None


def load_tool_paths(
    env_file: Optional[Path] = None,
    cli_python: Optional[str] = None,
    cli_pypy: Optional[str] = None,
    cli_cc: Optional[str] = None,
    auto_load_env: bool = True,
) -> ToolPaths:
    """
    Load tool paths from multiple sources in priority order.
    
    Priority (highest to lowest):
    1. CLI arguments (cli_python, cli_pypy, cli_cc)
    2. Environment variables (PGSI_PYTHON_PATH, PGSI_PYPY_PATH, PGSI_CC_PATH)
    3. .env file (if env_file provided or auto_load_env=True)
    4. Defaults (sys.executable, PATH detection for pypy/gcc)
    
    Args:
        env_file: Optional path to .env file. If None and auto_load_env=True,
                  will try to load .env from current working directory.
        cli_python: CLI-provided Python path (highest priority)
        cli_pypy: CLI-provided PyPy path (highest priority)
        cli_cc: CLI-provided C compiler path (highest priority)
        auto_load_env: If True, automatically load .env from current directory
                       if env_file is not provided
    
    Returns:
        ToolPaths object with resolved paths
    """
    # Step 1: Load .env file if provided or auto-load enabled
    if HAS_DOTENV:
        if env_file:
            # Load specific .env file
            load_dotenv(env_file, override=False)  # Don't override existing env vars
        elif auto_load_env:
            # Try to load .env from current directory
            env_path = Path.cwd() / ".env"
            if env_path.exists():
                load_dotenv(env_path, override=False)
    elif env_file or (auto_load_env and (Path.cwd() / ".env").exists()):
        # Warn if .env file exists but python-dotenv not installed
        import warnings
        warnings.warn(
            "python-dotenv not installed. Install it to use .env file support: "
            "pip install python-dotenv",
            UserWarning
        )
    
    # Step 2: Resolve paths in priority order
    # Python path
    python_path = None
    if cli_python:
        python_path = _resolve_path(cli_python)
    elif os.getenv("PGSI_PYTHON_PATH"):
        python_path = _resolve_path(os.getenv("PGSI_PYTHON_PATH"))
    
    if not python_path:
        # Default: use current Python interpreter
        python_path = Path(sys.executable)
    
    # PyPy path
    pypy_path = None
    if cli_pypy:
        pypy_path = _resolve_path(cli_pypy)
    elif os.getenv("PGSI_PYPY_PATH"):
        pypy_path = _resolve_path(os.getenv("PGSI_PYPY_PATH"))
    
    if not pypy_path:
        # Default: try to find on PATH
        pypy_path = _find_pypy_default()
    
    # C compiler path
    cc_path = None
    if cli_cc:
        cc_path = _resolve_path(cli_cc)
    elif os.getenv("PGSI_CC_PATH"):
        cc_path = _resolve_path(os.getenv("PGSI_CC_PATH"))
    
    if not cc_path:
        # Default: try to find on PATH
        cc_path = _find_c_compiler_default()
    
    tool_paths = ToolPaths(
        python=python_path,
        pypy=pypy_path,
        c_compiler=cc_path,
    )
    verify_tool_paths_against_env(tool_paths)
    return tool_paths


def verify_tool_paths_against_env(tool_paths: ToolPaths) -> list:
    """
    Compare ToolPaths with os.environ after dotenv load.
    Returns a list of verification messages (match/mismatch) for testing and diagnostics.
    """
    results = []
    env_python = os.environ.get("PGSI_PYTHON_PATH")
    env_pypy = os.environ.get("PGSI_PYPY_PATH")
    env_cc = os.environ.get("PGSI_CC_PATH")
    if env_python is not None:
        resolved_env = _resolve_path(env_python)
        expected = str(tool_paths.python.resolve()) if tool_paths.python else None
        actual = str(resolved_env.resolve()) if resolved_env else env_python
        if expected == actual:
            results.append("PGSI_PYTHON_PATH matches tool_paths.python")
        else:
            results.append(f"PGSI_PYTHON_PATH mismatch: env->{actual}, tool_paths.python->{expected}")
    if env_pypy is not None:
        resolved_env = _resolve_path(env_pypy)
        expected = str(tool_paths.pypy.resolve()) if tool_paths.pypy else None
        actual = str(resolved_env.resolve()) if resolved_env else env_pypy
        if expected == actual:
            results.append("PGSI_PYPY_PATH matches tool_paths.pypy")
        else:
            results.append(f"PGSI_PYPY_PATH mismatch: env->{actual}, tool_paths.pypy->{expected}")
    if env_cc is not None:
        resolved_env = _resolve_path(env_cc)
        expected = str(tool_paths.c_compiler.resolve()) if tool_paths.c_compiler else None
        actual = str(resolved_env.resolve()) if resolved_env else env_cc
        if expected == actual:
            results.append("PGSI_CC_PATH matches tool_paths.c_compiler")
        else:
            results.append(f"PGSI_CC_PATH mismatch: env->{actual}, tool_paths.c_compiler->{expected}")
    return results

