# End-to-End Guide: Create, Register, and Run a Custom Benchmark

This guide shows the full developer workflow for adding a new benchmark outside
the `pgsi-analyzer` package source and running analysis end-to-end.

---

## 1) Prerequisites

- Python 3.8+
- `pgsi-analyzer` installed in your environment

Install:

```bash
pip install pgsi-analyzer
```

First-run shortcut:

```bash
pgsi-analyzer
```

Running `pgsi-analyzer` with no command now bootstraps a default project at
`./benchmarks` (if it does not already exist).

It also prints next-step commands so you can immediately create a benchmark and run it.

---

## 2) Create a Benchmark Project Folder

You can scaffold a full project (Django-like style):

```bash
pgsi-analyzer startproject my-benchmarks --algorithms hanoi
```

This copies the **pre-implemented benchmark source code** from PGSI built-ins
into your project folder for the selected algorithms/methods.

Optional: scaffold all built-in algorithm folders:

```bash
pgsi-analyzer startproject my-benchmarks --algorithms all
```

Use this when you want ready-to-run code that you can modify.

---

## 3) Create a New Custom Benchmark and Auto-Register It

From your project root, create a single new benchmark:

```bash
pgsi-analyzer create benchmark --name A1 --benchmarks-dir ./my-benchmarks
```

What this does:

1. Creates:
   - `./my-benchmarks/A1/cpython/main.py`
   - `./my-benchmarks/A1/pypy/main.py`
   - `./my-benchmarks/A1/py_compile/main.py`
   - `./my-benchmarks/A1/cython/main.py`, `raw.pyx`, `setup.py`
   - `./my-benchmarks/A1/ctypes/main.py`, `raw.c`
2. Updates:
   - `./my-benchmarks/pgsi_registry.json`

That registry file is used for user benchmark discovery and registration.

---

## 4) Implement Your Workload

Open generated files and replace `run_workload()` with your actual algorithm logic.

Keep these decorators (required):

- `@measure_energy_to_csv(...)`
- `@measure_time_to_csv(...)`

The generated templates already include correct defaults like:

- `csv_filename="A1_cpython"` (or other method suffixes)
- `n=get_measurement_runs("A1")`

For `cython` and `ctypes` methods:

- move heavy code into `raw.pyx` / `raw.c`
- call those from `main.py`

---

## 5) Verify Benchmark Discovery

### Option A: Explicit path

```bash
pgsi-analyzer benchmark list --algorithms --benchmarks-dir ./my-benchmarks
```

You should see `A1` in the list.

### Option B: Auto-detect mode

If your current working directory contains `./benchmarks/pgsi_registry.json`,
you can omit `--benchmarks-dir`:

```bash
pgsi-analyzer benchmark list --algorithms
```

Note: auto-detect checks only `./benchmarks/pgsi_registry.json`.

Registry behavior detail:

- PGSI first discovers folders from `<benchmarks_dir>/<algorithm>/<method>/...`
- Then, if present, it loads `<benchmarks_dir>/pgsi_registry.json`
- Entries from `pgsi_registry.json` override discovered paths for the same benchmark name

This lets you keep explicit path mappings when needed.

---

## 6) Run Analysis for Your New Benchmark

Run one method:

```bash
pgsi-analyzer benchmark run \
  --algorithms A1 \
  --methods cpython \
  --runs 5 \
  --benchmarks-dir ./my-benchmarks
```

Run all methods:

```bash
pgsi-analyzer benchmark run \
  --algorithms A1 \
  --methods all \
  --runs 5 \
  --benchmarks-dir ./my-benchmarks
```

Run multiple custom benchmarks:

```bash
pgsi-analyzer benchmark run \
  --algorithms A1 A2 \
  --methods all \
  --runs 10 \
  --benchmarks-dir ./my-benchmarks
```

---

## 7) Understand Outputs

After a run, results are written to your output directory (`results/` by default):

- per-method aggregated files:
  - `results/cpython/energy_aggregated.csv`
  - `results/cpython/time_aggregated.csv`
- combined files:
  - `results/energy_combined.csv`
  - `results/time_combined.csv`
- environmental metrics:
  - `results/carbon_footprint.csv`
- final ranking:
  - `results/GreenScore.csv`

Lower GreenScore is better.

---

## 8) Common Commands Cheat Sheet

Create benchmark:

```bash
pgsi-analyzer create benchmark --name A1 --benchmarks-dir ./my-benchmarks
```

List benchmarks:

```bash
pgsi-analyzer benchmark list --algorithms --benchmarks-dir ./my-benchmarks
```

Run benchmark:

```bash
pgsi-analyzer benchmark run --algorithms A1 --methods cpython --runs 5 --benchmarks-dir ./my-benchmarks
```

Bootstrap default project in current directory:

```bash
pgsi-analyzer
```

---

## 9) Troubleshooting

### Benchmark name rejected

Use names with letters, numbers, `_`, `-` only.

Valid examples:

- `A1`
- `my_algo`
- `my-benchmark`

Invalid examples:

- `A*`
- `my algo`
- `algo!`

### Benchmark not listed

Check:

1. Folder exists: `./my-benchmarks/<name>/<method>/main.py`
2. `pgsi_registry.json` includes your benchmark entry
3. You passed correct `--benchmarks-dir` (or used auto-detect conditions)

### Cython/ctypes method fails

Check compiler/toolchain setup and dependencies, then retry with only `cpython` first:

```bash
pgsi-analyzer benchmark run --algorithms A1 --methods cpython --runs 3 --benchmarks-dir ./my-benchmarks
```

Once CPython works, enable other methods progressively.
