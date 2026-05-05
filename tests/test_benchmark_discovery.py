"""
Tests for user benchmark discovery from external directories.
"""

import json

from pathlib import Path

from pgsi_analyzer.benchmarks.discovery import (
    build_registry,
    discover_user_benchmarks,
    get_benchmark_path_from_registry,
)


def test_discover_user_benchmarks_finds_algorithm_method_main(tmp_path):
    root = tmp_path / "user-benchmarks"
    main_py = root / "my-knn" / "cpython" / "main.py"
    main_py.parent.mkdir(parents=True)
    main_py.write_text("print('hello')\n")

    discovered = discover_user_benchmarks(root)

    assert "my-knn" in discovered
    assert "cpython" in discovered["my-knn"]
    assert Path(discovered["my-knn"]["cpython"]).resolve() == main_py.resolve()


def test_build_registry_includes_user_benchmarks(tmp_path):
    root = tmp_path / "user-benchmarks"
    main_py = root / "my-algo" / "cpython" / "main.py"
    main_py.parent.mkdir(parents=True)
    main_py.write_text("print('hello')\n")

    registry = build_registry(root)

    assert "hanoi" in registry  # built-in still present
    assert "my-algo" in registry
    path = get_benchmark_path_from_registry(registry, "my-algo", "cpython")
    assert path.resolve() == main_py.resolve()


def test_build_registry_reads_pgsi_registry_json(tmp_path):
    root = tmp_path / "user-benchmarks"
    root.mkdir(parents=True)
    main_py = root / "from-registry" / "cpython" / "main.py"
    main_py.parent.mkdir(parents=True)
    main_py.write_text("print('x')\n")

    data = {
        "benchmarks": {
            "from-registry": {
                "cpython": "from-registry/cpython/main.py",
            }
        }
    }
    (root / "pgsi_registry.json").write_text(json.dumps(data), encoding="utf-8")

    registry = build_registry(root)
    path = get_benchmark_path_from_registry(registry, "from-registry", "cpython")
    assert path.resolve() == main_py.resolve()


def test_discover_user_benchmarks_uses_directory_for_cython_and_ctypes(tmp_path):
    root = tmp_path / "user-benchmarks"
    cython_dir = root / "my-algo" / "cython"
    ctypes_dir = root / "my-algo" / "ctypes"
    cython_dir.mkdir(parents=True)
    ctypes_dir.mkdir(parents=True)

    (cython_dir / "main.py").write_text("print('cython')\n", encoding="utf-8")
    (ctypes_dir / "main.py").write_text("print('ctypes')\n", encoding="utf-8")

    discovered = discover_user_benchmarks(root)

    assert Path(discovered["my-algo"]["cython"]).resolve() == cython_dir.resolve()
    assert Path(discovered["my-algo"]["ctypes"]).resolve() == ctypes_dir.resolve()

