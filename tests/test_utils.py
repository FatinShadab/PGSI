"""
Tests for pgsi_analyzer.utils module.

This test suite verifies error handling and validation functions.
"""

import pytest
import pandas as pd
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from pgsi_analyzer.utils import (
    validate_file_path,
    validate_dataframe,
    validate_weights,
    validate_platform,
    require_columns,
    PGSIAnalyzerError,
    MeasurementError,
    AnalysisError,
    PlatformError,
    ConfigurationError,
)


class TestErrorHierarchy:
    """Tests for custom exception classes."""

    def test_pgsi_analyzer_error_is_base(self):
        """Test that PGSIAnalyzerError is the base exception."""
        assert issubclass(MeasurementError, PGSIAnalyzerError)
        assert issubclass(AnalysisError, PGSIAnalyzerError)
        assert issubclass(PlatformError, PGSIAnalyzerError)
        assert issubclass(ConfigurationError, PGSIAnalyzerError)

    def test_measurement_error_raises(self):
        """Test that MeasurementError can be raised."""
        with pytest.raises(MeasurementError):
            raise MeasurementError("Test error")

    def test_analysis_error_raises(self):
        """Test that AnalysisError can be raised."""
        with pytest.raises(AnalysisError):
            raise AnalysisError("Test error")

    def test_platform_error_raises(self):
        """Test that PlatformError can be raised."""
        with pytest.raises(PlatformError):
            raise PlatformError("Test error")

    def test_configuration_error_raises(self):
        """Test that ConfigurationError can be raised."""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Test error")


class TestValidateFilePath:
    """Tests for validate_file_path function."""

    def test_validate_file_path_exists(self):
        """Test validation of existing file path."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")
            
            result = validate_file_path(test_file, must_exist=True)
            assert isinstance(result, Path)
            assert result == test_file

    def test_validate_file_path_string(self):
        """Test validation with string path."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")
            
            result = validate_file_path(str(test_file), must_exist=True)
            assert isinstance(result, Path)
            assert result == test_file

    def test_validate_file_path_missing_raises(self):
        """Test that missing file raises ConfigurationError."""
        with TemporaryDirectory() as tmpdir:
            missing_file = Path(tmpdir) / "nonexistent.txt"
            
            with pytest.raises(ConfigurationError, match="File not found"):
                validate_file_path(missing_file, must_exist=True)

    def test_validate_file_path_not_required(self):
        """Test that validation passes when must_exist=False."""
        missing_file = Path("/nonexistent/path/file.txt")
        
        result = validate_file_path(missing_file, must_exist=False)
        assert isinstance(result, Path)
        assert result == missing_file


class TestValidateDataFrame:
    """Tests for validate_dataframe function."""

    def test_validate_dataframe_success(self):
        """Test validation of DataFrame with required columns."""
        df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': [4, 5, 6],
            'col3': [7, 8, 9],
        })
        
        # Should not raise
        validate_dataframe(df, ['col1', 'col2'])

    def test_validate_dataframe_missing_column(self):
        """Test that missing column raises AnalysisError."""
        df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': [4, 5, 6],
        })
        
        with pytest.raises(AnalysisError, match="Missing required columns"):
            validate_dataframe(df, ['col1', 'col3'])

    def test_validate_dataframe_multiple_missing(self):
        """Test that multiple missing columns are reported."""
        df = pd.DataFrame({
            'col1': [1, 2, 3],
        })
        
        with pytest.raises(AnalysisError, match="Missing required columns"):
            validate_dataframe(df, ['col1', 'col2', 'col3'])


class TestValidateWeights:
    """Tests for validate_weights function."""

    def test_validate_weights_success(self):
        """Test validation of weights that sum to 1.0."""
        # Should not raise
        validate_weights(0.4, 0.4, 0.2)

    def test_validate_weights_not_one_raises(self):
        """Test that weights not summing to 1.0 raise AnalysisError."""
        with pytest.raises(AnalysisError, match="Weights must sum to 1.0"):
            validate_weights(0.5, 0.5, 0.5)

    def test_validate_weights_close_to_one(self):
        """Test that weights close to 1.0 (within tolerance) pass."""
        # Should not raise (within 1e-6 tolerance)
        validate_weights(0.4, 0.4, 0.2 + 1e-7)

    def test_validate_weights_zero(self):
        """Test that zero weights are valid if they sum to 1.0."""
        validate_weights(1.0, 0.0, 0.0)


class TestValidatePlatform:
    """Tests for validate_platform function."""

    def test_validate_platform_no_requirement(self):
        """Test validation without platform requirement."""
        # Should not raise
        validate_platform(require_linux_intel=False)

    @patch('pgsi_analyzer.utils.validation.is_linux_intel')
    @patch('pgsi_analyzer.utils.validation.detect_platform')
    def test_validate_platform_linux_intel_required_success(self, mock_detect, mock_is_linux):
        """Test validation when Linux Intel is required and available."""
        mock_detect.return_value = 'linux'
        mock_is_linux.return_value = True
        
        # Should not raise
        validate_platform(require_linux_intel=True)

    @patch('pgsi_analyzer.utils.validation.is_linux_intel')
    @patch('pgsi_analyzer.utils.validation.detect_platform')
    def test_validate_platform_linux_intel_required_failure(self, mock_detect, mock_is_linux):
        """Test validation when Linux Intel is required but not available."""
        mock_detect.return_value = 'windows'
        mock_is_linux.return_value = False
        
        with pytest.raises(PlatformError, match="Linux x86_64 required"):
            validate_platform(require_linux_intel=True)


class TestRequireColumns:
    """Tests for require_columns function."""

    def test_require_columns_success(self):
        """Test that require_columns works like validate_dataframe."""
        df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': [4, 5, 6],
        })
        
        # Should not raise
        require_columns(df, ['col1', 'col2'])

    def test_require_columns_missing(self):
        """Test that require_columns raises on missing columns."""
        df = pd.DataFrame({
            'col1': [1, 2, 3],
        })
        
        with pytest.raises(AnalysisError, match="Missing required columns"):
            require_columns(df, ['col1', 'col2'])


class TestUtilsIntegration:
    """Integration tests for utils module."""

    def test_all_exports_available(self):
        """Test that all expected exports are available."""
        from pgsi_analyzer.utils import (
            validate_file_path,
            validate_dataframe,
            validate_weights,
            validate_platform,
            require_columns,
            PGSIAnalyzerError,
            MeasurementError,
            AnalysisError,
            PlatformError,
            ConfigurationError,
        )
        # If we get here, all imports succeeded
        assert True

    def test_error_inheritance_chain(self):
        """Test that error inheritance chain is correct."""
        # All specific errors should be instances of base error
        assert isinstance(MeasurementError("test"), PGSIAnalyzerError)
        assert isinstance(AnalysisError("test"), PGSIAnalyzerError)
        assert isinstance(PlatformError("test"), PGSIAnalyzerError)
        assert isinstance(ConfigurationError("test"), PGSIAnalyzerError)

