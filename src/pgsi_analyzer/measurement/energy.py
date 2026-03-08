"""
Energy measurement decorator using pyRAPL (Linux/Intel) or estimation.

This module provides a decorator to measure energy consumption of Python functions.
On Linux systems with Intel x86_64 processors, it uses pyRAPL for hardware-based
energy measurement. On Windows and macOS, it uses estimation methods based on
CPU time, TDP, and utilization models.
"""

import csv
import json
import time
import warnings
from functools import wraps
from pathlib import Path
from typing import Callable, Union
from datetime import datetime

from ..platform.hardware import get_system_info, get_cpu_info, warn_if_rapl_unavailable
from ..platform.detection import is_linux_intel, detect_platform
from .estimators import estimate_energy


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

            # Create file paths using Path
            result_file_path = folder_path / f"{csv_filename}.csv"
            system_info_path = folder_path / "system_info_pyrapl.json"

            # Determine measurement method
            use_hardware = _pyrapl_available and pyRAPL is not None and is_linux_intel()
            use_estimation = not use_hardware
            
            # Warn user if using estimation
            if use_estimation:
                platform_name = detect_platform()
                warnings.warn(
                    f"Hardware energy counters (pyRAPL) not available on {platform_name}. "
                    f"Using estimation based on CPU time and TDP. "
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
                    'measurement_method'
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
                    else:
                        # Use estimation for non-Linux platforms
                        # Measure CPU time
                        start_cpu_time = time.process_time()
                        start_wall_time = time.time()
                        result = func(*args, **kwargs)
                        end_cpu_time = time.process_time()
                        end_wall_time = time.time()
                        
                        cpu_time = end_cpu_time - start_cpu_time
                        wall_time = end_wall_time - start_wall_time
                        
                        # Use CPU time for estimation (more accurate for CPU-bound tasks)
                        estimated_energy, estimation_model = estimate_energy(
                            cpu_time,
                            cpu_info
                        )
                        
                        package_energy = estimated_energy
                        dram_energy = 0  # DRAM estimation not implemented
                        method = 'estimation'
                        
                        # Update system info with estimation model on first run
                        if i == 1 and estimation_model:
                            system_info = get_system_info(result_file_path)
                            system_info['measurement_method'] = 'estimation'
                            system_info['platform'] = detect_platform()
                            system_info['estimation_model'] = estimation_model
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
                        method
                    ])
            
            return result
        return wrapper
    return decorator

