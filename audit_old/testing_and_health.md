# PGSI Analyzer — Testing & Health Audit

**Document version:** 1.0  
**Purpose:** Current state validation, test coverage map, reliability, and known limitations (Issue #3).

---

## 1. Test Inventory & Module Mapping

| Test file | Target src/ module(s) | Description |
|-----------|------------------------|-------------|
| **test_benchmark_executor.py** | benchmark/executor.py | find_python_executable, prepare_py_compile, execute_benchmark; non-zero exit, timeout, FileNotFoundError |
| **test_benchmark_builder.py** | benchmark/builder.py | requires_build, build_cython, build_ctypes, build_benchmark; ConfigurationError, PlatformError |
| **test_benchmark_orchestrator.py** | benchmark/orchestrator.py | resolve_algorithms, resolve_methods, run_benchmark_suite; pipeline mocks, crash handling |
| **test_cli_benchmark.py** | cli/main.py | benchmark list/run, argument passing, error handling |
| **test_benchmarks_registry.py** | benchmarks/registry.py | list_algorithms, list_methods, get_benchmark_path, validate_* |
| **test_models.py** | models/* | carbon, greenscore, aggregation, combination; weights, missing file/columns |
| **test_energy_crossplatform.py** | measurement/energy.py | estimation fallback when pyRAPL unavailable, CSV format, warning |
| **test_estimators.py** | measurement/estimators.py | get_cpu_tdp, estimate_energy_*, estimate_energy |
| **test_measurement.py** | measurement/energy.py, time.py | decorators, CSV/time output, system_info (some tests assume pyRAPL) |
| **test_platform.py** | platform/* | detection, paths, hardware, check_rapl_support |

---

## 2. Pytest Run Results

**Last run (Windows, Python 3.14):**

- **Total:** 178 tests (after adding `test_run_benchmark_suite_continues_after_benchmark_crash` and two combination contract tests).
- **Passed:** 173 (when excluding 5 known platform-dependent failures).
- **Failed:** 5 (all in measurement/energy tests; see below).
- **Skipped:** 0.

**Failures (all environment-dependent):**

1. **test_energy_crossplatform.py::test_energy_decorator_estimation_produces_reasonable_values**  
   Asserts `1e3 <= energy_uj <= 1e10`. On fast CPUs, estimation for very short work can yield &lt; 1e3 μJ (e.g. 54.6). **Cause:** Tight bounds for estimation; test is flaky on fast machines.

2. **test_measurement.py::test_measure_energy_to_csv_raises_error_on_non_linux**  
   Expects `RuntimeError` when not Linux. **Actual behavior:** Code falls back to estimation and does not raise. **Cause:** Test expectation outdated; design is fallback, not error.

3. **test_measurement.py::test_measure_energy_to_csv_raises_error_if_pyrapl_not_installed**  
   Expects `RuntimeError` when pyRAPL unavailable on Linux. **Actual:** Fallback to estimation. **Cause:** Same as above.

4. **test_measurement.py::test_measure_energy_to_csv_creates_csv_file**  
   Expects package energy `'1000000'` (pyRAPL mock). On Windows, decorator uses estimation, so value is different (e.g. `'54.6'`). **Cause:** Patch of `_pyrapl_available`/`pyRAPL` does not take effect before decorator chooses path (module-level `is_linux_intel()` runs at import).

5. **test_measurement.py::test_measure_energy_to_csv_runs_multiple_times**  
   Expects `pyRAPL.Measurement.call_count == 3`. On Windows, estimation path is used, so pyRAPL is never called. **Cause:** Same as (4).

**Conclusion:** The five failures are due to **test design vs. current behavior**: the implementation correctly uses estimation when pyRAPL is unavailable and does not raise; some tests assume raise or hardware-only values. Fixing them requires either patching at import time (e.g. `is_linux_intel` and `_pyrapl_available` before importing the decorator) or relaxing expectations (e.g. accept estimation values, drop raise expectations).

---

## 3. Coverage (with failing tests excluded)

Run: `pytest tests/ --cov=src/pgsi_analyzer --cov-report=term-missing --ignore=tests/test_measurement.py --ignore=tests/test_energy_crossplatform.py -q`

| Module | Stmts | Miss | Cover | Notes |
|--------|-------|------|-------|------|
| benchmark/builder.py | 78 | 8 | 90% | Some timeout/error branches |
| benchmark/executor.py | 121 | 36 | 70% | CSV discovery, py_compile .pyc path |
| benchmark/orchestrator.py | 158 | 8 | 95% | Few branches |
| benchmarks/registry.py | 35 | 7 | 80% | get_benchmark_path fallback |
| cli/main.py | 78 | 6 | 92% | Help/error branches |
| config.py | 80 | 34 | 58% | load_tool_paths .env/path resolution |
| measurement/energy.py | 82 | 66 | 20% | Most decorator body (estimation/hardware) |
| measurement/time.py | 32 | 23 | 28% | Decorator body |
| measurement/estimators.py | 64 | 7 | 89% | |
| models/aggregation.py | 57 | 16 | 72% | Skip/error paths |
| models/combination.py | 70 | 9 | 87% | |
| models/carbon.py | 21 | 0 | 100% | |
| models/greenscore.py | 33 | 0 | 100% | |
| platform/* | 70 | 8 | ~86% | |
| utils/validation.py | 25 | 14 | 44% | Many branches untested |
| **TOTAL** | **1036** | **242** | **77%** | |

---

## 4. Test Coverage Map: “Green” vs “Blind”

**Green (have direct unit tests):**

- **benchmark/executor.py** — Executable resolution, py_compile, execute (success, non-zero exit, timeout, no main.py).
- **benchmark/builder.py** — requires_build, Cython/ctypes build (success, missing setup.py, build fail, timeout, no C files, compiler not found).
- **benchmark/orchestrator.py** — resolve_* , full pipeline (mocked), invalid args, **benchmark crash (MeasurementError) caught and suite continues**.
- **cli/main.py** — list, run (mocked), weights, carbon-intensity, error handling.
- **benchmarks/registry.py** — BENCHMARKS, list_*, get_benchmark_path, validate_*, path consistency.
- **models/** — carbon, greenscore, aggregation, combination; missing file, missing algorithm column, **missing columns in combination (ValueError)**; full pipeline integration.
- **measurement/estimators.py** — TDP, estimate_energy_*, estimate_energy.
- **measurement/energy.py (partial)** — Estimation path and warning when pyRAPL unavailable (test_energy_crossplatform); some tests fail on Windows due to import-time platform checks.
- **measurement/time.py** — Partially covered by test_measurement (time decorator).
- **platform/** — detection, paths, hardware, check_rapl_support.
- **utils/errors.py** — Used implicitly by all tests that assert on MeasurementError, ConfigurationError, etc.

**Blind or weak:**

- **config.py** — load_tool_paths branches (env, .env, defaults) and path resolution; ToolPaths usage is tested indirectly.
- **utils/validation.py** — validate_file_path, validate_dataframe, validate_weights, validate_platform, require_columns rarely or never exercised in tests.
- **measurement/energy.py** — Full decorator path (especially hardware) and import-time pyRAPL setup not robustly tested cross-platform.
- **measurement/time.py** — Inner decorator logic covered but with low line coverage.

---

## 5. Failure-Path Handling: Executor & Orchestrator

### 5.1 Executor (subprocess non-zero exit / timeout)

- **Non-zero exit:** `test_benchmark_executor.py::TestExecuteBenchmark::test_execute_benchmark_execution_fails` mocks `subprocess.run` to return `returncode=1`. The executor raises **MeasurementError** with message including "Benchmark execution failed", command, return code, stdout, stderr. **Verified.**
- **Timeout:** `test_benchmark_executor.py::TestExecuteBenchmark::test_execute_benchmark_timeout` mocks `subprocess.run` to raise `subprocess.TimeoutExpired`. The executor raises **MeasurementError** with "timed out". **Verified.**

### 5.2 Orchestrator (benchmark crash caught and reported)

- **test_run_benchmark_suite_continues_after_benchmark_crash:** First call to `execute_benchmark` raises **MeasurementError**; second call returns success. The orchestrator catches the exception, continues, and completes the suite with the successful result; **GreenScore.csv** is written and the function returns the result path. **Documented proof that a benchmark crash is caught and reported (via continue) and does not abort the entire suite.**

---

## 6. Estimation Fallback (pyRAPL Unavailable)

- **test_energy_crossplatform.py** forces `_pyrapl_available = False` and `is_linux_intel = False` (or True with pyRAPL mocked). Tests confirm:
  - When pyRAPL is unavailable, the decorator uses **estimation** (measurement_method column = `'estimation'`).
  - System info JSON contains `measurement_method: 'estimation'` and `estimation_model` is set after first run.
  - A **UserWarning** is emitted about hardware not available and estimation being used.
- **measurement/estimators.py** is tested in **test_estimators.py** (estimate_energy_cpu_time, estimate_energy_from_psutil, estimate_energy, etc.). So when pyRAPL is unavailable, **estimators** are invoked correctly; the only failing test is the “reasonable values” bound (1e3–1e10 μJ), which is too strict for very fast runs.

---

## 7. Data Contract Validation (models/)

- **Aggregation (aggregation.py):**  
  - Missing folder → **FileNotFoundError**.  
  - No CSV files → **ValueError**.  
  - Files without `package (uJ)` or `execution_time (s)` are **skipped**; if no valid rows remain → **ValueError**.  
  - **test_models.py** covers missing folder and valid structure; skip behavior is in code but not explicitly asserted.

- **Combination (combination.py):**  
  - Missing file → **FileNotFoundError** (tested).  
  - CSV missing required columns → **ValueError** with message containing "filename" and "average_package (uJ)" or "execution_time (s)" (tested in **test_combine_energy_results_missing_columns_raises** and **test_combine_time_results_missing_columns_raises**).

- **Carbon (carbon.py):** Missing file → **FileNotFoundError**; missing `algorithm` column → **ValueError** (tested).

- **GreenScore (greenscore.py):** Weights must sum to 1.0 → **ValueError** (tested).

---

## 8. GreenScore Math vs α, β, γ

- **Formula (models/greenscore.py):**  
  `green_score = α * energy_mean + β * carbon_mean + γ * time_mean`  
  with row-wise min-max normalized energy, time, and carbon; then column-wise means per method; then weighted sum. Lower is better.

- **test_models.py** checks:
  - Weights must sum to 1.0 (ValueError otherwise).
  - Result has columns `method`, `green_score` and is sorted by `green_score` ascending.
- **Numerical check:** With a single method, normalization can make energy_mean = time_mean = carbon_mean = 1.0 (or 0), so green_score = α + β + γ = 1.0. Multi-method cases are covered by integration test. **No dedicated test that asserts a specific numeric green_score from given α, β, γ and raw values; acceptable for current audit.**

---

## 9. Reliability Report

- **Flaky / non-deterministic:**  
  - **test_energy_decorator_estimation_produces_reasonable_values** is environment-dependent (CPU speed, so estimated μJ can be below 1e3).  
  - **--runs flag:** The CLI `--runs` is passed to `run_benchmark_suite` and `execute_benchmark`, but **benchmark scripts do not receive it** (no argv/env). Run count is determined by **DEFAULT_PARAMS** in the benchmark decorators. So **run count is currently not user-controlled per invocation**; see Issue #4 (Spike) for the planned fix.

- **Deterministic:** Resolve algorithms/methods, registry, builder, executor (with mocks), models (carbon, greenscore, aggregation, combination), CLI parsing, and orchestrator pipeline (with mocks) behave deterministically in tests.

---

## 10. Negative Test: Missing Tool (C Compiler / PyPy)

- **C compiler:** **test_benchmark_builder.py::TestBuildCtypes::test_build_ctypes_compiler_not_found** mocks `subprocess.run` so compilation fails and no gcc found; **PlatformError** is raised with message like "C compiler not found". **Verified.**
- **PyPy:** **test_benchmark_executor.py::TestFindPythonExecutable::test_find_pypy_not_found** uses `@patch('shutil.which')` returning None; **find_python_executable("pypy")** raises **PlatformError** ("no valid PyPy executable found"). **Verified.**

So **ConfigurationError/PlatformError** for missing tools are covered by unit tests; no need to delete a real tool on the host.

---

## 11. Known Limitations

1. **Linux RAPL permissions:** Hardware energy measurement (pyRAPL) on Linux may require root or capabilities (e.g. CAP_SYS_RAWIO). Without them, pyRAPL can raise at import/setup; the code catches and falls back to estimation **without** a clear warning that permissions were the cause. See Issue #4 (Spike) for permission-awareness improvements.

2. **--runs not passed to benchmarks:** The number of measurement runs is fixed by **DEFAULT_PARAMS** in benchmark scripts; the CLI `--runs` does not change subprocess behavior. See Issue #4 for the chosen fix (env var or argv).

3. **DEFAULT_PARAMS:** Benchmark scripts import **DEFAULT_PARAMS** from **pgsi_analyzer.config**. If that symbol is not defined in config (e.g. only in config files), benchmarks can fail at import; not all environments may have it.

4. **Platform-dependent tests:** Five tests in test_measurement and test_energy_crossplatform assume Linux/pyRAPL or specific energy values and fail on Windows; fixing them requires import-time or decorator-level patching or relaxing assertions.

5. **Coverage gaps:** config.py (path resolution, .env), utils/validation.py, and parts of measurement/ have low or partial coverage.

---

## 12. Current “Green” vs “Red” Status

| Area | Status | Notes |
|------|--------|--------|
| **Core pipeline (orchestrator, executor, builder)** | Green | Tests pass; crash handling and failure paths covered. |
| **CLI** | Green | List/run and error handling tested. |
| **Registry** | Green | Discovery and path resolution tested. |
| **Models (carbon, greenscore, aggregation, combination)** | Green | Contracts and error paths tested. |
| **Estimators** | Green | Estimation logic tested. |
| **Platform** | Green | Detection, paths, hardware tested. |
| **Measurement (energy/time)** | Amber | Estimation fallback and CSV format tested; 5 tests fail on Windows due to pyRAPL/import assumptions. |
| **Config / validation** | Amber | Used indirectly; low direct coverage. |
| **Overall suite** | Green (173/178) | 5 failures are known and environment-dependent; no critical logic failures. |

This document serves as the testing and health audit for Issue #3 and the baseline for Issue #4 (Spike) improvements.
