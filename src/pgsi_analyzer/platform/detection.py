"""
Platform detection utilities for cross-platform compatibility.

This module provides functions to detect the current operating system
and architecture, enabling platform-specific behavior in the package.
"""

import platform
import sys
from typing import Literal

PlatformType = Literal["linux", "windows", "macos", "unknown"]


def detect_platform() -> PlatformType:
    """
    Detect the current operating system platform.

    Returns:
        Platform identifier: 'linux', 'windows', 'macos', or 'unknown'

    Examples:
        >>> detect_platform()
        'windows'  # or 'linux', 'macos', 'unknown'
    """
    system = platform.system().lower()
    
    if system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    else:
        return "unknown"


def is_linux_intel() -> bool:
    """
    Check if running on Linux with x86_64 architecture.

    This is required for Intel RAPL (Running Average Power Limit) support
    via pyRAPL library.

    Returns:
        True if running on Linux with x86_64 architecture, False otherwise

    Examples:
        >>> is_linux_intel()
        False  # On Windows
        True   # On Linux x86_64
    """
    return (
        detect_platform() == "linux"
        and platform.machine().lower() in ("x86_64", "amd64")
    )


def is_windows() -> bool:
    """
    Check if running on Windows.

    Returns:
        True if running on Windows, False otherwise

    Examples:
        >>> is_windows()
        True   # On Windows
        False  # On Linux or macOS
    """
    return detect_platform() == "windows"


def is_macos() -> bool:
    """
    Check if running on macOS.

    Returns:
        True if running on macOS, False otherwise

    Examples:
        >>> is_macos()
        True   # On macOS
        False  # On Linux or Windows
    """
    return detect_platform() == "macos"


def is_linux() -> bool:
    """
    Check if running on Linux.

    Returns:
        True if running on Linux, False otherwise

    Examples:
        >>> is_linux()
        True   # On Linux
        False  # On Windows or macOS
    """
    return detect_platform() == "linux"

