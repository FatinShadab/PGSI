# README: Current Implementation Status

**Document Version:** 1.0  
**Last Updated:** Based on repository analysis as of current state  
**Purpose:** High-fidelity guide for new developers to understand the codebase as it exists today

---

## 1. Project Overview

**Intended Goal:** This project aims to be a comprehensive benchmarking and analysis tool for comparing the energy consumption, execution time, and carbon footprint of five Python execution methods (CPython, PyPy, Cython, ctypes, py_compile) across 15 diverse CPU-bound algorithms. The research produces a composite "GreenScore" metric to rank execution methods by overall sustainability.

**Current State:** The project is **partially functional** with a complete benchmark suite and data processing pipeline, but lacks a centralized execution framework. The core measurement infrastructure (energy and time decorators) is fully implemented and tested. Data collection scripts are functional but require manual orchestration. Visualization tools exist but contain hardcoded paths. The synthetic survey module is implemented but requires API key configuration.

**Functional Components:**
- ✅ Energy measurement module (pyRAPL decorator)
- ✅ Time measurement module (decorator-based)
- ✅ 15 benchmark algorithms × 5 execution methods (75 implementations)
- ✅ Data aggregation and processing scripts
- ✅ GreenScore calculation pipeline
- ✅ Visualization tools (with path limitations)
- ✅ Synthetic survey generation framework

**Non-Functional/Incomplete Components:**
- ❌ Centralized benchmark runner (`run_benchmarks.py` referenced in main README but does not exist)
- ❌ Automated benchmark orchestration
- ❌ Configuration management system
- ❌ Path abstraction layer (hardcoded paths throughout)

---

## 2. Repository Structure

### Critical Files and Directories

```
python-energy-microscope/
│
├── benchmarks/                          # Core benchmark implementations
│   ├── [15 algorithm folders]/          # Binary-trees, FASTA, K-Nucleotide, etc.
│   │   ├── Cpython/main.py             # CPython implementation with decorators
│   │   ├── PyPy/main.py                # PyPy implementation
│   │   ├── Cython/                     # Cython implementation (includes .pyx, setup.py)
│   │   ├── Ctypes/                     # ctypes implementation (C code + Python wrapper)
│   │   └── py_compile/main.py          # py_compile implementation
│   └── README.md                        # Benchmark documentation
│
├── energy_module/                       # Energy measurement infrastructure
│   ├── decorator.py                    # Core decorator: measure_energy_to_csv()
│   └── README.md                        # Energy module documentation
│
├── time_modules/                        # Time measurement infrastructure
│   ├── decorator.py                    # Core decorator: measure_time_to_csv()
│   └── README.md                        # Time module documentation
│
├── input/                               # Default input parameters
│   └── __init__.py                      # Dictionary of default test parameters per algorithm
│
├── scripts/                             # Data processing pipeline
│   ├── energy_avg.py                   # Computes average energy from raw CSV logs
│   ├── time_avg.py                     # Computes average execution time from raw CSV logs
│   ├── combine_energy.py                # Merges energy results from all methods into one CSV
│   ├── combine_time.py                  # Merges time results from all methods into one CSV
│   ├── carbon.py                        # Converts energy (μJ) to carbon emissions (gCO₂e)
│   ├── greenscore.py                    # Full GreenScore calculation pipeline (normalization + ranking)
│   ├── avg_combine.py                   # Combines mean energy/time/carbon into unified summary
│   ├── std.py                           # Calculates standard deviation across methods
│   └── README.md                         # Scripts documentation
│
├── visualization/                       # Plotting and chart generation
│   ├── __main__.py                      # CLI tool for generating various chart types
│   └── README.md                        # Visualization documentation
│
├── synthetic_survey/                    # LLM-based synthetic survey generation
│   ├── chatgpt_agent.py                # OpenAI GPT-4o-mini integration
│   ├── gemini_agent.py                  # Google Gemini integration
│   ├── utils.py                         # Pydantic schema and shared utilities
│   └── README.md                        # Survey module documentation
│
├── data/                                # Collected benchmark results
│   └── collection_1/                    # First data collection run
│       ├── cpython/                    # Raw CSV logs for CPython runs
│       ├── pypy/                       # Raw CSV logs for PyPy runs
│       ├── cython/                     # Raw CSV logs for Cython runs
│       ├── ctypes/                     # Raw CSV logs for ctypes runs
│       ├── pycompile/                  # Raw CSV logs for py_compile runs
│       ├── combine/                    # Aggregated comparison CSVs
│       └── analysis/                   # Final normalized values and GreenScore summaries
│
└── README.md                            # Main project documentation (research-focused)
```

### Key File Descriptions

| File/Directory | Purpose |
|---------------|---------|
| `benchmarks/*/Cpython/main.py` | CPython benchmark implementations using energy/time decorators |
| `energy_module/decorator.py` | Decorator that wraps functions to measure energy via pyRAPL and log to CSV |
| `time_modules/decorator.py` | Decorator that wraps functions to measure execution time and log to CSV |
| `input/__init__.py` | Centralized default parameters (test_n, algorithm inputs) for all 15 benchmarks |
| `scripts/greenscore.py` | Complete pipeline: normalizes metrics, computes per-method means, calculates GreenScore |
| `scripts/combine_energy.py` | Aggregates `energy_avg.csv` files from each method into one comparison table |
| `scripts/carbon.py` | Converts energy consumption (μJ) to carbon emissions using global average factor |
| `visualization/__main__.py` | CLI tool generating bar charts, line charts, scatter plots from processed CSVs |
| `synthetic_survey/chatgpt_agent.py` | Generates synthetic survey responses using OpenAI API with Pydantic validation |

---

## 3. Core Logic/Data Flow

### Main Entry Point

**⚠️ CRITICAL LIMITATION:** There is **no centralized entry point**. The main README references `python3 run_benchmarks.py`, but this file does not exist in the repository. Benchmarks must be run **manually, individually** from each algorithm's subdirectory.

### Execution Flow (Current Manual Process)

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Individual Benchmark Execution (Manual)                 │
└─────────────────────────────────────────────────────────────────┘
    │
    ├─> Developer navigates to: benchmarks/[Algorithm]/[Method]/
    │
    ├─> Runs: python main.py
    │
    ├─> Decorator @measure_energy_to_csv() executes:
    │   ├─> Creates folder: energy_benchmark/ (or custom folder_name)
    │   ├─> Runs function n times (default: 50)
    │   ├─> Measures energy via pyRAPL.Measurement
    │   └─> Logs to CSV: energy_benchmark/[csv_filename].csv
    │
    └─> Decorator @measure_time_to_csv() executes:
        ├─> Creates folder: time_benchmark/ (or custom folder_name)
        ├─> Runs function n times (default: 50)
        ├─> Measures time via time.time()
        └─> Logs to CSV: time_benchmark/[csv_filename].csv

┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Data Aggregation (Scripts)                               │
└─────────────────────────────────────────────────────────────────┘
    │
    ├─> Run: scripts/energy_avg.py <folder_path> <output_csv>
    │   └─> Reads all CSV files in folder, computes average package (uJ)
    │
    ├─> Run: scripts/time_avg.py <folder_path> <output_csv>
    │   └─> Reads all CSV files in folder, computes average execution_time (s)
    │
    └─> Repeat for each method folder (cpython, pypy, cython, ctypes, pycompile)

┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Method Combination (Scripts)                            │
└─────────────────────────────────────────────────────────────────┘
    │
    ├─> Run: scripts/combine_energy.py <output_csv>
    │   └─> Merges energy_avg.csv from all methods into one table
    │       Format: [algorithm, cpython, pypy, cython, ctypes, pycompile]
    │
    ├─> Run: scripts/combine_time.py <output_csv>
    │   └─> Merges time_avg.csv from all methods into one table
    │
    └─> Run: scripts/carbon.py
        └─> Reads combined energy CSV, converts to carbon (gCO₂e)
            Formula: energy_μJ × 1e-6 × 0.000475

┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: GreenScore Calculation (Scripts)                        │
└─────────────────────────────────────────────────────────────────┘
    │
    └─> Run: scripts/greenscore.py
        ├─> Reads: energy_com.csv, time_com.csv, carbon_footprint.csv
        ├─> Normalizes each metric (row-wise min-max per algorithm)
        ├─> Computes per-method mean scores across all algorithms
        ├─> Calculates: GreenScore = 0.4×Energy_norm + 0.4×Carbon_norm + 0.2×Time_norm
        └─> Outputs: green_score_ranking_[weights].csv

┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Visualization (Optional)                                │
└─────────────────────────────────────────────────────────────────┘
    │
    └─> Run: python -m visualization --[chart_type] [args]
        ├─> --evcvt: Grouped bar chart (Energy vs Carbon vs Time)
        ├─> --lcpack: Line charts per algorithm
        ├─> --scatter: Scatter plot (Energy vs Time)
        └─> --line_compare: Overlayed line chart
```

### Data Structures

**Energy Measurement Decorator (`energy_module/decorator.py`):**
- **Function Signature:** `@measure_energy_to_csv(n: int, csv_filename: str, folder_name: str = "energy_benchmark")`
- **CSV Output Format:**
  ```
  timestamp, function, run, package (uJ), dram (uJ)
  ```
- **System Info JSON:** Stores CPU, RAM, OS, architecture, test result file path

**Time Measurement Decorator (`time_modules/decorator.py`):**
- **Function Signature:** `@measure_time_to_csv(n: int, csv_filename: str, folder_name: str = "time_benchmark")`
- **CSV Output Format:**
  ```
  timestamp, function, run, execution_time (s)
  ```

**Input Parameters (`input/__init__.py`):**
- **Structure:** Nested dictionary `__default__[algorithm_name][parameter_name]`
- **Keys:** `test_n` (number of repetitions), algorithm-specific parameters (e.g., `n`, `depth`, `k`)

**GreenScore Calculation (`scripts/greenscore.py`):**
- **Normalization:** Row-wise min-max: `(value - min) / (max - min)` per algorithm
- **Mean Calculation:** Column-wise average across all algorithms per method
- **Final Formula:** `GreenScore = α·Energy_norm + β·Carbon_norm + γ·Time_norm` (default: α=0.4, β=0.4, γ=0.2)

---

## 4. Key Implementation Details

### Primary Programming Language and Frameworks

- **Language:** Python 3.x (CPython 3.13.2, PyPy 7.3.19 compatible with Python 3.11.11)
- **Core Libraries:**
  - `pyRAPL`: Intel RAPL energy measurement (Linux/Intel only)
  - `pandas`: Data manipulation and CSV processing
  - `matplotlib`: Visualization and chart generation
  - `pydantic`: Data validation for synthetic survey responses
  - `openai` / `google-genai`: LLM API clients for synthetic survey
  - `psutil`: System information gathering
  - `csv`, `json`, `os`, `time`: Standard library utilities

### Architecture Patterns

**1. Decorator Pattern (Measurement Infrastructure)**
- Both energy and time modules use Python decorators to wrap benchmark functions
- Decorators handle file I/O, system info logging, and repeated execution
- Low overhead: measurement occurs at function call boundary

**2. Functional Data Pipeline (Scripts)**
- Each script is a standalone utility with a single responsibility
- Pipeline stages: Raw CSV → Average → Combine → Normalize → GreenScore
- No shared state; communication via CSV files

**3. Modular Benchmark Structure**
- Each algorithm is self-contained with identical interface across methods
- Benchmark functions follow pattern: `run_energy_benchmark()` and `run_time_benchmark()`
- Input parameters centralized in `input/__init__.py`

### Critical Data Structures

**Energy Measurement Result:**
```python
pyRAPL.Measurement.result.pkg[0]  # Package energy in microjoules (μJ)
pyRAPL.Measurement.result.dram[0]  # DRAM energy (often 0 on laptops)
```

**Combined Comparison CSV Structure:**
```csv
algorithm,cpython,pypy,cython,ctypes,pycompile
binary-trees,1234567,987654,1111111,888888,999999
fasta,2345678,876543,2222222,777777,888888
...
```

**GreenScore Ranking Output:**
```csv
method,energy_mean,time_mean,carbon_mean,green_score
ctypes,0.162,0.123,0.193,0.1666
cython,0.234,0.145,0.245,0.2234
...
```

---

## 5. Unfinished/TODO Areas (The Risk Register)

### High Priority

**1. Missing Centralized Benchmark Runner**
- **Location:** Referenced in main `README.md` line 126: `python3 run_benchmarks.py`
- **Status:** File does not exist
- **Intended Functionality:** Should automate execution of all 75 benchmark combinations (15 algorithms × 5 methods), handle folder creation, manage execution order, and provide progress tracking
- **Impact:** Manual execution is time-consuming and error-prone; no reproducibility guarantee
- **Priority:** **HIGH** - Core functionality blocker

**2. Hardcoded Absolute Paths**
- **Locations:**
  - `visualization/__main__.py` (lines 218, 226, 234, 256): Contains `/home/eaegon/Documents/GITHUB/...` paths
  - `input/__init__.py` (line 56): Contains `/home/eaegon/Documents/GITHUB/.../dna.txt`
  - `scripts/greenscore.py` (lines 25-27): Contains `C:\\Users\\User\\OneDrive\\...` paths (Windows)
  - `scripts/combine_energy.py` (lines 46-52): Contains relative paths that assume specific directory structure
- **Intended Functionality:** Paths should be configurable via environment variables, config files, or command-line arguments
- **Impact:** Code will fail on different machines or directory structures
- **Priority:** **HIGH** - Portability blocker

**3. Hardcoded API Keys**
- **Locations:**
  - `synthetic_survey/chatgpt_agent.py` (line 51): `api_key="api-key"`
  - `synthetic_survey/gemini_agent.py` (line 55): `api_key="api-key"`
- **Intended Functionality:** Should read from environment variables (e.g., `OPENAI_API_KEY`, `GEMINI_API_KEY`) or secure config files
- **Impact:** Synthetic survey module cannot function without manual code modification
- **Priority:** **HIGH** - Security and functionality issue

### Medium Priority

**4. Incomplete Error Handling**
- **Location:** Multiple scripts (e.g., `scripts/carbon.py`, `scripts/energy_avg.py`)
- **Status:** Basic try-except blocks exist but do not handle all edge cases (missing files, malformed CSVs, division by zero in normalization)
- **Intended Functionality:** Robust error messages, graceful degradation, validation of input file formats
- **Impact:** Scripts may fail silently or produce incorrect results
- **Priority:** **MEDIUM** - Data integrity risk

**5. No Configuration Management System**
- **Location:** Throughout codebase (test_n, folder names, carbon intensity factor, GreenScore weights)
- **Status:** Values are hardcoded or defined in multiple places
- **Intended Functionality:** Centralized config file (YAML/JSON) for:
  - Number of benchmark repetitions (`test_n`)
  - Output folder names
  - Carbon intensity factor (currently `0.000475 gCO₂e/J`)
  - GreenScore weights (α, β, γ)
- **Impact:** Changes require editing multiple files; no single source of truth
- **Priority:** **MEDIUM** - Maintainability issue

**6. Visualization Module Path Dependencies**
- **Location:** `visualization/__main__.py`
- **Status:** `--lcpack` and `--etc_compare` flags have hardcoded absolute paths
- **Intended Functionality:** Accept file paths as command-line arguments or use relative paths from project root
- **Impact:** Visualization cannot run on different systems without code modification
- **Priority:** **MEDIUM** - Usability issue

### Low Priority

**7. Commented-Out Code in GreenScore Script**
- **Location:** `scripts/greenscore.py` (lines 13-22)
- **Status:** Alternative file path definitions are commented out
- **Intended Functionality:** Should be removed or replaced with configurable path selection
- **Impact:** Code clutter, potential confusion
- **Priority:** **LOW** - Code quality

**8. Typo in Filename**
- **Location:** `benchmarks/Towers-of-Hanoi/py_compile/__compailer.py` (should be `__compiler.py`)
- **Status:** Filename has typo but file exists and may be functional
- **Intended Functionality:** Standardize filename to match other benchmarks
- **Impact:** Inconsistency, potential import issues
- **Priority:** **LOW** - Consistency issue

**9. Missing Documentation for Script Execution Order**
- **Location:** `scripts/README.md` describes individual scripts but lacks explicit workflow
- **Status:** Workflow is implied but not explicitly documented with example commands
- **Intended Functionality:** Step-by-step execution guide with example commands and expected outputs
- **Impact:** New developers may struggle to understand the correct sequence
- **Priority:** **LOW** - Documentation gap

**10. No Automated Testing**
- **Location:** Entire codebase
- **Status:** No unit tests, integration tests, or validation scripts
- **Intended Functionality:** Test suite for:
  - Decorator functionality
  - CSV parsing and aggregation
  - GreenScore calculation correctness
  - Normalization edge cases
- **Impact:** No verification of correctness after changes
- **Priority:** **LOW** - Quality assurance (acceptable for research code, but limits maintainability)

---

## Additional Notes

### Platform Dependencies

- **Energy Measurement:** Requires Intel CPU with RAPL support and Linux OS. Will not work on AMD, ARM, or Windows (pyRAPL limitation).
- **Cython Benchmarks:** Require compilation step (`python setup.py build_ext --inplace`) before execution.
- **ctypes Benchmarks:** Require compiled C shared libraries (`.so` files on Linux, `.dll` on Windows).

### Data Collection Workflow (As Implemented)

The research data in `data/collection_1/` was collected using the following manual process:
1. Each benchmark was run individually 50 times per method
2. Raw CSVs were aggregated using `energy_avg.py` and `time_avg.py`
3. Results were combined using `combine_energy.py` and `combine_time.py`
4. Carbon footprint was calculated using `carbon.py`
5. Final GreenScore was computed using `greenscore.py`

This process is **not automated** and requires significant manual coordination.

---

## Summary

The repository contains a **functional but incomplete** benchmarking framework. The core measurement infrastructure is solid, and the data processing pipeline works when executed manually. However, the lack of a centralized runner, hardcoded paths, and missing configuration management significantly limit portability and ease of use. The codebase is suitable for research reproducibility if the user follows the manual workflow, but it is not production-ready for automated benchmarking or distribution to new users without modification.

**Recommended Next Steps for Completion:**
1. Implement `run_benchmarks.py` with CLI arguments for algorithm/method selection
2. Replace all hardcoded paths with environment variables or config files
3. Move API keys to environment variables
4. Add comprehensive error handling and input validation
5. Create a configuration file (YAML/JSON) for all tunable parameters

