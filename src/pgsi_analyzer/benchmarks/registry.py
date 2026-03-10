"""
Benchmark registry - single source of truth for available benchmarks.

This module defines all built-in benchmarks and their execution methods,
providing a deterministic mapping for CLI discovery and execution.
"""

from typing import Dict, List
from pathlib import Path
import importlib.resources

# Registry mapping: algorithm_name -> method_name -> relative_path
# Paths are relative to pgsi_analyzer.benchmarks package
BENCHMARKS: Dict[str, Dict[str, str]] = {
    "binary-trees": {
        "cpython": "binary-trees/cpython/main.py",
        "pypy": "binary-trees/pypy/main.py",
        "cython": "binary-trees/cython",
        "ctypes": "binary-trees/ctypes",
        "py_compile": "binary-trees/py_compile/main.py",
    },
    "fannkuch-redux": {
        "cpython": "fannkuch-redux/cpython/main.py",
        "pypy": "fannkuch-redux/pypy/main.py",
        "cython": "fannkuch-redux/cython",
        "ctypes": "fannkuch-redux/ctypes",
        "py_compile": "fannkuch-redux/py_compile/main.py",
    },
    "fasta": {
        "cpython": "fasta/cpython/main.py",
        "pypy": "fasta/pypy/main.py",
        "cython": "fasta/cython",
        "ctypes": "fasta/ctypes",
        "py_compile": "fasta/py_compile/main.py",
    },
    "k-nucleotide": {
        "cpython": "k-nucleotide/cpython/main.py",
        "pypy": "k-nucleotide/pypy/main.py",
        "cython": "k-nucleotide/cython",
        "ctypes": "k-nucleotide/ctypes",
        "py_compile": "k-nucleotide/py_compile/main.py",
    },
    "mandelbrot": {
        "cpython": "mandelbrot/cpython/main.py",
        "pypy": "mandelbrot/pypy/main.py",
        "cython": "mandelbrot/cython",
        "ctypes": "mandelbrot/ctypes",
        "py_compile": "mandelbrot/py_compile/main.py",
    },
    "n-body": {
        "cpython": "n-body/cpython/main.py",
        "pypy": "n-body/pypy/main.py",
        "cython": "n-body/cython",
        "ctypes": "n-body/ctypes",
        "py_compile": "n-body/py_compile/main.py",
    },
    "n-queens": {
        "cpython": "n-queens/cpython/main.py",
        "pypy": "n-queens/pypy/main.py",
        "cython": "n-queens/cython",
        "ctypes": "n-queens/ctypes",
        "py_compile": "n-queens/py_compile/main.py",
    },
    "pi-digits": {
        "cpython": "pi-digits/cpython/main.py",
        "pypy": "pi-digits/pypy/main.py",
        "cython": "pi-digits/cython",
        "ctypes": "pi-digits/ctypes",
        "py_compile": "pi-digits/py_compile/main.py",
    },
    "regex-redux": {
        "cpython": "regex-redux/cpython/main.py",
        "pypy": "regex-redux/pypy/main.py",
        "cython": "regex-redux/cython",
        "ctypes": "regex-redux/ctypes",
        "py_compile": "regex-redux/py_compile/main.py",
    },
    "reverse-complement": {
        "cpython": "reverse-complement/cpython/main.py",
        "pypy": "reverse-complement/pypy/main.py",
        "cython": "reverse-complement/cython",
        "ctypes": "reverse-complement/ctypes",
        "py_compile": "reverse-complement/py_compile/main.py",
    },
    "sieve": {
        "cpython": "sieve/cpython/main.py",
        "pypy": "sieve/pypy/main.py",
        "cython": "sieve/cython",
        "ctypes": "sieve/ctypes",
        "py_compile": "sieve/py_compile/main.py",
    },
    "spectral-norm": {
        "cpython": "spectral-norm/cpython/main.py",
        "pypy": "spectral-norm/pypy/main.py",
        "cython": "spectral-norm/cython",
        "ctypes": "spectral-norm/ctypes",
        "py_compile": "spectral-norm/py_compile/main.py",
    },
    "strassen": {
        "cpython": "strassen/cpython/main.py",
        "pypy": "strassen/pypy/main.py",
        "cython": "strassen/cython",
        "ctypes": "strassen/ctypes",
        "py_compile": "strassen/py_compile/main.py",
    },
    "hanoi": {
        "cpython": "hanoi/cpython/main.py",
        "pypy": "hanoi/pypy/main.py",
        "cython": "hanoi/cython",
        "ctypes": "hanoi/ctypes",
        "py_compile": "hanoi/py_compile/main.py",
    },
    "knn": {
        "cpython": "knn/cpython/main.py",
        "pypy": "knn/pypy/main.py",
        "cython": "knn/cython",
        "ctypes": "knn/ctypes",
        "py_compile": "knn/py_compile/main.py",
    },
}

# Valid execution methods (deterministic order)
VALID_METHODS = ["cpython", "pypy", "cython", "ctypes", "py_compile"]


def list_algorithms() -> List[str]:
    """
    Return list of all available benchmark algorithms in deterministic order.
    
    Returns:
        List of algorithm names (sorted alphabetically)
    """
    return sorted(BENCHMARKS.keys())


def list_methods(algorithm: str = None) -> List[str]:
    """
    Return list of execution methods for an algorithm, or all methods if algorithm is None.
    
    Args:
        algorithm: Algorithm name, or None for all methods
        
    Returns:
        List of method names
    """
    if algorithm is None:
        return VALID_METHODS.copy()
    
    if algorithm not in BENCHMARKS:
        raise ValueError(f"Unknown algorithm: {algorithm}. Available: {list_algorithms()}")
    
    return list(BENCHMARKS[algorithm].keys())


def get_benchmark_path(algorithm: str, method: str) -> Path:
    """
    Get the filesystem path to a benchmark's main entry point.
    
    Uses importlib.resources to access package resources, falling back to
    filesystem path resolution for development.
    
    Args:
        algorithm: Algorithm name (e.g., 'hanoi')
        method: Execution method (e.g., 'cpython')
        
    Returns:
        Path object to the benchmark directory or main.py file
        
    Raises:
        ValueError: If algorithm or method is invalid
        FileNotFoundError: If benchmark path doesn't exist
    """
    if algorithm not in BENCHMARKS:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    
    if method not in BENCHMARKS[algorithm]:
        raise ValueError(f"Unknown method '{method}' for algorithm '{algorithm}'")
    
    relative_path = BENCHMARKS[algorithm][method]
    
    # Try to resolve as package resource first
    try:
        package = importlib.resources.files("pgsi_analyzer.benchmarks")
        resource_path = package / relative_path
        if resource_path.exists():
            return Path(str(resource_path))
    except (ImportError, ModuleNotFoundError):
        pass
    
    # Fallback: resolve relative to package directory
    # This works in development mode
    package_dir = Path(__file__).parent
    full_path = package_dir / relative_path
    
    if not full_path.exists():
        raise FileNotFoundError(
            f"Benchmark not found: {algorithm}/{method} at {full_path}"
        )
    
    return full_path


def validate_algorithm(algorithm: str) -> bool:
    """Check if algorithm exists in registry."""
    return algorithm in BENCHMARKS


def validate_method(algorithm: str, method: str) -> bool:
    """Check if method exists for algorithm."""
    return algorithm in BENCHMARKS and method in BENCHMARKS[algorithm]
