"""
Tests for pgsi_analyzer.cli module.

This test suite verifies the CLI interface works correctly with
subcommands, path handling, and error cases.
"""

import pytest
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for tests
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from pgsi_analyzer.cli import main
from pgsi_analyzer.cli.visualization import (
    generate_grouped_bar_chart,
    plot_metric_line_chart,
    plot_execution_vs_energy_scatter,
    plot_time_vs_energy_line_chart,
    plot_method_metric_line_chart,
)


class TestCLIMain:
    """Tests for CLI main function."""

    def test_main_help(self):
        """Test that --help works."""
        # argparse calls sys.exit(0) for --help, so we catch SystemExit
        with pytest.raises(SystemExit) as exc_info:
            main(['--help'])
        assert exc_info.value.code == 0

    def test_main_no_command(self):
        """Test that no command shows help and returns 1."""
        exit_code = main([])
        assert exit_code == 1

    def test_main_evcvt_missing_file(self):
        """Test evcvt command with missing file."""
        exit_code = main(['evcvt', 'nonexistent.csv'])
        assert exit_code == 1

    def test_main_evcvt_success(self):
        """Test evcvt command with valid file."""
        with TemporaryDirectory() as tmpdir:
            # Create test CSV
            df = pd.DataFrame({
                'method': ['cpython', 'pypy'],
                'energy_mean_μJ': [1000000, 500000],
                'time_mean_s': [1.0, 0.5],
                'carbon_mean_gCO2eq': [0.1, 0.05],
            })
            csv_path = Path(tmpdir) / "test.csv"
            df.to_csv(csv_path, index=False)
            
            output_path = Path(tmpdir) / "output.png"
            exit_code = main(['evcvt', str(csv_path), '-o', str(output_path)])
            
            assert exit_code == 0
            assert output_path.exists()

    def test_main_lcpack_missing_files(self):
        """Test lcpack command with missing files."""
        exit_code = main(['lcpack', '--energy', 'nonexistent.csv', '--time', 'nonexistent.csv', '--carbon', 'nonexistent.csv'])
        assert exit_code == 1

    def test_main_lcpack_success(self):
        """Test lcpack command with valid files."""
        with TemporaryDirectory() as tmpdir:
            # Create test CSVs
            energy_df = pd.DataFrame({
                'algorithm': ['algo1', 'algo2'],
                'cpython': [1000000, 2000000],
                'pypy': [500000, 1500000],
            })
            energy_path = Path(tmpdir) / "energy.csv"
            energy_df.to_csv(energy_path, index=False)
            
            time_df = pd.DataFrame({
                'algorithm': ['algo1', 'algo2'],
                'cpython': [1.0, 2.0],
                'pypy': [0.5, 1.5],
            })
            time_path = Path(tmpdir) / "time.csv"
            time_df.to_csv(time_path, index=False)
            
            carbon_df = pd.DataFrame({
                'algorithm': ['algo1', 'algo2'],
                'cpython_CO2e_g': [0.1, 0.2],
                'pypy_CO2e_g': [0.05, 0.15],
            })
            carbon_path = Path(tmpdir) / "carbon.csv"
            carbon_df.to_csv(carbon_path, index=False)
            
            output_dir = Path(tmpdir) / "output"
            exit_code = main([
                'lcpack',
                '--energy', str(energy_path),
                '--time', str(time_path),
                '--carbon', str(carbon_path),
                '-o', str(output_dir)
            ])
            
            assert exit_code == 0
            assert (output_dir / "line_energy_per_algorithm.png").exists()
            assert (output_dir / "line_time_per_algorithm.png").exists()
            assert (output_dir / "line_carbon_per_algorithm.png").exists()

    def test_main_scatter_success(self):
        """Test scatter command with valid files."""
        with TemporaryDirectory() as tmpdir:
            energy_df = pd.DataFrame({
                'algorithm': ['algo1'],
                'cpython': [1000000],
                'pypy': [500000],
            })
            energy_path = Path(tmpdir) / "energy.csv"
            energy_df.to_csv(energy_path, index=False)
            
            time_df = pd.DataFrame({
                'algorithm': ['algo1'],
                'cpython': [1.0],
                'pypy': [0.5],
            })
            time_path = Path(tmpdir) / "time.csv"
            time_df.to_csv(time_path, index=False)
            
            output_path = Path(tmpdir) / "scatter.png"
            exit_code = main(['scatter', str(energy_path), str(time_path), '-o', str(output_path)])
            
            assert exit_code == 0
            assert output_path.exists()

    def test_main_line_compare_success(self):
        """Test line-compare command with valid files."""
        with TemporaryDirectory() as tmpdir:
            energy_df = pd.DataFrame({
                'algorithm': ['algo1'],
                'cpython': [1000000],
            })
            energy_path = Path(tmpdir) / "energy.csv"
            energy_df.to_csv(energy_path, index=False)
            
            time_df = pd.DataFrame({
                'algorithm': ['algo1'],
                'cpython': [1.0],
            })
            time_path = Path(tmpdir) / "time.csv"
            time_df.to_csv(time_path, index=False)
            
            output_path = Path(tmpdir) / "line.png"
            exit_code = main(['line-compare', str(energy_path), str(time_path), '-o', str(output_path)])
            
            assert exit_code == 0
            assert output_path.exists()

    def test_main_etc_compare_success(self):
        """Test etc-compare command with valid file."""
        with TemporaryDirectory() as tmpdir:
            df = pd.DataFrame({
                'method': ['cpython', 'pypy'],
                'energy_mean_μJ': [1000000, 500000],
                'time_mean_s': [1.0, 0.5],
            })
            csv_path = Path(tmpdir) / "metrics.csv"
            df.to_csv(csv_path, index=False)
            
            output_path = Path(tmpdir) / "comparison.png"
            exit_code = main(['etc-compare', str(csv_path), '-o', str(output_path)])
            
            assert exit_code == 0
            assert output_path.exists()

    def test_main_etc_compare_missing_columns(self):
        """Test etc-compare command with missing required columns."""
        with TemporaryDirectory() as tmpdir:
            df = pd.DataFrame({
                'method': ['cpython'],
                'energy': [1000000],  # Wrong column name
            })
            csv_path = Path(tmpdir) / "metrics.csv"
            df.to_csv(csv_path, index=False)
            
            output_path = Path(tmpdir) / "comparison.png"
            exit_code = main(['etc-compare', str(csv_path), '-o', str(output_path)])
            
            assert exit_code == 1


class TestVisualizationFunctions:
    """Tests for visualization functions."""

    def test_generate_grouped_bar_chart_basic(self):
        """Test basic grouped bar chart generation."""
        with TemporaryDirectory() as tmpdir:
            df = pd.DataFrame({
                'method': ['cpython', 'pypy'],
                'energy_mean_μJ': [1000000, 500000],
                'time_mean_s': [1.0, 0.5],
            })
            csv_path = Path(tmpdir) / "test.csv"
            df.to_csv(csv_path, index=False)
            
            output_path = Path(tmpdir) / "chart.png"
            generate_grouped_bar_chart(
                csv_file=csv_path,
                metrics=['energy_mean_μJ', 'time_mean_s'],
                x_column='method',
                title='Test Chart',
                ylabel='Values',
                output_file=output_path
            )
            
            assert output_path.exists()

    def test_generate_grouped_bar_chart_missing_file(self):
        """Test grouped bar chart with missing file."""
        with pytest.raises(FileNotFoundError):
            generate_grouped_bar_chart(
                csv_file='nonexistent.csv',
                metrics=['energy_mean_μJ'],
                x_column='method',
                title='Test',
                ylabel='Values',
                output_file='output.png'
            )

    def test_plot_metric_line_chart_basic(self):
        """Test basic metric line chart."""
        with TemporaryDirectory() as tmpdir:
            df = pd.DataFrame({
                'algorithm': ['algo1', 'algo2'],
                'cpython': [1000000, 2000000],
                'pypy': [500000, 1500000],
            })
            csv_path = Path(tmpdir) / "test.csv"
            df.to_csv(csv_path, index=False)
            
            output_path = Path(tmpdir) / "chart.png"
            plot_metric_line_chart(
                file_path=csv_path,
                metric_unit='μJ',
                title='Test Chart',
                ylabel='Energy',
                output_file=output_path
            )
            
            assert output_path.exists()

    def test_plot_execution_vs_energy_scatter_basic(self):
        """Test basic scatter plot."""
        with TemporaryDirectory() as tmpdir:
            energy_df = pd.DataFrame({
                'algorithm': ['algo1'],
                'cpython': [1000000],
                'pypy': [500000],
            })
            energy_path = Path(tmpdir) / "energy.csv"
            energy_df.to_csv(energy_path, index=False)
            
            time_df = pd.DataFrame({
                'algorithm': ['algo1'],
                'cpython': [1.0],
                'pypy': [0.5],
            })
            time_path = Path(tmpdir) / "time.csv"
            time_df.to_csv(time_path, index=False)
            
            output_path = Path(tmpdir) / "scatter.png"
            plot_execution_vs_energy_scatter(
                energy_file=energy_path,
                time_file=time_path,
                output_file=output_path
            )
            
            assert output_path.exists()

    def test_plot_time_vs_energy_line_chart_basic(self):
        """Test basic time vs energy line chart."""
        with TemporaryDirectory() as tmpdir:
            energy_df = pd.DataFrame({
                'algorithm': ['algo1'],
                'cpython': [1000000],
            })
            energy_path = Path(tmpdir) / "energy.csv"
            energy_df.to_csv(energy_path, index=False)
            
            time_df = pd.DataFrame({
                'algorithm': ['algo1'],
                'cpython': [1.0],
            })
            time_path = Path(tmpdir) / "time.csv"
            time_df.to_csv(time_path, index=False)
            
            output_path = Path(tmpdir) / "line.png"
            plot_time_vs_energy_line_chart(
                energy_file=energy_path,
                time_file=time_path,
                output_file=output_path
            )
            
            assert output_path.exists()

    def test_plot_method_metric_line_chart_basic(self):
        """Test basic method metric line chart."""
        with TemporaryDirectory() as tmpdir:
            df = pd.DataFrame({
                'method': ['cpython', 'pypy'],
                'energy_mean_μJ': [1000000, 500000],
                'time_mean_s': [1.0, 0.5],
            })
            csv_path = Path(tmpdir) / "metrics.csv"
            df.to_csv(csv_path, index=False)
            
            output_path = Path(tmpdir) / "comparison.png"
            plot_method_metric_line_chart(
                csv_file=csv_path,
                output_file=output_path
            )
            
            assert output_path.exists()

    def test_plot_method_metric_line_chart_missing_columns(self):
        """Test method metric line chart with missing columns."""
        with TemporaryDirectory() as tmpdir:
            df = pd.DataFrame({
                'method': ['cpython'],
                'energy': [1000000],  # Wrong column name
            })
            csv_path = Path(tmpdir) / "metrics.csv"
            df.to_csv(csv_path, index=False)
            
            output_path = Path(tmpdir) / "comparison.png"
            with pytest.raises(ValueError, match="energy_mean_μJ"):
                plot_method_metric_line_chart(
                    csv_file=csv_path,
                    output_file=output_path
                )


class TestCLIIntegration:
    """Integration tests for CLI."""

    def test_cli_module_imports(self):
        """Test that CLI module can be imported."""
        from pgsi_analyzer.cli import main
        assert callable(main)

    def test_all_visualization_functions_importable(self):
        """Test that all visualization functions can be imported."""
        from pgsi_analyzer.cli.visualization import (
            generate_grouped_bar_chart,
            plot_metric_line_chart,
            plot_execution_vs_energy_scatter,
            plot_time_vs_energy_line_chart,
            plot_method_metric_line_chart,
        )
        # If we get here, imports succeeded
        assert True

