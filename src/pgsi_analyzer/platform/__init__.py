"""
Platform abstraction module for cross-platform compatibility.

This module provides utilities for platform detection, path resolution,
and hardware information gathering across different operating systems.
"""

from .detection import detect_platform, is_linux_intel, is_windows, is_macos, is_linux
from .paths import get_user_data_dir, resolve_data_path, resolve_benchmark_path
from .hardware import get_cpu_info, get_system_info, check_rapl_support

__all__ = [
    "detect_platform",
    "is_linux_intel",
    "is_windows",
    "is_macos",
    "is_linux",
    "get_user_data_dir",
    "resolve_data_path",
    "resolve_benchmark_path",
    "get_cpu_info",
    "get_system_info",
    "check_rapl_support",
]

