"""
Tests for benchmark registry module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from pgsi_analyzer.benchmarks.registry import (
    BENCHMARKS,
    list_algorithms,
    list_methods,
    get_benchmark_path,
    validate_algorithm,
    validate_method,
    VALID_METHODS,
)


class TestBenchmarkRegistry:
    """Test benchmark registry functionality."""

    def test_benchmarks_dict_structure(self):
        """Test that BENCHMARKS dict has correct structure."""
        assert isinstance(BENCHMARKS, dict)
        assert len(BENCHMARKS) > 0
        
        # Check each algorithm has all methods
        for algo_name, methods in BENCHMARKS.items():
            assert isinstance(methods, dict)
            assert len(methods) == 5  # Should have 5 methods
            for method in VALID_METHODS:
                assert method in methods, f"{algo_name} missing method {method}"

    def test_list_algorithms(self):
        """Test listing all algorithms."""
        algorithms = list_algorithms()
        
        assert isinstance(algorithms, list)
        assert len(algorithms) == 15  # Should have 15 algorithms
        assert all(isinstance(a, str) for a in algorithms)
        assert algorithms == sorted(algorithms)  # Should be sorted
        
        # Check some expected algorithms
        assert "hanoi" in algorithms
        assert "binary-trees" in algorithms
        assert "k-nucleotide" in algorithms

    def test_list_methods_all(self):
        """Test listing all methods."""
        methods = list_methods()
        
        assert isinstance(methods, list)
        assert len(methods) == 5
        assert methods == VALID_METHODS

    def test_list_methods_for_algorithm(self):
        """Test listing methods for a specific algorithm."""
        methods = list_methods("hanoi")
        
        assert isinstance(methods, list)
        assert len(methods) == 5
        assert all(m in VALID_METHODS for m in methods)

    def test_list_methods_invalid_algorithm(self):
        """Test listing methods for invalid algorithm raises error."""
        with pytest.raises(ValueError, match="Unknown algorithm"):
            list_methods("invalid-algorithm")

    def test_get_benchmark_path_success(self):
        """Test getting benchmark path for valid algorithm/method."""
        path = get_benchmark_path("hanoi", "cpython")
        
        assert isinstance(path, Path)
        assert path.exists()
        assert path.name == "main.py"
        assert "hanoi" in str(path).lower()
        assert "cpython" in str(path).lower()

    def test_get_benchmark_path_invalid_algorithm(self):
        """Test getting path for invalid algorithm raises error."""
        with pytest.raises(ValueError, match="Unknown algorithm"):
            get_benchmark_path("invalid-algorithm", "cpython")

    def test_get_benchmark_path_invalid_method(self):
        """Test getting path for invalid method raises error."""
        with pytest.raises(ValueError, match="Unknown method"):
            get_benchmark_path("hanoi", "invalid-method")

    def test_get_benchmark_path_cython_directory(self):
        """Test getting path for Cython (directory, not file)."""
        path = get_benchmark_path("hanoi", "cython")
        
        assert isinstance(path, Path)
        assert path.exists()
        assert path.is_dir()  # Cython is a directory

    def test_get_benchmark_path_ctypes_directory(self):
        """Test getting path for ctypes (directory, not file)."""
        path = get_benchmark_path("hanoi", "ctypes")
        
        assert isinstance(path, Path)
        assert path.exists()
        assert path.is_dir()  # ctypes is a directory

    def test_validate_algorithm_valid(self):
        """Test validating a valid algorithm."""
        assert validate_algorithm("hanoi") is True
        assert validate_algorithm("binary-trees") is True

    def test_validate_algorithm_invalid(self):
        """Test validating an invalid algorithm."""
        assert validate_algorithm("invalid-algorithm") is False

    def test_validate_method_valid(self):
        """Test validating a valid method for an algorithm."""
        assert validate_method("hanoi", "cpython") is True
        assert validate_method("hanoi", "pypy") is True

    def test_validate_method_invalid_algorithm(self):
        """Test validating method for invalid algorithm."""
        assert validate_method("invalid-algorithm", "cpython") is False

    def test_validate_method_invalid_method(self):
        """Test validating invalid method for valid algorithm."""
        assert validate_method("hanoi", "invalid-method") is False

    def test_benchmark_paths_consistent(self):
        """Test that all benchmark paths in registry are consistent."""
        for algo_name, methods in BENCHMARKS.items():
            for method_name, relative_path in methods.items():
                # Path should be a string
                assert isinstance(relative_path, str)
                # Path should start with algorithm name
                assert algo_name in relative_path.lower() or algo_name.replace("-", "_") in relative_path.lower()
                # Path should contain method name
                assert method_name in relative_path.lower()


class TestBenchmarkRegistryIntegration:
    """Integration tests for benchmark registry."""

    def test_all_algorithms_have_all_methods(self):
        """Test that every algorithm has all 5 methods."""
        algorithms = list_algorithms()
        
        for algo in algorithms:
            methods = list_methods(algo)
            assert len(methods) == 5, f"{algo} should have 5 methods, got {len(methods)}"
            assert set(methods) == set(VALID_METHODS), f"{algo} methods don't match expected"

    def test_all_paths_resolvable(self):
        """Test that all benchmark paths can be resolved."""
        algorithms = list_algorithms()
        
        for algo in algorithms[:3]:  # Test first 3 to avoid too many file operations
            for method in VALID_METHODS:
                try:
                    path = get_benchmark_path(algo, method)
                    assert path.exists(), f"Path should exist: {path}"
                except (ValueError, FileNotFoundError) as e:
                    pytest.fail(f"Failed to resolve path for {algo}/{method}: {e}")

