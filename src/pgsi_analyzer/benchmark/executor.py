"""
Benchmark execution module.

Handles subprocess execution of benchmarks with proper isolation
and environment setup. Ensures compilation time is excluded from
measurements. Writes audit log (.audit.log) in output_dir for each run.
Supports AuditLogger for path identity verification and audit_report.json.
"""

import json
import subprocess
import sys
import os
import shutil
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime

from ..utils import MeasurementError, PlatformError
from ..platform.detection import detect_platform
from ..config import ToolPaths

AUDIT_LOG_FILENAME = ".audit.log"
AUDIT_REPORT_FILENAME = "audit_report.json"


def get_runtime_executable(
    interpreter_path: str,
    env: Dict[str, str],
    cwd: Optional[str] = None,
) -> Optional[str]:
    """
    Run the interpreter with -c "import sys; print(sys.executable)" and return
    the path the runtime reports. Used for path identity verification.
    """
    try:
        result = subprocess.run(
            [interpreter_path, "-c", "import sys; print(sys.executable)"],
            env=env,
            cwd=cwd or os.getcwd(),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass
    return None


class AuditLogger:
    """
    Captures cmd list and env for every subprocess.run, and path identity
    (resolved vs runtime-reported) per method for audit_report.json.
    """

    def __init__(self) -> None:
        self._executions: List[Dict[str, Any]] = []
        self._path_identity: Dict[str, Dict[str, Any]] = {}  # method -> resolved, runtime_reported

    def log_execution(
        self,
        method: str,
        algorithm: str,
        cmd: List[str],
        env_slice: Dict[str, str],
        resolved_interpreter: str,
        runtime_reported_path: Optional[str] = None,
    ) -> None:
        self._executions.append({
            "method": method,
            "algorithm": algorithm,
            "cmd": cmd,
            "env_slice": env_slice,
            "resolved_interpreter": resolved_interpreter,
            "runtime_reported_path": runtime_reported_path,
        })
        if method not in self._path_identity and runtime_reported_path is not None:
            self._path_identity[method] = {
                "resolved": resolved_interpreter,
                "runtime_reported": runtime_reported_path,
            }

    def set_path_identity(self, method: str, resolved: str, runtime_reported: Optional[str]) -> None:
        """Set or update path identity for a method (e.g. after path identity check)."""
        self._path_identity[method] = {"resolved": resolved, "runtime_reported": runtime_reported or ""}

    def to_report_dict(
        self,
        path_sources: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Build the structure for audit_report.json: path_integrity per method,
        requested/resolved/runtime_reported, source (env/cli/system_default),
        and severity HIGH if mismatch.
        """
        method_to_tool = {"cpython": "python", "pypy": "pypy", "cython": "python", "ctypes": "python", "py_compile": "python"}
        methods = sorted(self._path_identity.keys())
        path_entries = []
        any_mismatch = False
        for method in methods:
            tool = method_to_tool.get(method, "python")
            sources = path_sources.get(tool, {"path": None, "source": "system_default"})
            requested = sources.get("path") or ""
            identity = self._path_identity[method]
            resolved = identity.get("resolved", "")
            runtime_reported = identity.get("runtime_reported", "")
            path_ok = bool(resolved and runtime_reported and Path(resolved).resolve() == Path(runtime_reported).resolve())
            if not path_ok and resolved and runtime_reported:
                any_mismatch = True
            path_entries.append({
                "method": method,
                "requested_path": requested,
                "resolved_path": resolved,
                "runtime_reported_path": runtime_reported,
                "path_source": sources.get("source", "system_default"),
                "path_integrity": path_ok,
            })
        report = {
            "timestamp": datetime.now().isoformat(),
            "path_entries": path_entries,
            "severity": "HIGH" if any_mismatch else "NONE",
        }
        if any_mismatch:
            report["message"] = "Path mismatch detected: resolved interpreter path does not match runtime-reported path (e.g. symlink or PATH shadowing)."
        return report


def _append_audit_log(
    output_dir: Optional[Path],
    algorithm: str,
    method: str,
    exec_args: List[str],
    exec_env: Dict[str, str],
    interpreter_absolute: str,
) -> None:
    """
    Append one audit record to output_dir/.audit.log.
    Logs exec_args, interpreter path (for cpython/pypy), and selected env vars.
    """
    if output_dir is None:
        return
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / AUDIT_LOG_FILENAME
    path_str = str(Path(exec_args[0]).resolve()) if exec_args else ""
    env_slice = {
        "PATH": exec_env.get("PATH", "")[:500] + ("..." if len(exec_env.get("PATH", "")) > 500 else ""),
        "PYTHONPATH": exec_env.get("PYTHONPATH", ""),
        "PGSI_RUNS": exec_env.get("PGSI_RUNS", ""),
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"\n--- {datetime.now().isoformat()} | {algorithm} | {method} ---\n")
        f.write(f"interpreter_absolute: {interpreter_absolute or path_str}\n")
        f.write(f"exec_args: {exec_args}\n")
        f.write(f"env PATH: {env_slice['PATH']}\n")
        f.write(f"env PYTHONPATH: {env_slice['PYTHONPATH']}\n")
        f.write(f"env PGSI_RUNS: {env_slice['PGSI_RUNS']}\n")


def find_python_executable(method: str, tool_paths: Optional[ToolPaths] = None) -> str:
    """
    Find the correct Python executable for a method.
    
    Args:
        method: Execution method ('cpython', 'pypy', etc.)
        tool_paths: Optional ToolPaths configuration. If None, uses defaults.
        
    Returns:
        Path to Python executable (as string for subprocess)
        
    Raises:
        PlatformError: If required runtime not found
    """
    if tool_paths is None:
        # Fallback to default behavior for backwards compatibility
        tool_paths = ToolPaths(python=Path(sys.executable))
    
    if method == "cpython":
        return str(tool_paths.python)
    
    elif method == "pypy":
        if tool_paths.pypy:
            return str(tool_paths.pypy)
        raise PlatformError(
            "PyPy method selected but no valid PyPy executable found. "
            "Configure PGSI_PYPY_PATH, use --pypy-path, or ensure 'pypy' is on PATH."
        )
    
    elif method in ("cython", "ctypes", "py_compile"):
        # These use standard Python after compilation/preparation
        return str(tool_paths.python)
    
    else:
        raise ValueError(f"Unknown execution method: {method}")


def prepare_py_compile(benchmark_path: Path, tool_paths: Optional[ToolPaths] = None) -> Path:
    """
    Pre-compile Python file to .pyc for py_compile method.

    Callers should execute ``main.py`` afterward (not the ``.pyc`` path directly) so
    CPython loads bytecode from ``__pycache__`` with normal script semantics.

    Args:
        benchmark_path: Path to main.py file or to the py_compile directory
        tool_paths: Optional ToolPaths configuration for Python executable

    Returns:
        Path to main.py (always — use this for subprocess execution)
    """
    if benchmark_path.is_file() and benchmark_path.name == "main.py":
        bench_dir = benchmark_path.parent
        main_py = benchmark_path
    else:
        bench_dir = benchmark_path
        main_py = benchmark_path / "main.py"
    if not main_py.exists():
        raise FileNotFoundError(f"main.py not found in {bench_dir}")
    
    # Use configured Python or default
    python_exe = str(tool_paths.python) if tool_paths else sys.executable
    
    # Compile to .pyc
    result = subprocess.run(
        [python_exe, "-m", "py_compile", str(main_py)],
        cwd=str(bench_dir),
        capture_output=True,
        text=True,
    )
    
    return main_py


def execute_benchmark(
    algorithm: str,
    method: str,
    benchmark_path: Path,
    runs: int = 50,
    output_dir: Path = None,
    env: Optional[Dict[str, str]] = None,
    tool_paths: Optional[ToolPaths] = None,
    audit_logger: Optional[AuditLogger] = None,
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
        tool_paths: Optional ToolPaths configuration for Python/PyPy executables
        
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
        # Pre-compile to __pycache__, then run main.py (CPython loads the .pyc automatically).
        # Do not execute ``python path/__pycache__/main.pyc`` directly: that sets sys.path[0]
        # to __pycache__ and skews imports/timing vs cpython and manual measurements.
        if benchmark_path.is_file() and benchmark_path.name == "main.py":
            main_py = benchmark_path
        else:
            main_py = benchmark_path / "main.py"
        prepare_py_compile(main_py.parent if main_py.is_file() else benchmark_path, tool_paths)
        python_exe = str(tool_paths.python) if tool_paths else sys.executable
        exec_args = [python_exe, str(main_py)]
    elif benchmark_path.is_file() and benchmark_path.name == "main.py":
        # Direct main.py execution
        python_exe = find_python_executable(method, tool_paths)
        exec_args = [python_exe, str(benchmark_path)]
    elif (benchmark_path / "main.py").exists():
        # Directory with main.py
        python_exe = find_python_executable(method, tool_paths)
        exec_args = [python_exe, str(benchmark_path / "main.py")]
    else:
        raise FileNotFoundError(
            f"Could not find main.py in {benchmark_path} for {algorithm}/{method}"
        )
    
    # Prepare environment
    exec_env = os.environ.copy()
    if env:
        exec_env.update(env)
    # Pass run count to benchmark subprocess (source of truth for decorator n)
    exec_env["PGSI_RUNS"] = str(runs)

    # Add package to Python path if needed
    package_root = Path(__file__).parent.parent.parent
    pythonpath = exec_env.get("PYTHONPATH", "")
    if pythonpath:
        exec_env["PYTHONPATH"] = f"{package_root}:{pythonpath}"
    else:
        exec_env["PYTHONPATH"] = str(package_root)

    # Audit log: record exec_args and env for this run (interpreter absolute path for cpython/pypy)
    interpreter_absolute = str(Path(exec_args[0]).resolve()) if exec_args else ""
    _append_audit_log(output_dir, algorithm, method, exec_args, exec_env, interpreter_absolute)

    # Path identity check: run interpreter to get runtime-reported sys.executable (once per method)
    cwd = str(benchmark_path.parent if benchmark_path.is_file() else benchmark_path)
    runtime_reported = None
    if audit_logger is not None:
        if method not in audit_logger._path_identity:
            runtime_reported = get_runtime_executable(exec_args[0], exec_env, cwd=cwd)
            audit_logger.set_path_identity(method, interpreter_absolute, runtime_reported)
        else:
            runtime_reported = audit_logger._path_identity[method].get("runtime_reported")
        env_slice = {
            "PATH": exec_env.get("PATH", "")[:500] + ("..." if len(exec_env.get("PATH", "")) > 500 else ""),
            "PYTHONPATH": exec_env.get("PYTHONPATH", ""),
            "PGSI_RUNS": exec_env.get("PGSI_RUNS", ""),
        }
        audit_logger.log_execution(
            method=method,
            algorithm=algorithm,
            cmd=exec_args,
            env_slice=env_slice,
            resolved_interpreter=interpreter_absolute,
            runtime_reported_path=runtime_reported,
        )
    
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
            err_msg = (
                f"Benchmark execution failed for {algorithm}/{method}:\n"
                f"Command: {' '.join(exec_args)}\n"
                f"Return code: {result.returncode}\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )
            if method == "pypy" and "ModuleNotFoundError" in result.stderr and "psutil" in result.stderr:
                err_msg += (
                    "\n\nPyPy is missing dependencies used by benchmark scripts. Install only what's needed:\n"
                    "  pypy3 -m ensurepip   # if pip is not installed\n"
                    "  pypy3 -m pip install psutil python-dotenv"
                )
            raise MeasurementError(err_msg)
        
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
    
    # Expected CSV filename pattern from benchmarks (audit: energy_*.csv and time_*.csv)
    # Many py_compile scripts use "pycompile" (no underscore) in csv_filename
    # Some benchmarks (e.g. n-body) use algorithm with hyphens removed (nbody not n_body)
    csv_base = f"{algorithm.replace('-', '_')}_{method}"
    alg_no_hyphen = algorithm.replace("-", "")
    csv_bases_to_try = [csv_base]
    if "-" in algorithm:
        csv_bases_to_try.append(f"{alg_no_hyphen}_{method}")
    if method == "py_compile":
        csv_bases_to_try.append(f"{algorithm.replace('-', '_')}_pycompile")
        if "-" in algorithm:
            csv_bases_to_try.append(f"{alg_no_hyphen}_py_compile")
            csv_bases_to_try.append(f"{alg_no_hyphen}_pycompile")
    # Prefer prefixed names (energy_*, time_*) for audit compliance
    energy_bases = [f"energy_{b}" for b in csv_bases_to_try] + csv_bases_to_try
    time_bases = [f"time_{b}" for b in csv_bases_to_try] + csv_bases_to_try
    
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
            for base in energy_bases:
                csv_file = energy_folder / f"{base}.csv"
                if csv_file.exists() and not energy_csv:
                    energy_csv = csv_file
                    break
            if not energy_csv:
                for csv_file in energy_folder.glob("energy_*.csv"):
                    if any(b.lower() in csv_file.stem.lower() for b in csv_bases_to_try) and not energy_csv:
                        energy_csv = csv_file
                        break
            if not energy_csv:
                for csv_file in energy_folder.glob("*.csv"):
                    if any(base.lower() in csv_file.name.lower() for base in csv_bases_to_try) and not energy_csv:
                        energy_csv = csv_file
                        break
        
        if time_folder.exists():
            for base in time_bases:
                csv_file = time_folder / f"{base}.csv"
                if csv_file.exists() and not time_csv:
                    time_csv = csv_file
                    break
            if not time_csv:
                for csv_file in time_folder.glob("time_*.csv"):
                    if any(b.lower() in csv_file.stem.lower() for b in csv_bases_to_try) and not time_csv:
                        time_csv = csv_file
                        break
            if not time_csv:
                for csv_file in time_folder.glob("*.csv"):
                    if any(base.lower() in csv_file.name.lower() for base in csv_bases_to_try) and not time_csv:
                        time_csv = csv_file
                        break
        
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
