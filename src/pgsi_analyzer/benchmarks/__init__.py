"""
Benchmark suite for pgsi-analyzer.

This module provides access to built-in CPU-bound benchmarks for comparing
Python execution methods across energy, time, and carbon metrics.
"""

from .registry import BENCHMARKS, get_benchmark_path, list_algorithms, list_methods

__all__ = [
    "BENCHMARKS",
    "get_benchmark_path",
    "list_algorithms",
    "list_methods",
]
