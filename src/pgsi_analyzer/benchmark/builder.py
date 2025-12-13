"""
Benchmark build system for Cython and ctypes benchmarks.

Handles compilation of Cython extensions and C shared libraries
before benchmark execution. Compilation is done separately from
measurement to ensure only execution time/energy is measured.
"""

import subprocess
import sys
import platform
from pathlib import Path
from typing import Optional

from ..utils import ConfigurationError, PlatformError


def requires_build(method: str) -> bool:
    """
    Check if a method requires compilation before execution.
    
    Args:
        method: Execution method name
        
    Returns:
        True if method requires build step
    """
    return method in ("cython", "ctypes")


def build_cython(benchmark_path: Path, build_dir: Optional[Path] = None) -> Path:
    """
    Build Cython extension module.
    
    Runs: python setup.py build_ext --inplace
    
    Args:
        benchmark_path: Path to Cython benchmark directory (contains setup.py)
        build_dir: Optional directory for build artifacts (defaults to benchmark_path)
        
    Returns:
        Path to benchmark directory (build artifacts are in-place)
        
    Raises:
        ConfigurationError: If setup.py not found or build fails
    """
    if build_dir is None:
        build_dir = benchmark_path
    
    setup_py = benchmark_path / "setup.py"
    if not setup_py.exists():
        raise ConfigurationError(f"setup.py not found in {benchmark_path}")
    
    # Change to benchmark directory for build
    original_cwd = Path.cwd()
    
    try:
        # Build extension in-place
        result = subprocess.run(
            [sys.executable, "setup.py", "build_ext", "--inplace"],
            cwd=str(benchmark_path),
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout for compilation
        )
        
        if result.returncode != 0:
            raise ConfigurationError(
                f"Cython build failed for {benchmark_path}:\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )
        
        return benchmark_path
        
    except subprocess.TimeoutExpired:
        raise ConfigurationError(f"Cython build timed out for {benchmark_path}")
    except Exception as e:
        raise ConfigurationError(f"Cython build error for {benchmark_path}: {e}")
    finally:
        # Restore original working directory
        import os
        os.chdir(str(original_cwd))


def build_ctypes(benchmark_path: Path, build_dir: Optional[Path] = None) -> Path:
    """
    Build C shared library for ctypes benchmark.
    
    Compiles .c files to .so (Linux) or .dll (Windows).
    
    Args:
        benchmark_path: Path to ctypes benchmark directory (contains .c files)
        build_dir: Optional directory for build artifacts (defaults to benchmark_path)
        
    Returns:
        Path to benchmark directory (shared library is in-place)
        
    Raises:
        ConfigurationError: If compilation fails
        PlatformError: If C compiler not available
    """
    if build_dir is None:
        build_dir = benchmark_path
    
    # Find .c files
    c_files = list(benchmark_path.glob("*.c"))
    if not c_files:
        raise ConfigurationError(f"No .c files found in {benchmark_path}")
    
    # Determine output library name and extension
    if platform.system() == "Windows":
        lib_ext = ".dll"
        # Use first .c file name as base
        lib_name = c_files[0].stem
    else:
        lib_ext = ".so"
        lib_name = f"lib{c_files[0].stem}"
    
    lib_path = benchmark_path / f"{lib_name}{lib_ext}"
    
    # Check if already compiled and up-to-date
    if lib_path.exists():
        # Check if .c files are newer than library
        c_newer = any(c.stat().st_mtime > lib_path.stat().st_mtime for c in c_files)
        if not c_newer:
            return benchmark_path  # Already built and up-to-date
    
    # Compile command
    if platform.system() == "Windows":
        # Windows: use cl.exe or gcc if available
        # Try gcc first (more common in development)
        compile_cmd = [
            "gcc",
            "-shared",
            "-o", str(lib_path),
            *[str(c) for c in c_files],
            "-fPIC",
        ]
    else:
        # Linux/macOS: use gcc
        compile_cmd = [
            "gcc",
            "-shared",
            "-fPIC",
            "-o", str(lib_path),
            *[str(c) for c in c_files],
        ]
    
    try:
        result = subprocess.run(
            compile_cmd,
            cwd=str(benchmark_path),
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )
        
        if result.returncode != 0:
            # Try alternative: check if gcc is available
            gcc_check = subprocess.run(
                ["gcc", "--version"],
                capture_output=True,
                text=True,
            )
            if gcc_check.returncode != 0:
                raise PlatformError(
                    "C compiler (gcc) not found. Install gcc to build ctypes benchmarks."
                )
            
            raise ConfigurationError(
                f"ctypes compilation failed for {benchmark_path}:\n"
                f"Command: {' '.join(compile_cmd)}\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )
        
        if not lib_path.exists():
            raise ConfigurationError(
                f"Compilation succeeded but library not found: {lib_path}"
            )
        
        return benchmark_path
        
    except subprocess.TimeoutExpired:
        raise ConfigurationError(f"ctypes compilation timed out for {benchmark_path}")
    except FileNotFoundError:
        raise PlatformError(
            "C compiler (gcc) not found. Install gcc to build ctypes benchmarks."
        )
    except Exception as e:
        raise ConfigurationError(f"ctypes compilation error for {benchmark_path}: {e}")


def build_benchmark(algorithm: str, method: str, benchmark_path: Path) -> Path:
    """
    Build a benchmark if it requires compilation.
    
    Args:
        algorithm: Algorithm name (for error messages)
        method: Execution method
        benchmark_path: Path to benchmark directory
        
    Returns:
        Path to benchmark directory (ready for execution)
        
    Raises:
        ConfigurationError: If build fails
        PlatformError: If build tools not available
    """
    if not requires_build(method):
        return benchmark_path  # No build needed
    
    if method == "cython":
        return build_cython(benchmark_path)
    elif method == "ctypes":
        return build_ctypes(benchmark_path)
    else:
        raise ValueError(f"Unknown build method: {method}")
