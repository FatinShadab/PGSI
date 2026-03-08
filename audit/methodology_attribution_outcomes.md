# Audit: Methodology Attribution and Data Source Labeling

**Issue:** Methodology Attribution and Data Source Labeling  
**Goal:** Record exactly which methodology (Main/Hardware vs. Fallback/Estimation) generated each data point so the audit can distinguish hardware-measured from estimated data.

---

## 1. Outcomes Summary

| Requirement | Status | Notes |
|-------------|--------|--------|
| Raw energy CSV has `methodology` column | ✅ | Every energy `*.csv` written by the decorator includes `methodology`. |
| Allowed values: `hardware_rapl_linux`, `estimated_cpu_tdp`, `estimated_fallback_generic` | ✅ | Defined in `measurement/energy.py` and `measurement/estimators.py`. |
| Aggregation preserves methodology | ✅ | `aggregate_energy()` reads `methodology` from raw CSVs and writes it to aggregated output. |
| GreenScore.csv contains measured vs estimated summary | ✅ | Columns `points_measured` and `points_estimated` added when `aggregated_energy_paths` is passed. |
| Unit test: failed RAPL → CSV labeled estimated | ✅ | `test_energy_csv_labeled_estimated_when_rapl_unavailable` mocks RAPL unavailable and asserts `methodology` is `estimated_cpu_tdp` or `estimated_fallback_generic`. |

---

## 2. Implementation Details

### 2.1 Methodology Values

- **`hardware_rapl_linux`** — Energy from pyRAPL on Linux/Intel (hardware RAPL counters).
- **`estimated_cpu_tdp`** — Energy from TDP-based estimation (CPU time × TDP model).
- **`estimated_fallback_generic`** — Energy from generic fallback (e.g. unknown CPU + default TDP).

### 2.2 Raw CSV (measurement/energy.py)

- Header includes: `timestamp`, `function`, `run`, `package (uJ)`, `dram (uJ)`, `measurement_method`, **`methodology`**.
- Hardware path: `methodology = METHODOLOGY_HARDWARE_RAPL_LINUX` (`hardware_rapl_linux`).
- Estimation path: `methodology` comes from `estimate_energy()` return value (third element).

### 2.3 Estimators (measurement/estimators.py)

- All estimation functions return `(energy, model_name, methodology)`.
- `estimate_energy_cpu_time`: returns `estimated_cpu_tdp` or `estimated_fallback_generic` (when processor is `"Unknown"` and default TDP is used).
- `estimate_energy_from_psutil`, `estimate_windows`, `estimate_macos`, `estimate_energy`: return the same 3-tuple with the appropriate methodology tag.

### 2.4 Aggregation (models/aggregation.py)

- `aggregate_energy()` reads each raw CSV; if `methodology` is present, uses the mode (most common value) per file; otherwise uses `"unknown"`.
- Aggregated output columns: `filename`, `average_package (uJ)`, **`methodology`**.

### 2.5 GreenScore (models/greenscore.py)

- `calculate_greenscore(..., aggregated_energy_paths=...)` accepts an optional dict `method -> path` to per-method `energy_aggregated.csv` files.
- For each method, counts rows where `methodology == "hardware_rapl_linux"` → **`points_measured`**, all other rows → **`points_estimated`**.
- GreenScore DataFrame and CSV include **`points_measured`** and **`points_estimated`** (0 when `aggregated_energy_paths` is not provided).

### 2.6 Orchestrator

- `run_benchmark_suite` passes `aggregated_energy_files` (method → path to `energy_aggregated.csv`) into `calculate_greenscore()`, so GreenScore.csv always contains the methodology summary when running the full suite.

---

## 3. Testing

- **test_energy_csv_labeled_estimated_when_rapl_unavailable** (`tests/test_energy_crossplatform.py`): Mocks RAPL as unavailable (`is_linux_intel` False, `_pyrapl_available` False), runs the decorator, and asserts the output CSV has a `methodology` column and that every row’s `methodology` is one of `estimated_cpu_tdp` or `estimated_fallback_generic`, and `measurement_method` is `estimation`.
- **test_energy_decorator_uses_estimation_on_windows**: Updated to assert header contains `methodology` and data rows have an estimated methodology value.
- **test_measure_energy_to_csv_creates_csv_file**: Asserts header includes `methodology` and hardware path writes `hardware_rapl_linux`.
- **test_aggregate_energy_basic**: Asserts result has `methodology` column.
- Estimator tests updated for 3-tuple return `(energy, model, methodology)`.

---

## 4. Acceptance Criteria

- ✅ Every energy `*.csv` file contains a **methodology** column.
- ✅ GreenScore.csv contains a summary count of points **measured** (`points_measured`) vs **estimated** (`points_estimated`).
- ✅ Unit test: Mock a failed RAPL import and verify the output CSV is labeled as estimated.
