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
        """
        Wrap a callable with repeatable runtime measurement and CSV logging.

        This inner decorator is intentionally separated from the outer factory so users can
        configure one measurement policy and apply it to multiple workload functions. The
        wrapper overwrites the target CSV on each invocation to keep result row counts
        deterministic (`n` rows) and easier to compare across runs.

        Args:
            func: Target workload function to execute and time repeatedly.

        Returns:
            Callable: A wrapped function with the same signature as `func` that writes
            timing artifacts before returning the final function result.

        Examples:
            >>> timer = measure_time_to_csv(n=3, csv_filename="hanoi_cpython")
            >>> @timer
            ... def workload():
            ...     return sum(range(1000))
            >>> result = workload()
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            """
            Execute the wrapped function `n` times and persist timing artifacts.

            The wrapper captures per-run wall-clock duration, records host system metadata
            once per output directory, and returns the final invocation result so benchmark
            call sites can preserve existing control flow.

            Args:
                *args: Positional arguments forwarded to the wrapped function.
                **kwargs: Keyword arguments forwarded to the wrapped function.

            Returns:
                Any: The return value produced by the last execution of the wrapped function.

            Raises:
                OSError: If output folders/files cannot be created or written.
                TypeError: If passed arguments are incompatible with the wrapped function.

            Examples:
                >>> @measure_time_to_csv(n=2, csv_filename="demo")
                ... def multiply(a, b):
                ...     return a * b
                >>> multiply(3, 4)
                12
            """
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

