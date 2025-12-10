"""
Tests for pgsi_analyzer.measurement module.

This test suite verifies energy and time measurement decorators work correctly
with pathlib, platform abstraction, and cross-platform compatibility.
"""

import csv
import json
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from tempfile import TemporaryDirectory

from pgsi_analyzer.measurement import (
    measure_energy_to_csv,
    measure_time_to_csv,
)


class TestTimeMeasurement:
    """Tests for time measurement decorator."""

    def test_measure_time_to_csv_decorator_works(self):
        """Test that time decorator can be applied to a function."""
        @measure_time_to_csv(n=1, csv_filename="test_time")
        def sample_function():
            return 42
        
        result = sample_function()
        assert result == 42

    def test_measure_time_to_csv_creates_directory(self):
        """Test that time decorator creates output directory."""
        with TemporaryDirectory() as tmpdir:
            folder_path = Path(tmpdir) / "test_time_benchmark"
            
            @measure_time_to_csv(n=1, csv_filename="test", folder_name=folder_path)
            def sample_function():
                return 42
            
            sample_function()
            
            assert folder_path.exists()
            assert folder_path.is_dir()

    def test_measure_time_to_csv_creates_csv_file(self):
        """Test that time decorator creates CSV file with correct format."""
        with TemporaryDirectory() as tmpdir:
            folder_path = Path(tmpdir) / "test_time_benchmark"
            csv_file = folder_path / "test.csv"
            
            @measure_time_to_csv(n=2, csv_filename="test", folder_name=folder_path)
            def sample_function():
                time.sleep(0.01)  # Small delay for measurable time
                return 42
            
            sample_function()
            
            assert csv_file.exists()
            
            # Read and verify CSV content
            with csv_file.open('r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
                # Check header
                assert rows[0] == ['timestamp', 'function', 'run', 'execution_time (s)']
                
                # Check data rows
                assert len(rows) == 3  # Header + 2 data rows
                assert rows[1][1] == 'sample_function'
                assert rows[1][2] == '1'
                assert float(rows[1][3]) > 0  # Execution time should be positive
                assert rows[2][2] == '2'

    def test_measure_time_to_csv_creates_system_info_json(self):
        """Test that time decorator creates system info JSON file."""
        with TemporaryDirectory() as tmpdir:
            folder_path = Path(tmpdir) / "test_time_benchmark"
            json_file = folder_path / "system_info.json"
            
            @measure_time_to_csv(n=1, csv_filename="test", folder_name=folder_path)
            def sample_function():
                return 42
            
            sample_function()
            
            assert json_file.exists()
            
            # Read and verify JSON content
            with json_file.open('r', encoding='utf-8') as f:
                system_info = json.load(f)
                
                assert 'CPU' in system_info
                assert 'RAM_GB' in system_info
                assert 'OS' in system_info
                assert 'Architecture' in system_info
                assert 'Test_Result_File' in system_info
                assert 'Platform' in system_info

    def test_measure_time_to_csv_runs_multiple_times(self):
        """Test that time decorator runs function multiple times."""
        with TemporaryDirectory() as tmpdir:
            folder_path = Path(tmpdir) / "test_time_benchmark"
            csv_file = folder_path / "test.csv"
            call_count = {'count': 0}
            
            @measure_time_to_csv(n=5, csv_filename="test", folder_name=folder_path)
            def sample_function():
                call_count['count'] += 1
                return call_count['count']
            
            result = sample_function()
            
            assert result == 5
            assert call_count['count'] == 5
            
            # Verify CSV has 6 rows (header + 5 data rows)
            with csv_file.open('r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                assert len(rows) == 6

    def test_measure_time_to_csv_with_path_object(self):
        """Test that time decorator accepts Path objects."""
        with TemporaryDirectory() as tmpdir:
            folder_path = Path(tmpdir) / "test_time_benchmark"
            
            @measure_time_to_csv(n=1, csv_filename="test", folder_name=folder_path)
            def sample_function():
                return 42
            
            sample_function()
            
            assert (folder_path / "test.csv").exists()

    def test_measure_time_to_csv_preserves_function_metadata(self):
        """Test that time decorator preserves function metadata."""
        @measure_time_to_csv(n=1, csv_filename="test")
        def sample_function():
            """A sample function for testing."""
            return 42
        
        assert sample_function.__name__ == 'sample_function'
        assert 'sample function for testing' in sample_function.__doc__

    def test_measure_time_to_csv_handles_function_arguments(self):
        """Test that time decorator handles function arguments correctly."""
        with TemporaryDirectory() as tmpdir:
            folder_path = Path(tmpdir) / "test_time_benchmark"
            
            @measure_time_to_csv(n=1, csv_filename="test", folder_name=folder_path)
            def add_numbers(a, b, c=10):
                return a + b + c
            
            result = add_numbers(5, 3, c=2)
            assert result == 10


class TestEnergyMeasurement:
    """Tests for energy measurement decorator."""

    @patch('pgsi_analyzer.measurement.energy.is_linux_intel')
    @patch('pgsi_analyzer.measurement.energy._pyrapl_available', False)
    def test_measure_energy_to_csv_raises_error_on_non_linux(self, mock_is_linux_intel):
        """Test that energy decorator raises error on non-Linux systems."""
        mock_is_linux_intel.return_value = False
        
        @measure_energy_to_csv(n=1, csv_filename="test_energy")
        def sample_function():
            return 42
        
        with pytest.raises(RuntimeError) as exc_info:
            sample_function()
        
        assert "only available on Linux" in str(exc_info.value)
        assert "Intel x86_64" in str(exc_info.value)

    @patch('pgsi_analyzer.measurement.energy.is_linux_intel')
    @patch('pgsi_analyzer.measurement.energy._pyrapl_available', False)
    def test_measure_energy_to_csv_raises_error_if_pyrapl_not_installed(self, mock_is_linux_intel):
        """Test that energy decorator raises error if pyRAPL not installed."""
        mock_is_linux_intel.return_value = True
        
        @measure_energy_to_csv(n=1, csv_filename="test_energy")
        def sample_function():
            return 42
        
        with pytest.raises(RuntimeError) as exc_info:
            sample_function()
        
        assert "pyRAPL is not available" in str(exc_info.value)
        assert "pip install" in str(exc_info.value)

    @patch('pgsi_analyzer.measurement.energy._pyrapl_available', True)
    @patch('pgsi_analyzer.measurement.energy.pyRAPL')
    def test_measure_energy_to_csv_creates_directory(self, mock_pyrapl_module):
        """Test that energy decorator creates output directory."""
        # Setup mock pyRAPL
        mock_measurement = MagicMock()
        mock_measurement.result.pkg = [1000000]  # 1 mJ in microjoules
        mock_measurement.result.dram = [500000]
        mock_pyrapl_module.Measurement.return_value = mock_measurement
        # Make pyRAPL available in the module
        import pgsi_analyzer.measurement.energy as energy_module
        energy_module.pyRAPL = mock_pyrapl_module
        
        with TemporaryDirectory() as tmpdir:
            folder_path = Path(tmpdir) / "test_energy_benchmark"
            
            @measure_energy_to_csv(n=1, csv_filename="test", folder_name=folder_path)
            def sample_function():
                return 42
            
            sample_function()
            
            assert folder_path.exists()
            assert folder_path.is_dir()

    @patch('pgsi_analyzer.measurement.energy._pyrapl_available', True)
    @patch('pgsi_analyzer.measurement.energy.pyRAPL')
    def test_measure_energy_to_csv_creates_csv_file(self, mock_pyrapl_module):
        """Test that energy decorator creates CSV file with correct format."""
        # Setup mock pyRAPL
        mock_measurement = MagicMock()
        mock_measurement.result.pkg = [1000000]
        mock_measurement.result.dram = [500000]
        mock_pyrapl_module.Measurement.return_value = mock_measurement
        # Make pyRAPL available in the module
        import pgsi_analyzer.measurement.energy as energy_module
        energy_module.pyRAPL = mock_pyrapl_module
        
        with TemporaryDirectory() as tmpdir:
            folder_path = Path(tmpdir) / "test_energy_benchmark"
            csv_file = folder_path / "test.csv"
            
            @measure_energy_to_csv(n=2, csv_filename="test", folder_name=folder_path)
            def sample_function():
                return 42
            
            sample_function()
            
            assert csv_file.exists()
            
            # Read and verify CSV content
            with csv_file.open('r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
                # Check header
                assert 'timestamp' in rows[0]
                assert 'function' in rows[0]
                assert 'run' in rows[0]
                assert 'package (uJ)' in rows[0]
                assert 'dram (uJ)' in rows[0]
                assert 'measurement_method' in rows[0]
                
                # Check data rows
                assert len(rows) == 3  # Header + 2 data rows
                assert rows[1][1] == 'sample_function'
                assert rows[1][2] == '1'
                assert rows[1][3] == '1000000'  # Package energy
                assert rows[1][4] == '500000'    # DRAM energy
                assert rows[1][5] == 'hardware'  # Measurement method

    @patch('pgsi_analyzer.measurement.energy._pyrapl_available', True)
    @patch('pgsi_analyzer.measurement.energy.pyRAPL')
    def test_measure_energy_to_csv_creates_system_info_json(self, mock_pyrapl_module):
        """Test that energy decorator creates system info JSON file."""
        # Setup mock pyRAPL
        mock_measurement = MagicMock()
        mock_measurement.result.pkg = [1000000]
        mock_measurement.result.dram = [500000]
        mock_pyrapl_module.Measurement.return_value = mock_measurement
        # Make pyRAPL available in the module
        import pgsi_analyzer.measurement.energy as energy_module
        energy_module.pyRAPL = mock_pyrapl_module
        
        with TemporaryDirectory() as tmpdir:
            folder_path = Path(tmpdir) / "test_energy_benchmark"
            json_file = folder_path / "system_info_pyrapl.json"
            
            @measure_energy_to_csv(n=1, csv_filename="test", folder_name=folder_path)
            def sample_function():
                return 42
            
            sample_function()
            
            assert json_file.exists()
            
            # Read and verify JSON content
            with json_file.open('r', encoding='utf-8') as f:
                system_info = json.load(f)
                
                assert 'CPU' in system_info
                assert 'RAM_GB' in system_info
                assert 'OS' in system_info
                assert 'Architecture' in system_info
                assert 'Test_Result_File' in system_info
                assert 'Platform' in system_info

    @patch('pgsi_analyzer.measurement.energy._pyrapl_available', True)
    @patch('pgsi_analyzer.measurement.energy.pyRAPL')
    def test_measure_energy_to_csv_runs_multiple_times(self, mock_pyrapl_module):
        """Test that energy decorator runs function multiple times."""
        # Setup mock pyRAPL
        mock_measurement = MagicMock()
        mock_measurement.result.pkg = [1000000]
        mock_measurement.result.dram = [500000]
        mock_pyrapl_module.Measurement.return_value = mock_measurement
        # Make pyRAPL available in the module
        import pgsi_analyzer.measurement.energy as energy_module
        energy_module.pyRAPL = mock_pyrapl_module
        
        with TemporaryDirectory() as tmpdir:
            folder_path = Path(tmpdir) / "test_energy_benchmark"
            csv_file = folder_path / "test.csv"
            call_count = {'count': 0}
            
            @measure_energy_to_csv(n=3, csv_filename="test", folder_name=folder_path)
            def sample_function():
                call_count['count'] += 1
                return call_count['count']
            
            result = sample_function()
            
            assert result == 3
            assert call_count['count'] == 3
            
            # Verify pyRAPL.Measurement was called 3 times
            assert mock_pyrapl_module.Measurement.call_count == 3
            
            # Verify CSV has 4 rows (header + 3 data rows)
            with csv_file.open('r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                assert len(rows) == 4

    @patch('pgsi_analyzer.measurement.energy._pyrapl_available', True)
    @patch('pgsi_analyzer.measurement.energy.pyRAPL')
    def test_measure_energy_to_csv_with_path_object(self, mock_pyrapl_module):
        """Test that energy decorator accepts Path objects."""
        # Setup mock pyRAPL
        mock_measurement = MagicMock()
        mock_measurement.result.pkg = [1000000]
        mock_measurement.result.dram = [500000]
        mock_pyrapl_module.Measurement.return_value = mock_measurement
        # Make pyRAPL available in the module
        import pgsi_analyzer.measurement.energy as energy_module
        energy_module.pyRAPL = mock_pyrapl_module
        
        with TemporaryDirectory() as tmpdir:
            folder_path = Path(tmpdir) / "test_energy_benchmark"
            
            @measure_energy_to_csv(n=1, csv_filename="test", folder_name=folder_path)
            def sample_function():
                return 42
            
            sample_function()
            
            assert (folder_path / "test.csv").exists()

    @patch('pgsi_analyzer.measurement.energy._pyrapl_available', True)
    @patch('pgsi_analyzer.measurement.energy.pyRAPL')
    def test_measure_energy_to_csv_handles_no_dram(self, mock_pyrapl_module):
        """Test that energy decorator handles missing DRAM measurement."""
        # Setup mock pyRAPL with no DRAM
        mock_measurement = MagicMock()
        mock_measurement.result.pkg = [1000000]
        mock_measurement.result.dram = None
        mock_pyrapl_module.Measurement.return_value = mock_measurement
        # Make pyRAPL available in the module
        import pgsi_analyzer.measurement.energy as energy_module
        energy_module.pyRAPL = mock_pyrapl_module
        
        with TemporaryDirectory() as tmpdir:
            folder_path = Path(tmpdir) / "test_energy_benchmark"
            csv_file = folder_path / "test.csv"
            
            @measure_energy_to_csv(n=1, csv_filename="test", folder_name=folder_path)
            def sample_function():
                return 42
            
            sample_function()
            
            # Verify DRAM is 0 when not available
            with csv_file.open('r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                assert rows[1][4] == '0'  # DRAM should be 0


class TestMeasurementIntegration:
    """Integration tests for measurement modules."""

    def test_measurement_modules_import(self):
        """Test that measurement modules can be imported."""
        from pgsi_analyzer.measurement import (
            measure_energy_to_csv,
            measure_time_to_csv,
        )
        assert callable(measure_energy_to_csv)
        assert callable(measure_time_to_csv)

    @patch('pgsi_analyzer.measurement.energy._pyrapl_available', True)
    @patch('pgsi_analyzer.measurement.energy.pyRAPL')
    def test_both_decorators_work_together(self, mock_pyrapl_module):
        """Test that both decorators can be used on the same function."""
        # Setup mock pyRAPL
        mock_measurement = MagicMock()
        mock_measurement.result.pkg = [1000000]
        mock_measurement.result.dram = [500000]
        mock_pyrapl_module.Measurement.return_value = mock_measurement
        # Make pyRAPL available in the module
        import pgsi_analyzer.measurement.energy as energy_module
        energy_module.pyRAPL = mock_pyrapl_module
        
        with TemporaryDirectory() as tmpdir:
            energy_folder = Path(tmpdir) / "energy"
            time_folder = Path(tmpdir) / "time"
            
            @measure_energy_to_csv(n=1, csv_filename="test", folder_name=energy_folder)
            @measure_time_to_csv(n=1, csv_filename="test", folder_name=time_folder)
            def sample_function():
                return 42
            
            result = sample_function()
            
            assert result == 42
            assert (energy_folder / "test.csv").exists()
            assert (time_folder / "test.csv").exists()

    def test_pathlib_usage_in_time_decorator(self):
        """Test that time decorator uses pathlib.Path exclusively."""
        with TemporaryDirectory() as tmpdir:
            folder_path = Path(tmpdir) / "test_time"
            
            @measure_time_to_csv(n=1, csv_filename="test", folder_name=folder_path)
            def sample_function():
                return 42
            
            sample_function()
            
            # Verify all paths are Path objects (no os.path usage)
            assert isinstance(folder_path, Path)
            assert (folder_path / "test.csv").exists()

    @patch('pgsi_analyzer.measurement.energy._pyrapl_available', True)
    @patch('pgsi_analyzer.measurement.energy.pyRAPL')
    def test_pathlib_usage_in_energy_decorator(self, mock_pyrapl_module):
        """Test that energy decorator uses pathlib.Path exclusively."""
        # Setup mock pyRAPL
        mock_measurement = MagicMock()
        mock_measurement.result.pkg = [1000000]
        mock_measurement.result.dram = [500000]
        mock_pyrapl_module.Measurement.return_value = mock_measurement
        # Make pyRAPL available in the module
        import pgsi_analyzer.measurement.energy as energy_module
        energy_module.pyRAPL = mock_pyrapl_module
        
        with TemporaryDirectory() as tmpdir:
            folder_path = Path(tmpdir) / "test_energy"
            
            @measure_energy_to_csv(n=1, csv_filename="test", folder_name=folder_path)
            def sample_function():
                return 42
            
            sample_function()
            
            # Verify all paths are Path objects (no os.path usage)
            assert isinstance(folder_path, Path)
            assert (folder_path / "test.csv").exists()

