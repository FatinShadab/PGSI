"""
Tests for pgsi_analyzer.models module.

This test suite verifies carbon footprint, GreenScore, aggregation,
and combination functions work correctly with pathlib and DataFrames.
"""

import pytest
import pandas as pd
from pathlib import Path
from tempfile import TemporaryDirectory

from pgsi_analyzer.models import (
    calculate_carbon_footprint,
    normalize_metrics,
    calculate_greenscore,
    aggregate_energy,
    aggregate_time,
    combine_energy_results,
    combine_time_results,
)


class TestCarbonFootprint:
    """Tests for carbon footprint calculation."""

    def test_calculate_carbon_footprint_basic(self):
        """Test basic carbon footprint calculation."""
        with TemporaryDirectory() as tmpdir:
            # Create test energy CSV
            energy_data = {
                'algorithm': ['algo1', 'algo2'],
                'cpython': [1000000, 2000000],  # μJ
                'pypy': [500000, 1500000],
            }
            energy_df = pd.DataFrame(energy_data)
            energy_path = Path(tmpdir) / "energy.csv"
            energy_df.to_csv(energy_path, index=False)
            
            # Calculate carbon
            carbon_df = calculate_carbon_footprint(energy_path)
            
            # Verify structure
            assert 'algorithm' in carbon_df.columns
            assert 'cpython_CO2e_g' in carbon_df.columns
            assert 'pypy_CO2e_g' in carbon_df.columns
            assert len(carbon_df) == 2

    def test_calculate_carbon_footprint_values(self):
        """Test carbon footprint calculation produces correct values."""
        with TemporaryDirectory() as tmpdir:
            # Create test energy CSV
            energy_data = {
                'algorithm': ['algo1'],
                'cpython': [1000000],  # 1,000,000 μJ = 1 J
            }
            energy_df = pd.DataFrame(energy_data)
            energy_path = Path(tmpdir) / "energy.csv"
            energy_df.to_csv(energy_path, index=False)
            
            # Calculate carbon with default intensity
            carbon_df = calculate_carbon_footprint(energy_path, carbon_intensity=0.000475)
            
            # 1 J * 0.000475 gCO₂e/J = 0.000475 gCO₂e
            expected = 0.000475
            actual = carbon_df['cpython_CO2e_g'].iloc[0]
            assert abs(actual - expected) < 1e-6

    def test_calculate_carbon_footprint_custom_intensity(self):
        """Test carbon footprint with custom intensity factor."""
        with TemporaryDirectory() as tmpdir:
            energy_data = {
                'algorithm': ['algo1'],
                'cpython': [1000000],
            }
            energy_df = pd.DataFrame(energy_data)
            energy_path = Path(tmpdir) / "energy.csv"
            energy_df.to_csv(energy_path, index=False)
            
            # Custom intensity
            carbon_df = calculate_carbon_footprint(energy_path, carbon_intensity=0.001)
            
            # 1 J * 0.001 gCO₂e/J = 0.001 gCO₂e
            assert abs(carbon_df['cpython_CO2e_g'].iloc[0] - 0.001) < 1e-6

    def test_calculate_carbon_footprint_saves_file(self):
        """Test that carbon footprint can be saved to file."""
        with TemporaryDirectory() as tmpdir:
            energy_data = {
                'algorithm': ['algo1'],
                'cpython': [1000000],
            }
            energy_df = pd.DataFrame(energy_data)
            energy_path = Path(tmpdir) / "energy.csv"
            energy_df.to_csv(energy_path, index=False)
            
            output_path = Path(tmpdir) / "carbon.csv"
            carbon_df = calculate_carbon_footprint(energy_path, output_path=output_path)
            
            assert output_path.exists()
            loaded_df = pd.read_csv(output_path)
            assert len(loaded_df) == len(carbon_df)

    def test_calculate_carbon_footprint_missing_file(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            calculate_carbon_footprint("nonexistent.csv")

    def test_calculate_carbon_footprint_missing_algorithm_column(self):
        """Test error handling for missing algorithm column."""
        with TemporaryDirectory() as tmpdir:
            energy_data = {'cpython': [1000000]}
            energy_df = pd.DataFrame(energy_data)
            energy_path = Path(tmpdir) / "energy.csv"
            energy_df.to_csv(energy_path, index=False)
            
            with pytest.raises(ValueError, match="algorithm"):
                calculate_carbon_footprint(energy_path)


class TestNormalizeMetrics:
    """Tests for metric normalization."""

    def test_normalize_metrics_basic(self):
        """Test basic metric normalization."""
        df = pd.DataFrame({
            'algorithm': ['algo1', 'algo2'],
            'cpython': [100, 200],
            'pypy': [50, 150],
        })
        
        normalized = normalize_metrics(df)
        
        assert 'algorithm' in normalized.columns
        assert 'cpython' in normalized.columns
        assert 'pypy' in normalized.columns
        assert len(normalized) == 2

    def test_normalize_metrics_values(self):
        """Test that normalization produces values between 0 and 1."""
        df = pd.DataFrame({
            'algorithm': ['algo1'],
            'cpython': [100],
            'pypy': [50],
        })
        
        normalized = normalize_metrics(df)
        
        # Min should be 0, max should be 1
        # For row [100, 50]: min=50, max=100
        # cpython: (100-50)/(100-50) = 1.0 (max)
        # pypy: (50-50)/(100-50) = 0.0 (min)
        assert normalized['cpython'].iloc[0] == 1.0
        assert normalized['pypy'].iloc[0] == 0.0

    def test_normalize_metrics_constant_row(self):
        """Test normalization handles constant rows."""
        df = pd.DataFrame({
            'algorithm': ['algo1'],
            'cpython': [100],
            'pypy': [100],  # Same value
        })
        
        normalized = normalize_metrics(df)
        
        # Constant rows should be set to 0
        assert normalized['cpython'].iloc[0] == 0.0
        assert normalized['pypy'].iloc[0] == 0.0

    def test_normalize_metrics_saves_file(self):
        """Test that normalized metrics can be saved to file."""
        with TemporaryDirectory() as tmpdir:
            df = pd.DataFrame({
                'algorithm': ['algo1'],
                'cpython': [100],
                'pypy': [50],
            })
            
            output_path = Path(tmpdir) / "normalized.csv"
            normalized = normalize_metrics(df, output_path=output_path)
            
            assert output_path.exists()
            loaded_df = pd.read_csv(output_path)
            assert len(loaded_df) == len(normalized)


class TestGreenScore:
    """Tests for GreenScore calculation."""

    def test_calculate_greenscore_basic(self):
        """Test basic GreenScore calculation."""
        energy_df = pd.DataFrame({
            'algorithm': ['algo1', 'algo2'],
            'cpython': [100, 200],
            'pypy': [50, 150],
        })
        
        time_df = pd.DataFrame({
            'algorithm': ['algo1', 'algo2'],
            'cpython': [1.0, 2.0],
            'pypy': [0.5, 1.5],
        })
        
        carbon_df = pd.DataFrame({
            'algorithm': ['algo1', 'algo2'],
            'cpython_CO2e_g': [0.1, 0.2],
            'pypy_CO2e_g': [0.05, 0.15],
        })
        
        result = calculate_greenscore(energy_df, time_df, carbon_df)
        
        assert 'method' in result.columns
        assert 'green_score' in result.columns
        assert len(result) > 0

    def test_calculate_greenscore_weights_validation(self):
        """Test that weights must sum to 1.0."""
        energy_df = pd.DataFrame({
            'algorithm': ['algo1'],
            'cpython': [100],
        })
        time_df = pd.DataFrame({
            'algorithm': ['algo1'],
            'cpython': [1.0],
        })
        carbon_df = pd.DataFrame({
            'algorithm': ['algo1'],
            'cpython_CO2e_g': [0.1],
        })
        
        with pytest.raises(ValueError, match="sum to 1.0"):
            calculate_greenscore(energy_df, time_df, carbon_df, alpha=0.5, beta=0.5, gamma=0.5)

    def test_calculate_greenscore_sorted(self):
        """Test that GreenScore results are sorted (lower is better)."""
        energy_df = pd.DataFrame({
            'algorithm': ['algo1'],
            'cpython': [100],
            'pypy': [50],
        })
        
        time_df = pd.DataFrame({
            'algorithm': ['algo1'],
            'cpython': [1.0],
            'pypy': [0.5],
        })
        
        carbon_df = pd.DataFrame({
            'algorithm': ['algo1'],
            'cpython_CO2e_g': [0.1],
            'pypy_CO2e_g': [0.05],
        })
        
        result = calculate_greenscore(energy_df, time_df, carbon_df)
        
        # Should be sorted ascending
        scores = result['green_score'].values
        assert all(scores[i] <= scores[i+1] for i in range(len(scores)-1))

    def test_calculate_greenscore_saves_file(self):
        """Test that GreenScore can be saved to file."""
        with TemporaryDirectory() as tmpdir:
            energy_df = pd.DataFrame({
                'algorithm': ['algo1'],
                'cpython': [100],
            })
            time_df = pd.DataFrame({
                'algorithm': ['algo1'],
                'cpython': [1.0],
            })
            carbon_df = pd.DataFrame({
                'algorithm': ['algo1'],
                'cpython_CO2e_g': [0.1],
            })
            
            output_path = Path(tmpdir) / "greenscore.csv"
            result = calculate_greenscore(energy_df, time_df, carbon_df, output_path=output_path)
            
            assert output_path.exists()
            loaded_df = pd.read_csv(output_path)
            assert len(loaded_df) == len(result)


class TestAggregation:
    """Tests for energy and time aggregation."""

    def test_aggregate_energy_basic(self):
        """Test basic energy aggregation."""
        with TemporaryDirectory() as tmpdir:
            # Create test CSV files
            for i, filename in enumerate(['test1.csv', 'test2.csv']):
                df = pd.DataFrame({
                    'package (uJ)': [1000000 + i*100000, 2000000 + i*100000],
                })
                (Path(tmpdir) / filename).write_text(df.to_csv(index=False))
            
            result = aggregate_energy(tmpdir)
            
            assert 'filename' in result.columns
            assert 'average_package (uJ)' in result.columns
            assert 'methodology' in result.columns
            assert len(result) == 2

    def test_aggregate_energy_values(self):
        """Test that aggregation computes correct averages."""
        with TemporaryDirectory() as tmpdir:
            df = pd.DataFrame({
                'package (uJ)': [1000000, 2000000, 3000000],
            })
            (Path(tmpdir) / "test.csv").write_text(df.to_csv(index=False))
            
            result = aggregate_energy(tmpdir)
            
            # Average should be 2,000,000
            assert abs(result['average_package (uJ)'].iloc[0] - 2000000) < 1e-6

    def test_aggregate_energy_saves_file(self):
        """Test that aggregated energy can be saved to file."""
        with TemporaryDirectory() as tmpdir:
            df = pd.DataFrame({
                'package (uJ)': [1000000],
            })
            (Path(tmpdir) / "test.csv").write_text(df.to_csv(index=False))
            
            output_path = Path(tmpdir) / "energy_avg.csv"
            result = aggregate_energy(tmpdir, output_path=output_path)
            
            assert output_path.exists()
            loaded_df = pd.read_csv(output_path)
            assert len(loaded_df) == len(result)

    def test_aggregate_energy_missing_folder(self):
        """Test error handling for missing folder."""
        with pytest.raises(FileNotFoundError):
            aggregate_energy("nonexistent_folder")

    def test_aggregate_time_basic(self):
        """Test basic time aggregation."""
        with TemporaryDirectory() as tmpdir:
            df = pd.DataFrame({
                'execution_time (s)': [1.0, 2.0, 3.0],
            })
            (Path(tmpdir) / "test.csv").write_text(df.to_csv(index=False))
            
            result = aggregate_time(tmpdir)
            
            assert 'filename' in result.columns
            assert 'execution_time (s)' in result.columns
            assert len(result) == 1

    def test_aggregate_time_values(self):
        """Test that time aggregation computes correct averages."""
        with TemporaryDirectory() as tmpdir:
            df = pd.DataFrame({
                'execution_time (s)': [1.0, 2.0, 3.0],
            })
            (Path(tmpdir) / "test.csv").write_text(df.to_csv(index=False))
            
            result = aggregate_time(tmpdir)
            
            # Average should be 2.0
            assert abs(result['execution_time (s)'].iloc[0] - 2.0) < 1e-6


class TestCombination:
    """Tests for combining results from multiple methods."""

    def test_combine_energy_results_basic(self):
        """Test basic energy combination."""
        with TemporaryDirectory() as tmpdir:
            # Create test files in subdirectories
            cpython_dir = Path(tmpdir) / "cpython"
            pypy_dir = Path(tmpdir) / "pypy"
            cpython_dir.mkdir()
            pypy_dir.mkdir()
            
            # Create aggregated energy files
            cpython_df = pd.DataFrame({
                'filename': ['algo1_cpython', 'algo2_cpython'],
                'average_package (uJ)': [1000000, 2000000],
            })
            cpython_df.to_csv(cpython_dir / "energy_avg.csv", index=False)
            
            pypy_df = pd.DataFrame({
                'filename': ['algo1_pypy', 'algo2_pypy'],
                'average_package (uJ)': [500000, 1500000],
            })
            pypy_df.to_csv(pypy_dir / "energy_avg.csv", index=False)
            
            file_paths = [
                cpython_dir / "energy_avg.csv",
                pypy_dir / "energy_avg.csv",
            ]
            output_path = Path(tmpdir) / "energy_com.csv"
            
            result = combine_energy_results(file_paths, output_path)
            
            assert 'algorithm' in result.columns
            assert 'cpython' in result.columns
            assert 'pypy' in result.columns
            assert len(result) == 2
            assert output_path.exists()

    def test_combine_time_results_basic(self):
        """Test basic time combination."""
        with TemporaryDirectory() as tmpdir:
            cpython_dir = Path(tmpdir) / "cpython"
            pypy_dir = Path(tmpdir) / "pypy"
            cpython_dir.mkdir()
            pypy_dir.mkdir()
            
            cpython_df = pd.DataFrame({
                'filename': ['algo1_cpython'],
                'execution_time (s)': [1.0],
            })
            cpython_df.to_csv(cpython_dir / "time_avg.csv", index=False)
            
            pypy_df = pd.DataFrame({
                'filename': ['algo1_pypy'],
                'execution_time (s)': [0.5],
            })
            pypy_df.to_csv(pypy_dir / "time_avg.csv", index=False)
            
            file_paths = [
                cpython_dir / "time_avg.csv",
                pypy_dir / "time_avg.csv",
            ]
            output_path = Path(tmpdir) / "time_com.csv"
            
            result = combine_time_results(file_paths, output_path)
            
            assert 'algorithm' in result.columns
            assert 'cpython' in result.columns
            assert 'pypy' in result.columns
            assert len(result) == 1
            assert output_path.exists()

    def test_combine_energy_results_missing_file(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            combine_energy_results(["nonexistent.csv"], "output.csv")

    def test_combine_energy_results_extract_algorithm(self):
        """Test that algorithm names are extracted correctly."""
        with TemporaryDirectory() as tmpdir:
            cpython_dir = Path(tmpdir) / "cpython"
            cpython_dir.mkdir()
            
            cpython_df = pd.DataFrame({
                'filename': ['bubble_sort_cpython'],
                'average_package (uJ)': [1000000],
            })
            cpython_df.to_csv(cpython_dir / "energy_avg.csv", index=False)
            
            file_paths = [cpython_dir / "energy_avg.csv"]
            output_path = Path(tmpdir) / "energy_com.csv"
            
            result = combine_energy_results(file_paths, output_path)
            
            assert result['algorithm'].iloc[0] == 'bubble_sort'

    def test_combine_energy_results_missing_columns_raises(self):
        """Test that combine_energy_results raises ValueError when CSV lacks required columns."""
        with TemporaryDirectory() as tmpdir:
            cpython_dir = Path(tmpdir) / "cpython"
            cpython_dir.mkdir()
            # Missing 'average_package (uJ)' and/or 'filename'
            bad_df = pd.DataFrame({"wrong_col": [1, 2]})
            bad_df.to_csv(cpython_dir / "energy_avg.csv", index=False)
            with pytest.raises(ValueError, match="filename.*average_package"):
                combine_energy_results([cpython_dir / "energy_avg.csv"], Path(tmpdir) / "out.csv")

    def test_combine_time_results_missing_columns_raises(self):
        """Test that combine_time_results raises ValueError when CSV lacks required columns."""
        with TemporaryDirectory() as tmpdir:
            cpython_dir = Path(tmpdir) / "cpython"
            cpython_dir.mkdir()
            bad_df = pd.DataFrame({"wrong_col": [1.0]})
            bad_df.to_csv(cpython_dir / "time_avg.csv", index=False)
            with pytest.raises(ValueError, match="filename.*execution_time"):
                combine_time_results([cpython_dir / "time_avg.csv"], Path(tmpdir) / "out.csv")


class TestModelsIntegration:
    """Integration tests for models module."""

    def test_full_pipeline(self):
        """Test full pipeline: aggregate -> combine -> carbon -> greenscore."""
        with TemporaryDirectory() as tmpdir:
            # Step 1: Create raw energy data
            energy_folder = Path(tmpdir) / "energy"
            energy_folder.mkdir()
            df = pd.DataFrame({
                'package (uJ)': [1000000, 2000000],
            })
            (energy_folder / "algo1_cpython.csv").write_text(df.to_csv(index=False))
            
            # Step 2: Aggregate energy
            energy_avg_path = Path(tmpdir) / "energy_avg.csv"
            aggregate_energy(energy_folder, energy_avg_path)
            
            # Step 3: Combine (simulate multiple methods)
            cpython_dir = Path(tmpdir) / "cpython"
            cpython_dir.mkdir()
            energy_avg_df = pd.read_csv(energy_avg_path)
            energy_avg_df.to_csv(cpython_dir / "energy_avg.csv", index=False)
            
            combine_path = Path(tmpdir) / "energy_com.csv"
            combine_energy_results([cpython_dir / "energy_avg.csv"], combine_path)
            
            # Step 4: Calculate carbon
            carbon_df = calculate_carbon_footprint(combine_path)
            
            # Step 5: Calculate GreenScore (simplified)
            time_df = pd.DataFrame({
                'algorithm': ['algo1'],
                'cpython': [1.0],
            })
            greenscore_df = calculate_greenscore(
                pd.read_csv(combine_path),
                time_df,
                carbon_df
            )
            
            assert len(greenscore_df) > 0
            assert 'green_score' in greenscore_df.columns

