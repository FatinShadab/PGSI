"""
Benchmark discovery helpers for built-in and user-defined benchmarks.

User-defined benchmarks are discovered from a folder with this layout:
    <benchmarks_dir>/<algorithm>/<method>/main.py

Methods should match pgsi execution methods (cpython, pypy, cython, ctypes, py_compile).
"""

from pathlib import Path
from typing import Dict, List, Optional

from .registry import BENCHMARKS as BUILTIN_BENCHMARKS
from .registry import VALID_METHODS


RegistryMap = Dict[str, Dict[str, str]]


def discover_user_benchmarks(benchmarks_dir: Path) -> RegistryMap:
    """Discover user-defined benchmarks from an external directory."""
    root = Path(benchmarks_dir)
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Benchmarks directory does not exist or is not a directory: {root}")

    discovered: RegistryMap = {}
    for algorithm_dir in sorted(root.iterdir()):
        if not algorithm_dir.is_dir():
            continue
        algorithm_name = algorithm_dir.name
        methods: Dict[str, str] = {}

        for method in VALID_METHODS:
            method_dir = algorithm_dir / method
            main_py = method_dir / "main.py"
            if main_py.exists() and main_py.is_file():
                methods[method] = str(main_py.resolve())
            elif method in ("cython", "ctypes") and method_dir.exists() and method_dir.is_dir():
                # Keep build-based methods compatible with builder/executor flow.
                methods[method] = str(method_dir.resolve())

        if methods:
            discovered[algorithm_name] = methods

    return discovered


def build_registry(benchmarks_dir: Optional[Path] = None) -> RegistryMap:
    """
    Build effective benchmark registry.

    Built-ins are always included. User-defined algorithms from benchmarks_dir are merged in.
    If names collide, user-defined entries override built-ins.
    """
    registry: RegistryMap = {
        algorithm: methods.copy() for algorithm, methods in BUILTIN_BENCHMARKS.items()
    }
    if benchmarks_dir is None:
        return registry

    user_registry = discover_user_benchmarks(benchmarks_dir)
    for algorithm, methods in user_registry.items():
        registry[algorithm] = methods
    return registry


def list_algorithms_from_registry(registry: RegistryMap) -> List[str]:
    return sorted(registry.keys())


def list_methods_from_registry(registry: RegistryMap, algorithm: Optional[str] = None) -> List[str]:
    if algorithm is None:
        return VALID_METHODS.copy()
    if algorithm not in registry:
        raise ValueError(f"Unknown algorithm: {algorithm}. Available: {list_algorithms_from_registry(registry)}")
    return [m for m in VALID_METHODS if m in registry[algorithm]]


def get_benchmark_path_from_registry(registry: RegistryMap, algorithm: str, method: str) -> Path:
    if algorithm not in registry:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    if method not in registry[algorithm]:
        raise ValueError(f"Unknown method '{method}' for algorithm '{algorithm}'")
    return Path(registry[algorithm][method])

