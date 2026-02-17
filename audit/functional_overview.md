# PGSI Analyzer — Functional Overview

**Document version:** 1.0  
**Purpose:** Source of truth for what the package does and its core user flows (Issue #1: System Purpose and Functional Mapping).

---

## 1. Primary Problem the Package Solves

**pgsi-analyzer** (Python GreenScore and Sustainability Analysis Tool) addresses the need to **compare the sustainability of different Python execution methods** in a reproducible way. It provides:

- **Benchmarking** of multiple algorithms (e.g., binary-trees, sieve, n-queens) across several execution methods: **CPython**, **PyPy**, **Cython**, **ctypes**, and **py_compile**.
- **Measurement** of **energy consumption** (hardware via pyRAPL on Linux/Intel, or estimation elsewhere), **execution time**, and derived **carbon footprint**.
- **A single composite metric (GreenScore)** that ranks methods by combining normalized energy, time, and carbon with configurable weights (α, β, γ), so users can answer: *“Which Python execution method is more sustainable for my workload?”*

In short: **the package solves the problem of objectively measuring and ranking Python execution methods by energy efficiency, runtime, and carbon impact using the GreenScore metric.**

---

## 2. Configuration and Entry Points

### 2.1 Project Configuration (pyproject.toml)

- **Package name:** `pgsi-analyzer`  
- **Version:** 1.0.0  
- **Python:** >=3.8  
- **Package layout:** `src` layout; package lives under `src/pgsi_analyzer/`.

### 2.2 Dependencies

| Type        | Dependencies |
|------------|----------------|
| **Core**   | `pandas>=2.0.0`, `matplotlib>=3.7.0`, `numpy>=1.24.0`, `psutil>=5.9.0`, `cython>=3.0.0`, `python-dotenv>=1.0.0` |
| **Optional [energy]** | `pyRAPL>=0.2.3` (Linux x86_64 only) |
| **Optional [analysis]** | `scipy>=1.10.0`, `statsmodels>=0.14.0` |
| **Optional [all]**     | `pgsi-analyzer[energy,analysis]` |

### 2.3 Declared Entry Points

| Entry point     | Reference                    | Purpose |
|-----------------|------------------------------|--------|
| **Console script** | `pgsi-analyzer = "pgsi_analyzer.cli:main"` | CLI entry; invokes `main()` in `pgsi_analyzer.cli` (re-exported from `cli/main.py`). |

**Verification:** The console script entry point is implemented and resolvable: `pgsi_analyzer.cli` is a package, and `cli/__init__.py` exports `main` from `cli/main.py`. The call `from pgsi_analyzer.cli import main` succeeds and returns the `main` function. **No other entry points (e.g. plugins or GUI) are declared in pyproject.toml.**

---

## 3. Top-Level Directory Structure and Core Modules

```
PGSI/
├── pyproject.toml          # Build, metadata, dependencies, script entry point
├── README.md
├── src/
│   └── pgsi_analyzer/      # Main package
│       ├── __init__.py      # Package metadata (version, author)
│       ├── config.py        # Tool paths (Python, PyPy, C compiler); .env / CLI
│       ├── cli/             # CLI layer
│       │   ├── __init__.py  # Exposes main
│       │   └── main.py      # Argument parsing; benchmark list/run
│       ├── benchmark/       # Execution pipeline (build + run)
│       │   ├── orchestrator.py  # run_benchmark_suite: build → execute → aggregate → combine → carbon → GreenScore
│       │   ├── executor.py      # execute_benchmark, find_python_executable, prepare_py_compile
│       │   └── builder.py      # build_benchmark (Cython/ctypes), requires_build
│       ├── benchmarks/      # Registry + per-algorithm/method implementations
│       │   ├── registry.py     # BENCHMARKS map, list_algorithms, list_methods, get_benchmark_path, validate_*
│       │   └── <algorithm>/    # e.g. hanoi, sieve, binary-trees, n-queens, ...
│       │       └── <method>/   # cpython, pypy, cython, ctypes, py_compile
│       │           └── main.py # run_energy_benchmark, run_time_benchmark
│       ├── models/         # Data processing and metrics
│       │   ├── aggregation.py  # aggregate_energy, aggregate_time
│       │   ├── combination.py  # combine_energy_results, combine_time_results
│       │   ├── carbon.py      # calculate_carbon_footprint
│       │   └── greenscore.py  # normalize_metrics, calculate_greenscore
│       ├── measurement/    # Energy and time measurement
│       │   ├── energy.py      # measure_energy_to_csv (pyRAPL or estimation)
│       │   ├── time.py        # measure_time_to_csv
│       │   └── estimators.py  # estimate_energy (non-Linux/estimation path)
│       ├── platform/       # OS/hardware abstraction
│       │   ├── detection.py   # detect_platform, is_linux_intel, is_windows, ...
│       │   ├── hardware.py    # get_cpu_info, get_system_info, check_rapl_support
│       │   └── paths.py       # get_user_data_dir, resolve_data_path, resolve_benchmark_path
│       └── utils/          # Shared helpers
│           ├── validation.py  # validate_file_path, validate_dataframe, validate_weights, validate_platform, require_columns
│           └── errors.py      # PGSIAnalyzerError, MeasurementError, AnalysisError, PlatformError, ConfigurationError
├── tests/
└── audit/                  # This audit artifact
    └── functional_overview.md
```

**Core modules** (by responsibility):

- **cli:** User-facing command-line interface.
- **benchmark (orchestrator, executor, builder):** Run full benchmark suite, run single benchmarks, build Cython/ctypes.
- **benchmarks (registry + algorithm/method trees):** Discovery and path resolution for all benchmark variants.
- **models:** Aggregation, combination, carbon, GreenScore.
- **measurement:** Energy and time collection (decorators / CSV output).
- **platform:** Platform detection, hardware info, paths.
- **config:** Tool path resolution (Python, PyPy, C compiler).
- **utils:** Validation and custom exceptions.

---

## 4. User-Facing Features / APIs

### 4.1 Command-Line Interface (Primary User Surface)

- **`pgsi-analyzer`** (console script)
  - **`benchmark list`**  
    - `--algorithms`: list available algorithms.  
    - `--methods`: list available execution methods.  
    - No flags: list both.
  - **`benchmark run`**  
    - `--algorithms`, `--methods` (defaults: `all`).  
    - `--runs`, `--output`, `--carbon-intensity`, `--alpha`, `--beta`, `--gamma`.  
    - `--env-file`, `--python-path`, `--pypy-path`, `--cc-path` for tool paths.  
    - Runs full pipeline and writes **GreenScore.csv** (and intermediate CSVs) under the output directory.

### 4.2 Programmatic APIs (Importable)

- **Orchestration**
  - `pgsi_analyzer.benchmark.orchestrator.run_benchmark_suite(...)` — full benchmark suite; returns path to GreenScore CSV.
- **Discovery**
  - `pgsi_analyzer.benchmarks.registry.list_algorithms()` — list algorithm names.  
  - `pgsi_analyzer.benchmarks.registry.list_methods(algorithm=None)` — list methods (optionally for one algorithm).  
  - `pgsi_analyzer.benchmarks.registry.get_benchmark_path(algorithm, method)` — path to benchmark entry.  
  - `pgsi_analyzer.benchmarks.registry.validate_algorithm`, `validate_method` — validation helpers.
- **Metrics and analysis**
  - `pgsi_analyzer.models.calculate_greenscore(energy_df, time_df, carbon_df, alpha, beta, gamma, ...)` — compute GreenScore ranking.  
  - `pgsi_analyzer.models.normalize_metrics(df, ...)` — min-max normalization.  
  - `pgsi_analyzer.models.calculate_carbon_footprint(...)` — carbon from energy.  
  - `pgsi_analyzer.models.aggregate_energy`, `aggregate_time` — aggregate raw CSVs.  
  - `pgsi_analyzer.models.combine_energy_results`, `combine_time_results` — combine per-method CSVs.
- **Configuration**
  - `pgsi_analyzer.config.load_tool_paths(env_file=..., cli_python=..., cli_pypy=..., cli_cc=...)` — resolve `ToolPaths`.  
  - `pgsi_analyzer.config.ToolPaths` — dataclass holding python, pypy, c_compiler paths.
- **Execution (lower-level)**
  - `pgsi_analyzer.benchmark.executor.execute_benchmark(...)` — run one benchmark and return paths to energy/time CSVs.  
  - `pgsi_analyzer.benchmark.executor.find_python_executable(method, tool_paths)`, `prepare_py_compile(...)`.
- **Build**
  - `pgsi_analyzer.benchmark.builder.build_benchmark(algorithm, method, benchmark_path, ...)`, `requires_build(method)`.
- **Utilities and platform**
  - `pgsi_analyzer.utils`: validation and error classes (see `utils/__init__.py`).  
  - `pgsi_analyzer.platform`: detection, hardware, paths (see `platform/__init__.py`).

The **main intended user flow** is: run `pgsi-analyzer benchmark run` (optionally with `--algorithms`/`--methods`) and use the generated **GreenScore.csv** and supporting CSVs for analysis. Power users can call `run_benchmark_suite` and the models/registry APIs from Python.

---

## 5. Main vs Helper Logic

| Role   | Components | Description |
|--------|------------|-------------|
| **Main** | **CLI** (`cli/main.py`) | Entry point; parses args and dispatches to benchmark list/run. |
| **Main** | **Orchestrator** (`benchmark/orchestrator.py`) | Coordinates the full pipeline: resolve algorithms/methods → build → execute → aggregate → combine → carbon → GreenScore; single function `run_benchmark_suite`. |
| **Main** | **Executor** (`benchmark/executor.py`) | Runs a single benchmark (subprocess), resolves Python executable, prepares py_compile; produces energy/time CSVs. |
| **Main** | **Builder** (`benchmark/builder.py`) | Builds Cython and ctypes benchmarks so they can be executed. |
| **Main** | **Registry** (`benchmarks/registry.py`) | Source of truth for algorithms and methods; resolves benchmark paths. |
| **Main** | **Models** (`models/`) | GreenScore, carbon, aggregation, combination — core analysis and output (e.g. GreenScore.csv). |
| **Main** | **Measurement** (`measurement/energy.py`, `measurement/time.py`) | Energy and time collection used by benchmark scripts (decorators/CSV). |
| **Helper** | **Config** (`config.py`) | Resolves tool paths (Python, PyPy, C compiler) from env, .env, CLI. |
| **Helper** | **Platform** (`platform/`) | Detects OS/arch (e.g. Linux Intel for pyRAPL), hardware info, path helpers. |
| **Helper** | **Utils** (`utils/`) | Validation (file, dataframe, weights, platform), custom exceptions. |
| **Helper** | **Benchmark implementations** (`benchmarks/<algo>/<method>/main.py`) | Per-algorithm, per-method runnable scripts; invoked by executor, not by end users directly. |

**Main** = user-facing flow and core pipeline (CLI → orchestration → run/build → metrics). **Helper** = configuration, platform detection, validation, errors, and the individual benchmark scripts that the executor runs.

---

## 6. Entry Point Verification Summary

| Documented entry point | Location in code | Status |
|------------------------|-------------------|--------|
| `pgsi-analyzer = "pgsi_analyzer.cli:main"` | `src/pgsi_analyzer/cli/__init__.py` exports `main` from `cli/main.py`; `main(argv=None)` exists in `cli/main.py`. | **Verified** |

All documented entry points in `pyproject.toml` exist and resolve correctly in the codebase.

---

## 7. High-Level Summary of Current Capabilities

- **Benchmarking:** Run a fixed set of algorithms (binary-trees, fannkuch-redux, fasta, k-nucleotide, mandelbrot, n-body, n-queens, pi-digits, regex-redux, reverse-complement, sieve, spectral-norm, strassen, hanoi, knn) across five execution methods (cpython, pypy, cython, ctypes, py_compile) with configurable run count.
- **Measurement:** Energy (pyRAPL on Linux/Intel, or CPU-time–based estimation elsewhere) and execution time, written to CSVs by benchmark scripts.
- **Analysis pipeline:** Aggregate raw CSVs per method → combine across methods → compute carbon from energy (configurable intensity) → compute GreenScore (configurable α, β, γ) → output GreenScore.csv and intermediate files.
- **Configuration:** Tool paths via environment variables, .env file, or CLI flags; optional C compiler and PyPy for cython/ctypes and pypy methods.
- **Discovery:** List algorithms and methods from the registry; validate algorithm/method before run.
- **Cross-platform:** Windows, macOS, Linux; energy hardware measurement only on Linux/Intel; elsewhere estimation is used.

This document serves as the **functional source of truth** for the package’s purpose, structure, user flows, and main vs helper roles for subsequent technical deep-dives.
