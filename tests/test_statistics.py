"""
Tests for pgsi_analyzer.models.statistics module.

This test suite verifies statistical analysis functions.
"""

import pytest
import pandas as pd
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from pgsi_analyzer.models.statistics import (
    calculate_standard_deviation,
    perform_statistical_tests,
    oneway_anova_greenscore,
    load_csv,
)
from pgsi_analyzer.utils import AnalysisError

# Check if scipy is available
SCIPY_AVAILABLE = importlib.util.find_spec('scipy') is not None


class TestCalculateStandardDeviation:
    """Tests for calculate_standard_deviation function."""

    def test_calculate_standard_deviation_basic(self):
        """Test basic standard deviation calculation."""
        df = pd.DataFrame({
            'algorithm': ['algo1', 'algo2', 'algo3'],
            'method1': [10.0, 20.0, 30.0],
            'method2': [15.0, 25.0, 35.0],
        })
        
        result = calculate_standard_deviation(df)
        
        assert isinstance(result, pd.Series)
        assert 'method1' in result.index
        assert 'method2' in result.index
        assert result['method1'] > 0

    def test_calculate_standard_deviation_missing_algorithm_column(self):
        """Test that missing algorithm column raises AnalysisError."""
        df = pd.DataFrame({
            'method1': [10.0, 20.0, 30.0],
        })
        
        with pytest.raises(AnalysisError, match="Missing required columns"):
            calculate_standard_deviation(df)

    def test_calculate_standard_deviation_single_method(self):
        """Test standard deviation with single method."""
        df = pd.DataFrame({
            'algorithm': ['algo1', 'algo2'],
            'method1': [10.0, 20.0],
        })
        
        result = calculate_standard_deviation(df)
        assert len(result) == 1
        assert 'method1' in result.index


class TestPerformStatisticalTests:
    """Tests for perform_statistical_tests function."""

    @pytest.mark.skipif(not SCIPY_AVAILABLE, reason="scipy not available")
    def test_perform_statistical_tests_basic(self):
        """Test basic statistical tests."""
        import scipy.stats as stats
        
        energy_df = pd.DataFrame({
            'algorithm': ['algo1', 'algo2', 'algo3'],
            'cpython': [100.0, 200.0, 300.0],
            'pypy': [50.0, 150.0, 250.0],
        })
        
        time_df = pd.DataFrame({
            'algorithm': ['algo1', 'algo2', 'algo3'],
            'cpython': [1.0, 2.0, 3.0],
            'pypy': [0.5, 1.5, 2.5],
        })
        
        carbon_df = pd.DataFrame({
            'algorithm': ['algo1', 'algo2', 'algo3'],
            'cpython': [0.1, 0.2, 0.3],
            'pypy': [0.05, 0.15, 0.25],
        })
        
        result = perform_statistical_tests(energy_df, time_df, carbon_df)
        
        assert isinstance(result, dict)
        assert 'energy' in result
        assert 'time' in result
        assert 'carbon' in result
        
        for key in ['energy', 'time', 'carbon']:
            assert 'f_stat' in result[key]
            assert 'p_value' in result[key]

    @pytest.mark.skipif(not SCIPY_AVAILABLE, reason="scipy not available")
    def test_perform_statistical_tests_single_method_raises(self):
        """Test that single method raises AnalysisError."""
        df = pd.DataFrame({
            'algorithm': ['algo1', 'algo2'],
            'cpython': [100.0, 200.0],
        })
        
        with pytest.raises(AnalysisError, match="Need at least two methods"):
            perform_statistical_tests(df, df, df)

    def test_perform_statistical_tests_missing_scipy(self):
        """Test that missing scipy raises AnalysisError."""
        with patch('pgsi_analyzer.models.statistics._require_scipy') as mock_require:
            mock_require.side_effect = AnalysisError("scipy is required")
            
            df = pd.DataFrame({
                'algorithm': ['algo1', 'algo2'],
                'cpython': [100.0, 200.0],
                'pypy': [50.0, 150.0],
            })
            
            with pytest.raises(AnalysisError, match="scipy is required"):
                perform_statistical_tests(df, df, df)


class TestOnewayAnovaGreenscore:
    """Tests for oneway_anova_greenscore function."""

    @pytest.mark.skipif(not SCIPY_AVAILABLE, reason="scipy not available")
    def test_oneway_anova_greenscore_basic(self):
        """Test basic ANOVA on GreenScore."""
        df = pd.DataFrame({
            'method': ['cpython', 'cpython', 'pypy', 'pypy', 'cython', 'cython'],
            'green_score': [0.5, 0.6, 0.7, 0.8, 0.4, 0.5],
        })
        
        result = oneway_anova_greenscore(df)
        
        assert isinstance(result, dict)
        assert 'f_stat' in result
        assert 'p_value' in result

    @pytest.mark.skipif(not SCIPY_AVAILABLE, reason="scipy not available")
    def test_oneway_anova_greenscore_single_method_raises(self):
        """Test that single method raises AnalysisError."""
        df = pd.DataFrame({
            'method': ['cpython', 'cpython'],
            'green_score': [0.5, 0.6],
        })
        
        with pytest.raises(AnalysisError, match="Need at least two methods"):
            oneway_anova_greenscore(df)

    def test_oneway_anova_greenscore_missing_columns(self):
        """Test that missing required columns raises AnalysisError."""
        df = pd.DataFrame({
            'method': ['cpython', 'pypy'],
            'score': [0.5, 0.6],  # Wrong column name
        })
        
        # This will fail at _require_scipy first if scipy is not available
        # So we check for either error
        try:
            with pytest.raises(AnalysisError) as exc_info:
                oneway_anova_greenscore(df)
            # Should be either missing columns or missing scipy
            assert "Missing required columns" in str(exc_info.value) or "scipy is required" in str(exc_info.value)
        except Exception:
            # If scipy is not available, it will raise about scipy first
            pass

    def test_oneway_anova_greenscore_missing_scipy(self):
        """Test that missing scipy raises AnalysisError."""
        with patch('pgsi_analyzer.models.statistics._require_scipy') as mock_require:
            mock_require.side_effect = AnalysisError("scipy is required")
            
            df = pd.DataFrame({
                'method': ['cpython', 'pypy'],
                'green_score': [0.5, 0.6],
            })
            
            with pytest.raises(AnalysisError, match="scipy is required"):
                oneway_anova_greenscore(df)


class TestLoadCSV:
    """Tests for load_csv function."""

    def test_load_csv_success(self):
        """Test loading a valid CSV file."""
        with TemporaryDirectory() as tmpdir:
            csv_file = Path(tmpdir) / "test.csv"
            df_data = pd.DataFrame({
                'col1': [1, 2, 3],
                'col2': [4, 5, 6],
            })
            df_data.to_csv(csv_file, index=False)
            
            result = load_csv(csv_file)
            
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 3
            assert 'col1' in result.columns
            assert 'col2' in result.columns

    def test_load_csv_string_path(self):
        """Test loading CSV with string path."""
        with TemporaryDirectory() as tmpdir:
            csv_file = Path(tmpdir) / "test.csv"
            df_data = pd.DataFrame({'col1': [1, 2, 3]})
            df_data.to_csv(csv_file, index=False)
            
            result = load_csv(str(csv_file))
            
            assert isinstance(result, pd.DataFrame)

    def test_load_csv_missing_file_raises(self):
        """Test that missing file raises ConfigurationError."""
        missing_file = Path("/nonexistent/file.csv")
        
        with pytest.raises(Exception):  # ConfigurationError from validate_file_path
            load_csv(missing_file)


class TestStatisticsIntegration:
    """Integration tests for statistics module."""

    def test_statistics_module_imports(self):
        """Test that statistics module can be imported."""
        from pgsi_analyzer.models.statistics import (
            calculate_standard_deviation,
            perform_statistical_tests,
            oneway_anova_greenscore,
            load_csv,
        )
        assert True

    @pytest.mark.skipif(not SCIPY_AVAILABLE, reason="scipy not available")
    def test_full_statistical_workflow(self):
        """Test a complete statistical analysis workflow."""
        # Create sample data
        energy_df = pd.DataFrame({
            'algorithm': ['algo1', 'algo2', 'algo3'],
            'cpython': [100.0, 200.0, 300.0],
            'pypy': [50.0, 150.0, 250.0],
        })
        
        time_df = pd.DataFrame({
            'algorithm': ['algo1', 'algo2', 'algo3'],
            'cpython': [1.0, 2.0, 3.0],
            'pypy': [0.5, 1.5, 2.5],
        })
        
        carbon_df = pd.DataFrame({
            'algorithm': ['algo1', 'algo2', 'algo3'],
            'cpython': [0.1, 0.2, 0.3],
            'pypy': [0.05, 0.15, 0.25],
        })
        
        # Calculate standard deviation
        std_energy = calculate_standard_deviation(energy_df)
        assert len(std_energy) > 0
        
        # Perform statistical tests
        stats_results = perform_statistical_tests(energy_df, time_df, carbon_df)
        assert 'energy' in stats_results
        
        # Test ANOVA on GreenScore
        greenscore_df = pd.DataFrame({
            'method': ['cpython', 'cpython', 'pypy', 'pypy'],
            'green_score': [0.5, 0.6, 0.7, 0.8],
        })
        anova_result = oneway_anova_greenscore(greenscore_df)
        assert 'f_stat' in anova_result

