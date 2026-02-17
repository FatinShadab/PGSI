# PGSI Analyzer — Usage Guide

**Audit document.** Step-by-step setup and the "Golden Path" for running benchmarks and interpreting results. Use this guide to get from a fresh machine to a completed benchmark run.

---

## 1. Installation

### 1.1 Python and pip

- **Python 3.8 or newer** (tested up to 3.14).
- Ensure `pip` is available:

  ```bash
  python -m pip --version
  ```

### 1.2 Install the package

From the project root (or PyPI):

```bash
pip install -e .
```

Or from PyPI when published:

```bash
pip install pgsi-analyzer
```

Core dependencies (installed automatically) include: `pandas`, `matplotlib`, `numpy`, `psutil`, `cython`, `python-dotenv`.

### 1.3 CPython (default)

- The tool uses the **Python interpreter you run it with** for the `cpython` method and for building/running Cython and ctypes benchmarks. No extra setup beyond a working Python 3.8+.

### 1.4 PyPy (optional, for `pypy` method)

- Install PyPy so that `pypy` or `pypy3` is on your PATH, or set **PGSI_PYPY_PATH** (see Configuration below).
- Download: [PyPy](https://www.pypy.org/download.html).
- Example (Linux):

  ```bash
  # Example: add PyPy to PATH or set in .env
  export PGSI_PYPY_PATH=/path/to/pypy3
  ```

### 1.5 C compiler (for `cython` and `ctypes` methods)

- **Linux / macOS:** Install `gcc` or `clang` (e.g. `sudo apt install build-essential` on Debian/Ubuntu).
- **Windows:** Install Visual Studio Build Tools (for `cl.exe`) or MinGW/MSYS2 (for `gcc`). Ensure the compiler is on PATH or set **PGSI_CC_PATH**.

### 1.6 Optional: Hardware energy measurement (Linux x86_64 only)

- For **hardware** energy measurement (Intel RAPL), install the optional extra on Linux x86_64:

  ```bash
  pip install pgsi-analyzer[energy]
  ```

  This installs `pyRAPL`. You may need to run with elevated permissions or `cap_sys_rawio` (see Hardware Setup below). On Windows and macOS, the tool uses **estimation** instead; no extra install is required.

---

## 2. The Golden Path

These commands are the standard way to run a benchmark suite and interpret results. All examples match the CLI implemented in `cli/main.py`.

### 2.1 List what’s available

```bash
pgsi-analyzer benchmark list
```

Lists all algorithms and all execution methods.

List only algorithms:

```bash
pgsi-analyzer benchmark list --algorithms
```

List only methods:

```bash
pgsi-analyzer benchmark list --methods
```

### 2.2 Run a small test (single algorithm, single method)

```bash
pgsi-analyzer benchmark run --algorithms hanoi --methods cpython --runs 5
```

- Writes output under the default directory **`results/`**.
- You should see phases: Build (if needed), Execute, Aggregate, Combine, Carbon, GreenScore, then a path to `GreenScore.csv`.

### 2.3 Run the “standard” benchmark suite (Golden Path)

```bash
pgsi-analyzer benchmark run --algorithms hanoi binary-trees sieve --methods cpython pypy --runs 10 --output results/
```

- Runs three algorithms × two methods = 6 combinations, 10 runs each.
- Output directory: **`results/`** (or the path you pass to `--output`).

### 2.4 Run full suite (all algorithms, all methods)

```bash
pgsi-analyzer benchmark run --algorithms all --methods all --runs 50 --output results/
```

- **Warning:** This can take hours. Default `--runs` is 50; default `--output` is `results`.

### 2.5 Run count and PGSI_RUNS

- **`--runs`** (e.g. `--runs 10`) sets how many measurement runs the orchestrator requests per benchmark. Default is **50**.
- The **executor** sets **`PGSI_RUNS`** in each benchmark subprocess environment; **PGSI_RUNS** is the **source of truth** for run count inside subprocesses. Benchmark scripts use **get_measurement_runs(algorithm)** from **pgsi_analyzer.config**, which reads **PGSI_RUNS** (with fallback to **DEFAULT_PARAMS**) for `measure_energy_to_csv(n=...)` and `measure_time_to_csv(n=...)`. Implementation is complete. See **audit/spike_4_runs_and_permissions.md** and **audit/architecture.md** (Section 13).

### 2.6 Interpreting GreenScore.csv

After a run, open **`results/GreenScore.csv`** (or your `--output` path). It contains:

- **method** — Execution method (e.g. cpython, pypy).
- **energy_mean**, **time_mean**, **carbon_mean** — Normalized means (0–1 scale) across algorithms.
- **green_score** — Composite: **α·energy + β·carbon + γ·time**. **Lower is better.**

Example:

```bash
cat results/GreenScore.csv
```

Or in Python:

```python
import pandas as pd
df = pd.read_csv('results/GreenScore.csv')
print(df.sort_values('green_score'))
```

The first row is the most sustainable method for your run.

### 2.7 Optional: Custom GreenScore weights and carbon intensity

```bash
pgsi-analyzer benchmark run --algorithms hanoi --methods cpython --runs 5 \
  --alpha 0.5 --beta 0.3 --gamma 0.2 \
  --carbon-intensity 0.0005
```

- **--alpha**, **--beta**, **--gamma**: Weights for energy, carbon, and time (must sum to 1.0). Defaults: 0.4, 0.4, 0.2.
- **--carbon-intensity**: gCO₂e per Joule (default 0.000475).

---

## 3. Hardware Setup (Linux: RAPL for energy measurement)

On **Linux x86_64**, hardware energy measurement uses Intel RAPL via pyRAPL. This often requires **elevated permissions**.

### 3.1 Option A: Run as root

```bash
sudo pgsi-analyzer benchmark run --algorithms hanoi --methods cpython --runs 5
```

### 3.2 Option B: Grant cap_sys_rawio (recommended for development)

Allow the Python binary to read RAPL MSRs without full root:

```bash
# Find your Python path
which python3

# Grant capability (Linux; replace /usr/bin/python3 with your interpreter path)
sudo setcap cap_sys_rawio+ep /usr/bin/python3
```

Then run as your normal user:

```bash
pgsi-analyzer benchmark run --algorithms hanoi --methods cpython --runs 5
```

- If pyRAPL still cannot read RAPL, the tool falls back to **estimation** and will warn that hardware measurement is unavailable (see Troubleshooting below).

### 3.3 Troubleshooting Permissions

On **Linux x86_64**, if the tool cannot access Intel RAPL (e.g. you are not root and have not set `cap_sys_rawio`), it will emit an explicit **UserWarning** stating that RAPL is unavailable due to permission denied and that estimation will be used. The message includes actionable instructions:

- **Grant capability (recommended):**  
  `sudo setcap cap_sys_rawio+ep $(which python3)`  
  (Replace with your interpreter path if needed.)
- **Or run as root:**  
  `sudo pgsi-analyzer benchmark run ...`

The tool does **not** crash: it continues with estimation so that benchmarks still produce results. After a run, check `system_info_pyrapl.json` or the energy CSV: **measurement_method** will be **estimation** if RAPL was blocked. On **Windows** and **macOS**, no permission-specific message is shown (estimation is the normal mode).

### 3.4 Verifying hardware measurement

- After a run, check the energy CSV or `system_info_pyrapl.json` in the energy output folder. If **measurement_method** is **hardware**, RAPL was used. If **estimation**, the tool fell back (e.g. permissions or non-Linux). See **audit/spike_4_runs_and_permissions.md**.

---

## 4. Configuration: ToolPaths (Python, PyPy, C compiler)

The tool needs to find: **Python** (for cpython/cython/ctypes/py_compile), **PyPy** (for pypy), and **C compiler** (for building cython/ctypes). Resolution order (highest priority first):

1. **CLI flags**
2. **Environment variables**
3. **.env file**
4. **Built-in defaults** (PATH lookup)

### 4.1 CLI flags

Override paths directly:

```bash
pgsi-analyzer benchmark run --algorithms hanoi --methods cpython --runs 5 \
  --python-path /usr/bin/python3 \
  --pypy-path /usr/bin/pypy3 \
  --cc-path /usr/bin/gcc
```

- **--python-path** — Python executable for running benchmarks (and builds).
- **--pypy-path** — PyPy executable (required if you use `--methods pypy` and PyPy is not on PATH).
- **--cc-path** — C compiler (gcc or cl.exe).

### 4.2 Environment variables

Set before running (no .env file needed):

- **PGSI_PYTHON_PATH** — Python executable.
- **PGSI_PYPY_PATH** — PyPy executable.
- **PGSI_CC_PATH** — C compiler executable.

Example (Linux/macOS):

```bash
export PGSI_PYPY_PATH=/usr/bin/pypy3
export PGSI_CC_PATH=/usr/bin/gcc
pgsi-analyzer benchmark run --algorithms hanoi --methods pypy --runs 5
```

### 4.3 .env file

Create a **`.env`** in the directory from which you run the tool (or pass it with **--env-file**):

```env
PGSI_PYTHON_PATH=/usr/bin/python3
PGSI_PYPY_PATH=/usr/bin/pypy3
PGSI_CC_PATH=/usr/bin/gcc
```

Then run:

```bash
pgsi-analyzer benchmark run --algorithms hanoi --methods cpython --runs 5
```

If the file is not in the current directory, specify it:

```bash
pgsi-analyzer benchmark run --algorithms hanoi --methods cpython --runs 5 --env-file /path/to/.env
```

### 4.4 Defaults

- **Python:** `sys.executable` (the interpreter running `pgsi-analyzer`).
- **PyPy:** Lookup on PATH for `pypy3`, `pypy`, `pypy3.11`, etc.
- **C compiler:** On Windows, `cl.exe` then `gcc`; on Linux/macOS, `gcc` then `cc`.

---

## 5. Output layout (reference)

After a run, the output directory (e.g. `results/`) typically contains:

- **energy_benchmark/** — Raw energy CSVs from decorators.
- **time_benchmark/** — Raw time CSVs.
- **\<method\>/** (e.g. **cpython/**, **pypy/**) — **energy_aggregated.csv**, **time_aggregated.csv** per method.
- **energy_combined.csv** — Energy per algorithm × method.
- **time_combined.csv** — Time per algorithm × method.
- **carbon_footprint.csv** — Carbon per algorithm × method.
- **GreenScore.csv** — Final ranking (method, energy_mean, time_mean, carbon_mean, green_score).

For more detail on the pipeline and contracts, see **audit/architecture.md** and **audit/functional_overview.md**.
