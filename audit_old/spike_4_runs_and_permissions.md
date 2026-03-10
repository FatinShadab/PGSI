# Spike #4: Deterministic Run Control & Permission Awareness

**Document version:** 1.0  
**Purpose:** Resolve architectural gaps from Issue #2 Spike Rule: (1) pass `--runs` to benchmark subprocesses, (2) improve user feedback when RAPL is inaccessible (Issue #4).

---

## 1. Investigation: Passing `--runs` to Subprocesses

### 1.1 Options

| Option | Pros | Cons |
|--------|------|------|
| **Environment variable (e.g. PGSI_RUNS)** | No change to benchmark script CLI surface; scripts already import from pgsi_analyzer.config; one place to read (os.environ in config or at decorator call site). | Requires all benchmark scripts to read env in the right place (e.g. when building decorator `n`). |
| **CLI argument (e.g. python main.py --runs 50)** | Explicit, easy to debug. | Every benchmark main.py must parse argv; current scripts have no argparse. |
| **Config file (e.g. DEFAULT_PARAMS override)** | Centralized. | Same as env: benchmarks must read it; already have DEFAULT_PARAMS from config. |

### 1.2 Recommendation: **Environment variable PGSI_RUNS**

- **Rationale:**  
  - Executor already sets **PYTHONPATH** in the subprocess env; adding **PGSI_RUNS** is consistent and requires no change to how the process is invoked (no argv parsing in 65+ benchmark scripts).  
  - Benchmark scripts already use **DEFAULT_PARAMS** from `pgsi_analyzer.config`. The config module (or a small helper) can resolve run count as: **int(os.environ.get("PGSI_RUNS", DEFAULT_PARAMS[algo]["test_n"]))** (or similar key).  
  - Single contract: if **PGSI_RUNS** is set in the subprocess environment, use it; otherwise fall back to DEFAULT_PARAMS.  
- **Alternative (argv):** Would require adding argparse (or sys.argv parsing) to every benchmark `if __name__ == "__main__"` and passing `--runs` from the executor. More invasive and error-prone across many files.

**Decision:** Use **PGSI_RUNS** environment variable. Executor sets it in `exec_env` before `subprocess.run`. Benchmark scripts (or the decorator/config they use) read it when determining `n` for the measurement decorators.

---

## 2. Investigation: pyRAPL Under Non-Root and Silent Fallback

### 2.1 Current Behavior (measurement/energy.py)

- At **import time**, if `is_linux_intel()` is True, the module runs:
  - `import pyRAPL` then `pyRAPL.setup()`.
  - On **ImportError, OSError, RuntimeError** it sets `_pyrapl_available = False` and `pyRAPL = None`. No message is printed; later, when the decorator runs, it sees `_pyrapl_available` False and uses estimation, and a **UserWarning** is emitted that hardware is not available and estimation is used.
- So the fallback is **not silent** at first use of the decorator (there is a warning), but:
  - The **reason** for unavailability (e.g. permission denied for RAPL MSRs) is not distinguished from “not Linux” or “pyRAPL not installed”.
  - The warning happens at **decorator execution** time, not at import; if no benchmark is run, the user never sees it.

### 2.2 Desired Behavior

- When on Linux/Intel and pyRAPL is **installed** but **fails at setup** (e.g. permission denied): emit a **clear warning** that RAPL is unavailable due to permissions (or similar) and that estimation will be used; optionally suggest running with appropriate capabilities or root.
- When on Linux/Intel and pyRAPL is **not installed**: keep current behavior (estimation + generic “hardware not available” warning).
- Do not change the decision to fall back to estimation (no raise); only improve the message.

### 2.3 Strategy for Improving User Feedback

1. **Catch and classify at import/setup:** In `measurement/energy.py`, in the `except (ImportError, OSError, RuntimeError)` block, optionally inspect the exception (e.g. errno or message) to distinguish “permission denied” from “module not found”.  
2. **Emit a warning at setup time:** When setup fails, issue a **warnings.warn** with a message that:
   - States that hardware energy measurement (RAPL) is unavailable.
   - If the exception looks like a permission error (e.g. OSError errno 13, or message containing “permission”/“Permission”), add: “This may be due to insufficient permissions (try running with cap_sys_rawio or as root for RAPL).”
   - States that estimation will be used instead.
3. **Optional: Permission-check utility in platform/hardware.py:** Add a function, e.g. **check_rapl_readable()** or **warn_if_rapl_unavailable()**, that:
   - Returns True if we are not on Linux/Intel (no check needed), or if pyRAPL is not installed (no check), or if we can successfully read RAPL (e.g. try a minimal pyRAPL.Measurement or a known RAPL read).
   - Returns False (and optionally warns) if on Linux/Intel, pyRAPL is installed, but read fails (e.g. permission).  
   This can be called from the energy module at setup time to issue a single, clear warning instead of a generic one.

**Documented strategy:**  
- Prefer **improving the exception handling in measurement/energy.py** at the existing `except (ImportError, OSError, RuntimeError)` block: log or warn with a message that distinguishes permission-denied from other failures and suggests cap_sys_rawio/root.  
- Optionally add **platform/hardware.py::warn_if_rapl_unavailable()** (or similar) that attempts a minimal RAPL read and warns with the same message if it fails on Linux/Intel, so that the “permission” case is explicit and testable.

---

## 3. Draft Implementation Plan

### 3.1 Executor: Pass Runs to Benchmark Scripts

- In **benchmark/executor.py**, in **execute_benchmark**, after building `exec_env = os.environ.copy()` and updating with `env` if provided:
  - Set **exec_env["PGSI_RUNS"] = str(runs)** (use the `runs` argument passed to execute_benchmark).
- No change to `exec_args` (still `[python_exe, main_py_path]`).
- **Benchmark scripts / config:**  
  - In **config.py** (or a shared helper used by benchmarks): provide a helper that returns the run count for the current process, e.g. **get_measurement_runs(algorithm: str) -> int**, which does:
    - `return int(os.environ.get("PGSI_RUNS", DEFAULT_PARAMS[algorithm]["test_n"]))` (or equivalent key).
  - Each benchmark script that currently uses **DEFAULT_PARAMS[algo]["test_n"]** (or similar) for the decorator `n` should switch to this helper so that when the orchestrator sets PGSI_RUNS, the subprocess uses it.  
  - If DEFAULT_PARAMS is not yet defined in config, the helper can fall back to a constant (e.g. 50) until DEFAULT_PARAMS exists.

### 3.2 Permission Check / RAPL Feedback (platform/hardware.py)

- Add a function, e.g. **warn_if_rapl_unavailable()**, that:
  - If not Linux or not x86_64: return without warning.
  - If pyRAPL is not installed: return without warning (or a single “estimation will be used” if desired).
  - If pyRAPL is installed: try a minimal RAPL operation (e.g. `pyRAPL.setup()` and/or a one-shot Measurement). On exception (OSError, RuntimeError), issue **warnings.warn** with a message that:
    - RAPL hardware measurement is unavailable.
    - If the exception suggests permission denied: “This may be due to insufficient permissions. On Linux, RAPL may require root or cap_sys_rawio.”
    - Estimation will be used instead.
- Call this from **measurement/energy.py** inside the `if is_linux_intel(): try: ... except ...` block when setup fails (and optionally at the start of the decorator’s first use), so that the user sees the improved message instead of a silent fallback.

---

## 4. Testing Requirements (Spike)

- **Runs:** Unit test that executor, when called with `runs=42`, passes `PGSI_RUNS=42` in the environment of the subprocess (mock subprocess.run and assert on `env`).
- **Manual/simulated pyRAPL on Linux:** On a Linux machine (or container), run without root and without cap_sys_rawio; confirm that either pyRAPL fails at setup or at first use, and that the new warning appears with the permission hint. With root or cap_sys_rawio, confirm that hardware measurement is used and no permission warning is shown. Document result in this spike or in testing_and_health.md.

---

## 5. Summary of Decisions

| Topic | Decision |
|-------|----------|
| **How to pass runs to subprocesses** | **Environment variable PGSI_RUNS.** Executor sets it; benchmarks (or config helper) read it and use it for decorator `n` when present. |
| **RAPL permission feedback** | Improve the existing `except` block in measurement/energy.py to warn with a message that distinguishes permission-denied and suggests cap_sys_rawio/root. Optionally add **warn_if_rapl_unavailable()** in platform/hardware.py and call it when RAPL setup fails. |

These decisions are reflected in **architecture.md** (Section 13) as the finalized design for the spike.
