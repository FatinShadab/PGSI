"""
Tests for pgsi_analyzer.measurement.estimators module.

This test suite verifies energy estimation functions work correctly
across different platforms and CPU models.
"""

import pytest
from unittest.mock import patch, MagicMock

from pgsi_analyzer.measurement.estimators import (
    get_cpu_tdp,
    resolve_cpu_power_provenance,
    estimate_energy_cpu_time,
    estimate_energy_from_codecarbon,
    estimate_energy_from_psutil,
    estimate_windows,
    estimate_macos,
    estimate_energy,
    CODECARBON_TDP_MAX_RATIO,
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
        assert tdp == 10.0

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
        assert tdp == 95.0


class TestEnergyEstimation:
    """Tests for energy estimation functions."""

    def test_estimate_energy_cpu_time_returns_tuple(self):
        """Test that estimate_energy_cpu_time returns a tuple (energy, model, methodology)."""
        result = estimate_energy_cpu_time(1.0)
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_estimate_energy_cpu_time_returns_positive_energy(self):
        """Test that estimated energy is positive."""
        energy, model, methodology = estimate_energy_cpu_time(1.0)
        assert energy > 0
        assert isinstance(energy, float)

    def test_estimate_energy_cpu_time_returns_model_name(self):
        """Test that estimation model name is returned."""
        energy, model, methodology = estimate_energy_cpu_time(1.0)
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
        energy, model, methodology = estimate_energy_cpu_time(1.0, cpu_info)
        assert energy > 0

    def test_estimate_energy_cpu_time_scales_with_time(self):
        """Test that energy scales with CPU time."""
        energy1, _, _ = estimate_energy_cpu_time(1.0)
        energy2, _, _ = estimate_energy_cpu_time(2.0)
        # Energy should roughly double (within 10% tolerance for rounding)
        assert abs(energy2 - 2 * energy1) < energy1 * 0.1

    def test_estimate_energy_from_psutil_returns_tuple(self):
        """Test that estimate_energy_from_psutil returns a tuple (energy, model, methodology)."""
        result = estimate_energy_from_psutil(1.0)
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_estimate_energy_from_psutil_returns_positive_energy(self):
        """Test that estimated energy is positive."""
        energy, model, methodology = estimate_energy_from_psutil(1.0)
        assert energy > 0
        assert isinstance(energy, float)

    @patch('pgsi_analyzer.measurement.estimators.psutil.cpu_percent')
    def test_estimate_energy_from_psutil_uses_cpu_percent(self, mock_cpu_percent):
        """Test that estimation uses CPU percent from psutil."""
        mock_cpu_percent.return_value = 80.0
        energy, model, methodology = estimate_energy_from_psutil(1.0)
        assert energy > 0
        mock_cpu_percent.assert_called_once()

    def test_estimate_windows_returns_tuple(self):
        """Test that estimate_windows returns a tuple."""
        result = estimate_windows(1.0)
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_estimate_windows_returns_positive_energy(self):
        """Test that Windows estimation returns positive energy."""
        energy, model, methodology = estimate_windows(1.0)
        assert energy > 0

    def test_estimate_macos_returns_tuple(self):
        """Test that estimate_macos returns a tuple."""
        result = estimate_macos(1.0)
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_estimate_macos_returns_positive_energy(self):
        """Test that macOS estimation returns positive energy."""
        energy, model, methodology = estimate_macos(1.0)
        assert energy > 0

    @patch('pgsi_analyzer.measurement.estimators.get_cpu_info')
    def test_estimate_macos_apple_silicon(self, mock_get_cpu_info):
        """Test macOS estimation for Apple Silicon."""
        mock_get_cpu_info.return_value = {
            "processor": "Apple M1",
            "cores_physical": 8,
            "cores_logical": 8,
        }
        energy, model, methodology = estimate_macos(1.0)
        assert energy > 0

    def test_estimate_energy_platform_agnostic(self):
        """Test that estimate_energy works on any platform."""
        result = estimate_energy(1.0)
        assert isinstance(result, tuple)
        assert len(result) == 3
        energy, model, methodology = result
        assert energy > 0
        assert methodology in ("dataset_tdp", "generic_tdp", "estimated_codecarbon")

    def test_estimate_energy_reasonable_values(self):
        """Test that estimated energy values are reasonable."""
        # For 1 second of CPU time, energy should be in a reasonable range
        # Typical CPU at 65W TDP, 80% utilization = ~52W average
        # Energy = 52W * 1s = 52J = 52,000,000 μJ
        energy, _, _ = estimate_energy_cpu_time(1.0)
        
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
            energy, model, methodology = estimate_energy_cpu_time(1.0, cpu_info)
            assert energy > 0
            assert isinstance(model, str)
            assert methodology in ("dataset_tdp", "generic_tdp", "estimated_codecarbon")


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
        energy1, model1, meth1 = estimate_energy_cpu_time(1.0)
        energy2, model2, meth2 = estimate_energy_cpu_time(1.0)
        
        # Should be very close (within 1% for same inputs)
        assert abs(energy1 - energy2) < energy1 * 0.01
        assert model1 == model2
        assert meth1 == meth2

    def test_estimation_units(self):
        """Test that estimation returns energy in microjoules."""
        energy, _, _ = estimate_energy_cpu_time(1.0)
        
        # Convert to Joules
        energy_joules = energy / 1e6
        
        # For 1 second at ~50W, should be ~50J = 50,000,000 μJ
        # Check it's in reasonable range (10J to 200J)
        assert 10 <= energy_joules <= 200


class TestCodeCarbonEstimation:
    """Tests for CodeCarbon-based estimation helper."""

    def test_estimate_energy_from_codecarbon_uses_tracker_energy_when_in_band(self):
        wall = 0.5
        tdp_energy, _, _ = estimate_energy_cpu_time(
            0.0, {"processor": "Intel Core i7"}, wall_time_seconds=wall
        )
        # Pick CC within [0.5, 2.0]× TDP band
        cc_kwh = (tdp_energy * 1.25) / 3.6e12
        tracker = MagicMock()
        tracker.final_emissions_data = MagicMock()
        tracker.final_emissions_data.energy_consumed = cc_kwh
        tracker.final_emissions_data.country_name = "Testland"

        energy, model, methodology = estimate_energy_from_codecarbon(
            cpu_time_seconds=9.0,
            tracker=tracker,
            emissions_kg=0.0,
            cpu_info={"processor": "Intel Core i7"},
            wall_time_seconds=wall,
        )

        assert energy == pytest.approx(tdp_energy * 1.25)
        assert "CodeCarbon" in model
        assert methodology == "estimated_codecarbon"

    def test_estimate_energy_from_codecarbon_floors_when_below_tdp(self):
        """Tiny CodeCarbon readings (common on PyPy) must not undercut duration×TDP."""
        tracker = MagicMock()
        tracker.final_emissions_data = MagicMock()
        tracker.final_emissions_data.energy_consumed = 1e-12  # kWh — positive but negligible

        energy, model, methodology = estimate_energy_from_codecarbon(
            cpu_time_seconds=0.0,
            tracker=tracker,
            emissions_kg=0.0,
            cpu_info={"processor": "Intel Core i7"},
            wall_time_seconds=0.5,
        )

        tdp_energy, _, tdp_meth = estimate_energy_cpu_time(
            0.0,
            {"processor": "Intel Core i7"},
            wall_time_seconds=0.5,
        )
        assert energy == pytest.approx(tdp_energy)
        assert "TDP floor" in model
        assert methodology == tdp_meth

    def test_estimate_energy_from_codecarbon_ceiling_when_above_tdp(self):
        """Short ctypes/cython runs: CodeCarbon can over-report vs wall×TDP."""
        wall = 0.036
        tdp_energy, _, tdp_meth = estimate_energy_cpu_time(
            9.8,
            {"processor": "Intel Core i7"},
            wall_time_seconds=wall,
        )
        # Simulate inflated CodeCarbon (~535M uJ for ~2M uJ TDP)
        cc_kwh = (tdp_energy * 100) / 3.6e12
        tracker = MagicMock()
        tracker.final_emissions_data = MagicMock()
        tracker.final_emissions_data.energy_consumed = cc_kwh

        energy, model, methodology = estimate_energy_from_codecarbon(
            cpu_time_seconds=9.8,
            tracker=tracker,
            emissions_kg=0.0,
            cpu_info={"processor": "Intel Core i7"},
            wall_time_seconds=wall,
        )

        assert energy == pytest.approx(tdp_energy)
        assert "TDP ceiling" in model
        assert methodology == tdp_meth
        assert (tdp_energy * CODECARBON_TDP_MAX_RATIO) < tdp_energy * 100

    def test_fast_run_energy_scales_with_wall_not_cpu(self):
        """Energy for a 36ms wall run must not use multi-second process_time."""
        wall = 0.036
        energy_wall, model, _ = estimate_energy_cpu_time(
            9.8, {"processor": "Intel Core i7"}, wall_time_seconds=wall
        )
        energy_cpu, _, _ = estimate_energy_cpu_time(
            9.8, {"processor": "Intel Core i7"}, wall_time_seconds=0.0
        )
        assert "wall_time" in model
        assert energy_wall < energy_cpu * 0.1

    def test_estimate_energy_from_codecarbon_falls_back_when_missing_energy(self):
        tracker = MagicMock()
        tracker.final_emissions_data = MagicMock()
        tracker.final_emissions_data.energy_consumed = None

        energy, model, methodology = estimate_energy_from_codecarbon(
            cpu_time_seconds=1.0,
            tracker=tracker,
            emissions_kg=0.0,
            cpu_info={"processor": "Unknown"},
        )

        assert energy > 0
        assert methodology in ("dataset_tdp", "generic_tdp")

    def test_estimate_energy_from_codecarbon_fallback_uses_wall_when_cpu_zero(self):
        tracker = MagicMock()
        tracker.final_emissions_data = MagicMock()
        tracker.final_emissions_data.energy_consumed = None

        energy_floor, _, _ = estimate_energy_from_codecarbon(
            cpu_time_seconds=0.0,
            tracker=tracker,
            emissions_kg=0.0,
            cpu_info={"processor": "Unknown"},
            wall_time_seconds=0.0,
        )
        energy_wall, model, _ = estimate_energy_from_codecarbon(
            cpu_time_seconds=0.0,
            tracker=tracker,
            emissions_kg=0.0,
            cpu_info={"processor": "Unknown"},
            wall_time_seconds=0.05,
        )

        assert energy_wall > energy_floor
        assert "wall_time" in model

    def test_resolve_cpu_power_provenance_raspberry_pi(self):
        provenance = resolve_cpu_power_provenance("ARM Cortex-A72 BCM2711")
        assert provenance["methodology"] in ("dataset_tdp", "generic_tdp")
        assert provenance["source"] in ("codecarbon_cpu_power_csv", "generic_tdp_default")

    def test_resolve_cpu_power_provenance_unknown(self):
        provenance = resolve_cpu_power_provenance("mystery-cpu-123")
        assert provenance["methodology"] == "generic_tdp"
        assert provenance["source"] == "generic_tdp_default"

