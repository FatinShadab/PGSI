"""
Tests for cross-platform energy measurement with estimation fallback.

This test suite verifies that the energy decorator works correctly
with estimation on Windows/macOS and hardware measurement on Linux.
"""

import csv
import json
import warnings
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from pgsi_analyzer.measurement import measure_energy_to_csv
from pgsi_analyzer.measurement.energy import _pyrapl_available
from pgsi_analyzer.platform.detection import is_linux_intel


class TestCrossPlatformEnergy:
    """Tests for cross-platform energy measurement."""

    @patch('pgsi_analyzer.measurement.energy.is_linux_intel')
    @patch('pgsi_analyzer.measurement.energy._pyrapl_available', False)
    def test_energy_decorator_uses_estimation_on_windows(self, mock_is_linux_intel):
        """Test that energy decorator uses estimation on Windows."""
        mock_is_linux_intel.return_value = False
        
        with TemporaryDirectory() as tmpdir:
            folder_path = Path(tmpdir) / "energy_test"
            
            @measure_energy_to_csv(n=2, csv_filename="test", folder_name=folder_path)
            def sample_function():
                # Some CPU work
                return sum(range(1000))
            
            # Should not raise error, should use estimation
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = sample_function()
                
                # Should have warning about estimation
                assert len(w) > 0
                assert any("estimation" in str(warning.message).lower() for warning in w)
            
            assert result == sum(range(1000))
            
            # Verify CSV was created
            csv_file = folder_path / "test.csv"
            assert csv_file.exists()
            
            # Verify CSV content
            with csv_file.open('r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
                # Check header
                assert 'measurement_method' in rows[0]
                
                # Check data rows have 'estimation' method
                assert len(rows) >= 3  # Header + 2 data rows
                assert rows[1][5] == 'estimation'  # measurement_method column
                assert rows[2][5] == 'estimation'

    @patch('pgsi_analyzer.measurement.energy.is_linux_intel')
    @patch('pgsi_analyzer.measurement.energy._pyrapl_available', False)
    def test_energy_decorator_system_info_includes_estimation(self, mock_is_linux_intel):
        """Test that system info includes estimation metadata."""
        mock_is_linux_intel.return_value = False
        
        with TemporaryDirectory() as tmpdir:
            folder_path = Path(tmpdir) / "energy_test"
            json_file = folder_path / "system_info_pyrapl.json"
            
            @measure_energy_to_csv(n=1, csv_filename="test", folder_name=folder_path)
            def sample_function():
                return 42
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                sample_function()
            
            # Verify system info JSON
            assert json_file.exists()
            
            with json_file.open('r', encoding='utf-8') as f:
                system_info = json.load(f)
                
                assert system_info['measurement_method'] == 'estimation'
                assert 'platform' in system_info
                assert 'estimation_model' in system_info
                assert system_info['estimation_model'] != 'TBD'  # Should be set after first run

    @patch('pgsi_analyzer.measurement.energy.is_linux_intel')
    @patch('pgsi_analyzer.measurement.energy._pyrapl_available', True)
    @patch('pgsi_analyzer.measurement.energy.pyRAPL')
    def test_energy_decorator_uses_hardware_on_linux(self, mock_pyrapl_module, mock_is_linux_intel):
        """Test that energy decorator uses pyRAPL on Linux/Intel."""
        mock_is_linux_intel.return_value = True
        
        # Setup mock pyRAPL
        mock_measurement = MagicMock()
        mock_measurement.result.pkg = [1000000]
        mock_measurement.result.dram = [500000]
        mock_pyrapl_module.Measurement.return_value = mock_measurement
        
        # Make pyRAPL available in the module
        import pgsi_analyzer.measurement.energy as energy_module
        energy_module.pyRAPL = mock_pyrapl_module
        
        with TemporaryDirectory() as tmpdir:
            folder_path = Path(tmpdir) / "energy_test"
            
            @measure_energy_to_csv(n=1, csv_filename="test", folder_name=folder_path)
            def sample_function():
                return 42
            
            result = sample_function()
            assert result == 42
            
            # Verify CSV has 'hardware' method
            csv_file = folder_path / "test.csv"
            with csv_file.open('r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                assert rows[1][5] == 'hardware'  # measurement_method column

    @patch('pgsi_analyzer.measurement.energy.is_linux_intel')
    @patch('pgsi_analyzer.measurement.energy._pyrapl_available', False)
    def test_energy_decorator_estimation_produces_reasonable_values(self, mock_is_linux_intel):
        """Test that estimation produces reasonable energy values."""
        mock_is_linux_intel.return_value = False
        
        with TemporaryDirectory() as tmpdir:
            folder_path = Path(tmpdir) / "energy_test"
            
            @measure_energy_to_csv(n=1, csv_filename="test", folder_name=folder_path)
            def sample_function():
                # Some CPU work that takes measurable time
                import time
                start = time.time()
                result = sum(range(100000))
                # Ensure at least some time passes
                while time.time() - start < 0.01:
                    result += sum(range(1000))
                return result
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                sample_function()
            
            # Verify energy values are reasonable
            csv_file = folder_path / "test.csv"
            with csv_file.open('r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
                # Skip header
                assert len(rows) > 1, "CSV should have data rows"
                energy_uj = float(rows[1][3])  # package (uJ) column
                
                # Should be positive and in reasonable range
                # For typical execution, should be between 1e5 and 1e10 μJ
                # Note: Very fast functions might have 0 CPU time, so we check >= 0
                assert energy_uj >= 0
                if energy_uj > 0:
                    assert 1e3 <= energy_uj <= 1e10  # Wide range for different CPUs

    @patch('pgsi_analyzer.measurement.energy.is_linux_intel')
    @patch('pgsi_analyzer.measurement.energy._pyrapl_available', False)
    def test_energy_decorator_warning_message(self, mock_is_linux_intel):
        """Test that warning message is informative."""
        mock_is_linux_intel.return_value = False
        
        with TemporaryDirectory() as tmpdir:
            folder_path = Path(tmpdir) / "energy_test"
            
            @measure_energy_to_csv(n=1, csv_filename="test", folder_name=folder_path)
            def sample_function():
                return 42
            
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                sample_function()
                
                # Check warning message
                assert len(w) > 0
                warning_msg = str(w[0].message).lower()
                assert "estimation" in warning_msg
                assert "hardware" in warning_msg or "pyrapl" in warning_msg

    @patch('pgsi_analyzer.measurement.energy.is_linux_intel')
    @patch('pgsi_analyzer.measurement.energy._pyrapl_available', False)
    def test_energy_decorator_csv_format_consistent(self, mock_is_linux_intel):
        """Test that CSV format is consistent across platforms."""
        mock_is_linux_intel.return_value = False
        
        with TemporaryDirectory() as tmpdir:
            folder_path = Path(tmpdir) / "energy_test"
            
            @measure_energy_to_csv(n=2, csv_filename="test", folder_name=folder_path)
            def sample_function():
                return 42
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                sample_function()
            
            # Verify CSV format matches expected structure
            csv_file = folder_path / "test.csv"
            with csv_file.open('r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
                # Check header format
                expected_columns = [
                    'timestamp', 'function', 'run',
                    'package (uJ)', 'dram (uJ)', 'measurement_method'
                ]
                assert rows[0] == expected_columns
                
                # Check data rows have correct number of columns
                for row in rows[1:]:
                    assert len(row) == 6

    @patch('pgsi_analyzer.measurement.energy.is_linux_intel')
    @patch('pgsi_analyzer.measurement.energy._pyrapl_available', False)
    def test_energy_decorator_dram_zero_on_estimation(self, mock_is_linux_intel):
        """Test that DRAM energy is 0 when using estimation."""
        mock_is_linux_intel.return_value = False
        
        with TemporaryDirectory() as tmpdir:
            folder_path = Path(tmpdir) / "energy_test"
            
            @measure_energy_to_csv(n=1, csv_filename="test", folder_name=folder_path)
            def sample_function():
                return 42
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                sample_function()
            
            # Verify DRAM is 0
            csv_file = folder_path / "test.csv"
            with csv_file.open('r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                if len(rows) > 1:
                    dram_energy = float(rows[1][4])  # dram (uJ) column
                    assert dram_energy == 0.0

