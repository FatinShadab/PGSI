"""
Tests for user benchmark discovery from external directories.
"""

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

