# PGSI Analyzer — Contributor Guide

**Audit document.** For developers adding benchmarks, running tests, and respecting data contracts. Use this guide to onboard as a contributor.

---

## 1. Adding a New Benchmark (Algorithm)

To add a new algorithm to the suite, you must: (1) create the folder structure and `main.py` for each method, (2) use the measurement decorators with the correct CSV naming, and (3) register the algorithm in the benchmark registry.

### 1.1 Folder structure

Each **algorithm** has one subfolder under `src/pgsi_analyzer/benchmarks/`. Inside it, create one subfolder per **execution method**. Use lowercase, hyphenated names for the algorithm (e.g. `my-algo`).

```
src/pgsi_analyzer/benchmarks/
└── my-algo/
    ├── cpython/
    │   └── main.py
    ├── pypy/
    │   └── main.py
    ├── cython/
    │   └── main.py      # plus .pyx, setup.py as needed
    ├── ctypes/
    │   └── main.py      # plus .c and optional build
    └── py_compile/
        └── main.py
```

- **cpython / pypy / py_compile:** Each contains **main.py** only (Python source).
- **cython:** Contains **main.py**, **setup.py**, and Cython sources (e.g. **.pyx**). Build produces an extension in the same directory.
- **ctypes:** Contains **main.py** and **.c** file(s). Build produces a shared library (e.g. **.so** / **.dll**) in the same directory.

You can add methods incrementally; the registry only needs entries for the methods you implement.

### 1.2 main.py requirements

Each **main.py** must:

1. **Implement the same algorithm** across methods (so results are comparable).
2. **Expose two functions** with the correct decorators and CSV filenames:
   - **run_energy_benchmark** — decorated with **measure_energy_to_csv(n=..., csv_filename="\<algo\>_\<method\>", ...)**.
   - **run_time_benchmark** — decorated with **measure_time_to_csv(n=..., csv_filename="\<algo\>_\<method\>", ...)**.
3. **Use a run count** that respects the pipeline: read from config (e.g. DEFAULT_PARAMS) or, once Spike #4 is implemented, from **PGSI_RUNS** (see Data Contracts and architecture.md Section 13).
4. **Be invocable as a script:** under `if __name__ == "__main__"`, call both `run_energy_benchmark` and `run_time_benchmark` (with the same parameters your algorithm needs).

**CSV filename convention:** Use **\<algorithm_name\>_\<method\>** with underscores (e.g. `my_algo_cpython`, `my_algo_pypy`). The executor discovers CSVs by matching this base name under `energy_benchmark/` and `time_benchmark/` in the benchmark directory.

**Example skeleton (cpython):**

```python
from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv
from pgsi_analyzer.config import DEFAULT_PARAMS as __default__

def main(n: int) -> None:
    # Your algorithm logic
    pass

# Run count: prefer PGSI_RUNS (set by executor per Spike #4); else DEFAULT_PARAMS for your algorithm.
n_runs = __default__["my-algo"]["test_n"]  # add "my-algo" to config if using DEFAULT_PARAMS
@measure_energy_to_csv(n=n_runs, csv_filename="my_algo_cpython")
def run_energy_benchmark(n: int) -> None:
    main(n)

@measure_time_to_csv(n=n_runs, csv_filename="my_algo_cpython")
def run_time_benchmark(n: int) -> None:
    main(n)

if __name__ == "__main__":
    n = __default__["my-algo"]["depth"]  # or your param
    run_energy_benchmark(n)
    run_time_benchmark(n)
```

For **cython** and **ctypes**, the same pattern applies; ensure the built artifact (extension or shared lib) is in the same directory and that **main.py** runs the workload that should be measured.

### 1.3 Registry entry

Edit **src/pgsi_analyzer/benchmarks/registry.py**. In the **BENCHMARKS** dict, add an entry for your algorithm:

```python
BENCHMARKS: Dict[str, Dict[str, str]] = {
    # ... existing entries ...
    "my-algo": {
        "cpython": "my-algo/cpython/main.py",
        "pypy": "my-algo/pypy/main.py",
        "cython": "my-algo/cython",           # directory for cython (contains setup.py)
        "ctypes": "my-algo/ctypes",           # directory for ctypes
        "py_compile": "my-algo/py_compile/main.py",
    },
}
```

- Keys are **algorithm name** (same as folder name) and **method name** (must be one of **cpython**, **pypy**, **cython**, **ctypes**, **py_compile**).
- Value for **cpython**, **pypy**, **py_compile** is the path to **main.py** relative to the `pgsi_analyzer.benchmarks` package.
- Value for **cython** and **ctypes** is the **directory** path (no main.py in the string); the executor still runs **main.py** inside that directory.

After adding the entry, run:

```bash
pgsi-analyzer benchmark list --algorithms
```

Your algorithm should appear. Then run a quick test:

```bash
pgsi-analyzer benchmark run --algorithms my-algo --methods cpython --runs 2 --output results/
```

---

## 2. Running Tests

### 2.1 Full test suite

From the project root:

```bash
pytest tests/ -v
```

Shorter:

```bash
pytest tests/
```

### 2.2 With coverage

```bash
pip install pytest-cov
pytest tests/ --cov=src/pgsi_analyzer --cov-report=term-missing
```

To avoid known platform-dependent failures (Windows) when measuring coverage, you can exclude the measurement and cross-platform energy tests:

```bash
pytest tests/ --cov=src/pgsi_analyzer --cov-report=term-missing \
  --ignore=tests/test_measurement.py --ignore=tests/test_energy_crossplatform.py
```

### 2.3 Platform-specific failures (Windows vs Linux)

Some tests assume **Linux** and **pyRAPL** (hardware energy). On **Windows** (and often on macOS), the following can **fail**:

- **test_measurement.py:** Tests that expect **RuntimeError** when pyRAPL is unavailable (the code actually falls back to estimation). Tests that assert exact energy values (e.g. from a pyRAPL mock) may see estimation values instead.
- **test_energy_crossplatform.py:** One test asserts estimated energy is in a fixed range (e.g. 1e3–1e10 μJ); on very fast machines the value can fall below that.

**Interpretation:**

- These failures are **environment-dependent**, not failures of core pipeline logic. The implementation is correct: it falls back to estimation when hardware is unavailable.
- To get a **green** suite on Windows, you can run excluding the two files above, or fix the tests (e.g. patch at import time or relax assertions) as described in **audit/testing_and_health.md**.

On **Linux x86_64** with pyRAPL installed (and optionally with RAPL permissions), the same tests may pass when hardware measurement is used.

### 2.4 Running a subset of tests

By module:

```bash
pytest tests/test_models.py -v
pytest tests/test_benchmark_orchestrator.py -v
```

By test name:

```bash
pytest tests/test_benchmark_executor.py::TestExecuteBenchmark::test_execute_benchmark_execution_fails -v
```

---

## 3. Data Contracts (CSV columns and file naming)

If you add or change measurement logic, the pipeline expects the following. See **audit/architecture.md** (Internal Contracts) for full detail.

### 3.0 Allowed file naming (regex, audit)

The **ResultsCollector** and **aggregation** layer accept only files whose basename matches one of these patterns. Any other file (e.g. **invalid_file.txt**, **energy_data.csv.bak**, **file.csv.tmp**) is ignored.

- **Energy CSVs:** **`^energy_.*\.csv$`** — e.g. **energy_hanoi_cpython.csv**, **energy_sort_v2_cpython.csv**.
- **Time CSVs:** **`^time_.*\.csv$`** — e.g. **time_hanoi_cpython.csv**.

The decorators **measure_energy_to_csv** and **measure_time_to_csv** automatically prefix the given **csv_filename** with **energy_** and **time_** so output files satisfy these patterns. Partial/temp files (**.csv.tmp**, **.csv.bak**) are never accepted by the aggregator.

### 3.1 Raw energy CSV (from measure_energy_to_csv)

- **Required column:** **`package (uJ)`** (energy in microjoules). Aggregation uses this.
- Optional but present: `timestamp`, `function`, `run`, `dram (uJ)`, `measurement_method`, **`methodology`** (audit).
- Written under **energy_benchmark/** in the benchmark’s working directory. Output filename is **energy_\<csv_filename\>.csv** (e.g. **energy_my_algo_cpython.csv**).

### 3.2 Raw time CSV (from measure_time_to_csv)

- **Required column:** **`execution_time (s)`** (seconds). Aggregation uses this.
- Optional: `timestamp`, `function`, `run`.
- Written under **time_benchmark/** as **time_\<csv_filename\>.csv** (e.g. **time_my_algo_cpython.csv**).

### 3.3 Downstream contracts (for reference)

- **Aggregated energy:** **filename**, **average_package (uJ)**. Produced by `aggregate_energy`; consumed by `combine_energy_results`. Method name is taken from the **parent directory name** of the aggregated file (e.g. **cpython/energy_aggregated.csv** → method **cpython**).
- **Aggregated time:** **filename**, **execution_time (s)** (one row per file, value = mean). Consumed by `combine_time_results`.
- **Combined:** **algorithm** + one column per method (numeric). **Carbon:** **algorithm** + method columns with **\_CO2e_g** suffix. **GreenScore:** **method**, **energy_mean**, **time_mean**, **carbon_mean**, **green_score**.

When adding a new benchmark, you only need to satisfy the **raw** energy and time contracts; the rest of the pipeline is driven by the orchestrator and existing models.

---

## 4. Quick reference: CLI vs tests

| Goal | Command |
|------|--------|
| List algorithms/methods | `pgsi-analyzer benchmark list` [ `--algorithms` \| `--methods` ] |
| Run benchmarks | `pgsi-analyzer benchmark run --algorithms <names or all> --methods <names or all> [ --runs N ] [ --output DIR ] [ --env-file .env ] [ --python-path ... ] [ --pypy-path ... ] [ --cc-path ... ]` |
| Run tests | `pytest tests/ -v` |
| Run tests with coverage | `pytest tests/ --cov=src/pgsi_analyzer --cov-report=term-missing` |

All CLI options are defined in **src/pgsi_analyzer/cli/main.py**; the examples in this guide and in **audit/usage_guide.md** match that implementation.
