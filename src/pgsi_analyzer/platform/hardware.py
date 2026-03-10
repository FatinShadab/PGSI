"""
Hardware detection and system information utilities.

This module provides functions to gather system information and detect
hardware capabilities, including Intel RAPL support for energy measurement.
"""

import os
import platform
import warnings
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import psutil
except Exception:
    psutil = None  # Optional: e.g. PyPy may fail to load psutil's C extension

try:
    from cpuinfo import get_cpu_info as _cpuinfo_get
except Exception:
    _cpuinfo_get = None  # Optional: py-cpuinfo works on CPython and PyPy

from .detection import is_linux_intel


def get_cpu_info() -> Dict[str, Any]:
    """
    Get CPU information using psutil (when available) and platform modules.

    When psutil is not available (e.g. on PyPy), tries py-cpuinfo if installed,
    then falls back to platform and os.

    Returns:
        Dictionary containing CPU information:
        - processor: CPU processor name
        - cores_physical: Number of physical CPU cores
        - cores_logical: Number of logical CPU cores
        - frequency_current: Current CPU frequency (MHz)
        - architecture: CPU architecture

    Examples:
        >>> info = get_cpu_info()
        >>> info['processor']
        'Intel64 Family 6 Model 142 Stepping 10, GenuineIntel'
    """
    if psutil is not None:
        try:
            freq = psutil.cpu_freq()
            freq_current = freq.current if freq else None
        except Exception:
            freq_current = None
        cores_physical = psutil.cpu_count(logical=False) or 0
        cores_logical = psutil.cpu_count(logical=True) or 0
    else:
        # Fallback: py-cpuinfo (works on CPython and PyPy) or stdlib
        if _cpuinfo_get is not None:
            try:
                info = _cpuinfo_get()
                processor = (info.get("brand_raw") or platform.processor() or "Unknown").strip()
                cores_logical = int(info["count"]) if info.get("count") is not None else (os.cpu_count() or 0)
                cores_physical = 0  # py-cpuinfo does not expose physical vs logical
                hz_actual = info.get("hz_actual")
                freq_current = (float(hz_actual[0]) / 1e6) if hz_actual else None
                architecture = info.get("arch") or platform.machine()
                return {
                    "processor": processor,
                    "cores_physical": cores_physical,
                    "cores_logical": cores_logical,
                    "frequency_current": freq_current,
                    "architecture": architecture,
                }
            except Exception:
                pass
        freq_current = None
        cores_logical = os.cpu_count() or 0
        cores_physical = 0

    return {
        "processor": platform.processor() or "Unknown",
        "cores_physical": cores_physical,
        "cores_logical": cores_logical,
        "frequency_current": freq_current,
        "architecture": platform.machine(),
    }


def get_system_info(result_file_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Get comprehensive system information.

    Returns a dictionary with system information including CPU, RAM, OS,
    architecture, and test result file path.

    Args:
        result_file_path: Optional path to test result file. If provided as
                         string, will be converted to Path.

    Returns:
        Dictionary containing system information:
        - CPU: CPU processor name
        - RAM_GB: Total RAM in GB
        - OS: Operating system name and version
        - Architecture: System architecture
        - Test_Result_File: Path to test result file (if provided)
        - Platform: Detected platform ('linux', 'windows', 'macos', 'unknown')

    Examples:
        >>> info = get_system_info(Path('test.csv'))
        >>> info['OS']
        'Windows 10'
        >>> info['RAM_GB']
        16.0
    """
    if result_file_path is not None:
        if isinstance(result_file_path, str):
            result_file_path = Path(result_file_path)
        result_file_str = str(result_file_path)
    else:
        result_file_str = ""

    cpu_info = get_cpu_info()
    ram_gb = (
        round(psutil.virtual_memory().total / (1024 ** 3), 2)
        if psutil is not None
        else 0.0
    )

    return {
        "CPU": cpu_info["processor"],
        "RAM_GB": ram_gb,
        "OS": f"{platform.system()} {platform.release()}",
        "Architecture": platform.machine(),
        "Test_Result_File": result_file_str,
        "Platform": platform.system().lower(),
        "Cores_Physical": cpu_info["cores_physical"],
        "Cores_Logical": cpu_info["cores_logical"],
    }


def check_rapl_support() -> bool:
    """
    Check if Intel RAPL (Running Average Power Limit) is available.

    RAPL is only available on Linux systems with Intel x86_64 processors.
    This function checks both platform compatibility and whether pyRAPL
    can be imported and initialized.

    Returns:
        True if RAPL support is available, False otherwise

    Examples:
        >>> check_rapl_support()
        False  # On Windows or non-Intel systems
        True   # On Linux with Intel x86_64 and pyRAPL installed
    """
    # First check platform compatibility
    if not is_linux_intel():
        return False
    
    # Try to import and initialize pyRAPL
    try:
        import pyRAPL
        pyRAPL.setup()
        return True
    except (ImportError, OSError, RuntimeError, PermissionError):
        # pyRAPL not installed or RAPL not available on this system
        return False


def _is_permission_related(exc: BaseException) -> bool:
    """Return True if the exception indicates RAPL access was denied by permissions."""
    if isinstance(exc, PermissionError):
        return True
    if isinstance(exc, OSError) and getattr(exc, "errno", None) == 13:
        return True
    msg = str(exc).lower()
    return "permission" in msg or "denied" in msg or "access" in msg


def warn_if_rapl_unavailable(exc: BaseException) -> None:
    """
    Emit a UserWarning when RAPL is unavailable on Linux/Intel due to permissions.

    Call this from the pyRAPL setup exception handler. On Linux x86_64, if the
    exception looks permission-related (PermissionError, errno 13, or message
    containing "permission"), warns with actionable advice (cap_sys_rawio or root).
    On other platforms, does nothing so that no permission-specific instructions
    appear for Windows/macOS.
    """
    if not is_linux_intel():
        return
    if not _is_permission_related(exc):
        return
    warnings.warn(
        "Hardware energy measurement (RAPL) is unavailable: permission denied. "
        "Using estimation instead. For RAPL on Linux, run with cap_sys_rawio "
        "(e.g. sudo setcap cap_sys_rawio+ep $(which python3)) or as root.",
        UserWarning,
        stacklevel=2,
    )

