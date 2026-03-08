"""
Tests for benchmark results_collector module.
"""

import pytest
from pathlib import Path

from pgsi_analyzer.benchmark.results_collector import (
    ResultsCollector,
    ENERGY_AGGREGATED,
    TIME_AGGREGATED,
    ENERGY_COMBINED,
    TIME_COMBINED,
    CARBON_FOOTPRINT,
    GREENSCORE,
)


class TestResultsCollectorCollectPaths:
    """Test ResultsCollector.collect_paths groups by method."""

    def test_collect_paths_groups_by_method(self):
        """collect_paths groups energy and time CSV paths by execution method."""
        collector = ResultsCollector()
        # execution_results: algorithm -> method -> { energy_csv, time_csv }
        d_energy = Path("/run/hanoi/cpython/energy_benchmark")
        d_time = Path("/run/hanoi/cpython/time_benchmark")
        execution_results = {
            "hanoi": {
                "cpython": {
                    "energy_csv": d_energy / "hanoi_cpython.csv",
                    "time_csv": d_time / "hanoi_cpython.csv",
                },
            },
            "sieve": {
                "cpython": {
                    "energy_csv": d_energy / "sieve_cpython.csv",  # same dir
                    "time_csv": d_time / "sieve_cpython.csv",
                },
                "pypy": {
                    "energy_csv": Path("/run/sieve/pypy/energy_benchmark/sieve_pypy.csv"),
                    "time_csv": Path("/run/sieve/pypy/time_benchmark/sieve_pypy.csv"),
                },
            },
        }
        collected = collector.collect_paths(execution_results)

        assert "energy" in collected
        assert "time" in collected
        # cpython: one dir for energy (shared by hanoi and sieve), one for time
        assert collected["energy"]["cpython"] == [d_energy]
        assert collected["time"]["cpython"] == [d_time]
        # pypy: one dir each
        assert len(collected["energy"]["pypy"]) == 1
        assert collected["energy"]["pypy"][0].name == "energy_benchmark"
        assert len(collected["time"]["pypy"]) == 1
        assert collected["time"]["pypy"][0].name == "time_benchmark"

    def test_collect_paths_skips_missing_keys(self):
        """collect_paths skips algorithms/methods without energy_csv or time_csv."""
        collector = ResultsCollector()
        execution_results = {
            "hanoi": {
                "cpython": {"energy_csv": Path("/a/energy.csv")},  # no time_csv
                "pypy": {"time_csv": Path("/b/time.csv")},  # no energy_csv
            },
        }
        collected = collector.collect_paths(execution_results)
        assert collected["energy"]["cpython"] == [Path("/a")]
        assert collected["time"]["pypy"] == [Path("/b")]
        assert "pypy" not in collected["energy"]
        assert "cpython" not in collected["time"]


class TestResultsCollectorGetOutputPath:
    """Test ResultsCollector.get_output_path."""

    def test_get_output_path_aggregated_creates_method_dir(self, tmp_path):
        """get_output_path for energy_aggregated returns output_dir/method/energy_aggregated.csv."""
        collector = ResultsCollector()
        p = collector.get_output_path(tmp_path, method="cpython", file_type=ENERGY_AGGREGATED)
        assert p == tmp_path / "cpython" / "energy_aggregated.csv"
        p = collector.get_output_path(tmp_path, method="pypy", file_type=TIME_AGGREGATED)
        assert p == tmp_path / "pypy" / "time_aggregated.csv"

    def test_get_output_path_combined_and_final(self, tmp_path):
        """get_output_path for combined/carbon/GreenScore returns correct names."""
        collector = ResultsCollector()
        assert collector.get_output_path(tmp_path, file_type=ENERGY_COMBINED) == tmp_path / "energy_combined.csv"
        assert collector.get_output_path(tmp_path, file_type=TIME_COMBINED) == tmp_path / "time_combined.csv"
        assert collector.get_output_path(tmp_path, file_type=CARBON_FOOTPRINT) == tmp_path / "carbon_footprint.csv"
        assert collector.get_output_path(tmp_path, file_type=GREENSCORE) == tmp_path / "GreenScore.csv"

    def test_get_output_path_aggregated_requires_method(self):
        """get_output_path for energy_aggregated without method raises."""
        collector = ResultsCollector()
        with pytest.raises(ValueError, match="method required"):
            collector.get_output_path(Path("/out"), file_type=ENERGY_AGGREGATED)


class TestResultsCollectorPrepareAggregationWorkspace:
    """Test ResultsCollector.prepare_aggregation_workspace."""

    def test_prepare_aggregation_workspace_copies_csvs(self, tmp_path):
        """prepare_aggregation_workspace creates dir and copies energy_*.csv from raw_dirs."""
        collector = ResultsCollector()
        raw1 = tmp_path / "raw1"
        raw1.mkdir()
        (raw1 / "energy_a.csv").write_text("col\n1\n")
        (raw1 / "energy_b.csv").write_text("col\n2\n")
        raw2 = tmp_path / "raw2"
        raw2.mkdir()
        (raw2 / "energy_c.csv").write_text("col\n3\n")
        out = tmp_path / "results"
        out.mkdir()

        workspace = collector.prepare_aggregation_workspace(
            out, "cpython", [raw1, raw2], "energy"
        )
        assert workspace == out / "temp_energy_cpython"
        assert workspace.exists()
        assert (workspace / "energy_a.csv").read_text() == "col\n1\n"
        assert (workspace / "energy_b.csv").read_text() == "col\n2\n"
        assert (workspace / "energy_c.csv").read_text() == "col\n3\n"
