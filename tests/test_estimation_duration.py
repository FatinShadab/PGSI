"""Tests for estimation duration selection (PyPy / zero CPU time)."""

from unittest.mock import patch

import pytest

from pgsi_analyzer.measurement.estimation_duration import (
    effective_estimation_duration,
    is_pypy_runtime,
)
from pgsi_analyzer.measurement.estimators import estimate_energy_cpu_time


class TestEffectiveEstimationDuration:
    def test_zero_cpu_uses_wall_on_cpython(self):
        duration, basis = effective_estimation_duration(0.0, 0.5)
        assert basis == "wall_time"
        assert duration == pytest.approx(0.5)

    def test_positive_cpu_uses_wall_when_wall_available(self):
        duration, basis = effective_estimation_duration(0.25, 0.5)
        assert basis == "wall_time"
        assert duration == pytest.approx(0.5)

    def test_inflated_cpu_uses_wall_for_ctypes_like_runs(self):
        """Native extensions can report cpu_time >> wall; energy must follow wall."""
        duration, basis = effective_estimation_duration(9.8, 0.036)
        assert basis == "wall_time"
        assert duration == pytest.approx(0.036)

    @patch("pgsi_analyzer.measurement.estimation_duration.is_pypy_runtime", return_value=True)
    def test_pypy_prefers_wall_when_available(self, _mock_pypy):
        duration, basis = effective_estimation_duration(0.001, 0.4)
        assert basis == "wall_time"
        assert duration == pytest.approx(0.4)

    @patch("pgsi_analyzer.measurement.estimation_duration.is_pypy_runtime", return_value=True)
    def test_pypy_zero_cpu_zero_wall_uses_floor(self, _mock_pypy):
        duration, basis = effective_estimation_duration(0.0, 0.0)
        assert basis == "minimum_floor"
        assert duration == pytest.approx(1e-6)


class TestEstimateEnergyCpuTimeWallFallback:
    def test_zero_cpu_with_wall_produces_larger_energy_than_floor(self):
        floor_energy, _, _ = estimate_energy_cpu_time(0.0, wall_time_seconds=0.0)
        wall_energy, model, _ = estimate_energy_cpu_time(0.0, wall_time_seconds=0.05)
        assert wall_energy > floor_energy
        assert "wall_time" in model

    @patch("pgsi_analyzer.measurement.estimation_duration.is_pypy_runtime", return_value=True)
    def test_pypy_zero_cpu_uses_wall_for_tdp(self, _mock_pypy):
        energy, model, _ = estimate_energy_cpu_time(0.0, wall_time_seconds=0.1)
        assert energy > 12.6
        assert "wall_time" in model
