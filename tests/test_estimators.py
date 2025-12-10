"""
Tests for pgsi_analyzer.measurement.estimators module.

This test suite verifies energy estimation functions work correctly
across different platforms and CPU models.
"""

import pytest
from unittest.mock import patch, MagicMock

from pgsi_analyzer.measurement.estimators import (
    get_cpu_tdp,
    estimate_energy_cpu_time,
    estimate_energy_from_psutil,
    estimate_windows,
    estimate_macos,
    estimate_energy,
)


class TestCPUTDP:
    """Tests for CPU TDP lookup function."""

    def test_get_cpu_tdp_intel_core_i7(self):
        """Test TDP lookup for Intel Core i7."""
        tdp = get_cpu_tdp("Intel Core i7")
        assert tdp == 65.0

    def test_get_cpu_tdp_amd_ryzen_5(self):
        """Test TDP lookup for AMD Ryzen 5."""
        tdp = get_cpu_tdp("AMD Ryzen 5")
        assert tdp == 65.0

    def test_get_cpu_tdp_apple_m1(self):
        """Test TDP lookup for Apple M1."""
        tdp = get_cpu_tdp("Apple M1")
        assert tdp == 20.0

    def test_get_cpu_tdp_unknown_cpu(self):
        """Test TDP lookup for unknown CPU returns default."""
        tdp = get_cpu_tdp("Unknown CPU Model XYZ")
        assert tdp == 65.0  # Default TDP

    def test_get_cpu_tdp_case_insensitive(self):
        """Test TDP lookup is case-insensitive."""
        tdp1 = get_cpu_tdp("INTEL CORE I7")
        tdp2 = get_cpu_tdp("intel core i7")
        tdp3 = get_cpu_tdp("Intel Core i7")
        assert tdp1 == tdp2 == tdp3 == 65.0

    def test_get_cpu_tdp_partial_match(self):
        """Test TDP lookup with partial matches."""
        tdp = get_cpu_tdp("Intel Core i7-9700K")
        assert tdp == 65.0


class TestEnergyEstimation:
    """Tests for energy estimation functions."""

    def test_estimate_energy_cpu_time_returns_tuple(self):
        """Test that estimate_energy_cpu_time returns a tuple."""
        result = estimate_energy_cpu_time(1.0)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_estimate_energy_cpu_time_returns_positive_energy(self):
        """Test that estimated energy is positive."""
        energy, model = estimate_energy_cpu_time(1.0)
        assert energy > 0
        assert isinstance(energy, float)

    def test_estimate_energy_cpu_time_returns_model_name(self):
        """Test that estimation model name is returned."""
        energy, model = estimate_energy_cpu_time(1.0)
        assert isinstance(model, str)
        assert len(model) > 0
        assert "TDP" in model or "tdp" in model.lower()

    def test_estimate_energy_cpu_time_with_cpu_info(self):
        """Test estimation with explicit CPU info."""
        cpu_info = {
            "processor": "Intel Core i7",
            "cores_physical": 4,
            "cores_logical": 8,
        }
        energy, model = estimate_energy_cpu_time(1.0, cpu_info)
        assert energy > 0

    def test_estimate_energy_cpu_time_scales_with_time(self):
        """Test that energy scales with CPU time."""
        energy1, _ = estimate_energy_cpu_time(1.0)
        energy2, _ = estimate_energy_cpu_time(2.0)
        # Energy should roughly double (within 10% tolerance for rounding)
        assert abs(energy2 - 2 * energy1) < energy1 * 0.1

    def test_estimate_energy_from_psutil_returns_tuple(self):
        """Test that estimate_energy_from_psutil returns a tuple."""
        result = estimate_energy_from_psutil(1.0)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_estimate_energy_from_psutil_returns_positive_energy(self):
        """Test that estimated energy is positive."""
        energy, model = estimate_energy_from_psutil(1.0)
        assert energy > 0
        assert isinstance(energy, float)

    @patch('pgsi_analyzer.measurement.estimators.psutil.cpu_percent')
    def test_estimate_energy_from_psutil_uses_cpu_percent(self, mock_cpu_percent):
        """Test that estimation uses CPU percent from psutil."""
        mock_cpu_percent.return_value = 80.0
        energy, model = estimate_energy_from_psutil(1.0)
        assert energy > 0
        mock_cpu_percent.assert_called_once()

    def test_estimate_windows_returns_tuple(self):
        """Test that estimate_windows returns a tuple."""
        result = estimate_windows(1.0)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_estimate_windows_returns_positive_energy(self):
        """Test that Windows estimation returns positive energy."""
        energy, model = estimate_windows(1.0)
        assert energy > 0

    def test_estimate_macos_returns_tuple(self):
        """Test that estimate_macos returns a tuple."""
        result = estimate_macos(1.0)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_estimate_macos_returns_positive_energy(self):
        """Test that macOS estimation returns positive energy."""
        energy, model = estimate_macos(1.0)
        assert energy > 0

    @patch('pgsi_analyzer.measurement.estimators.get_cpu_info')
    def test_estimate_macos_apple_silicon(self, mock_get_cpu_info):
        """Test macOS estimation for Apple Silicon."""
        mock_get_cpu_info.return_value = {
            "processor": "Apple M1",
            "cores_physical": 8,
            "cores_logical": 8,
        }
        energy, model = estimate_macos(1.0)
        assert energy > 0

    def test_estimate_energy_platform_agnostic(self):
        """Test that estimate_energy works on any platform."""
        result = estimate_energy(1.0)
        assert isinstance(result, tuple)
        assert len(result) == 2
        energy, model = result
        assert energy > 0

    def test_estimate_energy_reasonable_values(self):
        """Test that estimated energy values are reasonable."""
        # For 1 second of CPU time, energy should be in a reasonable range
        # Typical CPU at 65W TDP, 80% utilization = ~52W average
        # Energy = 52W * 1s = 52J = 52,000,000 μJ
        energy, _ = estimate_energy_cpu_time(1.0)
        
        # Should be between 1 million and 1 billion microjoules for 1 second
        # (1W to 1000W range)
        assert 1e6 <= energy <= 1e9

    def test_estimate_energy_different_cpus(self):
        """Test estimation with different CPU models."""
        cpu_models = [
            {"processor": "Intel Core i3"},
            {"processor": "AMD Ryzen 7"},
            {"processor": "Apple M1"},
        ]
        
        for cpu_info in cpu_models:
            energy, model = estimate_energy_cpu_time(1.0, cpu_info)
            assert energy > 0
            assert isinstance(model, str)


class TestEstimationIntegration:
    """Integration tests for estimation module."""

    def test_estimators_module_imports(self):
        """Test that all estimator functions can be imported."""
        from pgsi_analyzer.measurement.estimators import (
            get_cpu_tdp,
            estimate_energy_cpu_time,
            estimate_energy_from_psutil,
            estimate_windows,
            estimate_macos,
            estimate_energy,
        )
        # If we get here, imports succeeded
        assert True

    def test_estimation_consistency(self):
        """Test that estimation is consistent across calls."""
        energy1, model1 = estimate_energy_cpu_time(1.0)
        energy2, model2 = estimate_energy_cpu_time(1.0)
        
        # Should be very close (within 1% for same inputs)
        assert abs(energy1 - energy2) < energy1 * 0.01
        assert model1 == model2

    def test_estimation_units(self):
        """Test that estimation returns energy in microjoules."""
        energy, _ = estimate_energy_cpu_time(1.0)
        
        # Convert to Joules
        energy_joules = energy / 1e6
        
        # For 1 second at ~50W, should be ~50J = 50,000,000 μJ
        # Check it's in reasonable range (10J to 200J)
        assert 10 <= energy_joules <= 200

