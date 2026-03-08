"""
Time measurement decorator for execution time profiling.

This module provides a decorator to measure execution time of Python functions
and store the results in CSV format along with system information.
"""

import csv
import json
import time
from functools import wraps
from pathlib import Path
from typing import Callable, Union
from datetime import datetime

from ..platform.hardware import get_system_info


def measure_time_to_csv(
    n: int,
    csv_filename: str,
    folder_name: Union[str, Path] = "time_benchmark"
):
    """
    Decorator to measure execution time, store system info in a JSON file,
    and store execution time results in a CSV file.

    Args:
        n: Number of times to run the function and measure execution time
        csv_filename: Base name for the CSV output file (without .csv extension)
        folder_name: Directory name or Path where results will be stored

    Returns:
        Decorator function

    Examples:
        >>> @measure_time_to_csv(n=10, csv_filename="test_time")
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

            # Create file paths using Path (prefix for audit: only time_*.csv accepted by collector)
            result_file_path = folder_path / f"time_{csv_filename}.csv"
            system_info_path = folder_path / "system_info.json"

            # Write system info to JSON if the file does not exist
            if not system_info_path.exists():
                system_info = get_system_info(result_file_path)
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
                    'execution_time (s)'
                ])

                # Run the function n times and log execution time
                for i in range(1, n + 1):
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    end_time = time.time()

                    execution_time = end_time - start_time

                    writer.writerow([
                        datetime.now().isoformat(),
                        func.__name__,
                        i,
                        execution_time
                    ])
            
            return result
        return wrapper
    return decorator

