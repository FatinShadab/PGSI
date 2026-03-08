# PGSI Analyzer — Architectural Changes

**Purpose:** Differences between the architecture documented in `audit_old/` and the current implementation. For the current system description, see [README.md](./README.md).

---

## 1. Summary of Changes

| Area | Old (audit_old) | Current |
|------|------------------|---------|
| **Orchestrator I/O** | Delegated to ResultsCollector (prepare_workspace, get_output_path) | Delegated to **FileSystemProvider**; orchestrator accepts optional `provider`; ResultsCollector delegates to same provider |
| **New module** | — | **benchmark/provider.py** (FileSystemProvider) |
| **ResultsCollector** | Own implementation of prepare_aggregation_workspace, get_output_path | **Delegates** to FileSystemProvider; keeps collect_paths and constants/patterns |
| **Audit / methodology** | Raw CSV without methodology column | Raw energy CSV has **methodology** (hardware_rapl_linux, estimated_cpu_tdp, estimated_fallback_generic); GreenScore has **points_measured**, **points_estimated**, **data_source_consistency** |
| **Audit report** | Path identity (requested/resolved/runtime) | Same plus **data_methodology_summary**, **normalization_bounds** (after Phase 7) |
| **File naming** | General *.csv or algo_method naming | **Strict regex**: only `^energy_.*\.csv$` and `^time_.*\.csv$` accepted for aggregation; partial/temp suffixes excluded |
| **Exceptions** | No AuditError | **AuditError** for unregistered method in collector |
| **PGSI_RUNS** | Documented as gap (Spike #4) | **Implemented**: executor sets PGSI_RUNS; config.get_measurement_runs(algorithm); benchmarks use it for decorator n |
| **RAPL permissions** | Silent fallback | **warn_if_rapl_unavailable** (platform/hardware.py); UserWarning with cap_sys_rawio/root suggestion on Linux |
| **GreenScore normalization** | Min-max | Same; **zero-variance** handling (constant row → 0) to avoid division by zero |
| **Aggregation** | Read CSVs from folder | **Strict pattern** filtering; **methodology** column preserved in aggregate_energy |

---

## 2. Structural Changes

### 2.1 New Component: FileSystemProvider

- **Added:** `src/pgsi_analyzer/benchmark/provider.py`.
- **Reason:** Separate pipeline coordination from filesystem I/O so that:
  - The orchestrator does not perform direct `shutil.copy2` or path construction.
  - Tests can inject a mock provider and run the full pipeline without disk I/O.
  - Path and workspace logic is unit-tested in one place (FileSystemProvider).
- **Responsibilities:** `prepare_aggregation_workspace`, `get_output_path`, `collect_aggregated_paths`. Uses patterns and constants from `results_collector` (ENERGY_CSV_PATTERN, TIME_CSV_PATTERN, GARBAGE_ENTRIES, file-type constants).
- **Benefit:** Improved testability and maintainability; clear boundary between “what to do” (orchestrator) and “how to do I/O” (provider).

### 2.2 Orchestrator

- **Change:** `run_benchmark_suite` now accepts an optional **`provider`** argument (default: `FileSystemProvider()`). All workspace preparation and output path resolution go through **`fs_provider`** (and optionally the same instance is passed to `ResultsCollector(provider=fs_provider)`).
- **Removed from orchestrator:** Direct use of ResultsCollector for `prepare_aggregation_workspace` and `get_output_path`; orchestrator no longer calls these on the collector for Phase 4–7 path resolution, only on the provider.
- **Reason:** Single place to mock for integration tests; no shutil or glob in orchestrator.
- **Reference:** `benchmark/orchestrator.py` (provider parameter; fs_provider.prepare_aggregation_workspace, fs_provider.get_output_path).

### 2.3 ResultsCollector

- **Change:** No longer implements `prepare_aggregation_workspace` or `get_output_path`; it **delegates** to an internal `FileSystemProvider` (or an injected one). Constructor: `ResultsCollector(provider=None)`.
- **Unchanged:** `collect_paths(execution_results)` still groups energy/time CSV paths by method; raises **AuditError** if a method is not in **VALID_METHODS** (registry whitelist).
- **Reason:** Backward compatibility for code that still calls `collector.prepare_aggregation_workspace` or `collector.get_output_path`; single implementation lives in FileSystemProvider.
- **Reference:** `benchmark/results_collector.py`.

---

## 3. Module Responsibility Changes

### 3.1 Aggregation and File Naming

- **Old:** Aggregation read CSV files from a folder with minimal naming contract.
- **Current:** `models/aggregation.py` uses **ALLOWED_ENERGY_CSV_PATTERN** (`^energy_.*\.csv$`) and **ALLOWED_TIME_CSV_PATTERN** (`^time_.*\.csv$`); excludes files matching **PARTIAL_CSV_SUFFIXES** (e.g. `.csv.tmp`, `.csv.bak`). **methodology** column is read and preserved in `aggregate_energy` output.
- **Reason:** Audit and reproducibility: only intentionally named files are aggregated; methodology is traceable to GreenScore and audit report.
- **Reference:** `models/aggregation.py`; `benchmark/results_collector.py` (ENERGY_CSV_PATTERN, TIME_CSV_PATTERN).

### 3.2 Measurement and Methodology

- **Old:** Raw energy CSV had measurement_method (and similar); no standardized “methodology” tag for hardware vs estimation.
- **Current:** `measurement/energy.py` writes a **methodology** column: `hardware_rapl_linux` for pyRAPL; for estimation, the value comes from estimators (e.g. `estimated_cpu_tdp`, `estimated_fallback_generic`). `measurement/estimators.py` returns 3-tuples `(energy, model_name, methodology_tag)`.
- **Reason:** Enables GreenScore and audit report to report “measured” vs “estimated” counts and to flag mixed methodology per method.
- **Reference:** `measurement/energy.py`, `measurement/estimators.py`.

### 3.3 GreenScore

- **Old:** Output columns: method, energy_mean, time_mean, carbon_mean, green_score.
- **Current:** Additionally **points_measured**, **points_estimated** (from aggregated energy methodology counts), and **data_source_consistency** (“Consistent” vs “Inconsistent Data Source” when a method has both hardware and estimated points). **Zero-variance** handling in `normalize_metrics`: if `row.max() == row.min()`, normalized row is `row * 0` to avoid division by zero.
- **Reason:** Research validity and auditability; consistent handling of edge cases.
- **Reference:** `models/greenscore.py`.

### 3.4 Audit Report

- **Old:** audit_report.json contained path_entries (requested_path, resolved_path, runtime_reported_path, path_source, path_integrity) and severity.
- **Current:** Same, plus after Phase 7 the orchestrator **augments** the report with:
  - **data_methodology_summary:** total_points, hardware_percentage, estimation_percentage (from GreenScore points_measured/points_estimated when present).
  - **normalization_bounds:** min/max for energy, time, carbon (from combined DataFrames) so 0–1 scaling is auditable.
- **Reason:** Full audit trail for methodology mix and normalization range.
- **Reference:** `benchmark/orchestrator.py` (post–Phase 7 JSON read/update/write).

### 3.5 Config and Executor

- **Old (doc):** Spike #4 described PGSI_RUNS and run-count helper as design.
- **Current:** **Implemented.** Executor sets `PGSI_RUNS` in subprocess env; `config.get_measurement_runs(algorithm)` reads it with fallback to DEFAULT_PARAMS; benchmark scripts use it for decorator `n`. RAPL permission feedback: **platform/hardware.py** provides `warn_if_rapl_unavailable(exc)`; **measurement/energy.py** calls it when pyRAPL setup fails (e.g. PermissionError).
- **Reference:** `config.py`, `benchmark/executor.py`, `platform/hardware.py`, `measurement/energy.py`.

---

## 4. New Components and Files

| Component | Location | Purpose |
|-----------|----------|---------|
| **FileSystemProvider** | `benchmark/provider.py` | Workspace creation, pattern-based copy, output path resolution, collect_aggregated_paths |
| **AuditError** | `utils/errors.py` | Raised when collector finds data for a method not in VALID_METHODS |
| **get_runtime_executable** | `benchmark/executor.py` | Runs interpreter with `-c "import sys; print(sys.executable)"` for path identity |
| **AuditLogger** | `benchmark/executor.py` | Already in old doc; still captures executions and path identity for audit_report.json |
| **stress_test_aggregation_regex** | `models/aggregation.py` | Test helper for regex/partial-file behavior |
| **collect_aggregated_paths** | `benchmark/provider.py` | Returns { "energy": { method: path }, "time": { method: path } } for aggregated files |

---

## 5. Removed or Deprecated

- **None.** No modules or public APIs were removed. ResultsCollector’s `prepare_aggregation_workspace` and `get_output_path` remain as delegators to the provider.

---

## 6. Refactoring and Design Decisions

### 6.1 Provider Injection

- **Decision:** Orchestrator takes optional `provider: Optional[FileSystemProvider] = None` and uses it for all workspace and path operations; ResultsCollector is constructed with the same provider when used by the orchestrator.
- **Reason:** Enables testing the pipeline with a mock provider (no real file creation); keeps production default as real FileSystemProvider.
- **Benefit:** Scalability of tests; clear dependency inversion for I/O.

### 6.2 Methodology and Audit Trail

- **Decision:** Every energy data point is labeled with a methodology tag; GreenScore and audit report summarize hardware vs estimation and normalization bounds.
- **Reason:** Research and reproducibility: readers can see what fraction of data was hardware-measured vs estimated and verify normalization ranges.
- **Benefit:** Research validity; easier to detect misconfiguration (e.g. RAPL not used when expected).

### 6.3 Strict File Naming

- **Decision:** Only `energy_*.csv` and `time_*.csv` are accepted for aggregation; partial/temp suffixes are excluded; collector uses the same patterns for workspace copy.
- **Reason:** Avoid accidental inclusion of unrelated or partial files; consistent contract for tooling and audits.
- **Benefit:** Maintainability; fewer surprises when adding new benchmarks or cleaning output dirs.

### 6.4 Zero-Variance GreenScore

- **Decision:** When all methods have the same value for a metric (row), normalized value is set to 0 instead of dividing by zero.
- **Reason:** Stable behavior when there is no variation (e.g. all methods identical).
- **Benefit:** Robustness; no runtime error on edge-case inputs.

---

## 7. Benefits Gained

| Benefit | How it is achieved |
|---------|--------------------|
| **Scalability** | Provider abstraction allows swapping or mocking I/O; registry and config remain single source of truth for benchmarks and tools. |
| **Maintainability** | Clear split: orchestrator = phases; provider = paths and copies; collector = grouping; models = data transforms. |
| **Testability** | Mock provider in orchestrator tests; unit tests for FileSystemProvider path/pattern behavior; no need for real directories in pipeline tests. |
| **Research validity** | Methodology tagging, methodology summary in report, normalization bounds, path identity and path_integrity in audit report. |
| **Performance** | No structural change aimed at performance; same pipeline stages and subprocess model. |

---

## 8. Migration Notes

- **Existing scripts/tests** that call `ResultsCollector().prepare_aggregation_workspace` or `ResultsCollector().get_output_path` continue to work; they delegate to the default FileSystemProvider.
- **New tests** that want to avoid disk I/O should pass a mock `FileSystemProvider` into `run_benchmark_suite(..., provider=mock_provider)` and, if needed, into `ResultsCollector(provider=mock_provider)` when the collector is used.
- **Raw CSV consumers:** If downstream tools parse raw energy CSVs, they may now see a **methodology** column; combined and aggregated CSVs may carry methodology where applicable.
- **Documentation:** Old architecture docs in `audit_old/` still describe the pre–FileSystemProvider design (orchestrator delegating to ResultsCollector for I/O). The current design is described in `docs/architecture/README.md` and this file.

---

## 9. References to Old Documentation

- **audit_old/architecture.md** — Previous process boundaries, data pipeline, ToolPaths, ResultsCollector responsibilities, Mermaid diagram (orchestrator used ResultsCollector for I/O; no FileSystemProvider). Section 10.1 described orchestrator + ResultsCollector only.
- **audit_old/functional_overview.md** — Purpose, entry points, module list (no provider); still accurate for CLI and high-level flow.
- **audit_old/contributor_guide.md** — Data contracts updated to include methodology and file naming (energy_*.csv, time_*.csv); adding algorithms/methods still follows the same pattern plus VALID_METHODS.
- **audit_old/final_summary.md** — Completed items now include GreenScore methodology tracking and audit report augmentation; executor suite migrated to tmp_path (Issue #6); FileSystemProvider (Issue #5) is the current I/O abstraction.
