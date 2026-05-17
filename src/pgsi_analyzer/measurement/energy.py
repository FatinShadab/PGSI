"""
Energy measurement decorator using pyRAPL (Linux/Intel) or estimation.

This module provides a decorator to measure energy consumption of Python functions.
On Linux systems with Intel x86_64 processors, it uses pyRAPL for hardware-based
energy measurement. On Windows and macOS, it uses estimation methods based on
CPU time, TDP, and utilization models.
"""

import csv
import inspect
import json
import time
import warnings
from functools import wraps
from pathlib import Path
from typing import Callable, Union
from datetime import datetime

from ..platform.hardware import get_system_info, get_cpu_info, warn_if_rapl_unavailable
from ..platform.detection import is_linux_intel, detect_platform
from .estimators import (
    estimate_energy,
    estimate_energy_from_codecarbon,
    resolve_cpu_power_provenance,
)

# Methodology tags for data source labeling (audit)
METHODOLOGY_HARDWARE_RAPL_LINUX = "hardware_rapl_linux"


# Conditional pyRAPL import
_pyrapl_available = False
_pyrapl_setup_done = False
pyRAPL = None  # Will be set if available

if is_linux_intel():
    try:
        import pyRAPL as _pyrapl_module
        _pyrapl_module.setup()
        pyRAPL = _pyrapl_module
        _pyrapl_available = True
        _pyrapl_setup_done = True
    except (ImportError, OSError, RuntimeError, PermissionError) as e:
        _pyrapl_available = False
        pyRAPL = None
        warn_if_rapl_unavailable(e)


_codecarbon_available = False
_codecarbon_tracker_cls = None
_codecarbon_missing_warned = False
try:
    from codecarbon import EmissionsTracker as _tracker_cls

    _codecarbon_tracker_cls = _tracker_cls
    _codecarbon_available = True
except Exception:
    _codecarbon_available = False
    _codecarbon_tracker_cls = None


def _codecarbon_init_kwargs() -> dict:
    """Build EmissionsTracker kwargs supported by the installed CodeCarbon version."""
    kwargs = {}
    try:
        signature = inspect.signature(_codecarbon_tracker_cls.__init__)
        params = signature.parameters
        if "save_to_file" in params:
            kwargs["save_to_file"] = False
        if "save_to_logger" in params:
            kwargs["save_to_logger"] = False
        if "log_level" in params:
            kwargs["log_level"] = "error"
        if "allow_online_tracking" in params:
            kwargs["allow_online_tracking"] = False
        if "api_call_tracking" in params:
            kwargs["api_call_tracking"] = False
    except Exception:
        kwargs = {}
    return kwargs


def _create_codecarbon_tracker():
    """Build a best-effort CodeCarbon tracker across versions (including PyPy)."""
    if not _codecarbon_available or _codecarbon_tracker_cls is None:
        return None

    kwargs = _codecarbon_init_kwargs()
    attempts = [kwargs, {}]
    seen = []
    for attempt in attempts:
        key = tuple(sorted(attempt.items()))
        if key in seen:
            continue
        seen.append(key)
        try:
            return _codecarbon_tracker_cls(**attempt)
        except Exception:
            continue
    return None


def _start_codecarbon_tracker():
    """
    Start a CodeCarbon tracker, retrying with minimal options if needed.

    Returns:
        Tuple of (tracker or None, emissions_kg placeholder — always None at start).
    """
    tracker = _create_codecarbon_tracker()
    if tracker is None:
        return None

    for candidate in (tracker, _codecarbon_tracker_cls()):
        try:
            candidate.start()
            return candidate
        except Exception:
            continue
    return None


def _stop_codecarbon_tracker(tracker) -> object:
    """Stop CodeCarbon tracker and return emissions when available."""
    if tracker is None:
        return None
    try:
        return tracker.stop()
    except Exception:
        return None


def _warn_codecarbon_missing_once():
    """Warn once when CodeCarbon is unavailable in estimation mode."""
    global _codecarbon_missing_warned
    if not _codecarbon_available and not _codecarbon_missing_warned:
        _codecarbon_missing_warned = True
        warnings.warn(
            "CodeCarbon is not available; using deterministic CPU-power fallback.",
            UserWarning,
            stacklevel=2,
        )


def measure_energy_to_csv(
    n: int,
    csv_filename: str,
    folder_name: Union[str, Path] = "energy_benchmark"
):
    """
    Decorator to measure energy usage, store system info in a JSON file,
    and store energy results in a CSV file.

    On Linux/Intel systems, uses pyRAPL for hardware-based energy measurement.
    On Windows and macOS, uses estimation methods based on CPU time and TDP.

    Args:
        n: Number of times to run the function and measure energy
        csv_filename: Base name for the CSV output file (without .csv extension)
        folder_name: Directory name or Path where results will be stored

    Returns:
        Decorator function

    Examples:
        >>> @measure_energy_to_csv(n=10, csv_filename="test_energy")
        ... def my_function():
        ...     return sum(range(1000))
        >>> result = my_function()
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Convert folder_name to Path if it's a string
            folder_path = Path(folder_name) if isinstance(folder_name, str) else folder_name
            
            # Create the directory if it doesn't exist
            folder_path.mkdir(parents=True, exist_ok=True)

            # Create file paths using Path (prefix for audit: only energy_*.csv accepted by collector)
            result_file_path = folder_path / f"energy_{csv_filename}.csv"
            system_info_path = folder_path / "system_info_pyrapl.json"

            # Determine measurement method
            use_hardware = _pyrapl_available and pyRAPL is not None and is_linux_intel()
            use_estimation = not use_hardware
            
            # Warn user if using estimation
            if use_estimation:
                platform_name = detect_platform()
                warnings.warn(
                    f"Hardware energy counters (pyRAPL) not available on {platform_name}. "
                    f"Using estimation (CodeCarbon when available, otherwise CPU time/TDP). "
                    f"Estimated values may differ from actual hardware measurements.",
                    UserWarning,
                    stacklevel=2
                )

            # Get CPU info for estimation (if needed)
            cpu_info = None
            if use_estimation:
                cpu_info = get_cpu_info()

            # Write system info to JSON if the file does not exist
            if not system_info_path.exists():
                system_info = get_system_info(result_file_path)
                system_info['measurement_method'] = 'hardware' if use_hardware else 'estimation'
                system_info['platform'] = detect_platform()
                if use_estimation:
                    # Get estimation model name (will be set during first measurement)
                    system_info['estimation_model'] = 'TBD'
                system_info_path.write_text(
                    json.dumps(system_info, indent=4),
                    encoding='utf-8'
                )

            # Open the result CSV file and write the data (overwrite each run so row count = n)
            with result_file_path.open(mode='w', newline='', encoding='utf-8') as result_file:
                writer = csv.writer(result_file)
                writer.writerow([
                    'timestamp',
                    'function',
                    'run',
                    'package (uJ)',
                    'dram (uJ)',
                    'measurement_method',
                    'methodology',
                    'provenance_source',
                    'provenance_match_type',
                    'provenance_matched_model',
                ])

                # Run the function n times and log energy usage
                estimation_model = None
                for i in range(1, n + 1):
                    if use_hardware:
                        # Use pyRAPL for hardware-based measurement
                        measurement = pyRAPL.Measurement(label=f"{func.__name__}_run_{i}")
                        measurement.begin()
                        result = func(*args, **kwargs)
                        measurement.end()

                        package_energy = measurement.result.pkg[0]
                        dram_energy = measurement.result.dram[0] if measurement.result.dram else 0
                        method = 'hardware'
                        methodology = METHODOLOGY_HARDWARE_RAPL_LINUX
                        provenance_source = "rapl_hardware_counter"
                        provenance_match_type = "exact"
                        provenance_matched_model = "intel_rapl"
                    else:
                        # Use estimation fallback for non-RAPL environments.
                        # Prefer CodeCarbon in the active interpreter (CPython or PyPy),
                        # then TDP model using wall time when process_time() is zero.
                        start_cpu_time = time.process_time()
                        start_wall_time = time.perf_counter()
                        tracker = _start_codecarbon_tracker()
                        if tracker is None:
                            _warn_codecarbon_missing_once()

                        result = func(*args, **kwargs)

                        emissions_kg = _stop_codecarbon_tracker(tracker)
                        end_cpu_time = time.process_time()
                        end_wall_time = time.perf_counter()

                        cpu_time = end_cpu_time - start_cpu_time
                        wall_time = end_wall_time - start_wall_time

                        # Prefer CodeCarbon-derived energy when available, else TDP estimation.
                        if tracker is not None:
                            estimated_energy, estimation_model, methodology = (
                                estimate_energy_from_codecarbon(
                                    cpu_time,
                                    tracker=tracker,
                                    emissions_kg=emissions_kg,
                                    cpu_info=cpu_info,
                                    wall_time_seconds=wall_time,
                                )
                            )
                        else:
                            estimated_energy, estimation_model, methodology = estimate_energy(
                                cpu_time,
                                cpu_info,
                                wall_time_seconds=wall_time,
                            )
                        
                        package_energy = estimated_energy
                        dram_energy = 0  # DRAM estimation not implemented
                        method = 'estimation'
                        provenance = {
                            "source": "codecarbon_runtime",
                            "match_type": "exact",
                            "matched_model": "codecarbon_tracker_energy",
                        }
                        if methodology != "estimated_codecarbon":
                            provenance = resolve_cpu_power_provenance(
                                (cpu_info or {}).get("processor", "Unknown")
                            )
                        provenance_source = provenance["source"]
                        provenance_match_type = provenance["match_type"]
                        provenance_matched_model = provenance["matched_model"]
                        
                        # Update system info with estimation model on first run
                        if i == 1 and estimation_model:
                            system_info = get_system_info(result_file_path)
                            system_info['measurement_method'] = 'estimation'
                            system_info['platform'] = detect_platform()
                            system_info['estimation_model'] = estimation_model
                            system_info['methodology'] = methodology
                            system_info['provenance_source'] = provenance_source
                            system_info['provenance_match_type'] = provenance_match_type
                            system_info['provenance_matched_model'] = provenance_matched_model
                            system_info_path.write_text(
                                json.dumps(system_info, indent=4),
                                encoding='utf-8'
                            )

                    writer.writerow([
                        datetime.now().isoformat(),
                        func.__name__,
                        i,
                        package_energy,
                        dram_energy,
                        method,
                        methodology,
                        provenance_source,
                        provenance_match_type,
                        provenance_matched_model,
                    ])
            
            return result
        return wrapper
    return decorator

