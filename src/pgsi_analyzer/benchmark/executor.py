"""
Benchmark execution module.

Handles subprocess execution of benchmarks with proper isolation
and environment setup. Ensures compilation time is excluded from
measurements.
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path
from typing import Optional, Dict, List

from ..utils import MeasurementError, PlatformError
from ..platform.detection import detect_platform


def find_python_executable(method: str) -> str:
    """
    Find the correct Python executable for a method.
    
    Args:
        method: Execution method ('cpython', 'pypy', etc.)
        
    Returns:
        Path to Python executable
        
    Raises:
        PlatformError: If required runtime not found
    """
    if method == "cpython":
        return sys.executable
    
    elif method == "pypy":
        # Try common pypy names
        for pypy_cmd in ["pypy3", "pypy", "pypy3.11", "pypy3.10"]:
            if shutil.which(pypy_cmd):
                return pypy_cmd
        raise PlatformError(
            "PyPy not found. Install PyPy to run benchmarks with PyPy method."
        )
    
    elif method in ("cython", "ctypes", "py_compile"):
        # These use standard Python after compilation/preparation
        return sys.executable
    
    else:
        raise ValueError(f"Unknown execution method: {method}")


def prepare_py_compile(benchmark_path: Path) -> Path:
    """
    Pre-compile Python file to .pyc for py_compile method.
    
    Args:
        benchmark_path: Path to main.py file
        
    Returns:
        Path to compiled .pyc file (or main.py if compilation fails)
    """
    main_py = benchmark_path / "main.py"
    if not main_py.exists():
        raise FileNotFoundError(f"main.py not found in {benchmark_path}")
    
    # Compile to .pyc
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(main_py)],
        cwd=str(benchmark_path),
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        # Fallback: use .py file directly
        return main_py
    
    # Find the compiled .pyc file
    # Python 3.8+ uses __pycache__ directory
    pycache = benchmark_path / "__pycache__"
    if pycache.exists():
        pyc_files = list(pycache.glob("main*.pyc"))
        if pyc_files:
            return pyc_files[0]
    
    # Fallback to .py
    return main_py


def execute_benchmark(
    algorithm: str,
    method: str,
    benchmark_path: Path,
    runs: int = 50,
    output_dir: Path = None,
    env: Optional[Dict[str, str]] = None,
) -> Dict[str, Path]:
    """
    Execute a benchmark and collect measurement CSVs.
    
    This function runs the benchmark in a subprocess, allowing the
    measurement decorators to capture energy and time data.
    
    Args:
        algorithm: Algorithm name (for CSV naming)
        method: Execution method
        benchmark_path: Path to benchmark directory or main.py
        runs: Number of runs (passed to benchmark script)
        output_dir: Directory where CSVs will be written (defaults to benchmark_path)
        env: Optional environment variables for subprocess
        
    Returns:
        Dictionary with keys:
        - 'energy_csv': Path to energy CSV file
        - 'time_csv': Path to time CSV file
        - 'system_info': Path to system info JSON
        
    Raises:
        MeasurementError: If execution fails
    """
    if output_dir is None:
        output_dir = benchmark_path
    
    # Determine what to execute
    if method == "py_compile":
        # Pre-compile and execute .pyc
        exec_path = prepare_py_compile(benchmark_path)
        if exec_path.suffix == ".pyc":
            # Execute .pyc directly
            exec_args = [sys.executable, str(exec_path)]
        else:
            # Fallback to .py
            exec_args = [sys.executable, str(exec_path)]
    elif benchmark_path.is_file() and benchmark_path.name == "main.py":
        # Direct main.py execution
        python_exe = find_python_executable(method)
        exec_args = [python_exe, str(benchmark_path)]
    elif (benchmark_path / "main.py").exists():
        # Directory with main.py
        python_exe = find_python_executable(method)
        exec_args = [python_exe, str(benchmark_path / "main.py")]
    else:
        raise FileNotFoundError(
            f"Could not find main.py in {benchmark_path} for {algorithm}/{method}"
        )
    
    # Prepare environment
    exec_env = os.environ.copy()
    if env:
        exec_env.update(env)
    
    # Add package to Python path if needed
    package_root = Path(__file__).parent.parent.parent
    pythonpath = exec_env.get("PYTHONPATH", "")
    if pythonpath:
        exec_env["PYTHONPATH"] = f"{package_root}:{pythonpath}"
    else:
        exec_env["PYTHONPATH"] = str(package_root)
    
    # Execute benchmark
    # The benchmark script will use decorators to write CSVs
    try:
        result = subprocess.run(
            exec_args,
            cwd=str(benchmark_path.parent if benchmark_path.is_file() else benchmark_path),
            env=exec_env,
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout per benchmark
        )
        
        if result.returncode != 0:
            raise MeasurementError(
                f"Benchmark execution failed for {algorithm}/{method}:\n"
                f"Command: {' '.join(exec_args)}\n"
                f"Return code: {result.returncode}\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )
        
    except subprocess.TimeoutExpired:
        raise MeasurementError(
            f"Benchmark execution timed out for {algorithm}/{method}"
        )
    except Exception as e:
        raise MeasurementError(
            f"Benchmark execution error for {algorithm}/{method}: {e}"
        )
    
    # Locate output CSVs
    # Decorators write CSVs to folders:
    # - Energy: folder_name (default "energy_benchmark") / {csv_filename}.csv
    # - Time: folder_name (default "time_benchmark") / {csv_filename}.csv
    # Benchmarks use csv_filename like "hanoi_cpython", "hanoi_pypy", etc.
    
    # Determine search directory
    # Benchmarks write to current working directory when executed
    # The executor runs from benchmark_path, so CSVs will be relative to that
    if benchmark_path.is_file():
        search_dir = benchmark_path.parent
    else:
        search_dir = benchmark_path
    
    # Search in multiple locations
    search_dirs = [search_dir, output_dir, search_dir.parent, Path.cwd()]
    
    # Expected CSV filename pattern from benchmarks
    csv_base = f"{algorithm.replace('-', '_')}_{method}"
    
    # Find CSV files
    energy_csv = None
    time_csv = None
    system_info = None
    
    # Search for default folders: "energy_benchmark" and "time_benchmark"
    for search_base in search_dirs:
        if not search_base or not search_base.exists():
            continue
        
        # Check default folder names
        energy_folder = search_base / "energy_benchmark"
        time_folder = search_base / "time_benchmark"
        
        if energy_folder.exists():
            csv_file = energy_folder / f"{csv_base}.csv"
            if csv_file.exists() and not energy_csv:
                energy_csv = csv_file
            # Also check for any CSV with algorithm/method in name
            for csv_file in energy_folder.glob("*.csv"):
                if csv_base.lower() in csv_file.name.lower() and not energy_csv:
                    energy_csv = csv_file
        
        if time_folder.exists():
            csv_file = time_folder / f"{csv_base}.csv"
            if csv_file.exists() and not time_csv:
                time_csv = csv_file
            for csv_file in time_folder.glob("*.csv"):
                if csv_base.lower() in csv_file.name.lower() and not time_csv:
                    time_csv = csv_file
        
        # Check for system_info
        for folder in [energy_folder, time_folder]:
            if folder.exists():
                info_file = folder / "system_info_pyrapl.json"
                if not info_file.exists():
                    info_file = folder / "system_info.json"
                if info_file.exists() and not system_info:
                    system_info = info_file
    
    # Broader search if not found - look for any folder with algorithm/method name
    if not energy_csv or not time_csv:
        for search_base in search_dirs:
            if not search_base or not search_base.exists():
                continue
            for item in search_base.iterdir():
                if not item.is_dir():
                    continue
                folder_name_lower = item.name.lower()
                if csv_base.lower() in folder_name_lower or (
                    algorithm.replace("-", "_").lower() in folder_name_lower 
                    and method.lower() in folder_name_lower
                ):
                    for csv_file in item.glob("*.csv"):
                        try:
                            import pandas as pd
                            df = pd.read_csv(csv_file, nrows=1)
                            if 'package (uJ)' in df.columns and not energy_csv:
                                energy_csv = csv_file
                            elif 'execution_time (s)' in df.columns and not time_csv:
                                time_csv = csv_file
                        except:
                            pass
    
    return {
        "energy_csv": energy_csv,
        "time_csv": time_csv,
        "system_info": system_info,
    }
