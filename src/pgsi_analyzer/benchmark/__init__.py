"""
Benchmark execution framework for pgsi-analyzer.

This module provides tools for building, executing, and orchestrating
benchmark runs across multiple Python execution methods.
"""

from .builder import build_benchmark, requires_build
from .executor import execute_benchmark
from .orchestrator import run_benchmark_suite

__all__ = [
    "build_benchmark",
    "requires_build",
    "execute_benchmark",
    "run_benchmark_suite",
]
