"""
Tests for benchmark orchestrator module.
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from pgsi_analyzer.benchmark.orchestrator import (
    resolve_algorithms,
    resolve_methods,
    run_benchmark_suite,
)
from pgsi_analyzer.utils import AnalysisError, MeasurementError


class TestResolveAlgorithms:
    """Test resolve_algorithms function."""

    def test_resolve_all(self):
        """Test resolving 'all' to all algorithms."""
        from pgsi_analyzer.benchmarks.registry import list_algorithms
        
        result = resolve_algorithms(["all"])
        expected = list_algorithms()
        
        assert result == expected
        assert len(result) == 15

    def test_resolve_specific(self):
        """Test resolving specific algorithms."""
        result = resolve_algorithms(["hanoi", "binary-trees"])
        
        assert len(result) == 2
        assert "hanoi" in result
        assert "binary-trees" in result
        assert result == sorted(result)  # Should be sorted

    def test_resolve_deduplicates(self):
        """Test that duplicate algorithms are deduplicated."""
        result = resolve_algorithms(["hanoi", "hanoi", "binary-trees"])
        
        assert len(result) == 2
        assert result.count("hanoi") == 1

    def test_resolve_invalid_algorithm(self):
        """Test resolving invalid algorithm raises error."""
        with pytest.raises(ValueError, match="Invalid algorithms"):
            resolve_algorithms(["invalid-algorithm"])


class TestResolveMethods:
    """Test resolve_methods function."""

    def test_resolve_all(self):
        """Test resolving 'all' to all methods."""
        from pgsi_analyzer.benchmarks.registry import list_methods
        
        result = resolve_methods(["all"])
        expected = list_methods()
        
        assert result == expected
        assert len(result) == 5

    def test_resolve_specific(self):
        """Test resolving specific methods."""
        result = resolve_methods(["cpython", "pypy"])
        
        assert len(result) == 2
        assert "cpython" in result
        assert "pypy" in result

    def test_resolve_with_algorithm(self):
        """Test resolving methods with algorithm context."""
        result = resolve_methods(["cpython", "pypy"], algorithm="hanoi")
        
        assert len(result) == 2
        assert "cpython" in result
        assert "pypy" in result

    def test_resolve_invalid_method(self):
        """Test resolving invalid method raises error."""
        with pytest.raises(ValueError, match="Invalid methods"):
            resolve_methods(["invalid-method"])

    def test_resolve_invalid_method_for_algorithm(self):
        """Test resolving invalid method for algorithm raises error."""
        with pytest.raises(ValueError, match="Invalid methods for"):
            resolve_methods(["invalid-method"], algorithm="hanoi")


class TestRunBenchmarkSuite:
    """Test run_benchmark_suite function."""

    @patch('pgsi_analyzer.benchmark.orchestrator.build_benchmark')
    @patch('pgsi_analyzer.benchmark.orchestrator.execute_benchmark')
    @patch('pgsi_analyzer.benchmark.orchestrator.aggregate_energy')
    @patch('pgsi_analyzer.benchmark.orchestrator.aggregate_time')
    @patch('pgsi_analyzer.benchmark.orchestrator.combine_energy_results')
    @patch('pgsi_analyzer.benchmark.orchestrator.combine_time_results')
    @patch('pgsi_analyzer.benchmark.orchestrator.calculate_carbon_footprint')
    @patch('pgsi_analyzer.benchmark.orchestrator.calculate_greenscore')
    @patch('pgsi_analyzer.benchmark.orchestrator.get_benchmark_path')
    @patch('pgsi_analyzer.benchmark.orchestrator.requires_build')
    @patch('pandas.read_csv')
    def test_run_benchmark_suite_full_pipeline(
        self, mock_read_csv, mock_requires_build, mock_get_path,
        mock_greenscore, mock_carbon, mock_combine_time, mock_combine_energy,
        mock_agg_time, mock_agg_energy, mock_execute, mock_build
    ):
        """Test full benchmark suite pipeline."""
        # Setup mocks
        output_dir = Path("/test/results")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock benchmark paths
        mock_get_path.return_value = Path("/test/benchmark/main.py")
        
        # Mock build requirements
        mock_requires_build.side_effect = lambda m: m in ("cython", "ctypes")
        
        # Mock execution results - need to ensure parent directories exist for glob
        energy_csv = Path("/test/energy_benchmark/hanoi_cpython.csv")
        time_csv = Path("/test/time_benchmark/hanoi_cpython.csv")
        mock_execute.return_value = {
            "energy_csv": energy_csv,
            "time_csv": time_csv,
            "system_info": Path("/test/system_info.json"),
        }
        
        # Mock aggregation results
        mock_agg_energy.return_value = pd.DataFrame({
            "filename": ["hanoi_cpython"],
            "average_package (uJ)": [1000.0],
        })
        mock_agg_time.return_value = pd.DataFrame({
            "filename": ["hanoi_cpython"],
            "execution_time (s)": [1.0],
        })
        
        # Mock combination results
        mock_combine_energy.return_value = pd.DataFrame({
            "algorithm": ["hanoi"],
            "cpython": [1000.0],
        })
        mock_combine_time.return_value = pd.DataFrame({
            "algorithm": ["hanoi"],
            "cpython": [1.0],
        })
        
        # Mock carbon results
        mock_carbon.return_value = pd.DataFrame({
            "algorithm": ["hanoi"],
            "cpython": [0.000475],
        })
        
        # Mock GreenScore results
        mock_greenscore.return_value = pd.DataFrame({
            "method": ["cpython"],
            "green_score": [0.5],
        })
        
        # Mock read_csv for final steps
        mock_read_csv.side_effect = [
            pd.DataFrame({"algorithm": ["hanoi"], "cpython": [1000.0]}),  # energy
            pd.DataFrame({"algorithm": ["hanoi"], "cpython": [1.0]}),  # time
        ]
        
        # The orchestrator gets directories from energy_csv.parent and time_csv.parent
        # Then calls .glob("*.csv") on those directories
        # We need to create mock Path objects that have mock parents with glob methods
        # Create mock CSV Path objects with mock parents
        mock_energy_csv = MagicMock(spec=Path)
        mock_energy_csv.__str__ = lambda: str(energy_csv)
        mock_energy_csv.name = "hanoi_cpython.csv"
        mock_energy_csv.parent.glob.return_value = [mock_energy_csv]
        
        mock_time_csv = MagicMock(spec=Path)
        mock_time_csv.__str__ = lambda: str(time_csv)
        mock_time_csv.name = "hanoi_cpython.csv"
        mock_time_csv.parent.glob.return_value = [mock_time_csv]
        
        # Update execute_benchmark to return our mock Path objects
        mock_execute.return_value = {
            "energy_csv": mock_energy_csv,
            "time_csv": mock_time_csv,
            "system_info": Path("/test/system_info.json"),
        }
        
        # Mock shutil.copy2 to avoid file system operations
        with patch('shutil.copy2'):
            # Run suite with minimal configuration
            result = run_benchmark_suite(
                algorithms=["hanoi"],
                methods=["cpython"],
                runs=5,
                output_dir=output_dir,
            )
            
            # Verify result
            assert isinstance(result, Path)
            assert result.name == "GreenScore.csv"
            
            # Verify pipeline was called
            mock_execute.assert_called()
            mock_agg_energy.assert_called()
            mock_agg_time.assert_called()
            mock_combine_energy.assert_called()
            mock_combine_time.assert_called()
            mock_carbon.assert_called()
            mock_greenscore.assert_called()

    @patch('pgsi_analyzer.benchmark.orchestrator.get_benchmark_path')
    @patch('pgsi_analyzer.benchmark.orchestrator.requires_build')
    def test_run_benchmark_suite_builds_required(self, mock_requires_build, mock_get_path):
        """Test that benchmarks requiring build are built."""
        mock_get_path.return_value = Path("/test/benchmark")
        mock_requires_build.side_effect = lambda m: m in ("cython", "ctypes")
        
        with patch('pgsi_analyzer.benchmark.orchestrator.build_benchmark') as mock_build:
            energy_csv = Path("/test/energy_benchmark/hanoi_cython.csv")
            time_csv = Path("/test/time_benchmark/hanoi_cython.csv")
            with patch('pgsi_analyzer.benchmark.orchestrator.execute_benchmark') as mock_execute:
                mock_execute.return_value = {
                    "energy_csv": energy_csv,
                    "time_csv": time_csv,
                }
                with patch('pgsi_analyzer.benchmark.orchestrator.aggregate_energy'):
                    with patch('pgsi_analyzer.benchmark.orchestrator.aggregate_time'):
                        with patch('pgsi_analyzer.benchmark.orchestrator.combine_energy_results'):
                            with patch('pgsi_analyzer.benchmark.orchestrator.combine_time_results'):
                                with patch('pgsi_analyzer.benchmark.orchestrator.calculate_carbon_footprint'):
                                    with patch('pgsi_analyzer.benchmark.orchestrator.calculate_greenscore'):
                                        with patch('pandas.read_csv'):
                                            # Create mock CSV Path objects with mock parents
                                            mock_energy_csv = MagicMock(spec=Path)
                                            mock_energy_csv.__str__ = lambda: str(energy_csv)
                                            mock_energy_csv.name = "hanoi_cython.csv"
                                            mock_energy_csv.parent.glob.return_value = [mock_energy_csv]
                                            
                                            mock_time_csv = MagicMock(spec=Path)
                                            mock_time_csv.__str__ = lambda: str(time_csv)
                                            mock_time_csv.name = "hanoi_cython.csv"
                                            mock_time_csv.parent.glob.return_value = [mock_time_csv]
                                            
                                            # Update execute_benchmark to return our mock Path objects
                                            mock_execute.return_value = {
                                                "energy_csv": mock_energy_csv,
                                                "time_csv": mock_time_csv,
                                            }
                                            
                                            # Mock shutil.copy2 to avoid file system operations
                                            with patch('shutil.copy2'):
                                                output_dir = Path("/test/results")
                                                output_dir.mkdir(parents=True, exist_ok=True)
                                                
                                                run_benchmark_suite(
                                                    algorithms=["hanoi"],
                                                    methods=["cython"],
                                                    runs=5,
                                                    output_dir=output_dir,
                                                )
                                                
                                                # Verify build was called for cython
                                                mock_build.assert_called()

    def test_run_benchmark_suite_invalid_algorithms(self):
        """Test that invalid algorithms raise error."""
        with pytest.raises(ValueError, match="Invalid algorithms"):
            run_benchmark_suite(
                algorithms=["invalid-algorithm"],
                methods=["cpython"],
                runs=5,
            )

    def test_run_benchmark_suite_invalid_methods(self):
        """Test that invalid methods raise error."""
        with pytest.raises(ValueError, match="Invalid methods"):
            run_benchmark_suite(
                algorithms=["hanoi"],
                methods=["invalid-method"],
                runs=5,
            )

    @patch('pgsi_analyzer.benchmark.orchestrator.get_benchmark_path')
    @patch('pgsi_analyzer.benchmark.orchestrator.requires_build')
    @patch('pgsi_analyzer.benchmark.orchestrator.build_benchmark')
    @patch('pgsi_analyzer.benchmark.orchestrator.execute_benchmark')
    @patch('pgsi_analyzer.benchmark.orchestrator.aggregate_energy')
    @patch('pgsi_analyzer.benchmark.orchestrator.aggregate_time')
    @patch('pgsi_analyzer.benchmark.orchestrator.combine_energy_results')
    @patch('pgsi_analyzer.benchmark.orchestrator.combine_time_results')
    @patch('pgsi_analyzer.benchmark.orchestrator.calculate_carbon_footprint')
    @patch('pgsi_analyzer.benchmark.orchestrator.calculate_greenscore')
    @patch('pandas.read_csv')
    @patch('shutil.copy2')
    def test_run_benchmark_suite_continues_after_benchmark_crash(
        self, _mock_copy2, mock_read_csv, mock_greenscore, mock_carbon,
        mock_combine_time, mock_combine_energy, mock_agg_time, mock_agg_energy,
        mock_execute, mock_build, mock_requires_build, mock_get_path,
        tmp_path
    ):
        """Test that a benchmark crash (MeasurementError) is caught and suite continues."""
        mock_get_path.return_value = Path("/test/benchmark/main.py")
        mock_requires_build.return_value = False
        mock_read_csv.side_effect = [
            pd.DataFrame({"algorithm": ["sieve"], "cpython": [1000.0]}),
            pd.DataFrame({"algorithm": ["sieve"], "cpython": [1.0]}),
        ]
        mock_greenscore.return_value = pd.DataFrame({"method": ["cpython"], "green_score": [0.5]})

        energy_dir = tmp_path / "energy_benchmark"
        time_dir = tmp_path / "time_benchmark"
        energy_dir.mkdir()
        time_dir.mkdir()
        (energy_dir / "sieve_cpython.csv").write_text("package (uJ)\n1000\n")
        (time_dir / "sieve_cpython.csv").write_text("execution_time (s)\n1.0\n")
        success_result = {
            "energy_csv": energy_dir / "sieve_cpython.csv",
            "time_csv": time_dir / "sieve_cpython.csv",
        }
        call_count = [0]

        def execute_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise MeasurementError("Benchmark execution failed for hanoi/cpython")
            return success_result

        mock_execute.side_effect = execute_side_effect
        output_dir = tmp_path / "results"
        output_dir.mkdir(parents=True, exist_ok=True)

        result = run_benchmark_suite(
            algorithms=["hanoi", "sieve"],
            methods=["cpython"],
            runs=5,
            output_dir=output_dir,
        )

        assert result is not None
        assert result.name == "GreenScore.csv"
        assert mock_execute.call_count == 2
        mock_greenscore.assert_called_once()

