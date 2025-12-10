"""
Tests for pgsi_analyzer.platform module.

This test suite verifies platform detection, path resolution, and hardware
detection functionality across different operating systems.
"""

import os
import platform
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from pgsi_analyzer.platform import (
    detect_platform,
    is_linux_intel,
    is_windows,
    is_macos,
    is_linux,
    get_user_data_dir,
    resolve_data_path,
    resolve_benchmark_path,
    get_cpu_info,
    get_system_info,
    check_rapl_support,
)


class TestPlatformDetection:
    """Tests for platform detection functions."""

    def test_detect_platform_returns_string(self):
        """Test that detect_platform returns a valid platform string."""
        result = detect_platform()
        assert isinstance(result, str)
        assert result in ("linux", "windows", "macos", "unknown")

    def test_detect_platform_consistency(self):
        """Test that detect_platform is consistent with platform.system()."""
        result = detect_platform()
        system = platform.system().lower()
        
        if system == "linux":
            assert result == "linux"
        elif system == "windows":
            assert result == "windows"
        elif system == "darwin":
            assert result == "macos"

    def test_is_windows(self):
        """Test is_windows function."""
        result = is_windows()
        assert isinstance(result, bool)
        if platform.system().lower() == "windows":
            assert result is True
        else:
            assert result is False

    def test_is_macos(self):
        """Test is_macos function."""
        result = is_macos()
        assert isinstance(result, bool)
        if platform.system().lower() == "darwin":
            assert result is True
        else:
            assert result is False

    def test_is_linux(self):
        """Test is_linux function."""
        result = is_linux()
        assert isinstance(result, bool)
        if platform.system().lower() == "linux":
            assert result is True
        else:
            assert result is False

    def test_is_linux_intel_on_windows(self):
        """Test is_linux_intel returns False on Windows."""
        if platform.system().lower() != "linux":
            assert is_linux_intel() is False

    @patch("pgsi_analyzer.platform.detection.platform")
    def test_is_linux_intel_linux_x86_64(self, mock_platform):
        """Test is_linux_intel returns True on Linux x86_64."""
        mock_platform.system.return_value = "Linux"
        mock_platform.machine.return_value = "x86_64"
        assert is_linux_intel() is True

    @patch("pgsi_analyzer.platform.detection.platform")
    def test_is_linux_intel_linux_amd64(self, mock_platform):
        """Test is_linux_intel returns True on Linux amd64."""
        mock_platform.system.return_value = "Linux"
        mock_platform.machine.return_value = "amd64"
        assert is_linux_intel() is True

    @patch("pgsi_analyzer.platform.detection.platform")
    def test_is_linux_intel_linux_arm(self, mock_platform):
        """Test is_linux_intel returns False on Linux ARM."""
        mock_platform.system.return_value = "Linux"
        mock_platform.machine.return_value = "aarch64"
        assert is_linux_intel() is False


class TestPathResolution:
    """Tests for path resolution functions."""

    def test_get_user_data_dir_returns_path(self):
        """Test that get_user_data_dir returns a Path object."""
        result = get_user_data_dir()
        assert isinstance(result, Path)
        assert "pgsi_analyzer" in str(result)

    def test_get_user_data_dir_platform_specific(self):
        """Test that get_user_data_dir returns platform-specific paths."""
        result = get_user_data_dir()
        
        if os.name == "nt":  # Windows
            assert "AppData" in str(result) or "Roaming" in str(result)
        elif os.name == "posix":  # Linux/macOS
            assert ".local" in str(result) or "share" in str(result)

    def test_resolve_data_path_with_base(self):
        """Test resolve_data_path with explicit base path."""
        base = Path("/custom/path")
        result = resolve_data_path(base=base)
        assert result == base

    def test_resolve_data_path_with_env_var(self):
        """Test resolve_data_path with environment variable."""
        test_path = "/test/data/path"
        with patch.dict(os.environ, {"PGSI_ANALYZER_DATA_DIR": test_path}):
            result = resolve_data_path()
            assert result == Path(test_path)

    @patch("pgsi_analyzer.platform.paths.get_user_data_dir")
    def test_resolve_data_path_default(self, mock_get_user_data_dir):
        """Test resolve_data_path without environment variable."""
        mock_get_user_data_dir.return_value = Path("/test/user/data")
        with patch.dict(os.environ, {}, clear=True):
            # Remove the env var if it exists
            if "PGSI_ANALYZER_DATA_DIR" in os.environ:
                del os.environ["PGSI_ANALYZER_DATA_DIR"]
            result = resolve_data_path()
            assert isinstance(result, Path)
            assert "data" in str(result)
            assert result == Path("/test/user/data") / "data"

    def test_resolve_benchmark_path_default(self):
        """Test resolve_benchmark_path with default behavior."""
        result = resolve_benchmark_path("binary-trees", "cpython")
        assert isinstance(result, Path)
        assert "binary-trees" in str(result)
        assert "cpython" in str(result)

    def test_resolve_benchmark_path_with_env_var(self):
        """Test resolve_benchmark_path with environment variable."""
        test_base = "/benchmarks"
        with patch.dict(os.environ, {"PGSI_ANALYZER_BENCHMARKS_DIR": test_base}):
            result = resolve_benchmark_path("fasta", "pypy")
            assert result == Path(test_base) / "fasta" / "pypy"


class TestHardwareDetection:
    """Tests for hardware detection functions."""

    def test_get_cpu_info_returns_dict(self):
        """Test that get_cpu_info returns a dictionary."""
        result = get_cpu_info()
        assert isinstance(result, dict)
        assert "processor" in result
        assert "cores_physical" in result
        assert "cores_logical" in result
        assert "architecture" in result

    def test_get_cpu_info_has_valid_values(self):
        """Test that get_cpu_info returns valid values."""
        result = get_cpu_info()
        assert isinstance(result["processor"], str)
        assert isinstance(result["cores_physical"], int)
        assert isinstance(result["cores_logical"], int)
        assert result["cores_physical"] >= 0
        assert result["cores_logical"] >= 0

    def test_get_system_info_returns_dict(self):
        """Test that get_system_info returns a dictionary."""
        result = get_system_info()
        assert isinstance(result, dict)
        assert "CPU" in result
        assert "RAM_GB" in result
        assert "OS" in result
        assert "Architecture" in result
        assert "Platform" in result

    def test_get_system_info_with_path_string(self):
        """Test get_system_info with string path."""
        test_path = "test_results.csv"
        result = get_system_info(test_path)
        assert result["Test_Result_File"] == test_path

    def test_get_system_info_with_path_object(self):
        """Test get_system_info with Path object."""
        test_path = Path("test_results.csv")
        result = get_system_info(test_path)
        assert result["Test_Result_File"] == str(test_path)

    def test_get_system_info_ram_positive(self):
        """Test that RAM_GB is a positive number."""
        result = get_system_info()
        assert isinstance(result["RAM_GB"], (int, float))
        assert result["RAM_GB"] > 0

    def test_check_rapl_support_returns_bool(self):
        """Test that check_rapl_support returns a boolean."""
        result = check_rapl_support()
        assert isinstance(result, bool)

    @patch("pgsi_analyzer.platform.hardware.is_linux_intel")
    def test_check_rapl_support_non_linux(self, mock_is_linux_intel):
        """Test check_rapl_support returns False on non-Linux systems."""
        mock_is_linux_intel.return_value = False
        assert check_rapl_support() is False

    @patch("pgsi_analyzer.platform.hardware.is_linux_intel")
    @patch("builtins.__import__")
    def test_check_rapl_support_linux_with_pyrapl(self, mock_import, mock_is_linux_intel):
        """Test check_rapl_support returns True on Linux with pyRAPL."""
        mock_is_linux_intel.return_value = True
        # Mock pyRAPL import
        mock_pyrapl = MagicMock()
        mock_pyrapl.setup.return_value = None
        mock_import.return_value = mock_pyrapl
        assert check_rapl_support() is True

    @patch("pgsi_analyzer.platform.hardware.is_linux_intel")
    def test_check_rapl_support_import_error(self, mock_is_linux_intel):
        """Test check_rapl_support handles ImportError gracefully."""
        mock_is_linux_intel.return_value = True
        with patch("builtins.__import__", side_effect=ImportError("No module named 'pyRAPL'")):
            assert check_rapl_support() is False


class TestIntegration:
    """Integration tests for platform module."""

    def test_platform_module_imports(self):
        """Test that all platform module functions can be imported."""
        from pgsi_analyzer.platform import (
            detect_platform,
            is_linux_intel,
            is_windows,
            is_macos,
            get_user_data_dir,
            resolve_data_path,
            resolve_benchmark_path,
            get_cpu_info,
            get_system_info,
            check_rapl_support,
        )
        # If we get here, imports succeeded
        assert True

    def test_path_operations_use_pathlib(self):
        """Test that path functions return Path objects."""
        data_dir = get_user_data_dir()
        data_path = resolve_data_path()
        benchmark_path = resolve_benchmark_path("test", "method")
        
        assert isinstance(data_dir, Path)
        assert isinstance(data_path, Path)
        assert isinstance(benchmark_path, Path)

    def test_system_info_completeness(self):
        """Test that system info contains all expected fields."""
        info = get_system_info(Path("test.csv"))
        required_fields = [
            "CPU", "RAM_GB", "OS", "Architecture",
            "Test_Result_File", "Platform", "Cores_Physical", "Cores_Logical"
        ]
        for field in required_fields:
            assert field in info, f"Missing field: {field}"

