# Validation: LaTeX §PGSI Architecture and Implementation

This document validates the paper section **“PGSI Architecture and Implementation”** against the `pgsi-analyzer` codebase (`src/pgsi_analyzer/`) and internal architecture documentation (`docs/architecture/README.md`). Citations refer to paths relative to the repository root.

**Overall verdict:** The section is **largely accurate** as a high-level description of PGSI. A few claims need **precision** (hardware path, GreenScore normalization detail, carbon units, CI), and one tuple notation is **conceptual** rather than implemented as a formal type.

---

## 1. Design Goals and Architectural Principles

| Claim | Status | Notes |
|--------|--------|--------|
| Production-grade evolution of GreenScore research prototype | Narrative | Not contradicted by code; not empirically verifiable from source alone. |
| Reproducibility: deterministic multi-run, audit trails, methodology labeling | **Mostly valid** | `PGSI_RUNS` is set by the executor for subprocesses (`benchmark/executor.py`); algorithm/method resolution uses sorted, deterministic lists (`orchestrator.py` `resolve_algorithms` / `resolve_methods`). Audit: `.audit.log`, `audit_report.json`, methodology columns in CSVs. “Deterministic” applies to **ordering and configured run counts**, not bitwise-identical results across machines. |
| Cross-platform; no privileged hardware counters required | **Valid with nuance** | On **Linux Intel x86_64**, pyRAPL can be used when available; on Windows, macOS, or when RAPL is unavailable, **estimation** is used (`measurement/energy.py`). Users do not *have* to use RAPL; estimation works without special privileges. |
| Separation of concerns | **Valid** | CLI → orchestrator → executor/builder → models; models do not import benchmark execution (`docs/architecture/README.md` import graph). |
| Extensibility | **Valid** | Registry-based benchmarks (`benchmarks/registry.py`); build/execute separated from aggregation/scoring. |
| Python package, PyPI distribution | **Valid** | `pyproject.toml`: `name = "pgsi-analyzer"`, `[project.scripts]` entry `pgsi-analyzer`. |

**Suggested tightening for the paper:** State explicitly that **hardware measurement targets Linux on Intel x86_64 with pyRAPL**, not merely “Linux with RAPL,” and that **AMD or non-RAPL Linux** uses the same estimation path as other fallback cases.

---

## 2. High-Level System Architecture

| Claim | Status | Notes |
|--------|--------|--------|
| Pipeline-oriented architecture, central orchestrator | **Valid** | `benchmark/orchestrator.py` `run_benchmark_suite`. |
| Four layers: CLI, Orchestrator, Measurement & data processing, Metric & scoring | **Acceptable abstraction** | The codebase also separates **filesystem/path I/O** (`benchmark/provider.py`, `results_collector.py`) and **builder/executor** inside “orchestration.” The four-layer picture is consistent with the docs if “orchestrator” is read as the whole benchmark subsystem. |
| Well-defined contracts: CSV IRs and DataFrames | **Valid** | Pipeline reads/writes CSVs; pandas in models (`models/*.py`). |
| Figure placeholder | N/A | No diagram file in-repo; placeholder is fine. |

---

## 3. Execution Environment Orchestrator

| Claim | Status | Notes |
|--------|--------|--------|
| Seven phases: Build → Execute → Result Collection → Aggregation → Combination → Carbon → GreenScore | **Valid** | Matches `run_benchmark_suite`: Phase 1 build (`requires_build` / `build_benchmark`), Phase 2 execute (`execute_benchmark`), then `audit_report.json`, Phase 3 `ResultsCollector.collect_paths`, Phases 4–7 as stated (`orchestrator.py` lines 184–344). |
| Environments as ⟨P, M, H⟩ (Python release, method, hardware/OS) | **Conceptual only** | The code uses `ToolPaths` (python, pypy, c_compiler), registry **method** keys, and **runtime** platform detection (`platform/detection.py`, `hardware.py`). There is **no** single tuple type ⟨P, M, H⟩; this is reasonable **paper notation** if labeled as a conceptual model. |
| Multi-run via environment configuration | **Valid** | `PGSI_RUNS` in subprocess env (`executor.py`). |
| Subprocess isolation | **Valid** | `subprocess.run` per benchmark with dedicated `exec_env` (`executor.py`). |
| Logging tool paths and runtime identity | **Valid** | `AuditLogger`, path identity checks, `audit_report.json`. |
| Graceful degradation on build/execution failure | **Valid** | try/except with continue in build and execute loops (`orchestrator.py`). |
| Execution layer separate from metric computation | **Valid** | Models only consume CSV/DataFrame inputs. |

---

## 4. Measurement and Carbon Estimation Layer

### Energy measurement strategy

| Claim | Status | Notes |
|--------|--------|--------|
| Linux x86_64 + RAPL → package energy via hardware counters | **Refine** | Implementation requires **`is_linux_intel()`** and successful **pyRAPL** setup (`measurement/energy.py`). Not all Linux x86_64 CPUs expose RAPL the same way; **non-Intel Linux** uses estimation. |
| Windows, macOS, restricted Linux → time-based TDP estimation | **Valid** | Estimation in `measurement/estimators.py`; tags `estimated_cpu_tdp`, `estimated_fallback_generic`. |
| Methodology label on each measurement | **Valid** | CSV columns `measurement_method` and `methodology`; hardware tag `hardware_rapl_linux` (`measurement/energy.py`, `models/greenscore.py` `METHODOLOGY_MEASURED`). |
| CSV: timestamp, run index, package energy, optional DRAM, methodology | **Valid** | Headers include `timestamp`, `run`, `package (uJ)`, `dram (uJ)`, `measurement_method`, `methodology` (`measurement/energy.py`). |

### Carbon modeling

| Claim | Status | Notes |
|--------|--------|--------|
| CO₂ = E × CI | **Valid with units** | In code: carbon [gCO₂e] = energy [μJ] × 10⁻⁶ × `carbon_intensity` [gCO₂e/J] (`models/carbon.py`). In prose, **E should be energy in joules** when paired with CI in gCO₂e/J. |
| Decoupled from measurement; configurable intensity | **Valid** | `calculate_carbon_footprint(..., carbon_intensity=...)`; default `0.000475` gCO₂e/J. |

---

## 5. Data Processing Pipeline

| Stage | Status | Notes |
|--------|--------|--------|
| Aggregation: average multi-run energy and time per method | **Valid** | `models/aggregation.py` averages across runs; methodology preserved for energy. |
| Combination: align across execution environments | **Valid** | `combine_energy_results`, `combine_time_results` (`models/combination.py`). |
| Carbon derivation | **Valid** | `calculate_carbon_footprint`. |
| Normalization and weighted GreenScore | **Valid** | See next section for formula detail. |
| Analytical layer independent of execution | **Valid** | Same as above. |

---

## 6. GreenScore Computation and Methodology Awareness

| Claim | Status | Notes |
|--------|--------|--------|
| S = αE′ + βC′ + γT′ | **Valid** | `calculate_greenscore`: `green_score = alpha * energy_mean + beta * carbon_mean + gamma * time_mean` (`models/greenscore.py`). Default weights 0.4, 0.4, 0.2. Weights must sum to 1.0. |
| E′, C′, T′ as normalized metrics | **Refine** | Implementation: **row-wise min–max normalization per algorithm** for each of energy, time, and carbon DataFrames (`normalize_metrics`), then **per method** the code takes the **mean across algorithms** of those normalized values (`energy_mean`, `time_mean`, `carbon_mean`). So E′ is best described as **mean over benchmarks of row-normalized energy**, not a single normalized scalar per run. |
| Counts of hardware vs estimated points | **Valid** | `points_measured` / `points_estimated` from aggregated energy CSVs; measured iff `methodology == "hardware_rapl_linux"`. |
| Data-source consistency | **Valid** | `data_source_consistency`: `"Inconsistent Data Source"` if both measured and estimated counts &gt; 0 (`greenscore.py`). |
| Normalization bounds | **Partially valid** | **Min/max bounds** are written to **`audit_report.json`** under `normalization_bounds` (orchestrator after Phase 7), not as columns inside `GreenScore.csv`. The paper should say **audit report** (or “audit artifact”) for normalization bounds if that is what you cite. |

---

## 7. Registry-Based Extensibility

| Claim | Status | Notes |
|--------|--------|--------|
| Registry for workloads and methods | **Valid** | `benchmarks/registry.py`: `BENCHMARKS`, `VALID_METHODS`, `get_benchmark_path`, etc. |
| New workload: entry point + registry | **Valid** | Documented in `docs/architecture/README.md` §10. |
| New execution method: path + optional build | **Valid** | `requires_build` / `builder.py`; add paths and `VALID_METHODS`. |
| Extensions do not require metric engine changes | **Valid** | For typical additions. |

---

## 8. Packaging, CI, and Artifact Stability

| Claim | Status | Notes |
|--------|--------|--------|
| PyPI-oriented packaging; dependencies; CLI entry points | **Valid** | `pyproject.toml`. |
| Automated testing across multiple OSes via multi-platform CI | **Not supported by this repository** | **No** `.github/workflows` (or other CI config) was found in the workspace. Tests exist under `tests/` (e.g. `pytest`), but **claiming a multi-platform CI pipeline** should be **removed, qualified** (“tests can be run locally on multiple platforms”), or **supported by a citation** to an external CI setup not present here. |
| Explicit dependency management, reproducible install | **Valid** | `pyproject.toml` dependencies and optional extras (`energy`, `analysis`, `pypy`). |

---

## Recommended wording (copy-ready) for corrections

Use these fragments to align the paper with the implementation without changing the overall story.

**Hardware path (replace vague “Linux x86_64 + RAPL”):**

> On **Linux x86_64 with Intel processors**, PGSI uses **pyRAPL** for package (and optional DRAM) energy when initialization succeeds; the methodology tag is `hardware_rapl_linux`. On other platforms, on Linux without Intel/RAPL access, or when pyRAPL fails (including permission errors), energy is **estimated** from execution time and CPU TDP models, with explicit methodology tags (e.g. `estimated_cpu_tdp`).

**Carbon (units):**

> With energy \(E\) in **joules** and carbon intensity \(CI\) in **gCO₂e per joule**, \( \mathrm{CO_2\text{-}e} = E \cdot CI \). The implementation stores energy in **microjoules** in combined CSVs and converts to joules before applying \(CI\) (`models/carbon.py`).

**GreenScore (normalization):**

> For each metric (energy, time, carbon), values are **min–max normalized per algorithm (row-wise)**. For each execution method, PGSI aggregates these normalized values **across algorithms** (column-wise mean), then computes  
> \(S = \alpha \bar{E}' + \beta \bar{C}' + \gamma \bar{T}'\)  
> with defaults \(\alpha=\beta=0.4\), \(\gamma=0.2\).

**Normalization bounds metadata:**

> Summary **min/max** ranges used for reporting appear in **`audit_report.json`** (`normalization_bounds`), alongside methodology summaries, not only in `GreenScore.csv`.

**Execution environment tuple:**

> Execution contexts can be described abstractly as \(\langle P, M, H\rangle\) (interpreter, method, platform); the implementation realizes these through **`ToolPaths`**, the benchmark **registry**, and **runtime platform detection**, rather than a single typed tuple structure.

**CI:**

> Either remove the multi-platform CI sentence or replace with: automated tests are provided under `tests/` and intended to be run with **pytest**; operators may run them on each target OS.

---

## Source index (quick reference)

| Topic | Location |
|--------|----------|
| Phases 1–7 | `src/pgsi_analyzer/benchmark/orchestrator.py` |
| Subprocess + `PGSI_RUNS` | `src/pgsi_analyzer/benchmark/executor.py` |
| Energy / methodology | `src/pgsi_analyzer/measurement/energy.py`, `estimators.py` |
| Carbon | `src/pgsi_analyzer/models/carbon.py` |
| GreenScore | `src/pgsi_analyzer/models/greenscore.py` |
| Aggregation | `src/pgsi_analyzer/models/aggregation.py` |
| Registry | `src/pgsi_analyzer/benchmarks/registry.py` |
| Package / CLI | `pyproject.toml`, `src/pgsi_analyzer/cli/main.py` |
| Architecture narrative | `docs/architecture/README.md` |

---

*Generated from repository state at validation time; if CI is added later, update §8 accordingly.*
