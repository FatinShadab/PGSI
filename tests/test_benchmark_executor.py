"""
Tests for benchmark executor module.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from pgsi_analyzer.benchmark.executor import (
    find_python_executable,
    prepare_py_compile,
    execute_benchmark,
)
from pgsi_analyzer.utils import MeasurementError, PlatformError


class TestFindPythonExecutable:
    """Test find_python_executable function."""

    def test_find_cpython(self):
        """Test finding CPython executable."""
        exe = find_python_executable("cpython")
        assert exe == sys.executable

    def test_find_pypy_success(self):
        """Test finding PyPy executable when available."""
        from pgsi_analyzer.config import ToolPaths
        
        pypy_path = Path("/usr/bin/pypy3")
        tool_paths = ToolPaths(
            python=Path(sys.executable),
            pypy=pypy_path,
        )
        
        exe = find_python_executable("pypy", tool_paths=tool_paths)
        assert exe == str(pypy_path)

    @patch('shutil.which')
    def test_find_pypy_not_found(self, mock_which):
        """Test finding PyPy when not available raises error."""
        mock_which.return_value = None
        
        with pytest.raises(PlatformError, match="PyPy method selected but no valid PyPy executable found"):
            find_python_executable("pypy")

    def test_find_cython(self):
        """Test finding executable for Cython (uses CPython)."""
        exe = find_python_executable("cython")
        assert exe == sys.executable

    def test_find_ctypes(self):
        """Test finding executable for ctypes (uses CPython)."""
        exe = find_python_executable("ctypes")
        assert exe == sys.executable

    def test_find_py_compile(self):
        """Test finding executable for py_compile (uses CPython)."""
        exe = find_python_executable("py_compile")
        assert exe == sys.executable

    def test_find_invalid_method(self):
        """Test finding executable for invalid method raises error."""
        with pytest.raises(ValueError, match="Unknown execution method"):
            find_python_executable("invalid")


class TestPreparePyCompile:
    """Test prepare_py_compile function."""

    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_prepare_py_compile_success(self, mock_exists, mock_run):
        """Test successful py_compile preparation."""
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0)
        
        benchmark_path = Path("/test/benchmark")
        benchmark_path.mkdir(parents=True, exist_ok=True)
        (benchmark_path / "main.py").touch()
        
        with patch('pathlib.Path.is_dir', return_value=True):
            result = prepare_py_compile(benchmark_path)
            assert result == benchmark_path / "main.py"  # Falls back to .py if no .pyc found

    @patch('pathlib.Path.exists')
    def test_prepare_py_compile_no_main_py(self, mock_exists):
        """Test py_compile preparation fails when main.py missing."""
        mock_exists.return_value = False
        
        benchmark_path = Path("/test/benchmark")
        
        with pytest.raises(FileNotFoundError, match="main.py not found"):
            prepare_py_compile(benchmark_path)


class TestExecuteBenchmark:
    """Test execute_benchmark function."""

    @patch('pgsi_analyzer.benchmark.executor.find_python_executable')
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.glob')
    def test_execute_benchmark_cpython_success(
        self, mock_glob, mock_iterdir, mock_isdir, mock_isfile,
        mock_exists, mock_run, mock_find_exe
    ):
        """Test successful CPython benchmark execution."""
        # Setup mocks
        mock_find_exe.return_value = sys.executable
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        mock_isfile.return_value = True
        mock_isdir.return_value = False
        mock_exists.return_value = True
        
        # Mock CSV discovery
        mock_iterdir.return_value = [
            MagicMock(name="energy_benchmark", is_dir=lambda: True),
            MagicMock(name="time_benchmark", is_dir=lambda: True),
        ]
        
        # Mock glob to return CSV files
        def mock_glob_side_effect(pattern):
            if "energy_benchmark" in str(pattern):
                return [Path("/test/energy_benchmark/hanoi_cpython.csv")]
            elif "time_benchmark" in str(pattern):
                return [Path("/test/time_benchmark/hanoi_cpython.csv")]
            return []
        
        mock_glob.side_effect = mock_glob_side_effect
        
        # Mock pandas read_csv
        with patch('pandas.read_csv') as mock_read_csv:
            mock_read_csv.return_value = MagicMock(columns=['package (uJ)'])
            
            benchmark_path = Path("/test/benchmark/main.py")
            results = execute_benchmark(
                algorithm="hanoi",
                method="cpython",
                benchmark_path=benchmark_path,
                runs=5,
            )
            
            assert "energy_csv" in results
            assert "time_csv" in results
            mock_run.assert_called_once()

    @patch('pgsi_analyzer.benchmark.executor.find_python_executable')
    @patch('subprocess.run')
    def test_execute_benchmark_execution_fails(self, mock_run, mock_find_exe):
        """Test benchmark execution failure handling."""
        mock_find_exe.return_value = sys.executable
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="error",
            stderr="failed"
        )
        
        benchmark_path = Path("/test/benchmark/main.py")
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.is_file', return_value=True):
                with pytest.raises(MeasurementError, match="Benchmark execution failed"):
                    execute_benchmark(
                        algorithm="hanoi",
                        method="cpython",
                        benchmark_path=benchmark_path,
                        runs=5,
                    )

    @patch('pgsi_analyzer.benchmark.executor.find_python_executable')
    @patch('subprocess.run')
    def test_execute_benchmark_timeout(self, mock_run, mock_find_exe):
        """Test benchmark execution timeout handling."""
        import subprocess
        mock_find_exe.return_value = sys.executable
        mock_run.side_effect = subprocess.TimeoutExpired("python", 3600)
        
        benchmark_path = Path("/test/benchmark/main.py")
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.is_file', return_value=True):
                with pytest.raises(MeasurementError, match="timed out"):
                    execute_benchmark(
                        algorithm="hanoi",
                        method="cpython",
                        benchmark_path=benchmark_path,
                        runs=5,
                    )

    @patch('pathlib.Path.exists')
    def test_execute_benchmark_no_main_py(self, mock_exists):
        """Test execution fails when main.py not found."""
        mock_exists.return_value = False
        
        benchmark_path = Path("/test/benchmark")
        
        with pytest.raises(FileNotFoundError, match="Could not find main.py"):
            execute_benchmark(
                algorithm="hanoi",
                method="cpython",
                benchmark_path=benchmark_path,
                runs=5,
            )

