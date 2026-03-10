"""
Tests for benchmark executor module.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from pgsi_analyzer.config import ToolPaths
from pgsi_analyzer.benchmark.executor import (
    find_python_executable,
    prepare_py_compile,
    execute_benchmark,
    AUDIT_LOG_FILENAME,
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
    def test_prepare_py_compile_success(self, mock_exists, mock_run, tmp_path):
        """Test successful py_compile preparation."""
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0)
        benchmark_path = tmp_path / "benchmark"
        benchmark_path.mkdir(parents=True, exist_ok=True)
        (benchmark_path / "main.py").touch()
        (benchmark_path / "__pycache__").mkdir(exist_ok=True)  # so glob("main*.pyc") runs without FileNotFoundError
        with patch('pathlib.Path.is_dir', return_value=True):
            result = prepare_py_compile(benchmark_path)
            assert result == benchmark_path / "main.py"  # Falls back to .py if no .pyc found

    @patch('pathlib.Path.exists')
    def test_prepare_py_compile_no_main_py(self, mock_exists, tmp_path):
        """Test py_compile preparation fails when main.py missing."""
        mock_exists.return_value = False
        benchmark_path = tmp_path / "benchmark"
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
        mock_exists, mock_run, mock_find_exe, tmp_path
    ):
        """Test successful CPython benchmark execution."""
        mock_find_exe.return_value = sys.executable
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        mock_isfile.return_value = True
        mock_isdir.return_value = False
        mock_exists.return_value = True
        mock_iterdir.return_value = [
            MagicMock(name="energy_benchmark", is_dir=lambda: True),
            MagicMock(name="time_benchmark", is_dir=lambda: True),
        ]
        (tmp_path / "energy_benchmark").mkdir()
        (tmp_path / "time_benchmark").mkdir()
        (tmp_path / "energy_benchmark" / "energy_hanoi_cpython.csv").touch()
        (tmp_path / "time_benchmark" / "time_hanoi_cpython.csv").touch()

        def mock_glob_side_effect(pattern):
            if "energy_benchmark" in str(pattern) or "energy_" in str(pattern):
                return [tmp_path / "energy_benchmark" / "energy_hanoi_cpython.csv"]
            if "time_benchmark" in str(pattern) or "time_" in str(pattern):
                return [tmp_path / "time_benchmark" / "time_hanoi_cpython.csv"]
            return []
        mock_glob.side_effect = mock_glob_side_effect

        with patch('pandas.read_csv') as mock_read_csv:
            mock_read_csv.return_value = MagicMock(columns=['package (uJ)'])
            benchmark_path = tmp_path / "benchmark" / "main.py"
            benchmark_path.parent.mkdir(parents=True)
            benchmark_path.touch()
            output_dir = tmp_path / "results"
            results = execute_benchmark(
                algorithm="hanoi",
                method="cpython",
                benchmark_path=benchmark_path,
                runs=5,
                output_dir=output_dir,
            )
            assert "energy_csv" in results
            assert "time_csv" in results
            mock_run.assert_called_once()

    @patch('pgsi_analyzer.benchmark.executor.find_python_executable')
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.glob')
    def test_execute_benchmark_sets_pgsi_runs_in_env(
        self, mock_glob, mock_iterdir, mock_isdir, mock_isfile,
        mock_exists, mock_run, mock_find_exe, tmp_path
    ):
        """Executor must set PGSI_RUNS in subprocess env so benchmark scripts use the run count."""
        mock_find_exe.return_value = sys.executable
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        mock_isfile.return_value = True
        mock_isdir.return_value = False
        mock_exists.return_value = True
        mock_iterdir.return_value = [
            MagicMock(name="energy_benchmark", is_dir=lambda: True),
            MagicMock(name="time_benchmark", is_dir=lambda: True),
        ]
        (tmp_path / "energy_benchmark").mkdir()
        (tmp_path / "time_benchmark").mkdir()
        (tmp_path / "energy_benchmark" / "energy_hanoi_cpython.csv").touch()
        (tmp_path / "time_benchmark" / "time_hanoi_cpython.csv").touch()

        def mock_glob_side_effect(pattern):
            if "energy_benchmark" in str(pattern) or "energy_" in str(pattern):
                return [tmp_path / "energy_benchmark" / "energy_hanoi_cpython.csv"]
            if "time_benchmark" in str(pattern) or "time_" in str(pattern):
                return [tmp_path / "time_benchmark" / "time_hanoi_cpython.csv"]
            return []
        mock_glob.side_effect = mock_glob_side_effect

        with patch('pandas.read_csv') as mock_read_csv:
            mock_read_csv.return_value = MagicMock(columns=['package (uJ)'])
            benchmark_path = tmp_path / "benchmark" / "main.py"
            benchmark_path.parent.mkdir(parents=True)
            benchmark_path.touch()
            output_dir = tmp_path / "results"
            execute_benchmark(
                algorithm="hanoi",
                method="cpython",
                benchmark_path=benchmark_path,
                runs=7,
                output_dir=output_dir,
            )
            mock_run.assert_called_once()
            call_env = mock_run.call_args[1]["env"]
            assert call_env.get("PGSI_RUNS") == "7"

    @patch('pgsi_analyzer.benchmark.executor.find_python_executable')
    @patch('subprocess.run')
    def test_execute_benchmark_execution_fails(self, mock_run, mock_find_exe, tmp_path):
        """Test benchmark execution failure handling."""
        mock_find_exe.return_value = sys.executable
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="error",
            stderr="failed"
        )
        benchmark_path = tmp_path / "benchmark" / "main.py"
        benchmark_path.parent.mkdir(parents=True)
        benchmark_path.touch()
        output_dir = tmp_path / "results"
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.is_file', return_value=True):
                with pytest.raises(MeasurementError, match="Benchmark execution failed"):
                    execute_benchmark(
                        algorithm="hanoi",
                        method="cpython",
                        benchmark_path=benchmark_path,
                        runs=5,
                        output_dir=output_dir,
                    )

    @patch('pgsi_analyzer.benchmark.executor.find_python_executable')
    @patch('subprocess.run')
    def test_execute_benchmark_timeout(self, mock_run, mock_find_exe, tmp_path):
        """Test benchmark execution timeout handling."""
        import subprocess
        mock_find_exe.return_value = sys.executable
        mock_run.side_effect = subprocess.TimeoutExpired("python", 3600)
        benchmark_path = tmp_path / "benchmark" / "main.py"
        benchmark_path.parent.mkdir(parents=True)
        benchmark_path.touch()
        output_dir = tmp_path / "results"
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.is_file', return_value=True):
                with pytest.raises(MeasurementError, match="timed out"):
                    execute_benchmark(
                        algorithm="hanoi",
                        method="cpython",
                        benchmark_path=benchmark_path,
                        runs=5,
                        output_dir=output_dir,
                    )

    @patch('pathlib.Path.exists')
    def test_execute_benchmark_no_main_py(self, mock_exists, tmp_path):
        """Test execution fails when main.py not found."""
        mock_exists.return_value = False
        benchmark_path = tmp_path / "benchmark"
        with pytest.raises(FileNotFoundError, match="Could not find main.py"):
            execute_benchmark(
                algorithm="hanoi",
                method="cpython",
                benchmark_path=benchmark_path,
                runs=5,
            )

    @patch('pgsi_analyzer.benchmark.executor.find_python_executable')
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.glob')
    def test_execute_benchmark_uses_tool_paths_in_subprocess(
        self, mock_glob, mock_iterdir, mock_isdir, mock_isfile,
        mock_exists, mock_run, mock_find_exe, tmp_path
    ):
        """Executor must use interpreter from tool_paths (e.g. from .env) in subprocess.run."""
        fake_python = "/opt/fake/env/bin/python3"
        tool_paths = ToolPaths(python=Path(fake_python), pypy=None, c_compiler=None)
        mock_find_exe.return_value = fake_python
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        mock_isfile.return_value = True
        mock_isdir.return_value = False
        mock_exists.return_value = True
        mock_iterdir.return_value = [
            MagicMock(name="energy_benchmark", is_dir=lambda: True),
            MagicMock(name="time_benchmark", is_dir=lambda: True),
        ]

        def mock_glob_side_effect(pattern):
            if "energy_benchmark" in str(pattern):
                return [tmp_path / "energy_benchmark/hanoi_cpython.csv"]
            if "time_benchmark" in str(pattern):
                return [tmp_path / "time_benchmark/hanoi_cpython.csv"]
            return []

        mock_glob.side_effect = mock_glob_side_effect

        with patch('pandas.read_csv') as mock_read_csv:
            mock_read_csv.return_value = MagicMock(columns=['package (uJ)'])

            benchmark_path = tmp_path / "benchmark" / "main.py"
            benchmark_path.parent.mkdir(parents=True)
            benchmark_path.touch()
            output_dir = tmp_path / "results"
            execute_benchmark(
                algorithm="hanoi",
                method="cpython",
                benchmark_path=benchmark_path,
                runs=3,
                output_dir=output_dir,
                tool_paths=tool_paths,
            )

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == fake_python, "subprocess.run must be invoked with interpreter from tool_paths (e.g. from .env)"

    @patch('pgsi_analyzer.benchmark.executor.find_python_executable')
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.glob')
    def test_execute_benchmark_writes_audit_log_with_interpreter_path(
        self, mock_glob, mock_iterdir, mock_isdir, mock_isfile,
        mock_exists, mock_run, mock_find_exe, tmp_path
    ):
        """After every run a .audit.log exists and shows the absolute path of the Python interpreter (cpython/pypy)."""
        fake_python = "/usr/bin/pypy3"
        mock_find_exe.return_value = fake_python
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        mock_isfile.return_value = True
        mock_isdir.return_value = False
        mock_exists.return_value = True
        mock_iterdir.return_value = [
            MagicMock(name="energy_benchmark", is_dir=lambda: True),
            MagicMock(name="time_benchmark", is_dir=lambda: True),
        ]

        def mock_glob_side_effect(pattern):
            if "energy_benchmark" in str(pattern):
                return [tmp_path / "energy_benchmark/hanoi_pypy.csv"]
            if "time_benchmark" in str(pattern):
                return [tmp_path / "time_benchmark/hanoi_pypy.csv"]
            return []

        mock_glob.side_effect = mock_glob_side_effect
        (tmp_path / "energy_benchmark").mkdir()
        (tmp_path / "time_benchmark").mkdir()
        (tmp_path / "energy_benchmark/hanoi_pypy.csv").touch()
        (tmp_path / "time_benchmark/hanoi_pypy.csv").touch()

        with patch('pandas.read_csv') as mock_read_csv:
            mock_read_csv.return_value = MagicMock(columns=['package (uJ)'])

            benchmark_path = tmp_path / "benchmark" / "main.py"
            benchmark_path.parent.mkdir(parents=True)
            benchmark_path.touch()
            output_dir = tmp_path / "results"
            execute_benchmark(
                algorithm="hanoi",
                method="pypy",
                benchmark_path=benchmark_path,
                runs=2,
                output_dir=output_dir,
            )

        audit_log = output_dir / AUDIT_LOG_FILENAME
        assert audit_log.exists(), ".audit.log must exist after a run"
        content = audit_log.read_text()
        assert "interpreter_absolute:" in content
        assert fake_python in content or "pypy" in content
        assert "exec_args:" in content
        assert "PGSI_RUNS" in content

