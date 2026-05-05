"""
Energy estimation utilities for platforms without hardware counters.

This module provides energy estimation functions for Windows and macOS systems
where Intel RAPL hardware counters are not available. Estimation is based on
CPU time, TDP (Thermal Design Power), and utilization models.
"""

import time
from typing import Dict, Any, Tuple, Optional

# Methodology tags for data source labeling (audit)
METHODOLOGY_ESTIMATED_CPU_TDP = "estimated_cpu_tdp"
METHODOLOGY_ESTIMATED_FALLBACK_GENERIC = "estimated_fallback_generic"
METHODOLOGY_ESTIMATED_CODECARBON = "estimated_codecarbon"

try:
    import psutil
except Exception:
    psutil = None  # Optional: e.g. PyPy may fail to load psutil's C extension

from ..platform.hardware import get_cpu_info
from ..platform.detection import is_windows, is_macos, detect_platform


# CPU TDP (Thermal Design Power) lookup table in Watts
# Common CPU models and their typical TDP values
CPU_TDP_LOOKUP: Dict[str, float] = {
    # Intel Desktop CPUs
    "intel core i3": 65.0,
    "intel core i5": 65.0,
    "intel core i7": 65.0,
    "intel core i9": 95.0,
    "intel xeon": 95.0,
    
    # Intel Mobile CPUs
    "intel core i3 u": 15.0,
    "intel core i5 u": 15.0,
    "intel core i7 u": 15.0,
    "intel core i5 h": 45.0,
    "intel core i7 h": 45.0,
    
    # AMD Desktop CPUs
    "amd ryzen 3": 65.0,
    "amd ryzen 5": 65.0,
    "amd ryzen 7": 65.0,
    "amd ryzen 9": 105.0,
    
    # AMD Mobile CPUs
    "amd ryzen 3 u": 15.0,
    "amd ryzen 5 u": 15.0,
    "amd ryzen 7 u": 15.0,
    
    # Apple Silicon (M-series)
    "apple m1": 20.0,
    "apple m1 pro": 30.0,
    "apple m1 max": 40.0,
    "apple m2": 20.0,
    "apple m2 pro": 30.0,
    "apple m2 max": 40.0,
    "apple m3": 20.0,
    "apple m3 pro": 30.0,
    "apple m3 max": 40.0,
    
    # Default fallback
    "default": 65.0,  # Typical desktop CPU TDP
}


def get_cpu_tdp(cpu_model: str) -> float:
    """
    Get CPU TDP (Thermal Design Power) for a given CPU model.

    Args:
        cpu_model: CPU model string (case-insensitive)

    Returns:
        TDP in Watts. Returns default TDP if model not found.

    Examples:
        >>> get_cpu_tdp("Intel Core i7")
        65.0
        >>> get_cpu_tdp("AMD Ryzen 5")
        65.0
        >>> get_cpu_tdp("Unknown CPU")
        65.0  # Default
    """
    cpu_lower = cpu_model.lower()
    
    # Try exact match first
    if cpu_lower in CPU_TDP_LOOKUP:
        return CPU_TDP_LOOKUP[cpu_lower]
    
    # Try partial matches
    for key, tdp in CPU_TDP_LOOKUP.items():
        if key in cpu_lower or cpu_lower in key:
            return tdp
    
    # Default fallback
    return CPU_TDP_LOOKUP["default"]


def estimate_energy_cpu_time(
    cpu_time_seconds: float,
    cpu_info: Optional[Dict[str, Any]] = None
) -> Tuple[float, str, str]:
    """
    Estimate energy consumption based on CPU time and CPU model.

    Uses CPU TDP and a utilization model to estimate energy consumption.
    The model assumes:
    - Base power consumption: 20% of TDP (idle power)
    - Active power consumption: TDP (at full load)
    - Average utilization during execution: 80% (typical for CPU-bound tasks)

    Args:
        cpu_time_seconds: CPU time spent executing (seconds)
        cpu_info: Optional CPU info dictionary. If None, will fetch automatically.

    Returns:
        Tuple of (energy in microjoules, estimation model name, methodology tag)

    Examples:
        >>> energy, model = estimate_energy_cpu_time(1.0)
        >>> energy > 0
        True
    """
    if cpu_info is None:
        cpu_info = get_cpu_info()
    
    processor = cpu_info.get("processor", "Unknown")
    tdp_watts = get_cpu_tdp(processor)
    
    # Handle edge case: very fast functions might have 0 CPU time
    # Use a minimum time threshold (1 microsecond) to ensure non-zero energy
    if cpu_time_seconds <= 0:
        cpu_time_seconds = 1e-6  # 1 microsecond minimum
    
    # Power model: Average power = idle_power + (active_power - idle_power) * utilization
    # idle_power = 20% of TDP, active_power = TDP, utilization = 80%
    idle_power_watts = tdp_watts * 0.2
    active_power_watts = tdp_watts
    utilization = 0.8  # Assume 80% CPU utilization for CPU-bound tasks
    
    average_power_watts = idle_power_watts + (active_power_watts - idle_power_watts) * utilization
    
    # Energy (Joules) = Power (Watts) × Time (seconds)
    energy_joules = average_power_watts * cpu_time_seconds
    
    # Convert to microjoules (μJ)
    energy_microjoules = energy_joules * 1e6
    
    model_name = f"TDP-based (TDP={tdp_watts}W, util={utilization:.0%})"
    # Use fallback tag when we have no real CPU model (Unknown + default TDP)
    methodology = (
        METHODOLOGY_ESTIMATED_FALLBACK_GENERIC
        if (processor == "Unknown" and tdp_watts == CPU_TDP_LOOKUP["default"])
        else METHODOLOGY_ESTIMATED_CPU_TDP
    )
    return energy_microjoules, model_name, methodology


def estimate_energy_from_psutil(
    duration_seconds: float,
    cpu_info: Optional[Dict[str, Any]] = None
) -> Tuple[float, str, str]:
    """
    Estimate energy using psutil to monitor CPU utilization.

    When psutil is not available (e.g. on PyPy), falls back to CPU-time-based
    estimation.

    Monitors CPU percent during execution and applies power models
    based on CPU type and actual utilization.

    Args:
        duration_seconds: Duration of execution (seconds)
        cpu_info: Optional CPU info dictionary. If None, will fetch automatically.

    Returns:
        Tuple of (energy in microjoules, estimation model name, methodology tag)

    Examples:
        >>> energy, model = estimate_energy_from_psutil(1.0)
        >>> energy > 0
        True
    """
    if psutil is None:
        e, m, meth = estimate_energy_cpu_time(duration_seconds, cpu_info)
        return e, m, meth

    if cpu_info is None:
        cpu_info = get_cpu_info()
    
    processor = cpu_info.get("processor", "Unknown")
    tdp_watts = get_cpu_tdp(processor)
    
    # Get CPU utilization during the measurement period
    # Note: This is a simplified model - in practice, you'd monitor during execution
    # For estimation, we use a typical value
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        if cpu_percent == 0:
            cpu_percent = 50.0  # Fallback if measurement fails
    except Exception:
        cpu_percent = 50.0  # Default assumption
    
    # Normalize to 0-1
    cpu_utilization = cpu_percent / 100.0
    
    # Power model: Linear interpolation between idle and full load
    idle_power_watts = tdp_watts * 0.2
    active_power_watts = tdp_watts
    average_power_watts = idle_power_watts + (active_power_watts - idle_power_watts) * cpu_utilization
    
    # Energy (Joules) = Power (Watts) × Time (seconds)
    energy_joules = average_power_watts * duration_seconds
    
    # Convert to microjoules (μJ)
    energy_microjoules = energy_joules * 1e6
    
    model_name = f"psutil-based (TDP={tdp_watts}W, util={cpu_utilization:.0%})"
    return energy_microjoules, model_name, METHODOLOGY_ESTIMATED_CPU_TDP


def estimate_windows(
    cpu_time_seconds: float,
    cpu_info: Optional[Dict[str, Any]] = None
) -> Tuple[float, str, str]:
    """
    Windows-specific energy estimation.

    Uses CPU time-based estimation optimized for Windows systems.

    Args:
        cpu_time_seconds: CPU time spent executing (seconds)
        cpu_info: Optional CPU info dictionary

    Returns:
        Tuple of (energy in microjoules, estimation model name, methodology tag)
    """
    return estimate_energy_cpu_time(cpu_time_seconds, cpu_info)


def estimate_macos(
    cpu_time_seconds: float,
    cpu_info: Optional[Dict[str, Any]] = None
) -> Tuple[float, str, str]:
    """
    macOS-specific energy estimation.

    Uses CPU time-based estimation optimized for macOS systems.
    Includes special handling for Apple Silicon (M-series) processors.

    Args:
        cpu_time_seconds: CPU time spent executing (seconds)
        cpu_info: Optional CPU info dictionary

    Returns:
        Tuple of (energy in microjoules, estimation model name, methodology tag)
    """
    if cpu_info is None:
        cpu_info = get_cpu_info()
    
    processor = cpu_info.get("processor", "Unknown").lower()
    
    # Apple Silicon typically has lower power consumption
    # Adjust utilization model for Apple Silicon (when psutil is available)
    if psutil is not None and (
        "apple" in processor or "m1" in processor or "m2" in processor or "m3" in processor
    ):
        return estimate_energy_from_psutil(cpu_time_seconds, cpu_info)
    # Use standard CPU time estimation for Intel Macs or when psutil is unavailable
    return estimate_energy_cpu_time(cpu_time_seconds, cpu_info)


def estimate_energy(
    cpu_time_seconds: float,
    cpu_info: Optional[Dict[str, Any]] = None
) -> Tuple[float, str, str]:
    """
    Platform-agnostic energy estimation function.

    Automatically selects the appropriate estimation method based on platform.

    Args:
        cpu_time_seconds: CPU time spent executing (seconds)
        cpu_info: Optional CPU info dictionary

    Returns:
        Tuple of (energy in microjoules, estimation model name, methodology tag)

    Examples:
        >>> energy, model, methodology = estimate_energy(1.0)
        >>> energy > 0
        True
        >>> methodology in ("estimated_cpu_tdp", "estimated_fallback_generic")
        True
    """
    platform = detect_platform()
    
    if is_windows():
        return estimate_windows(cpu_time_seconds, cpu_info)
    elif is_macos():
        return estimate_macos(cpu_time_seconds, cpu_info)
    else:
        # Fallback to CPU time-based estimation
        return estimate_energy_cpu_time(cpu_time_seconds, cpu_info)


def estimate_energy_from_codecarbon(
    cpu_time_seconds: float,
    tracker: Optional[Any] = None,
    emissions_kg: Optional[float] = None,
    cpu_info: Optional[Dict[str, Any]] = None,
) -> Tuple[float, str, str]:
    """
    Estimate energy using CodeCarbon tracker output when available.

    If tracker metadata is insufficient to recover energy directly, this falls
    back to the CPU-TDP model to keep behavior deterministic across platforms.
    """
    energy_kwh = None
    model_name = "CodeCarbon-based"

    if tracker is not None:
        final_data = getattr(tracker, "final_emissions_data", None)
        if final_data is not None:
            energy_kwh = getattr(final_data, "energy_consumed", None)
            country = getattr(final_data, "country_name", None)
            if country:
                model_name = f"CodeCarbon-based ({country})"

        if energy_kwh is None:
            total_energy = getattr(tracker, "_total_energy", None)
            if total_energy is not None:
                if isinstance(total_energy, (int, float)):
                    energy_kwh = float(total_energy)
                else:
                    energy_kwh = getattr(total_energy, "kWh", None)

    if isinstance(energy_kwh, (int, float)) and energy_kwh > 0:
        return (
            float(energy_kwh) * 3.6e12,  # 1 kWh = 3.6e6 J = 3.6e12 uJ
            model_name,
            METHODOLOGY_ESTIMATED_CODECARBON,
        )

    # Fall back to current deterministic CPU-time/TDP estimation.
    return estimate_energy_cpu_time(cpu_time_seconds, cpu_info)

