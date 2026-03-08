# PGSI Analyzer — Next Steps Roadmap (Cursor-Ready Issues)

**Document version:** 1.0  
**Purpose:** Sequential, executable development tasks derived from the audit. Each issue follows the same template (Goal, Context, Tasks, Acceptance Criteria, Testing/Documentation where applicable) and can be used as a Cursor issue or sprint item.

---

## Issue Template (Reference)

Each roadmap issue below is structured as:

- **Goal** — One-sentence objective.
- **Context** — Why this is needed (audit finding or user need).
- **Tasks** — Ordered, actionable steps.
- **Acceptance Criteria** — How to verify completion.
- **Testing Requirements** — What to test (if any).
- **Documentation Requirements** — What to update (if any).

---

## Issue A (Fix): Implement Deterministic Run Control via PGSI_RUNS

**Type:** Fix  
**Source:** Spike #4 (audit/spike_4_runs_and_permissions.md), Technical Debt (Medium), Final Summary §3.2

### Goal

Ensure the **--runs** CLI flag actually controls how many times each benchmark runs inside its subprocess, by passing the run count via the **PGSI_RUNS** environment variable and using it in benchmark scripts.

### Context

The orchestrator passes `runs` to **execute_benchmark**, but the executor does not pass this value into the benchmark subprocess. Benchmark scripts use **DEFAULT_PARAMS** (or similar) at import time for the measurement decorator `n`, so `pgsi-analyzer benchmark run --runs 5` does not result in 5 iterations per script. This is confusing and non-deterministic. Spike #4 decided to use an environment variable **PGSI_RUNS** (not argv). This issue implements that design.

### Tasks

1. **Modify executor.py:** In **execute_benchmark**, after building `exec_env` (copy of `os.environ` and any caller-provided `env`), set **exec_env["PGSI_RUNS"] = str(runs)** before calling **subprocess.run**. Ensure this applies to all code paths that launch the benchmark process (cpython, pypy, cython, ctypes, py_compile).
2. **Create a run-count helper:** In **config.py** (or a small shared module used by benchmarks), add a function, e.g. **get_measurement_runs(algorithm: str) -> int**, that returns **int(os.environ.get("PGSI_RUNS", default))** where **default** is **DEFAULT_PARAMS[algorithm]["test_n"]** if DEFAULT_PARAMS exists for that algorithm, else a constant (e.g. 50). If **DEFAULT_PARAMS** is not yet defined in config, use a module-level fallback (e.g. 50) until it is.
3. **Update benchmark scripts to use the helper:** In each benchmark **main.py** that uses **measure_energy_to_csv(n=...)** and **measure_time_to_csv(n=...)**, replace the `n` argument with the value returned by the new helper (e.g. **get_measurement_runs("algorithm-name")**). Prefer a single place (e.g. one line per algorithm) so adding new algorithms stays simple. If there are many scripts, update at least the representative set (e.g. hanoi, binary-trees, sieve) and document the pattern for the rest.
4. **Document:** In **audit/usage_guide.md** (and README if needed), state that **PGSI_RUNS** is set by the executor and is the source of truth for run count inside subprocesses. Optionally add a short note in **config.py** docstring for the helper.

### Acceptance Criteria

- Running **pgsi-analyzer benchmark run --algorithms hanoi --methods cpython --runs 5** results in **exactly 5** energy and 5 time iterations per benchmark script (observable via CSV row count or decorator behavior).
- The executor sets **PGSI_RUNS** in the subprocess environment for every benchmark invocation.
- Benchmark scripts that were updated use the new helper for decorator `n`; remaining scripts are either updated or documented as follow-up.

### Testing Requirements

- **Unit test:** In **tests/test_benchmark_executor.py**, add a test that mocks **subprocess.run** and asserts that the call’s **env** argument contains **PGSI_RUNS** with the value of the **runs** parameter passed to **execute_benchmark** (e.g. **runs=7** → **env["PGSI_RUNS"] == "7"**).
- **Integration (optional):** Run one benchmark (e.g. hanoi/cpython) with **--runs 3** and confirm the raw energy and time CSVs have exactly 3 data rows each.

### Documentation Requirements

- **audit/usage_guide.md:** Run count section already references PGSI_RUNS; update to state that PGSI_RUNS is **set by the executor** and is the **source of truth** for subprocess run count (implementation complete).
- **audit/architecture.md:** Section 13.1 already describes the design; add a one-line note that implementation is in place (or leave as-is if the doc is design-only).

---

## Issue B (UX): Implement Permission-Aware RAPL Warnings

**Type:** UX / Observability  
**Source:** Spike #4, Technical Debt (silent fallback), Final Summary §2

### Goal

Stop the **silent fallback** to estimation when RAPL is unavailable on Linux due to permissions. Users should see a **clear warning** with actionable instructions (e.g. setcap or run as root) instead of only the generic “estimation will be used” message.

### Context

On Linux x86_64, hardware energy measurement uses pyRAPL (Intel RAPL). If the process lacks permission to read RAPL MSRs (e.g. non-root without cap_sys_rawio), pyRAPL can raise **OSError** or **RuntimeError** at import/setup. The code catches these and sets **\_pyrapl_available = False**, and later the decorator uses estimation and emits a generic UserWarning. The user does not know that the failure was due to **permissions** and may miss that they could enable hardware measurement with **setcap cap_sys_rawio+ep** or by running as root. This issue improves feedback without changing the fallback behavior (estimation remains the fallback).

### Tasks

1. **Update measurement/energy.py:** In the existing **except (ImportError, OSError, RuntimeError)** block where pyRAPL is imported and setup is called, after setting **\_pyrapl_available = False** and **pyRAPL = None**, emit a **warnings.warn**:
   - Message must state that **hardware energy measurement (RAPL) is unavailable** and that **estimation will be used**.
   - If the exception is or resembles a **permission error** (e.g. **OSError** with **errno 13** (Permission denied), or exception message containing “permission” / “Permission” / “denied”), append to the message: **“This may be due to insufficient permissions. On Linux, RAPL typically requires root or the cap_sys_rawio capability (e.g. setcap cap_sys_rawio+ep <path_to_python>).”**
   - Use a dedicated **UserWarning** (or existing one) so it can be filtered if needed.
2. **Optional:** Add **platform/hardware.py::warn_if_rapl_unavailable()** (or similar) that, when on Linux x86_64 and pyRAPL is installed, attempts a minimal RAPL read (e.g. pyRAPL.setup() or one Measurement). On failure, call **warnings.warn** with the same message as above. Call this from **measurement/energy.py** when setup fails so the warning is centralized and testable. If time-constrained, the inline warn in the except block is sufficient.
3. **Document:** In **audit/usage_guide.md** (Hardware Setup), the setcap and root instructions are already present; add a sentence that if RAPL is still unavailable, the tool will warn with permission suggestions and use estimation.

### Acceptance Criteria

- On **Linux**, when a **non-root** user runs the tool **without** cap_sys_rawio (and RAPL would fail), they see a **clear UserWarning** that:
  - States RAPL is unavailable and estimation will be used.
  - Includes **actionable instructions** (e.g. setcap command or run as root).
- The fallback behavior is **unchanged**: no exception is raised; estimation is used when RAPL is unavailable.
- On Windows/macOS, behavior is unchanged (no new errors; existing estimation warning may still appear).

### Testing Requirements

- **Unit test:** In **tests/test_measurement.py** or **tests/test_energy_crossplatform.py**, add a test that, on a Linux x86_64 build (or with platform mocked as Linux), mocks pyRAPL setup to raise **OSError(13, "Permission denied")** (or similar), then triggers the code path that catches it. Assert that **warnings.warn** was called with a message containing “permission” (or “cap_sys_rawio” / “root”).
- **Manual (optional):** On a Linux machine, run as non-root without setcap and confirm the new warning appears; then run with setcap or root and confirm hardware measurement is used and the permission warning does not appear.

### Documentation Requirements

- **audit/usage_guide.md:** Hardware Setup section updated to mention that a permission-related warning will appear when RAPL is denied and estimation is used.
- **audit/architecture.md** and **audit/spike_4_runs_and_permissions.md:** Already describe the strategy; add a one-line note that implementation is done (optional).

---

## Issue C (Refactor): Decompose the Orchestrator into PipelineManager and FileSystemProvider

**Type:** Refactor  
**Source:** God-file analysis (audit/architecture.md §10.1), Technical Debt (High), Final Summary §3.1

### Goal

Separate **pipeline orchestration** (what runs when) from **filesystem and I/O** (where files live, how they are collected and copied). This reduces the “god file” nature of **orchestrator.py** and makes phases easier to test and extend.

### Context

**run_benchmark_suite** in **orchestrator.py** is a long function that both coordinates the seven-phase pipeline and implements path collection, temp dir creation, shutil.copy2, and output layout. Mixing these concerns makes it harder to unit-test phases in isolation and to change output structure or add phases. The audit recommends extracting a **FileSystemProvider** (or equivalent) that owns: (1) collecting CSV paths from execution results and grouping by method, (2) creating temp dirs and copying CSVs for aggregation, (3) defining the output directory layout (e.g. **output_dir / method / energy_aggregated.csv**). The orchestrator would then call into this provider and into the existing model functions (aggregate_energy, aggregate_time, combine_*, calculate_carbon_footprint, calculate_greenscore) so that **run_benchmark_suite** becomes a thin coordinator.

### Tasks

1. **Define the I/O abstraction:** Create a class or module, e.g. **FileSystemProvider** (or **ResultsCollector**), in **benchmark/** that is responsible for:
   - **collect_csv_paths_by_method(execution_results)** — Given the dict of algorithm → method → { energy_csv, time_csv }, return a structure that groups energy (and time) CSV paths by method (e.g. **Dict[str, List[Path]]** for energy and for time).
   - **prepare_aggregation_dirs(output_dir, method, list_of_csv_paths)** — Create a temp directory (or a method-specific dir under output_dir), copy the given CSVs into it, and return the path to that directory (for use by aggregate_energy / aggregate_time).
   - **aggregated_paths(output_dir, method)** — Return the paths where aggregated energy and time files should be written (e.g. **output_dir / method / "energy_aggregated.csv"** and **output_dir / method / "time_aggregated.csv"**), so the orchestrator knows where to pass **output_path** to aggregate_* and where to find files for combine_*.
   Ensure the contract matches current orchestrator behavior (method name = parent dir name for combination).
2. **Refactor orchestrator.py:** In **run_benchmark_suite**, replace the inline logic for “Phase 3: Collect and organize raw CSVs” and “Phase 4: Aggregating results per method” (path collection, temp dirs, copying) with calls to the new provider. Keep phase order and print statements; only the implementation of path/dir handling moves. The orchestrator should not construct **method_energy_dirs** / **method_time_dirs** or call **shutil.copy2** directly; it should call the provider and then call **aggregate_energy** / **aggregate_time** with the paths returned by the provider.
3. **Preserve behavior:** Run the full pipeline (e.g. **pgsi-analyzer benchmark run --algorithms hanoi sieve --methods cpython --runs 2**) and compare output layout and **GreenScore.csv** with the pre-refactor version (or with existing tests). Existing orchestrator tests (mocked) should still pass; update mocks if the orchestrator’s call surface changes (e.g. it now takes a provider instance or uses a default one).
4. **Optional naming:** If the team prefers “PipelineManager” as the thin coordinator, rename or split so that **run_benchmark_suite** lives in a small **PipelineManager** and the new class is **FileSystemProvider** or **ResultsCollector**. The important part is the separation of concerns, not the exact class name.

### Acceptance Criteria

- **run_benchmark_suite** is shorter and does not contain direct filesystem logic (no shutil.copy2, no manual construction of method_energy_dirs / method_time_dirs). It delegates path and dir operations to the new provider.
- The new provider (or module) owns: collecting CSV paths by method, preparing aggregation input dirs (copying), and returning paths for aggregated and combined files.
- All existing **tests** for the orchestrator (e.g. **test_benchmark_orchestrator.py**) still pass. No regression in pipeline output (same **GreenScore.csv** and layout for the same inputs).
- **audit/architecture.md** (God-file section) is updated to state that the orchestrator has been refactored and to point to the new provider for I/O details.

### Testing Requirements

- **Existing tests:** **pytest tests/test_benchmark_orchestrator.py** must pass. Adjust mocks if the orchestrator now uses a provider (e.g. inject a mock provider or use the real one with a temp dir).
- **Optional:** Add a unit test for the new provider: given a fake **execution_results**, assert that **collect_csv_paths_by_method** returns the expected grouping; given **prepare_aggregation_dirs**, assert that the directory exists and contains the expected copied files.

### Documentation Requirements

- **audit/architecture.md:** Update §10.1 (orchestrator) to state that pipeline coordination is separated from I/O and that a **FileSystemProvider** (or equivalent) handles path collection and aggregation dir preparation. Update the Mermaid diagram if needed to show the provider.
- **audit/final_summary.md:** In §3.1 (Technical Debt), mark the orchestrator refactor as **addressed** and reference Issue C.

---

## Execution Order

Recommended order:

1. **Issue A** — Deterministic run control. Small, high user impact, unblocks clear reproduction.
2. **Issue B** — RAPL permission warnings. Improves UX on Linux without changing behavior.
3. **Issue C** — Orchestrator decomposition. Larger refactor; do after A and B so that run control and warnings are stable.

Low-priority coverage work (config.py, utils/validation.py) can be scheduled after A–C or in parallel as time allows.
