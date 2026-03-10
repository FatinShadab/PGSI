"""
Tests for benchmark builder module.
"""

import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from pgsi_analyzer.benchmark.builder import (
    requires_build,
    build_cython,
    build_ctypes,
    build_benchmark,
)
from pgsi_analyzer.utils import ConfigurationError, PlatformError


class TestRequiresBuild:
    """Test requires_build function."""

    def test_cython_requires_build(self):
        """Test that Cython requires build."""
        assert requires_build("cython") is True

    def test_ctypes_requires_build(self):
        """Test that ctypes requires build."""
        assert requires_build("ctypes") is True

    def test_cpython_no_build(self):
        """Test that CPython doesn't require build."""
        assert requires_build("cpython") is False

    def test_pypy_no_build(self):
        """Test that PyPy doesn't require build."""
        assert requires_build("pypy") is False

    def test_py_compile_no_build(self):
        """Test that py_compile doesn't require build."""
        assert requires_build("py_compile") is False


class TestBuildCython:
    """Test Cython build functionality."""

    @patch('os.chdir')
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.cwd')
    def test_build_cython_success(self, mock_cwd, mock_exists, mock_run, mock_chdir):
        """Test successful Cython build."""
        # Setup mocks
        mock_exists.return_value = True
        mock_cwd.return_value = Path.cwd()  # Use real current directory
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        
        benchmark_path = Path("/test/benchmark")
        result = build_cython(benchmark_path)
        
        assert result == benchmark_path
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "setup.py" in args
        assert "build_ext" in args
        assert "--inplace" in args

    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_build_cython_no_setup_py(self, mock_exists, mock_run):
        """Test Cython build fails when setup.py is missing."""
        mock_exists.return_value = False
        
        benchmark_path = Path("/test/benchmark")
        
        with pytest.raises(ConfigurationError, match="setup.py not found"):
            build_cython(benchmark_path)

    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_build_cython_build_fails(self, mock_exists, mock_run):
        """Test Cython build failure handling."""
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="error output",
            stderr="build failed"
        )
        
        benchmark_path = Path("/test/benchmark")
        
        with pytest.raises(ConfigurationError, match="Cython build failed"):
            build_cython(benchmark_path)

    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_build_cython_timeout(self, mock_exists, mock_run):
        """Test Cython build timeout handling."""
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired("setup.py", 300)
        
        benchmark_path = Path("/test/benchmark")
        
        with pytest.raises(ConfigurationError, match="timed out"):
            build_cython(benchmark_path)


class TestBuildCtypes:
    """Test ctypes build functionality."""

    @patch('subprocess.run')
    @patch('pathlib.Path.stat')
    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.exists')
    @patch('platform.system')
    def test_build_ctypes_success_linux(self, mock_system, mock_exists, mock_glob, mock_stat, mock_run):
        """Test successful ctypes build on Linux."""
        mock_system.return_value = "Linux"
        mock_glob.return_value = [Path("/test/benchmark/test.c")]
        
        # Mock stat for .c files
        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mtime = 1000
        mock_stat.return_value = mock_stat_obj
        
        # Mock exists: library doesn't exist initially, then exists after compilation
        exists_calls = []
        def exists_side_effect(*args, **kwargs):
            # When Path.exists() is called, the Path object is 'self', not passed as arg
            # But when mocked, we need to get the Path from the mock's call
            # We'll track by checking the call count
            exists_calls.append(len(exists_calls))
            # First call: library doesn't exist (before compilation)
            if len(exists_calls) == 1:
                return False
            # Subsequent calls: library exists (after compilation)
            return True
        
        mock_exists.side_effect = exists_side_effect
        mock_run.return_value = MagicMock(returncode=0)
        
        benchmark_path = Path("/test/benchmark")
        result = build_ctypes(benchmark_path)
        
        assert result == benchmark_path
        # Verify compilation was called
        assert mock_run.call_count >= 1
        # Find the compilation call (not the gcc --version check)
        compile_calls = [c for c in mock_run.call_args_list if len(c[0][0]) > 0 and 'gcc' in str(c[0][0][0]) and '--version' not in str(c[0][0])]
        if not compile_calls:
            # If no compile calls found, check all calls
            compile_calls = [c for c in mock_run.call_args_list if len(c[0][0]) > 0 and 'gcc' in str(c[0][0][0])]
        assert len(compile_calls) > 0
        args = compile_calls[0][0][0]
        assert "gcc" in args
        assert "-shared" in args
        assert "-fPIC" in args

    @patch('subprocess.run')
    @patch('pathlib.Path.stat')
    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.exists')
    @patch('platform.system')
    def test_build_ctypes_success_windows(self, mock_system, mock_exists, mock_glob, mock_stat, mock_run):
        """Test successful ctypes build on Windows."""
        mock_system.return_value = "Windows"
        mock_glob.return_value = [Path("/test/benchmark/test.c")]
        
        # Mock stat for .c files
        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mtime = 1000
        mock_stat.return_value = mock_stat_obj
        
        # Mock exists: library doesn't exist initially, then exists after compilation
        exists_calls = []
        def exists_side_effect(*args, **kwargs):
            # When Path.exists() is called, the Path object is 'self', not passed as arg
            # But when mocked, we need to get the Path from the mock's call
            # We'll track by checking the call count
            exists_calls.append(len(exists_calls))
            # First call: library doesn't exist (before compilation)
            if len(exists_calls) == 1:
                return False
            # Subsequent calls: library exists (after compilation)
            return True
        
        mock_exists.side_effect = exists_side_effect
        mock_run.return_value = MagicMock(returncode=0)
        
        benchmark_path = Path("/test/benchmark")
        result = build_ctypes(benchmark_path)
        
        assert result == benchmark_path
        # Verify compilation was called
        assert mock_run.call_count >= 1
        # Find the compilation call (not the gcc --version check)
        compile_calls = [c for c in mock_run.call_args_list if len(c[0][0]) > 0 and 'gcc' in str(c[0][0][0]) and '--version' not in str(c[0][0])]
        if not compile_calls:
            # If no compile calls found, check all calls
            compile_calls = [c for c in mock_run.call_args_list if len(c[0][0]) > 0 and 'gcc' in str(c[0][0][0])]
        assert len(compile_calls) > 0
        args = compile_calls[0][0][0]
        assert "gcc" in args

    @patch('pathlib.Path.glob')
    def test_build_ctypes_no_c_files(self, mock_glob):
        """Test ctypes build fails when no .c files found."""
        mock_glob.return_value = []
        
        benchmark_path = Path("/test/benchmark")
        
        with pytest.raises(ConfigurationError, match="No .c files found"):
            build_ctypes(benchmark_path)

    @patch('subprocess.run')
    @patch('pathlib.Path.stat')
    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.exists')
    @patch('platform.system')
    def test_build_ctypes_compiler_not_found(self, mock_system, mock_exists, mock_glob, mock_stat, mock_run):
        """Test ctypes build fails when compiler not found."""
        mock_system.return_value = "Linux"
        mock_exists.return_value = False
        mock_glob.return_value = [Path("/test/benchmark/test.c")]
        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mtime = 1000
        mock_stat.return_value = mock_stat_obj
        mock_run.side_effect = FileNotFoundError("gcc not found")
        
        benchmark_path = Path("/test/benchmark")
        
        with pytest.raises(PlatformError, match="C compiler.*not found"):
            build_ctypes(benchmark_path)

    @patch('subprocess.run')
    @patch('pathlib.Path.stat')
    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.exists')
    @patch('platform.system')
    def test_build_ctypes_compilation_fails(self, mock_system, mock_exists, mock_glob, mock_stat, mock_run):
        """Test ctypes build failure handling."""
        mock_system.return_value = "Linux"
        mock_exists.return_value = False
        mock_glob.return_value = [Path("/test/benchmark/test.c")]
        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mtime = 1000
        mock_stat.return_value = mock_stat_obj
        
        # First call (gcc check) succeeds, second call (compile) fails
        def run_side_effect(*args, **kwargs):
            if '--version' in args[0] or args[0][0] == 'gcc' and '--version' in str(args[0]):
                return MagicMock(returncode=0)
            return MagicMock(returncode=1, stdout="", stderr="compile error")
        
        mock_run.side_effect = run_side_effect
        
        benchmark_path = Path("/test/benchmark")
        
        with pytest.raises(ConfigurationError, match="ctypes compilation failed"):
            build_ctypes(benchmark_path)


class TestBuildBenchmark:
    """Test build_benchmark function."""

    @patch('pgsi_analyzer.benchmark.builder.build_cython')
    def test_build_benchmark_cython(self, mock_build_cython):
        """Test building Cython benchmark."""
        mock_build_cython.return_value = Path("/test/benchmark")
        
        result = build_benchmark("hanoi", "cython", Path("/test/benchmark"))
        
        assert result == Path("/test/benchmark")
        # build_cython is called with just benchmark_path (build_dir defaults to None)
        mock_build_cython.assert_called_once()
        assert mock_build_cython.call_args[0][0] == Path("/test/benchmark")

    @patch('pgsi_analyzer.benchmark.builder.build_ctypes')
    def test_build_benchmark_ctypes(self, mock_build_ctypes):
        """Test building ctypes benchmark."""
        mock_build_ctypes.return_value = Path("/test/benchmark")
        
        result = build_benchmark("hanoi", "ctypes", Path("/test/benchmark"))
        
        assert result == Path("/test/benchmark")
        # build_ctypes is called with just benchmark_path (build_dir defaults to None)
        mock_build_ctypes.assert_called_once()
        assert mock_build_ctypes.call_args[0][0] == Path("/test/benchmark")

    def test_build_benchmark_no_build_needed(self):
        """Test that methods not requiring build return path unchanged."""
        benchmark_path = Path("/test/benchmark")
        
        for method in ["cpython", "pypy", "py_compile"]:
            result = build_benchmark("hanoi", method, benchmark_path)
            assert result == benchmark_path

    def test_build_benchmark_invalid_method(self):
        """Test building with invalid method raises error."""
        # Invalid method that requires build but isn't recognized
        # Since requires_build("invalid") returns False, it won't try to build
        # So we need to test a method that requires build but has invalid build logic
        # Actually, if method doesn't require build, it just returns the path
        # So we test with a method that requires build but has no handler
        with patch('pgsi_analyzer.benchmark.builder.requires_build', return_value=True):
            with pytest.raises((ValueError, KeyError), match="Unknown|invalid"):
                build_benchmark("hanoi", "invalid", Path("/test/benchmark"))

