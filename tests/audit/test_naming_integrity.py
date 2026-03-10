"""
Audit tests: regex and file naming integrity.

Validates that file discovery and aggregation use strict patterns so that
noise files or non-standard naming do not corrupt audit data.
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from pgsi_analyzer.models.aggregation import (
    aggregate_energy,
    aggregate_time,
    stress_test_aggregation_regex,
    ALLOWED_ENERGY_CSV_PATTERN,
    ALLOWED_TIME_CSV_PATTERN,
    _allowed_energy_csv_files,
    _allowed_time_csv_files,
    _is_partial_or_temp,
)
from pgsi_analyzer.benchmark.results_collector import (
    ResultsCollector,
    ENERGY_CSV_PATTERN,
    TIME_CSV_PATTERN,
)
from pgsi_analyzer.utils.errors import AuditError


# Minimal valid energy CSV content (has package (uJ) and methodology)
ENERGY_CSV_CONTENT = "timestamp,function,run,package (uJ),dram (uJ),measurement_method,methodology\n0,a,1,1000,0,hardware,hardware_rapl_linux\n"
# Minimal valid time CSV content
TIME_CSV_CONTENT = "timestamp,function,run,execution_time (s)\n0,a,1,1.0\n"


class TestAggregationRegex:
    """Strict regex and partial-file filtering in aggregation."""

    def test_allowed_energy_pattern_matches(self):
        """^energy_.*\\.csv$ matches energy_*.csv and rejects others."""
        assert ALLOWED_ENERGY_CSV_PATTERN.match("energy_hanoi_cpython.csv")
        assert ALLOWED_ENERGY_CSV_PATTERN.match("energy__double_underscore.csv")
        assert ALLOWED_ENERGY_CSV_PATTERN.match("energy_sort_v2_cpython.csv")
        assert not ALLOWED_ENERGY_CSV_PATTERN.match("valid_energy.csv")
        assert not ALLOWED_ENERGY_CSV_PATTERN.match("hanoi_cpython.csv")
        assert not ALLOWED_ENERGY_CSV_PATTERN.match("energy_data.csv.bak")
        assert not ALLOWED_ENERGY_CSV_PATTERN.match("energy_data.csv.tmp")

    def test_allowed_time_pattern_matches(self):
        """^time_.*\\.csv$ matches time_*.csv and rejects others."""
        assert TIME_CSV_PATTERN.match("time_hanoi_cpython.csv")
        assert TIME_CSV_PATTERN.match("time__double.csv")
        assert not TIME_CSV_PATTERN.match("hanoi_cpython.csv")
        assert not TIME_CSV_PATTERN.match("time_data.csv.bak")

    def test_partial_temp_ignored(self):
        """Partial/temp suffixes are detected."""
        assert _is_partial_or_temp(Path("x.csv.tmp"))
        assert _is_partial_or_temp(Path("x.csv.bak"))
        assert _is_partial_or_temp(Path("x.csv.part"))
        assert not _is_partial_or_temp(Path("energy_x.csv"))

    def test_stress_test_aggregation_regex(self):
        """Stress test: multiple underscores, version numbers, partial files."""
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            (tmp / "energy_sort_v2_cpython.csv").write_text(ENERGY_CSV_CONTENT)
            (tmp / "energy__double_underscore.csv").write_text(ENERGY_CSV_CONTENT)
            (tmp / "energy_legacy.csv.tmp").write_text("x")
            (tmp / "energy_legacy.csv.bak").write_text("x")
            (tmp / "invalid_file.txt").write_text("x")
            (tmp / "energy_data.csv.bak").write_text("x")
            result = stress_test_aggregation_regex(tmp, kind="energy")
            assert result["accepted"] == 2
            assert result["rejected_pattern"] == 0
            assert result["skipped_partial"] == 3  # energy_legacy.csv.tmp, energy_legacy.csv.bak, energy_data.csv.bak

    def test_aggregator_ignores_partial_files(self):
        """Aggregator only processes energy_*.csv and ignores .csv.tmp / .csv.bak."""
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            (tmp / "energy_valid.csv").write_text(ENERGY_CSV_CONTENT)
            (tmp / "energy__double_underscore.csv").write_text(ENERGY_CSV_CONTENT)
            (tmp / "invalid_file.txt").write_text("x")
            (tmp / "energy_data.csv.bak").write_text(ENERGY_CSV_CONTENT)
            (tmp / "energy_other.csv.tmp").write_text(ENERGY_CSV_CONTENT)
            df = aggregate_energy(tmp)
            # Only energy_valid.csv and energy__double_underscore.csv
            assert len(df) == 2
            names = set(df["filename"])
            assert "energy_valid" in names
            assert "energy__double_underscore" in names

    def test_aggregator_time_ignores_partial(self):
        """Time aggregation ignores non-time_*.csv and partial files."""
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            (tmp / "time_valid.csv").write_text(TIME_CSV_CONTENT)
            (tmp / "time_other.csv.tmp").write_text(TIME_CSV_CONTENT)
            (tmp / "random.csv").write_text(TIME_CSV_CONTENT)
            df = aggregate_time(tmp)
            assert len(df) == 1
            assert df["filename"].iloc[0] == "time_valid"


class TestResultsCollectorFilter:
    """ResultsCollector only copies files matching energy_*.csv / time_*.csv."""

    def test_collector_energy_pattern(self):
        """Collector energy pattern matches only energy_*.csv."""
        assert ENERGY_CSV_PATTERN.match("energy_foo.csv")
        assert not ENERGY_CSV_PATTERN.match("foo.csv")
        assert not ENERGY_CSV_PATTERN.match("energy_foo.csv.bak")

    def test_collector_prepare_workspace_copies_only_matching(self):
        """prepare_aggregation_workspace copies only energy_*.csv or time_*.csv."""
        with TemporaryDirectory() as src:
            with TemporaryDirectory() as out:
                src_p = Path(src)
                out_p = Path(out)
                (src_p / "energy_keep.csv").write_text(ENERGY_CSV_CONTENT)
                (src_p / "noise.csv").write_text(ENERGY_CSV_CONTENT)
                (src_p / "invalid_file.txt").write_text("x")
                (src_p / "energy_data.csv.bak").write_text("x")
                collector = ResultsCollector()
                workspace = collector.prepare_aggregation_workspace(
                    out_p, "cpython", [src_p], "energy"
                )
                copied = list(workspace.iterdir())
                assert len(copied) == 1
                assert copied[0].name == "energy_keep.csv"


class TestMethodWhitelist:
    """Method name must be in registry VALID_METHODS."""

    def test_collect_paths_accepts_registered_method(self):
        """collect_paths does not raise when all methods are in VALID_METHODS."""
        collector = ResultsCollector()
        execution_results = {
            "hanoi": {
                "cpython": {"energy_csv": Path("/x/energy_hanoi_cpython.csv"), "time_csv": Path("/x/time_hanoi_cpython.csv")},
            }
        }
        result = collector.collect_paths(execution_results)
        assert "energy" in result
        assert "cpython" in result["energy"]

    def test_collect_paths_raises_audit_error_for_unregistered_method(self):
        """Audit error raised if data file is for a method not in registry."""
        collector = ResultsCollector()
        execution_results = {
            "hanoi": {
                "unknown_method": {"energy_csv": Path("/x/energy_hanoi.csv"), "time_csv": Path("/x/time_hanoi.csv")},
            }
        }
        with pytest.raises(AuditError) as exc_info:
            collector.collect_paths(execution_results)
        assert "not registered" in str(exc_info.value)
        assert "unknown_method" in str(exc_info.value)
