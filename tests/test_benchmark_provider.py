"""
Tests for benchmark FileSystemProvider.

Verifies directory creation, path resolution, and that energy_aggregated.csv
vs time_aggregated.csv are correctly identified.
"""

import pytest
from pathlib import Path

from pgsi_analyzer.benchmark.provider import FileSystemProvider
from pgsi_analyzer.benchmark.results_collector import (
    ENERGY_AGGREGATED,
    TIME_AGGREGATED,
    ENERGY_COMBINED,
    TIME_COMBINED,
    CARBON_FOOTPRINT,
    GREENSCORE,
)


class TestFileSystemProviderOutputPaths:
    """get_output_path returns correct paths for each file type."""

    def test_energy_aggregated_creates_method_dir(self, tmp_path):
        """energy_aggregated returns output_dir/method/energy_aggregated.csv and creates dir."""
        provider = FileSystemProvider()
        p = provider.get_output_path(tmp_path, method="cpython", file_type=ENERGY_AGGREGATED)
        assert p == tmp_path / "cpython" / "energy_aggregated.csv"
        assert p.parent.exists()

    def test_time_aggregated_creates_method_dir(self, tmp_path):
        """time_aggregated returns output_dir/method/time_aggregated.csv."""
        provider = FileSystemProvider()
        p = provider.get_output_path(tmp_path, method="pypy", file_type=TIME_AGGREGATED)
        assert p == tmp_path / "pypy" / "time_aggregated.csv"

    def test_combined_and_final_paths(self, tmp_path):
        """Combined and final file types return correct names."""
        provider = FileSystemProvider()
        assert provider.get_output_path(tmp_path, file_type=ENERGY_COMBINED) == tmp_path / "energy_combined.csv"
        assert provider.get_output_path(tmp_path, file_type=TIME_COMBINED) == tmp_path / "time_combined.csv"
        assert provider.get_output_path(tmp_path, file_type=CARBON_FOOTPRINT) == tmp_path / "carbon_footprint.csv"
        assert provider.get_output_path(tmp_path, file_type=GREENSCORE) == tmp_path / "GreenScore.csv"

    def test_aggregated_requires_method(self):
        """get_output_path for energy_aggregated without method raises."""
        provider = FileSystemProvider()
        with pytest.raises(ValueError, match="method required"):
            provider.get_output_path(Path("/out"), file_type=ENERGY_AGGREGATED)


class TestFileSystemProviderCollectAggregatedPaths:
    """collect_aggregated_paths returns energy and time paths per method."""

    def test_collect_aggregated_paths_identifies_energy_and_time(self, tmp_path):
        """collect_aggregated_paths returns energy_aggregated.csv and time_aggregated.csv per method."""
        provider = FileSystemProvider()
        result = provider.collect_aggregated_paths(tmp_path, ["cpython", "pypy"])
        assert "energy" in result
        assert "time" in result
        assert result["energy"]["cpython"] == tmp_path / "cpython" / "energy_aggregated.csv"
        assert result["energy"]["pypy"] == tmp_path / "pypy" / "energy_aggregated.csv"
        assert result["time"]["cpython"] == tmp_path / "cpython" / "time_aggregated.csv"
        assert result["time"]["pypy"] == tmp_path / "pypy" / "time_aggregated.csv"


class TestFileSystemProviderPrepareWorkspace:
    """prepare_aggregation_workspace copies only matching pattern."""

    def test_prepare_workspace_copies_energy_csv_only(self, tmp_path):
        """Only energy_*.csv files are copied for kind=energy."""
        provider = FileSystemProvider()
        raw = tmp_path / "raw"
        raw.mkdir()
        (raw / "energy_hanoi_cpython.csv").write_text("data\n")
        (raw / "time_hanoi_cpython.csv").write_text("time\n")
        (raw / "other.txt").write_text("x\n")
        out = tmp_path / "out"
        out.mkdir()
        workspace = provider.prepare_aggregation_workspace(out, "cpython", [raw], "energy")
        assert workspace == out / "temp_energy_cpython"
        assert (workspace / "energy_hanoi_cpython.csv").exists()
        assert not (workspace / "time_hanoi_cpython.csv").exists()
        assert not (workspace / "other.txt").exists()
