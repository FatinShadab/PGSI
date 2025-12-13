# Critical Architecture Analysis: pgsi-analyzer Benchmark Execution Capability

**Analysis Date:** 2025-12-14  
**Analyst Role:** Expert Software Systems Researcher & IEEE Reviewer  
**Focus:** Benchmarking Frameworks & Green Computing Tools

---

## Executive Summary

**Verdict:** The current system **CANNOT** support the claimed functionality: *"Using pgsi-analyzer, users can execute built-in benchmarks from the CLI and automatically obtain energy, runtime, carbon, and GreenScore comparisons across Python execution methods."*

**Critical Gap:** The package provides measurement and analysis tools, but **lacks a benchmark execution orchestrator**. Benchmarks exist as external files, not as integrated, discoverable, executable components.

---

## 1. Benchmark Integration Analysis

### 1.1 Are benchmarks included inside the package?

**Answer: NO**

**Evidence:**
- `MANIFEST.in` line 3: `prune benchmarks` — explicitly excludes benchmarks from package distribution
- Benchmarks exist in repository root `benchmarks/` directory, not in `src/pgsi_analyzer/`
- `pyproject.toml` package-data only includes `config/*.json` and `config/*.yaml`, not benchmarks
- Benchmarks are **external artifacts**, not packaged resources

**Impact:** Users installing from PyPI will have **zero benchmarks** available. Benchmarks are only accessible in development repository.

### 1.2 Are benchmarks structured for multi-method execution?

**Answer: PARTIALLY**

**Evidence:**
- ✅ Directory structure: `benchmarks/{Algorithm}/{Method}/main.py` exists for all 15 algorithms
- ✅ Five execution methods present: `Cpython/`, `PyPy/`, `Ctypes/`, `Cython/`, `py_compile/`
- ✅ Each `main.py` imports `pgsi_analyzer.measurement` decorators
- ⚠️ **Critical Issue:** Benchmarks use hardcoded decorator calls with `__default__["algorithm"]["test_n"]` (n=50)
- ⚠️ **Critical Issue:** Benchmarks must be run as standalone scripts (`python main.py`), not via package API

**Structure Example:**
```
benchmarks/Towers-of-Hanoi/
├── Cpython/main.py  ← Uses @measure_energy_to_csv(n=50, ...)
├── PyPy/main.py     ← Uses @measure_energy_to_csv(n=50, ...)
├── Ctypes/main.py   ← Uses @measure_energy_to_csv(n=50, ...)
├── Cython/main.py   ← Uses @measure_energy_to_csv(n=50, ...)
└── py_compile/main.py ← Uses @measure_energy_to_csv(n=50, ...)
```

**Problem:** No programmatic interface to discover, load, or execute these benchmarks.

### 1.3 Clear mapping: benchmark → execution method → runnable artifact?

**Answer: NO**

**Evidence:**
- `resolve_benchmark_path()` exists but only resolves **paths**, not execution logic
- No registry/catalog of available benchmarks
- No mapping from algorithm name → executable entry point
- No method dispatcher (e.g., "run with PyPy" → `pypy main.py`)
- Cython/Ctypes require **compilation** before execution — no build orchestration

**Missing Components:**
1. Benchmark discovery mechanism
2. Execution method dispatcher (python vs pypy vs compiled extension)
3. Build system integration (Cython setup.py, Ctypes compilation)
4. Subprocess isolation for cross-method execution

---

## 2. CLI Orchestration Analysis

### 2.1 Can users run `pgsi-analyzer benchmark run --suite cpu --methods all --runs 50`?

**Answer: NO**

**Evidence:**
- `src/pgsi_analyzer/cli/main.py` contains **zero** benchmark-related subcommands
- Available commands: `evcvt`, `lcpack`, `scatter`, `line-compare`, `etc-compare`, `statistics`
- All commands are **post-processing** (visualization, analysis of existing CSVs)
- No `benchmark` subcommand exists

**Current CLI Capability:**
```bash
pgsi-analyzer evcvt data.csv          # ✅ Works (visualization)
pgsi-analyzer benchmark run ...        # ❌ Does not exist
```

### 2.2 Does CLI discover benchmarks automatically?

**Answer: NO**

**Evidence:**
- No benchmark discovery code in `cli/main.py`
- No scanning of `benchmarks/` directory
- No algorithm registry or catalog
- `resolve_benchmark_path()` requires manual algorithm/method specification

### 2.3 Does CLI invoke correct runtime?

**Answer: NO** (feature doesn't exist)

**Missing Runtime Dispatcher:**
- No subprocess execution logic
- No method-specific runtime detection:
  - CPython: `python main.py`
  - PyPy: `pypy main.py` (requires PyPy installation check)
  - Cython: `python setup.py build_ext --inplace` then `python main.py`
  - Ctypes: Compile `.c` → `.so`/`.dll`, then `python main.py`
  - py_compile: `python -m py_compile main.py` then `python main.pyc`

**Critical Gap:** No execution abstraction layer.

### 2.4 Subprocess isolation?

**Answer: N/A** (feature doesn't exist)

**Required but Missing:**
- Process isolation for energy measurement (pyRAPL requires separate process on Linux)
- Environment variable isolation (PYTHONPATH, LD_LIBRARY_PATH)
- Working directory management
- Error handling and timeout management

---

## 3. Measurement Pipeline Analysis

### 3.1 Is energy/time measurement applied only to execution, not compilation?

**Answer: UNCLEAR** (depends on manual execution)

**Evidence:**
- Decorators `@measure_energy_to_csv` and `@measure_time_to_csv` wrap function execution
- **Problem:** If user runs `python setup.py build_ext` (Cython), compilation energy is **not measured**
- **Problem:** If user compiles C code for ctypes, compilation is **not measured**
- Decorators only measure **function execution**, which is correct, but **no orchestration ensures compilation happens separately**

**Current Behavior:**
```python
# In benchmarks/Towers-of-Hanoi/Cython/main.py
@measure_energy_to_csv(n=50, csv_filename="hanoi_cython")
def run_energy_benchmark(n):
    main(n)  # Only measures main(), not compilation
```

**Required:** Pre-execution build step that is **excluded** from measurement.

### 3.2 Are measurements consistent across execution methods?

**Answer: YES** (decorator implementation is consistent)

**Evidence:**
- Same decorators used across all methods
- Same `n=50` default (from `__default__`)
- Same CSV output format
- Same system info JSON generation

**However:** No validation that all methods were run with **identical parameters** (algorithm inputs, n runs).

### 3.3 Are CSV outputs automatically generated?

**Answer: PARTIALLY**

**Evidence:**
- ✅ Decorators automatically write CSVs when functions execute
- ❌ **No automatic orchestration** — user must manually:
  1. Navigate to each `benchmarks/{Algorithm}/{Method}/` directory
  2. Run `python main.py` (or appropriate runtime)
  3. Repeat for all 15 algorithms × 5 methods = 75 manual executions
  4. Collect CSVs from 75 different directories

**Missing:** Automated collection and aggregation pipeline.

---

## 4. Data Flow Correctness Analysis

### 4.1 Does pipeline follow: execution → raw CSV → aggregated CSV → carbon CSV → GreenScore CSV?

**Answer: FUNCTIONS EXIST, BUT NO AUTOMATION**

**Evidence:**
- ✅ `aggregate_energy()` exists — aggregates raw CSVs from folder
- ✅ `aggregate_time()` exists — aggregates raw CSVs from folder
- ✅ `combine_energy_results()` exists — combines multiple method CSVs
- ✅ `combine_time_results()` exists — combines multiple method CSVs
- ✅ `calculate_carbon_footprint()` exists — converts energy to carbon
- ✅ `calculate_greenscore()` exists — computes final ranking

**Problem:** These functions are **not chained automatically**. User must:
1. Manually collect raw CSVs from 75 benchmark runs
2. Manually call `aggregate_energy()` for each method
3. Manually call `combine_energy_results()` with 5 method CSVs
4. Manually call `calculate_carbon_footprint()`
5. Manually call `calculate_greenscore()`

**Missing:** End-to-end pipeline orchestrator.

### 4.2 Are normalization and aggregation done per-algorithm before cross-algorithm averaging?

**Answer: YES** (implementation is correct)

**Evidence:**
- `normalize_metrics()` applies row-wise (per-algorithm) min-max normalization
- `calculate_greenscore()` normalizes each DataFrame (energy, time, carbon) separately
- Then computes column-wise means (across algorithms) per method
- Finally combines with weighted average

**Implementation is methodologically sound.**

---

## 5. Reproducibility & Research Validity Analysis

### 5.1 Are runs repeated (n=50) in a statistically valid way?

**Answer: YES** (decorator implementation)

**Evidence:**
- `@measure_energy_to_csv(n=50)` hardcoded in all benchmarks
- Decorator runs function `n` times and logs each run
- Aggregation computes mean across runs

**However:** No validation that:
- All 50 runs completed successfully
- No outliers were filtered
- System state was consistent (CPU throttling, thermal limits)

### 5.2 Is methodology defensible for IEEE review?

**Answer: PARTIALLY**

**Strengths:**
- ✅ Consistent measurement decorators
- ✅ Proper normalization methodology
- ✅ Statistical analysis tools (ANOVA) available
- ✅ Cross-platform energy estimation fallback

**Weaknesses:**
- ❌ No automated execution — manual intervention required
- ❌ No reproducibility script — cannot guarantee identical runs
- ❌ No parameter validation — user could run with different `n` values
- ❌ No result verification — no checksums or validation of CSV integrity

### 5.3 Are platform-specific limitations clearly isolated?

**Answer: YES**

**Evidence:**
- `platform/detection.py` clearly identifies OS and architecture
- `platform/hardware.py` checks RAPL availability
- Energy measurement falls back to estimation on Windows/macOS
- Warnings issued when estimation is used

**Implementation is sound.**

---

## 6. Missing or Incomplete Components

### 6.1 Critical Missing Components (Priority Order)

#### **PRIORITY 1: Benchmark Execution Orchestrator** (CRITICAL)

**What's Missing:**
- CLI subcommand: `pgsi-analyzer benchmark run`
- Benchmark discovery: Scan and catalog available benchmarks
- Execution dispatcher: Route to correct runtime (python/pypy/compiled)
- Build orchestration: Compile Cython/Ctypes before execution
- Subprocess management: Isolated execution with proper environment

**Required Implementation:**
```python
# src/pgsi_analyzer/cli/benchmark.py
def run_benchmark_suite(
    algorithms: List[str],
    methods: List[str],
    runs: int = 50,
    output_dir: Path
) -> None:
    # 1. Discover benchmarks
    # 2. For each algorithm × method:
    #    a. Build if needed (Cython/Ctypes)
    #    b. Execute in subprocess with measurement
    #    c. Collect raw CSVs
    # 3. Aggregate and combine
    # 4. Calculate carbon and GreenScore
    # 5. Generate final report
```

#### **PRIORITY 2: Benchmark Package Integration** (CRITICAL)

**What's Missing:**
- Include benchmarks in package distribution
- Package benchmarks as importable resources
- Benchmark registry/catalog system

**Required Changes:**
- Update `MANIFEST.in`: Remove `prune benchmarks` or move benchmarks to `src/pgsi_analyzer/benchmarks/`
- Update `pyproject.toml`: Add benchmarks to package-data
- Create `src/pgsi_analyzer/benchmarks/__init__.py` with discovery API

#### **PRIORITY 3: Build System Integration** (HIGH)

**What's Missing:**
- Cython compilation automation
- Ctypes shared library compilation
- Dependency checking (PyPy installed? C compiler available?)

**Required Implementation:**
```python
# src/pgsi_analyzer/benchmark/build.py
def build_cython_benchmark(algorithm: str) -> Path:
    # Run: python setup.py build_ext --inplace
    # Return path to compiled extension

def build_ctypes_benchmark(algorithm: str) -> Path:
    # Compile .c to .so/.dll
    # Return path to shared library
```

#### **PRIORITY 4: End-to-End Pipeline Automation** (HIGH)

**What's Missing:**
- Automatic CSV collection from benchmark runs
- Automatic aggregation and combination
- Automatic carbon and GreenScore calculation
- Single command execution

**Required Implementation:**
```python
# src/pgsi_analyzer/cli/benchmark.py
def execute_full_pipeline(...) -> Path:
    # 1. Run all benchmarks
    # 2. Collect raw CSVs
    # 3. Aggregate per method
    # 4. Combine methods
    # 5. Calculate carbon
    # 6. Calculate GreenScore
    # 7. Return path to final CSV
```

#### **PRIORITY 5: Result Validation & Verification** (MEDIUM)

**What's Missing:**
- Checksum validation of benchmark outputs
- Run count verification (all 50 runs completed?)
- Outlier detection and reporting
- Platform consistency checks

#### **PRIORITY 6: Documentation & Examples** (MEDIUM)

**What's Missing:**
- CLI usage examples for benchmark execution
- Troubleshooting guide for compilation issues
- Platform-specific setup instructions

---

## 7. Final Verdict

### 7.1 Can the system support the claimed functionality?

**Answer: NO**

**Claim:** *"Using pgsi-analyzer, users can execute built-in benchmarks from the CLI and automatically obtain energy, runtime, carbon, and GreenScore comparisons across Python execution methods."*

**Reality:**
- ❌ Benchmarks are **not built-in** (excluded from package)
- ❌ No CLI command to execute benchmarks
- ❌ No automatic execution — requires 75 manual script runs
- ❌ No automatic pipeline — requires manual CSV collection and function calls
- ✅ Analysis functions exist and work correctly
- ✅ Measurement decorators are sound
- ✅ GreenScore calculation is methodologically correct

### 7.2 What is Missing (Ordered by Priority)

1. **Benchmark Execution CLI** (`pgsi-analyzer benchmark run`)
2. **Benchmark Package Integration** (include in distribution)
3. **Build System Integration** (Cython/Ctypes compilation)
4. **End-to-End Pipeline Automation** (single command execution)
5. **Subprocess Management** (isolated execution, error handling)
6. **Result Validation** (checksums, run verification)

### 7.3 Architectural Changes Required

**Minimum Viable Implementation:**

1. **Create `src/pgsi_analyzer/benchmark/` module:**
   - `discovery.py` — Scan and catalog benchmarks
   - `executor.py` — Execute benchmarks in subprocess
   - `builder.py` — Compile Cython/Ctypes benchmarks
   - `orchestrator.py` — Coordinate full pipeline

2. **Add CLI subcommand:**
   - `pgsi-analyzer benchmark list` — List available benchmarks
   - `pgsi-analyzer benchmark run --algorithms all --methods all --runs 50`

3. **Package benchmarks:**
   - Move or symlink `benchmarks/` to `src/pgsi_analyzer/benchmarks/`
   - Update `MANIFEST.in` and `pyproject.toml`

4. **Pipeline automation:**
   - Chain: execution → aggregation → combination → carbon → GreenScore
   - Single command produces final ranking CSV

**Estimated Development Effort:** 2-3 weeks for experienced developer

---

## 8. Recommendations

### For Immediate Research Validity:
1. Create a **manual execution script** (`scripts/run_all_benchmarks.py`) that:
   - Iterates through all algorithms × methods
   - Executes each benchmark
   - Collects and aggregates results
   - Generates final GreenScore CSV

2. Document the **manual workflow** clearly in README

### For Production Package:
1. Implement Priority 1-4 components (execution orchestrator, package integration, build system, pipeline automation)
2. Add comprehensive tests for benchmark execution
3. Create platform-specific installation guides (PyPy, Cython, C compiler requirements)

### For IEEE Publication:
1. Include reproducibility script in repository
2. Document exact execution environment (OS, Python versions, compiler versions)
3. Provide pre-computed results for validation
4. Add checksum verification for benchmark outputs

---

## Conclusion

The `pgsi-analyzer` package provides **excellent measurement and analysis infrastructure**, but **lacks the execution orchestration layer** required for the claimed CLI-driven benchmark execution. The gap is significant but addressable with focused development on benchmark discovery, execution dispatch, build integration, and pipeline automation.

**Current State:** Analysis tool ✅ | Benchmark executor ❌  
**Required State:** Integrated benchmark execution system with CLI interface

**Recommendation:** Implement Priority 1-4 components before claiming CLI-driven benchmark execution capability.

