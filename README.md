# PGSI Analyzer: Python GreenScore and Sustainability Analyzer

**PGSI Analyzer** is a comprehensive benchmarking and sustainability analysis tool for Python implementations. It measures and compares the **energy consumption**, **execution time**, **carbon footprint**, and overall **sustainability** of different Python execution methods using a novel composite metric called **GreenScore**.

## Project Overview

### What is PGSI Analyzer?

PGSI Analyzer is a CLI-driven benchmark execution framework that runs a suite of CPU-bound algorithms across multiple Python execution methods. It automatically collects raw measurement data, aggregates results, computes carbon emissions, and produces a final **GreenScore** ranking that helps researchers and developers identify the most sustainable Python execution strategies.

### What It Measures

- **Execution Time**: Precise runtime measurement using Python's `time.time()`
- **Energy Consumption**: Cross-platform fallback chain: `pyRAPL` (Linux x86_64) -> `codecarbon` (all platforms) -> CPU-time/TDP estimation
- **Carbon Footprint**: Derived from energy consumption using configurable carbon intensity factors
- **GreenScore**: A weighted composite metric integrating energy, carbon, and time (lower is better)

### What It Runs

The tool executes a suite of **15 diverse CPU-bound algorithms**, each available across **5 execution methods**:

- **CPython**: Standard Python interpreter
- **PyPy**: Just-In-Time (JIT) compiler
- **Cython**: Ahead-of-Time (AOT) compiler
- **ctypes**: Foreign Function Interface to native C code
- **py_compile**: Bytecode-compiled Python

This results in **75 total benchmark combinations** (15 algorithms × 5 methods), providing comprehensive coverage of real-world Python workloads.

## Features

### Benchmarks

- **15 algorithms** covering diverse computational patterns:
  - `binary-trees`, `fannkuch-redux`, `fasta`, `k-nucleotide`, `mandelbrot`
  - `n-body`, `n-queens`, `pi-digits`, `regex-redux`, `reverse-complement`
  - `sieve`, `spectral-norm`, `strassen`, `hanoi`, `knn`
- Each algorithm available for all 5 execution methods
- Deterministic benchmark registry with automatic discovery
- Package-integrated benchmarks (no external scripts required)

### Add a Benchmark (Developer Pattern)

End-user workflow (outside package source):

1. Install PGSI Analyzer in your project environment:

```bash
pip install pgsi-analyzer
```

2. Generate a benchmark scaffold in your own project folder:

```bash
pgsi-analyzer startproject my-benchmarks --algorithms hanoi
```

Equivalent command (also supported):

```bash
pgsi-analyzer benchmark init-template --output ./my-benchmarks --algorithms hanoi
```

Create a single custom benchmark and auto-register it:

```bash
pgsi-analyzer create benchmark --name A1 --benchmarks-dir ./my-benchmarks
```

This creates `./my-benchmarks/A1/...` and updates `./my-benchmarks/pgsi_registry.json`.

Tip: when running from a project that has `./benchmarks/pgsi_registry.json`,
`benchmark list` and `benchmark run` auto-detect `./benchmarks` even if
`--benchmarks-dir` is omitted.

3. Implement your algorithm workload by editing generated files under:
   `<benchmarks_dir>/<algorithm>/<method>/main.py`
4. Keep the PGSI decorators on your benchmark functions:
   - `@measure_energy_to_csv(n=get_measurement_runs("<algorithm>"), csv_filename="<algorithm>_<method>")`
   - `@measure_time_to_csv(n=get_measurement_runs("<algorithm>"), csv_filename="<algorithm>_<method>")`
5. Run/list with `--benchmarks-dir <benchmarks_dir>` to include your custom benchmarks

The included KNN CPython benchmark is a concrete decorator example:
- `src/pgsi_analyzer/benchmarks/knn/cpython/main.py`

List algorithms including your custom folder:

```bash
pgsi-analyzer benchmark list --algorithms --benchmarks-dir ./my-benchmarks
```

Run your custom algorithm:

```bash
pgsi-analyzer benchmark run \
  --algorithms my-algo \
  --methods cpython \
  --benchmarks-dir ./my-benchmarks
```

Generate a full template first (recommended):

```bash
pgsi-analyzer benchmark init-template --output ./my-benchmarks --algorithms all
```

This scaffolds the benchmark tree with commented starter files (including `cython`/`ctypes` support files), so end developers can implement directly in their own project folder.

Quick help:

```bash
pgsi-analyzer benchmark init-template --help
```

Example generated tree (trimmed):

```text
my-benchmarks/
├── README.md
├── hanoi/
│   ├── cpython/main.py
│   ├── pypy/main.py
│   ├── py_compile/main.py
│   ├── cython/
│   │   ├── main.py
│   │   ├── raw.pyx
│   │   └── setup.py
│   └── ctypes/
│       ├── main.py
│       └── raw.c
└── knn/
    └── ...
```

### Full Pipeline

The tool orchestrates a complete measurement and analysis pipeline:

1. **Build**: Compiles Cython and ctypes benchmarks (if needed)
2. **Execute**: Runs benchmarks in isolated subprocesses
3. **Collect**: Gathers raw CSV data from measurement decorators
4. **Aggregate**: Processes raw data per method
5. **Combine**: Merges results across methods
6. **Carbon**: Calculates carbon footprint from energy data
7. **GreenScore**: Computes final sustainability ranking

### Cross-Platform CLI

- `pgsi-analyzer benchmark list`: Lists available algorithms and methods
- `pgsi-analyzer benchmark run`: Executes benchmarks and generates results
- `pgsi-analyzer benchmark init-template`: Generates a Django-style user benchmark scaffold
- `pgsi-analyzer startproject <name>`: Django-like one-command project scaffold
- `pgsi-analyzer create benchmark --name <name>`: Creates one benchmark scaffold and registers it
- Supports flexible algorithm/method selection (`all` or specific names)
- Configurable global runs, per-algorithm run overrides, output directories, and GreenScore weights

### Configuration

- **Tool paths** configurable via:
  - `.env` file (recommended)
  - Environment variables (`PGSI_PYPY_PATH`, `PGSI_CC_PATH`, `PGSI_PYTHON_PATH`)
  - CLI flags (`--pypy-path`, `--cc-path`, `--python-path`)
- Priority: CLI flags > Environment variables > `.env` > Built-in defaults
- Reproducible ordering and deterministic CSV outputs

## Installation

### Python Requirements

- **Python 3.8+** (tested on 3.8 through 3.14)
- `pip` package manager

### Basic Installation

Install from PyPI (or install from source):

```bash
pip install pgsi-analyzer
```

This automatically installs Python dependencies including:
- `cython>=3.0.0` (for Cython benchmark compilation)
- `python-dotenv>=1.0.0` (for `.env` file support)
- `pandas`, `matplotlib`, `numpy`, `psutil` (core analysis libraries)

### System Prerequisites

**Required:**

- **C Compiler** (for `ctypes` and `cython` methods):
  - **Linux/macOS**: `gcc` or `clang` (install via package manager)
  - **Windows**: `cl.exe` (Visual Studio Build Tools) or `gcc` (MinGW/MSYS2)

- **Python development headers** (for **Cython** on Linux): If Cython build fails with *Python.h: No such file or directory*, install e.g. `python3-dev` (Debian/Ubuntu: `sudo apt install python3-dev`). See **audit/usage_guide.md** §1.5 for details.

**Optional but Recommended:**

- **PyPy** on system PATH (for `pypy` method):
  - Install from [PyPy website](https://www.pypy.org/download.html)
  - Ensure `pypy` or `pypy3` is accessible in your PATH
  - **Install only the dependencies used by benchmark scripts** (the runner sets `PYTHONPATH` so PyPy finds the project; you do not need to build pandas/pillow for PyPy). If PyPy has no pip, bootstrap it first:
    ```bash
    pypy3 -m ensurepip
    pypy3 -m pip install psutil python-dotenv
    ```
    (See **audit/usage_guide.md** §1.4 for details.)

**Platform Limitations:**

- **Hardware energy counters** (pyRAPL) are only available on **Linux x86_64**
- When `pyRAPL` is unavailable, PGSI tries this fallback chain in order:
  - `codecarbon`-based tracking (works on macOS, Windows, Linux, including ARM devices such as Raspberry Pi)
  - CPU-time/TDP estimation fallback (always available)
- On macOS, Windows, Linux ARM, and Raspberry Pi, this provides an OS-independent energy path even without RAPL counters
- All platforms support time measurement and carbon footprint calculation

### Energy Measurement Fallback Chain

PGSI uses a deterministic fallback chain so energy collection works across desktop and edge platforms:

1. **`pyRAPL`** (preferred): used only when running on **Linux x86_64** with Intel RAPL access.
2. **`codecarbon`**: used when `pyRAPL` is not available (for example on **macOS**, **Windows**, **Linux ARM**, and **Raspberry Pi**).
3. **CPU-time/TDP model**: final fallback when `codecarbon` is not installed or cannot return usable energy data.

This means benchmark runs can continue on macOS, Windows, Linux, and Raspberry Pi without failing due to missing hardware counters.

## Quick Start: Basic Usage

### List Available Benchmarks

```bash
pgsi-analyzer benchmark list
```

This displays all 15 available algorithms and 5 execution methods.

### Run a Small Test Benchmark

```bash
pgsi-analyzer benchmark run \
  --algorithms hanoi \
  --methods cpython \
  --runs 5
```

This runs the `hanoi` algorithm using CPython for 5 runs. The tool will:
- Execute the benchmark
- Collect energy and time measurements
- Generate raw CSVs in `energy_benchmark/` and `time_benchmark/` directories
- Produce aggregated results and a `GreenScore.csv` in the default `results/` directory

### Run Multiple Algorithms and Methods

```bash
pgsi-analyzer benchmark run \
  --algorithms hanoi binary-trees \
  --methods cpython pypy \
  --runs 10
```

This runs two algorithms across two methods, generating comparison data.

### Run Full Suite

```bash
pgsi-analyzer benchmark run \
  --algorithms all \
  --methods all \
  --runs 50 \
  --output results/
```

**Note**: This can take significant time (hours depending on your hardware). The `results/` directory will contain:
- Raw measurement CSVs organized by method
- Aggregated CSVs per method
- Combined results across all methods
- Final `GreenScore.csv` with sustainability rankings

### Launch the GUI (Easy setup + run)

You can launch a desktop GUI to configure paths, select algorithms/methods, set run options, and start PGSI without typing full CLI commands.

```bash
pgsi-analyzer-gui
```

The GUI provides:
- Step 1 project setup page (create a new benchmark project or load an existing one)
- Step 2 run page with benchmark/method selection and run configuration
- Setup field for `.env` path
- Per-algorithm run override dialog (set different run counts per selected algorithm)
- Live run log with progress bar updates from `[x/y]` execution progress
- Final GreenScore ranking popup (pyramid view) when a run completes successfully
- One-click output folder access

### GUI Quick Workflow (Screenshot)

Use this screen as the standard first-run workflow:

1. Set the `.env` path in **Setup: Tool Paths**
2. Configure output + run settings in **Run Configuration**
3. Choose algorithms/methods in **Benchmarks Selection**
4. Click **Run PGSI Analysis** and monitor **Run Log**

![PGSI GUI dark theme run configuration](docs/images/gui-dark-run-config.png)

> If the image does not render yet, place your screenshot at `docs/images/gui-dark-run-config.png`.

### Per-Algorithm Run Overrides (CLI)

You can override the global `--runs` value for specific algorithms:

```bash
pgsi-analyzer benchmark run \
  --algorithms hanoi sieve \
  --methods cpython \
  --runs 50 \
  --algorithm-runs hanoi=20 sieve=10
```

In this example, `hanoi` runs 20 times, `sieve` runs 10 times, and any algorithm not listed in `--algorithm-runs` uses the global `--runs` value.

### Custom GreenScore Weights

```bash
pgsi-analyzer benchmark run \
  --algorithms all \
  --methods all \
  --runs 50 \
  --alpha 0.5 --beta 0.3 --gamma 0.2
```

The `--alpha`, `--beta`, and `--gamma` flags control how energy, carbon footprint, and execution time contribute to the final GreenScore. Default values are `alpha=0.4`, `beta=0.4`, `gamma=0.2`.

## Tool-Path Configuration

### Using `.env` File (Recommended)

Create a `.env` file in your project directory:

```env
PGSI_PYTHON_PATH=/usr/bin/python3
PGSI_PYPY_PATH=/usr/bin/pypy3
PGSI_CC_PATH=/usr/bin/gcc
```

Then run benchmarks with:

```bash
pgsi-analyzer benchmark run \
  --algorithms hanoi \
  --methods cpython \
  --runs 5 \
  --env-file .env
```

### Using CLI Flags

Override paths directly from the command line:

```bash
pgsi-analyzer benchmark run \
  --algorithms hanoi \
  --methods cpython \
  --runs 5 \
  --python-path /path/to/python \
  --pypy-path /path/to/pypy \
  --cc-path /usr/bin/gcc
```

### Configuration Precedence

Paths are resolved in this order (highest to lowest priority):

1. **Command-line flags** (`--python-path`, `--pypy-path`, `--cc-path`)
2. **Environment variables** (`PGSI_PYTHON_PATH`, `PGSI_PYPY_PATH`, `PGSI_CC_PATH`)
3. **`.env` file** (if `--env-file` is specified or auto-detected)
4. **Built-in defaults** (system PATH detection)

## Outputs and Where to Find Them

After running benchmarks, you'll find the following structure in your output directory (default: `results/`):

```
results/
├── energy_benchmark/          # Raw energy measurement CSVs
│   └── hanoi_cpython.csv
├── time_benchmark/            # Raw time measurement CSVs
│   └── hanoi_cpython.csv
├── cpython/                   # Aggregated results per method
│   ├── energy_aggregated.csv
│   └── time_aggregated.csv
├── energy_combined.csv        # Combined energy across all methods
├── time_combined.csv          # Combined time across all methods
├── carbon_footprint.csv       # Carbon emissions per method
└── GreenScore.csv             # Final sustainability ranking
```

### Interpreting GreenScore.csv

The `GreenScore.csv` file contains the final sustainability rankings. You can open it in any spreadsheet application or analyze it with pandas:

```python
import pandas as pd
df = pd.read_csv('results/GreenScore.csv')
print(df.sort_values('green_score'))
```

**Lower GreenScore = better sustainability**. The file includes normalized energy, carbon, and time metrics along with the composite GreenScore for each execution method.

## Research Context

This tool was developed as part of the research study: **"Python Under the Microscope: A Comparative Energy Analysis of Execution Methods"** (IEEE Access, 2025).

### Research Objectives

1. **Energy & Environmental Profiling**: Quantitatively compare execution time, energy consumption, and CO₂ emissions across Python execution methods.
2. **Sustainable Runtime Selection**: Identify the most eco-friendly execution strategy for Python workloads.
3. **Benchmark-Driven Insights**: Establish a reproducible, algorithmically diverse benchmark suite reflective of real-world Python usage.

### Methodology

- **15 diverse CPU-bound algorithms** (10 from Computer Language Benchmarks Game + 5 supplementary)
- **5 execution methods** with identical algorithm implementations
- **50 runs per combination** for statistical significance
- **Hardware-first, cross-platform energy measurement**: `pyRAPL` on Linux x86_64, then `codecarbon`, then CPU-time/TDP fallback

## Citation

If you use this work in your research, please cite:

```bibtex
@article{shadab2025microscope,
  title   = {Python Under the Microscope: A Comparative Energy Analysis of Execution Methods},
  author  = {Turja, Md Fatin Shadab and Others},
  journal = {IEEE Access},
  year    = {2025}
}
```

## Additional Documentation

### Audit documentation suite (`/audit`)

The **audit** folder contains structured documentation for users and contributors, produced from the project’s architecture and testing audits:

| Document | Purpose |
|----------|---------|
| **[audit/usage_guide.md](audit/usage_guide.md)** | **Start here.** Step-by-step installation (CPython, PyPy, C compiler), the "Golden Path" CLI examples, hardware setup (Linux RAPL / cap_sys_rawio), and ToolPaths configuration (CLI, .env, environment variables). Run count and **PGSI_RUNS** are explained. |
| **[audit/contributor_guide.md](audit/contributor_guide.md)** | Adding a new benchmark (folder structure, main.py decorators, registry entry), running pytest and interpreting platform-specific failures, and data contracts (required CSV columns). |
| **[audit/functional_overview.md](audit/functional_overview.md)** | What the package does, user-facing features, main vs helper logic, and entry points. |
| **[audit/architecture.md](audit/architecture.md)** | Process boundaries, data pipeline, internal CSV contracts, error propagation, ToolPaths, and Spike #4 design (PGSI_RUNS, RAPL permissions). |
| **[audit/testing_and_health.md](audit/testing_and_health.md)** | Test inventory, coverage map, failure handling, known limitations, and green/red status. |
| **[audit/spike_4_runs_and_permissions.md](audit/spike_4_runs_and_permissions.md)** | Design for deterministic run control (PGSI_RUNS) and RAPL permission feedback. |

A new developer can set up the environment and run a standard benchmark using **usage_guide.md** alone; contributors adding benchmarks or running tests should use **contributor_guide.md** and the architecture/testing docs as needed.

### Other docs

- **[Getting Started Guide](docs/getting_started.md)** (if present): Step-by-step setup and validation
- **[Implementation Summary](IMPLEMENTATION_SUMMARY.md)** (if present): Technical architecture details

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

This research was conducted as part of **EEE 4261 (Green Computing)** offered at United International University in Spring 2025. All code, data, and visualization tools are released for reproducibility and open sustainability research.
