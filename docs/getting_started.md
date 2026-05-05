# Getting Started with PGSI Analyzer

This guide provides step-by-step instructions for setting up and using PGSI Analyzer on a new device.

## Current State Overview

### Implemented Pipeline

PGSI Analyzer implements a complete benchmark execution and analysis pipeline:

1. **Algorithm × Method Execution**: Runs 15 algorithms across 5 execution methods (75 total combinations)
2. **Measurement Collection**: Uses decorators to automatically write energy and time CSVs during benchmark execution
3. **Data Aggregation**: Processes raw CSVs per method
4. **Result Combination**: Merges aggregated data across all methods
5. **Carbon Calculation**: Derives carbon footprint from energy measurements
6. **GreenScore Computation**: Produces final sustainability rankings

### CLI Surface

The tool provides project scaffolding plus benchmark execution commands:

- **`pgsi-analyzer`**: Bootstraps `./benchmarks` on first run (when no command is provided)
- **`pgsi-analyzer startproject <name> --algorithms ...`**: Creates a user benchmark project scaffold
- **`pgsi-analyzer create benchmark --name <name> --benchmarks-dir <dir>`**: Adds one benchmark scaffold and updates `pgsi_registry.json`
- **`pgsi-analyzer benchmark list`**: Lists available algorithms and execution methods
- **`pgsi-analyzer benchmark run`**: Executes benchmarks with configurable options:
  - `--algorithms`: Select specific algorithms or use `all`
  - `--methods`: Select specific methods or use `all`
  - `--runs`: Number of runs per benchmark (default: 50)
  - `--output`: Output directory (default: `results/`)
  - `--alpha`, `--beta`, `--gamma`: GreenScore weight configuration
  - `--benchmarks-dir`: Include user benchmark projects
  - `--env-file`, `--python-path`, `--pypy-path`, `--cc-path`: Tool path configuration

### Known Limitations and Warnings

- **C Compiler Required**: The `ctypes` and `cython` methods require a C compiler (gcc/clang on Linux/macOS, cl.exe or gcc on Windows)
- **PyPy Optional**: The `pypy` method is optional; benchmarks will fail if PyPy is requested but not found
- **Hardware Energy Counters**: Only available on Linux x86_64 systems with Intel processors. On other platforms, energy is estimated from CPU time
- **Full Suite Runtime**: Running all 15 algorithms × 5 methods × 50 runs can take several hours depending on hardware

## Environment Setup on a New Device

### Step 1: Install System Dependencies

#### Linux (Ubuntu/Debian)

```bash
# Install Python and pip
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv

# Install C compiler (required for ctypes/cython)
sudo apt-get install gcc

# Optionally install PyPy
sudo apt-get install pypy3
```

#### macOS

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python and pip
brew install python3

# Install C compiler (Xcode Command Line Tools)
xcode-select --install

# Optionally install PyPy
brew install pypy3
```

#### Windows

1. **Install Python**: Download from [python.org](https://www.python.org/downloads/) (Python 3.8+)
2. **Install C Compiler** (choose one):
   - **Option A**: Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022) (includes `cl.exe`)
   - **Option B**: Install [MinGW-w64](https://www.mingw-w64.org/) or [MSYS2](https://www.msys2.org/) (provides `gcc`)
3. **Optionally install PyPy**: Download from [pypy.org](https://www.pypy.org/download.html) and add to PATH

### Step 2: Create and Activate Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### Step 3: Install PGSI Analyzer

```bash
# Install from PyPI (includes CodeCarbon by default)
pip install pgsi-analyzer

# Recommended production benchmarking profile
pip install "pgsi-analyzer[energy,analysis]"

# Or install from source (if cloning repository)
pip install -e .
```

This installs core Python dependencies including:
- `cython>=3.0.0`
- `python-dotenv>=1.0.0`
- `pandas`, `matplotlib`, `numpy`, `psutil`, `codecarbon`

### Step 4: (Optional) Create `.env` File

Create a `.env` file in your project directory to pin specific tool paths:

```env
PGSI_PYTHON_PATH=/usr/bin/python3
PGSI_PYPY_PATH=/usr/bin/pypy3
PGSI_CC_PATH=/usr/bin/gcc
```

**Windows example:**
```env
PGSI_PYTHON_PATH=C:\Python314\python.exe
PGSI_PYPY_PATH=C:\pypy3.11-v7.3.15-win64\pypy3.exe
PGSI_CC_PATH=C:\Program Files\mingw-w64\x86_64-8.1.0-posix-seh-rt_v6-rev0\mingw64\bin\gcc.exe
```

### Step 5: Verify Installation

```bash
# Optional: bootstrap default local project scaffold
pgsi-analyzer

# List available benchmarks
pgsi-analyzer benchmark list
```

**Expected output:**
```
Available algorithms:
  - binary-trees
  - fannkuch-redux
  - fasta
  - hanoi
  - k-nucleotide
  - knn
  - mandelbrot
  - n-body
  - n-queens
  - pi-digits
  - regex-redux
  - reverse-complement
  - sieve
  - spectral-norm
  - strassen

Available execution methods:
  - cpython
  - pypy
  - cython
  - ctypes
  - py_compile
```

If you see this output, installation is successful!

## Running and Validating a Small Test

### Step 1: Run a Tiny Benchmark

Run a minimal test to verify everything works:

```bash
pgsi-analyzer benchmark run \
  --algorithms hanoi \
  --methods cpython \
  --runs 3 \
  --output test_results/
```

This command:
- Runs the `towers-of-hanoi` algorithm
- Uses the `cpython` method (no compilation needed)
- Executes 3 runs (quick test)
- Saves results to `test_results/` directory

### Step 2: Verify Output Structure

After execution completes, check the `test_results/` directory:

```bash
ls -R test_results/
```

**Expected structure:**
```
test_results/
├── energy_benchmark/
│   ├── hanoi_cpython.csv
│   └── system_info.json (or system_info_pyrapl.json on Linux)
├── time_benchmark/
│   ├── hanoi_cpython.csv
│   └── system_info.json
├── cpython/
│   ├── energy_aggregated.csv
│   └── time_aggregated.csv
├── energy_combined.csv
├── time_combined.csv
├── carbon_footprint.csv
└── GreenScore.csv
```

### Step 3: Validate Results

**Check CSV files exist and are non-empty:**

```bash
# On Linux/macOS:
wc -l test_results/*.csv test_results/*/*.csv

# On Windows (PowerShell):
Get-ChildItem -Recurse -Filter *.csv | Select-Object FullName, Length
```

**Inspect GreenScore.csv:**

```bash
# View the file
cat test_results/GreenScore.csv

# Or use Python
python3 -c "import pandas as pd; print(pd.read_csv('test_results/GreenScore.csv'))"
```

**Expected GreenScore.csv content:**
- Columns: `method`, `green_score`, and normalized metrics
- At least one row (for `cpython` method)
- GreenScore value should be a positive number

### Step 4: Test with Multiple Methods (Optional)

If you have PyPy installed, test multiple methods:

```bash
pgsi-analyzer benchmark run \
  --algorithms hanoi \
  --methods cpython pypy \
  --runs 5 \
  --output test_results_multi/
```

This verifies that:
- Multiple methods can be executed
- Results are properly combined
- GreenScore.csv contains multiple rows for comparison

## Running the Full Suite Safely

### Pre-Run Checklist

Before running the full benchmark suite, ensure:

1. **Power Management**:
   - Laptop is plugged into power (not running on battery)
   - Power settings prevent sleep during execution

2. **System Resources**:
   - Close unnecessary applications
   - Ensure sufficient disk space (results can be several MB)
   - Consider system load (avoid running during peak usage)

3. **Advanced (Optional)**:
   - Pin CPU governor to performance mode (Linux):
     ```bash
     sudo cpupower frequency-set -g performance
     ```
   - Disable CPU frequency scaling for consistent results

### Full Suite Command

```bash
pgsi-analyzer benchmark run \
  --algorithms all \
  --methods all \
  --runs 50 \
  --output full_results/
```

**Expected behavior:**
- Execution time: **Several hours** (depends on hardware)
- Progress indicators: The CLI shows progress for each algorithm/method combination
- Results accumulation: Files are written incrementally as benchmarks complete
- Final output: `full_results/GreenScore.csv` with rankings for all 5 methods

### Monitoring Progress

The CLI provides real-time progress updates:

```
Running benchmark suite:
  Algorithms: 15 (hanoi, binary-trees, fannkuch-redux...)
  Methods: 5 (cpython, pypy, cython, ctypes, py_compile)
  Runs per benchmark: 50
  Output directory: full_results/

Phase 1: Building benchmarks...
  Building hanoi/cython... ✓
  Building hanoi/ctypes... ✓
  ...

Phase 2: Executing benchmarks...
  [1/75] hanoi/cpython... ✓
  [2/75] hanoi/pypy... ✓
  ...
```

## Troubleshooting

### "gcc not found" or Compiler Errors

**Problem**: C compiler is not found when running `ctypes` or `cython` methods.

**Solutions**:

1. **Install compiler**:
   - Linux: `sudo apt-get install gcc`
   - macOS: `xcode-select --install`
   - Windows: Install Visual Studio Build Tools or MinGW

2. **Configure path**:
   ```bash
   # Using .env file
   echo "PGSI_CC_PATH=/usr/bin/gcc" >> .env
   
   # Or using CLI flag
   pgsi-analyzer benchmark run ... --cc-path /usr/bin/gcc
   ```

3. **Verify compiler**:
   ```bash
   gcc --version  # Should show version info
   ```

### PyPy Method Fails

**Problem**: Error message like "PyPy not found" or "PyPy method selected but no valid PyPy executable found".

**Solutions**:

1. **Install PyPy**:
   - Linux: `sudo apt-get install pypy3`
   - macOS: `brew install pypy3`
   - Windows: Download from [pypy.org](https://www.pypy.org/download.html)

2. **Verify PyPy is on PATH**:
   ```bash
   which pypy3  # Linux/macOS
   where pypy3  # Windows
   ```

3. **Configure path explicitly**:
   ```bash
   # Using .env file
   echo "PGSI_PYPY_PATH=/usr/bin/pypy3" >> .env
   
   # Or using CLI flag
   pgsi-analyzer benchmark run ... --pypy-path /usr/bin/pypy3
   ```

4. **Skip PyPy method** if not needed:
   ```bash
   pgsi-analyzer benchmark run --methods cpython cython ctypes py_compile ...
   ```

### Energy Measurement Not Available

**Problem**: Warning about energy estimation or missing hardware counters.

**Explanation**:
- Hardware energy counters (pyRAPL) are **only available on Linux x86_64** with Intel processors
- Non-RAPL fallback order is deterministic: `codecarbon` -> dataset-backed `cpu_power.csv` TDP -> generic TDP
- This is expected behavior; CSV rows include methodology/provenance fields for auditability

**What to expect**:
- Linux x86_64: `hardware_rapl_linux` when RAPL is available
- Other platforms: `estimated_codecarbon`, else `dataset_tdp`, else `generic_tdp`

**Note**: All platforms still produce valid time measurements and carbon footprint calculations.

### Benchmark Execution Timeout

**Problem**: Benchmarks fail with timeout errors.

**Solutions**:

1. **Increase timeout** (if modifying code): The default timeout is 3600 seconds (1 hour) per benchmark
2. **Check system resources**: Ensure CPU and memory are not exhausted
3. **Run fewer algorithms**: Test with a subset first:
   ```bash
   pgsi-analyzer benchmark run --algorithms hanoi binary-trees --methods cpython --runs 5
   ```

### Missing CSV Files

**Problem**: Expected CSV files are not found in output directory.

**Solutions**:

1. **Check output directory**: Verify the `--output` path is correct
2. **Check for errors**: Review CLI output for execution failures
3. **Verify benchmark completion**: Ensure benchmarks finished successfully (look for "✓" indicators)
4. **Check file permissions**: Ensure write permissions in output directory

### Import Errors

**Problem**: `ModuleNotFoundError` or import errors when running benchmarks.

**Solutions**:

1. **Reinstall package**:
   ```bash
   pip uninstall pgsi-analyzer
   pip install pgsi-analyzer
   ```

2. **Check virtual environment**: Ensure virtual environment is activated
3. **Verify Python version**: Ensure Python 3.8+ is being used:
   ```bash
   python3 --version
   ```

## Next Steps

After successfully running benchmarks:

1. **Analyze Results**: Open `GreenScore.csv` in a spreadsheet or use pandas for analysis
2. **Compare Methods**: Compare GreenScore values across different execution methods
3. **Explore Visualizations**: Use the CLI visualization commands (see main README)
4. **Customize Weights**: Experiment with different `--alpha`, `--beta`, `--gamma` values
5. **Read Research Paper**: Understand the methodology behind GreenScore calculation

For more information, see the [main README](../README.md) or [Implementation Summary](../IMPLEMENTATION_SUMMARY.md).

