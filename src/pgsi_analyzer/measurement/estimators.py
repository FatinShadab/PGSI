"""
Energy estimation utilities for platforms without hardware counters.

This module provides energy estimation functions for Windows and macOS systems
where Intel RAPL hardware counters are not available. Estimation is based on
CPU time, TDP (Thermal Design Power), and utilization models.
"""

from typing import Dict, Any, Tuple, Optional

# Methodology tags for data source labeling (audit)
METHODOLOGY_DATASET_TDP = "dataset_tdp"
METHODOLOGY_GENERIC_TDP = "generic_tdp"
METHODOLOGY_ESTIMATED_CODECARBON = "estimated_codecarbon"

# Keep CodeCarbon only when it is within this band of wall×TDP (avoids PyPy under-
# report and CPython/ctypes/cython over-report on short benchmark runs).
CODECARBON_TDP_MIN_RATIO = 0.5
CODECARBON_TDP_MAX_RATIO = 2.0

try:
    import psutil
except Exception:
    psutil = None  # Optional: e.g. PyPy may fail to load psutil's C extension

from ..platform.hardware import get_cpu_info
from ..platform.detection import is_windows, is_macos
from .cpu_power_resolver import resolve_cpu_power, DEFAULT_TDP_WATTS
from .estimation_duration import effective_estimation_duration


CPU_TDP_LOOKUP: Dict[str, float] = {"default": DEFAULT_TDP_WATTS}


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
    return resolve_cpu_power(cpu_model).tdp_watts


def resolve_cpu_power_provenance(cpu_model: str) -> Dict[str, str]:
    """Return audit metadata for CPU power resolution."""
    resolution = resolve_cpu_power(cpu_model)
    methodology = (
        METHODOLOGY_DATASET_TDP
        if resolution.source == "codecarbon_cpu_power_csv"
        else METHODOLOGY_GENERIC_TDP
    )
    return {
        "methodology": methodology,
        "match_type": resolution.match_type,
        "matched_model": resolution.matched_model,
        "source": resolution.source,
    }


def estimate_energy_cpu_time(
    cpu_time_seconds: float,
    cpu_info: Optional[Dict[str, Any]] = None,
    wall_time_seconds: Optional[float] = None,
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
        wall_time_seconds: Optional wall time from ``time.perf_counter()`` used when
            CPU time is zero or when running on PyPy.

    Returns:
        Tuple of (energy in microjoules, estimation model name, methodology tag)

    Examples:
        >>> energy, model = estimate_energy_cpu_time(1.0)
        >>> energy > 0
        True
    """
    if cpu_info is None:
        cpu_info = get_cpu_info()

    duration_seconds, duration_basis = effective_estimation_duration(
        cpu_time_seconds,
        wall_time_seconds if wall_time_seconds is not None else 0.0,
    )
    
    processor = cpu_info.get("processor", "Unknown")
    provenance = resolve_cpu_power_provenance(processor)
    tdp_watts = get_cpu_tdp(processor)
    
    # Power model: Average power = idle_power + (active_power - idle_power) * utilization
    # idle_power = 20% of TDP, active_power = TDP, utilization = 80%
    idle_power_watts = tdp_watts * 0.2
    active_power_watts = tdp_watts
    utilization = 0.8  # Assume 80% CPU utilization for CPU-bound tasks
    
    average_power_watts = idle_power_watts + (active_power_watts - idle_power_watts) * utilization
    
    # Energy (Joules) = Power (Watts) × Time (seconds)
    energy_joules = average_power_watts * duration_seconds
    
    # Convert to microjoules (μJ)
    energy_microjoules = energy_joules * 1e6
    
    model_name = (
        f"TDP-based ({duration_basis}, TDP={tdp_watts}W, util={utilization:.0%}, "
        f"match={provenance['match_type']}, source={provenance['source']})"
    )
    methodology = provenance["methodology"]
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
    provenance = resolve_cpu_power_provenance(processor)
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
    
    model_name = (
        f"psutil-based (TDP={tdp_watts}W, util={cpu_utilization:.0%}, "
        f"match={provenance['match_type']}, source={provenance['source']})"
    )
    return energy_microjoules, model_name, provenance["methodology"]


def estimate_windows(
    cpu_time_seconds: float,
    cpu_info: Optional[Dict[str, Any]] = None,
    wall_time_seconds: Optional[float] = None,
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
    return estimate_energy_cpu_time(cpu_time_seconds, cpu_info, wall_time_seconds)


def estimate_macos(
    cpu_time_seconds: float,
    cpu_info: Optional[Dict[str, Any]] = None,
    wall_time_seconds: Optional[float] = None,
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
    return estimate_energy_cpu_time(cpu_time_seconds, cpu_info, wall_time_seconds)


def estimate_energy(
    cpu_time_seconds: float,
    cpu_info: Optional[Dict[str, Any]] = None,
    wall_time_seconds: Optional[float] = None,
) -> Tuple[float, str, str]:
    """
    Platform-agnostic energy estimation function.

    Automatically selects the appropriate estimation method based on platform.

    Args:
        cpu_time_seconds: CPU time spent executing (seconds)
        cpu_info: Optional CPU info dictionary
        wall_time_seconds: Optional wall time for PyPy / zero CPU-time fallback.

    Returns:
        Tuple of (energy in microjoules, estimation model name, methodology tag)

    Examples:
        >>> energy, model, methodology = estimate_energy(1.0)
        >>> energy > 0
        True
        >>> methodology in ("dataset_tdp", "generic_tdp")
        True
    """
    if is_windows():
        return estimate_windows(cpu_time_seconds, cpu_info, wall_time_seconds)
    elif is_macos():
        return estimate_macos(cpu_time_seconds, cpu_info, wall_time_seconds)
    else:
        # Fallback to CPU time-based estimation
        return estimate_energy_cpu_time(cpu_time_seconds, cpu_info, wall_time_seconds)


def estimate_energy_from_codecarbon(
    cpu_time_seconds: float,
    tracker: Optional[Any] = None,
    emissions_kg: Optional[float] = None,
    cpu_info: Optional[Dict[str, Any]] = None,
    wall_time_seconds: Optional[float] = None,
) -> Tuple[float, str, str]:
    """
    Estimate energy using CodeCarbon tracker output when available.

    If tracker metadata is insufficient to recover energy directly, this falls
    back to the CPU-TDP model to keep behavior deterministic across platforms.

    When CodeCarbon is outside a plausible band around wall×TDP (under on PyPy,
    over on short ctypes/cython/cpython runs), the wall×TDP estimate is used so
    energy stays consistent with measured execution time.
    """
    tdp_energy, tdp_model, tdp_methodology = estimate_energy_cpu_time(
        cpu_time_seconds,
        cpu_info,
        wall_time_seconds=wall_time_seconds,
    )

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
        cc_energy_uj = float(energy_kwh) * 3.6e12  # 1 kWh = 3.6e6 J = 3.6e12 uJ
        if tdp_energy > 0:
            ratio = cc_energy_uj / tdp_energy
            if ratio < CODECARBON_TDP_MIN_RATIO:
                return (
                    tdp_energy,
                    f"{tdp_model} (CodeCarbon below TDP floor)",
                    tdp_methodology,
                )
            if ratio > CODECARBON_TDP_MAX_RATIO:
                return (
                    tdp_energy,
                    f"{tdp_model} (CodeCarbon above TDP ceiling)",
                    tdp_methodology,
                )
        return (
            cc_energy_uj,
            model_name,
            METHODOLOGY_ESTIMATED_CODECARBON,
        )

    return tdp_energy, tdp_model, tdp_methodology

