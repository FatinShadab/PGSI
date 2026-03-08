"""
Audit tests: path resolution and execution verification (audit_report.json).

Validates that the audit report records requested/resolved/runtime-reported paths,
path_source (env/cli/system_default), path_integrity, and severity HIGH on mismatch.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from pgsi_analyzer.benchmark.executor import (
    AuditLogger,
    get_runtime_executable,
    AUDIT_REPORT_FILENAME,
)
from pgsi_analyzer.config import load_tool_paths, ToolPaths


class TestGetRuntimeExecutable:
    """Path identity check: interpreter reports its own sys.executable."""

    def test_returns_stripped_stdout(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="/usr/bin/python3\n")
            out = get_runtime_executable("/usr/bin/python3", {})
            assert out == "/usr/bin/python3"

    def test_returns_none_on_nonzero_exit(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            assert get_runtime_executable("/usr/bin/python3", {}) is None

    def test_returns_none_on_exception(self):
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            assert get_runtime_executable("/nonexistent/python", {}) is None


class TestAuditLoggerReport:
    """audit_report.json structure and path_integrity / severity."""

    def test_to_report_dict_includes_path_source_and_integrity(self):
        logger = AuditLogger()
        logger.set_path_identity("cpython", "/usr/bin/python3", "/usr/bin/python3")
        path_sources = {
            "python": {"path": "/usr/bin/python3", "source": "env"},
            "pypy": {"path": None, "source": "system_default"},
            "c_compiler": {"path": None, "source": "system_default"},
        }
        report = logger.to_report_dict(path_sources)
        assert "path_entries" in report
        assert report["severity"] == "NONE"
        entry = report["path_entries"][0]
        assert entry["method"] == "cpython"
        assert entry["requested_path"] == "/usr/bin/python3"
        assert entry["resolved_path"] == "/usr/bin/python3"
        assert entry["runtime_reported_path"] == "/usr/bin/python3"
        assert entry["path_source"] == "env"
        assert entry["path_integrity"] is True

    def test_path_mismatch_sets_severity_high(self):
        """When .env path is valid but interpreter reports a different location (e.g. symlink/PATH shadowing)."""
        logger = AuditLogger()
        # Resolved (what we invoked) vs runtime-reported (what the process says) differ
        logger.set_path_identity(
            "cpython",
            "/opt/pgsi/python3",  # what config resolved
            "/usr/bin/python3.8",  # what the subprocess actually reported
        )
        path_sources = {
            "python": {"path": "/opt/pgsi/python3", "source": "env"},
            "pypy": {"path": None, "source": "system_default"},
            "c_compiler": {"path": None, "source": "system_default"},
        }
        report = logger.to_report_dict(path_sources)
        assert report["severity"] == "HIGH"
        assert "message" in report
        assert "mismatch" in report["message"].lower()
        entry = report["path_entries"][0]
        assert entry["path_integrity"] is False
        assert entry["resolved_path"] == "/opt/pgsi/python3"
        assert entry["runtime_reported_path"] == "/usr/bin/python3.8"


class TestEnvFileSource:
    """Audit report identifies path source as .env when loaded from env file."""

    def test_load_tool_paths_returns_path_sources_with_env_source(self, tmp_path):
        """Use tmp_path to create a custom .env; verify path_sources identifies env as source."""
        env_file = tmp_path / ".env"
        env_file.write_text(f"PGSI_PYTHON_PATH={sys.executable}\n", encoding="utf-8")
        tool_paths, path_sources = load_tool_paths(env_file=env_file)
        # When .env is loaded, Python path should be from env (file was loaded into os.environ)
        assert path_sources["python"]["source"] == "env"
        assert path_sources["python"]["path"] is not None

    def test_load_tool_paths_cli_overrides_env_source(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("PGSI_PYTHON_PATH=/from/env\n", encoding="utf-8")
        tool_paths, path_sources = load_tool_paths(
            env_file=env_file,
            cli_python=sys.executable,
        )
        assert path_sources["python"]["source"] == "cli"


class TestAuditReportProduced:
    """audit_report.json is produced after suite run."""

    @patch("pgsi_analyzer.benchmark.orchestrator.calculate_greenscore")
    @patch("pgsi_analyzer.benchmark.orchestrator.calculate_carbon_footprint")
    @patch("pgsi_analyzer.benchmark.orchestrator.combine_time_results")
    @patch("pgsi_analyzer.benchmark.orchestrator.combine_energy_results")
    @patch("pgsi_analyzer.benchmark.orchestrator.aggregate_time")
    @patch("pgsi_analyzer.benchmark.orchestrator.aggregate_energy")
    @patch("pgsi_analyzer.benchmark.orchestrator.ResultsCollector")
    @patch("pgsi_analyzer.benchmark.orchestrator.execute_benchmark")
    @patch("pgsi_analyzer.benchmark.orchestrator.get_benchmark_path")
    @patch("pgsi_analyzer.benchmark.orchestrator.requires_build")
    def test_audit_report_json_written_after_phase2(
        self,
        mock_requires_build,
        mock_get_path,
        mock_execute,
        mock_collector_cls,
        mock_agg_energy,
        mock_agg_time,
        mock_combine_energy,
        mock_combine_time,
        mock_carbon,
        mock_greenscore,
        tmp_path,
    ):
        import pandas as pd
        from pgsi_analyzer.benchmark.results_collector import (
            ENERGY_AGGREGATED,
            TIME_AGGREGATED,
            ENERGY_COMBINED,
            TIME_COMBINED,
            CARBON_FOOTPRINT,
            GREENSCORE,
        )
        from pgsi_analyzer.benchmark.orchestrator import run_benchmark_suite

        mock_requires_build.return_value = False
        mock_get_path.return_value = tmp_path / "bench" / "main.py"
        (tmp_path / "bench").mkdir(parents=True)
        (tmp_path / "bench" / "main.py").write_text("")
        out_dir = tmp_path / "results"
        out_dir.mkdir()
        energy_dir = out_dir / "temp_energy_cpython"
        time_dir = out_dir / "temp_time_cpython"
        energy_dir.mkdir()
        time_dir.mkdir()
        (energy_dir / "energy_hanoi_cpython.csv").write_text(
            "timestamp,function,run,package (uJ),dram (uJ),measurement_method,methodology\n0,a,1,100,0,e,m\n"
        )
        (time_dir / "time_hanoi_cpython.csv").write_text(
            "timestamp,function,run,execution_time (s)\n0,a,1,1.0\n"
        )
        mock_execute.return_value = {
            "energy_csv": energy_dir / "energy_hanoi_cpython.csv",
            "time_csv": time_dir / "time_hanoi_cpython.csv",
        }
        mock_collector = MagicMock()
        mock_collector.collect_paths.return_value = {
            "energy": {"cpython": [energy_dir]},
            "time": {"cpython": [time_dir]},
        }
        mock_collector.prepare_aggregation_workspace.return_value = energy_dir

        def _get_output_path(od, method=None, file_type=None):
            od = Path(od)
            if method:
                if file_type == ENERGY_AGGREGATED:
                    return od / method / "energy_aggregated.csv"
                if file_type == TIME_AGGREGATED:
                    return od / method / "time_aggregated.csv"
            if file_type == ENERGY_COMBINED:
                return od / "energy_combined.csv"
            if file_type == TIME_COMBINED:
                return od / "time_combined.csv"
            if file_type == CARBON_FOOTPRINT:
                return od / "carbon_footprint.csv"
            if file_type == GREENSCORE:
                return od / "GreenScore.csv"
            return od / str(file_type)

        mock_collector.get_output_path.side_effect = _get_output_path
        mock_collector_cls.return_value = mock_collector
        mock_combine_energy.return_value = None
        mock_combine_time.return_value = None
        mock_carbon.return_value = MagicMock()
        mock_greenscore.return_value = pd.DataFrame({"method": ["cpython"], "green_score": [0.5]})
        # Phase 7 reads energy_combined and time_combined CSVs
        (out_dir / "energy_combined.csv").write_text("algorithm,cpython\nhanoi,100\n")
        (out_dir / "time_combined.csv").write_text("algorithm,cpython\nhanoi,1.0\n")

        run_benchmark_suite(
            algorithms=["hanoi"],
            methods=["cpython"],
            runs=2,
            output_dir=out_dir,
            path_sources={
                "python": {"path": sys.executable, "source": "env"},
                "pypy": {"path": None, "source": "system_default"},
                "c_compiler": {"path": None, "source": "system_default"},
            },
        )

        report_path = out_dir / AUDIT_REPORT_FILENAME
        assert report_path.exists(), "audit_report.json must be produced after suite run"
        data = json.loads(report_path.read_text())
        assert "path_entries" in data
        assert "timestamp" in data
        assert "severity" in data
        assert "data_methodology_summary" in data, "audit_report.json must contain data_methodology_summary"
        assert "total_points" in data["data_methodology_summary"]
        assert "hardware_percentage" in data["data_methodology_summary"]
        assert "estimation_percentage" in data["data_methodology_summary"]
        assert "normalization_bounds" in data
        assert "energy" in data["normalization_bounds"]
        assert "time" in data["normalization_bounds"]
        assert "carbon" in data["normalization_bounds"]
