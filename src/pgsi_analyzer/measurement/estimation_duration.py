"""
Duration selection for energy estimation when hardware counters are unavailable.

PyPy often reports ``time.process_time()`` as zero for short JIT-backed runs while
wall-clock time remains measurable. CodeCarbon may still be used when installed in
the active interpreter; TDP fallback should use wall time in those cases.
"""

from __future__ import annotations

import platform
from typing import Tuple

_MINIMUM_DURATION_SECONDS = 1e-6


def is_pypy_runtime() -> bool:
    """Return True when benchmarks run under PyPy."""
    return platform.python_implementation() == "PyPy"


def effective_estimation_duration(
    cpu_time_seconds: float,
    wall_time_seconds: float,
) -> Tuple[float, str]:
    """
    Choose a duration basis for TDP-based energy estimation.

    On PyPy, prefer wall-clock time because ``process_time()`` is often zero.
    Otherwise use CPU time when positive, then wall time, then a tiny floor.

    Args:
        cpu_time_seconds: Elapsed process CPU time from ``time.process_time()``.
        wall_time_seconds: Elapsed wall time from ``time.perf_counter()``.

    Returns:
        Tuple of (duration_seconds, basis_label) where basis_label is one of
        ``cpu_time``, ``wall_time``, or ``minimum_floor``.
    """
    cpu = max(0.0, float(cpu_time_seconds or 0.0))
    wall = max(0.0, float(wall_time_seconds or 0.0))

    if is_pypy_runtime():
        if wall > 0:
            return wall, "wall_time"
        if cpu > 0:
            return cpu, "cpu_time"
        return _MINIMUM_DURATION_SECONDS, "minimum_floor"

    if cpu <= 0:
        if wall > 0:
            return wall, "wall_time"
        return _MINIMUM_DURATION_SECONDS, "minimum_floor"

    return cpu, "cpu_time"
