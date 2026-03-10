# PGSI Analyzer — Final Audit Summary

**Document version:** 1.0  
**Purpose:** Formalize the final state of the audit and package findings for the development roadmap (Issue #6).

---

## 1. Executive Summary

**pgsi-analyzer** is a **robust tool** for measuring Python execution sustainability. It delivers a full pipeline: build (Cython/ctypes), execution across multiple runtimes (CPython, PyPy, Cython, ctypes, py_compile), collection of energy and time data, aggregation and combination, carbon footprint calculation, and a composite **GreenScore** ranking. The design is clear, the registry is a single source of truth for benchmarks, and the test suite covers core logic with a **97% pass rate**. The tool is suitable for research and for comparing execution methods on a fixed set of algorithms.

To **scale beyond the current 15 algorithms** (see **benchmarks/registry.py**) and to improve maintainability and user trust, the audit has identified targeted refactors: **(1)** make run count deterministic by passing **PGSI_RUNS** into subprocesses, **(2)** replace silent RAPL fallback with **permission-aware warnings** on Linux, and **(3)** decompose the **orchestrator** so pipeline logic is separated from filesystem and I/O details. These are captured as sequential, executable roadmap issues in **audit/next_steps_roadmap.md**.

---

## 2. Final Health Status

| Metric | Value |
|--------|--------|
| **Test pass rate** | **97%** (173 passed / 178 total) |
| **Failing tests** | 5 (all platform-dependent) |
| **Skipped tests** | 0 |
| **Coverage (excluding failing test files)** | ~77% (src/pgsi_analyzer) |

**Failure summary:** All 5 failures occur in **measurement/energy** tests and are **platform-dependent** (Windows vs Linux RAPL):

- On **Windows** (and often macOS), the decorator correctly uses **estimation** when pyRAPL is unavailable. Several tests expect **RuntimeError** or hardware-only values; the implementation intentionally does not raise and uses estimation instead. Patches to `_pyrapl_available` / `pyRAPL` can also be ineffective because platform checks run at import time.
- One test enforces a strict energy range (1e3–1e10 μJ) that can be violated on very fast machines under estimation.

**Conclusion:** Core pipeline (orchestrator, executor, builder, models, CLI, registry) is **green**. The failing tests reflect test design vs. current (correct) behavior; fixing them is a test-authoring task (import-time patching or relaxed assertions), not a product defect. See **audit/testing_and_health.md** for details.

---

## 3. Technical Debt Inventory

### 3.0 Completed / Addressed (implemented post-audit)

- **Benchmark Script Stability (Issue D):** **Resolved.** Benchmark scripts were updated to fix syntax errors (e.g. nested quotes in f-strings in hanoi/cython), missing imports (`import os` in binary-trees/ctypes), and parameter alignment with **DEFAULT_PARAMS** (fannkuch-redux uses `n` from config; KeyError avoided). py_compile folders for binary-trees, hanoi, and sieve contain valid **main.py** with correct `sys.path` where needed. regex-redux handles empty or missing input FASTA paths by using a minimal dummy sequence so the benchmark runs without failing. Documentation (**audit/usage_guide.md**, **README.md**) now states PyPy pip install for pandas/psutil/numpy and python3-dev (Linux) for Cython to fix *Python.h* missing errors.

- **RAPL permission warnings (Issue B):** Implemented. When RAPL is unavailable on Linux x86_64 due to permissions, the tool now emits a **UserWarning** with actionable advice (cap_sys_rawio or root). **platform/hardware.py::warn_if_rapl_unavailable()** centralizes the check; **measurement/energy.py** calls it from the pyRAPL setup exception handler. Fallback to estimation is unchanged; the tool does not crash. See **audit/architecture.md** §13.2 and **audit/usage_guide.md** §3.3 (Troubleshooting Permissions).

- **Orchestrator God-file (Issue C):** **Addressed.** **benchmark/results_collector.py** introduces **ResultsCollector** with **collect_paths**, **prepare_aggregation_workspace**, and **get_output_path**. The orchestrator no longer imports **shutil** or **tempfile**; it delegates all CSV collection, workspace preparation, and output path resolution to the collector. **run_benchmark_suite** is a thin coordinator; layout and I/O are testable in isolation. See **audit/architecture.md** §10.1.

- **GreenScore computation and methodology tracking (Issue #4):** **Fully audited and verified.** The GreenScore math (α·energy + β·carbon + γ·time on min–max normalized metrics) is stress-tested in **tests/audit/test_greenscore_integrity.py**. Zero-variance normalization (all methods identical) is handled without division by zero; the score is a stable default (0). **GreenScore.csv** includes **points_measured** and **points_estimated** correctly mapped from the **methodology** column in aggregated energy data (hardware RAPL vs fallback estimation). A **Methodology Consistency** check flags **"Inconsistent Data Source"** when a method has both hardware and estimation points. The **audit_report.json** is augmented after Phase 7 with **data_methodology_summary** (total_points, hardware_percentage, estimation_percentage) and **normalization_bounds** (min/max for energy, time, carbon) so the 0–1 scaling is auditable. See **models/greenscore.py** and **benchmark/orchestrator.py**.

### 3.2 Medium priority: Deterministic run control (PGSI_RUNS)

- **Location:** `benchmark/executor.py`, benchmark scripts / config
- **Issue:** The CLI **--runs** and orchestrator pass `runs` to **execute_benchmark**, but the executor does **not** pass this value to benchmark subprocesses. Scripts use **DEFAULT_PARAMS** (or similar) at import time for decorator `n`, so the user’s `--runs` does not control subprocess iteration count.
- **Impact:** Non-deterministic and confusing: users expect `--runs 5` to mean 5 iterations per benchmark.
- **Recommendation:** Implement **Spike #4** design: set **PGSI_RUNS** in the subprocess environment in the executor; provide a helper (e.g. in config) that reads **PGSI_RUNS** with fallback to DEFAULT_PARAMS; have benchmarks use that helper for decorator `n`. See **Issue A** in **audit/next_steps_roadmap.md**.

### 3.3 Low priority: Coverage for config and validation

- **Locations:** `src/pgsi_analyzer/config.py`, `src/pgsi_analyzer/utils/validation.py`
- **Issue:** **config.py** has ~58% coverage (load_tool_paths branches, .env and path resolution under-exercised). **utils/validation.py** has ~44% coverage (validate_file_path, validate_dataframe, validate_weights, validate_platform, require_columns rarely hit by tests).
- **Impact:** Regressions in path resolution or validation could go unnoticed. Lower risk than orchestrator or run-control issues.
- **Recommendation:** Add unit tests for **load_tool_paths** (env, .env, CLI, defaults) and for each validation function with valid/invalid inputs. Can be done incrementally after Issues A–C.

---

## 4. References

- **audit/functional_overview.md** — Purpose, features, main vs helper logic.
- **audit/architecture.md** — Process boundaries, data pipeline, contracts, ToolPaths, Spike #4 design.
- **audit/testing_and_health.md** — Test map, coverage, failure analysis, known limitations.
- **audit/spike_4_runs_and_permissions.md** — Design for PGSI_RUNS and RAPL warnings.
- **audit/usage_guide.md** — Installation, Golden Path, hardware setup, configuration.
- **audit/contributor_guide.md** — Adding benchmarks, running tests, data contracts.
- **audit/next_steps_roadmap.md** — Sequential Cursor issues A, B, C for implementation.
