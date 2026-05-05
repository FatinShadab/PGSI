# PGSI Full Codebase Audit (2026-05-05)

## Scope

This audit reviews the current PGSI software for:

- architecture and execution flow quality
- energy measurement correctness (primary focus)
- fallback behavior when pyRAPL is unavailable
- cross-platform readiness (Windows, Linux, macOS, Raspberry Pi OS)
- test and packaging posture

## Executive Summary

PGSI is structurally solid and test-backed, with a clear benchmark pipeline and deterministic outputs. The fallback chain is implemented in the expected direction (`pyRAPL -> CodeCarbon -> CPU-time/TDP`) and the behavior is validated by tests.

The main gap is not fallback order, but fallback fidelity and production readiness:

- CodeCarbon is optional at install time, so many users will silently run TDP estimation without realizing they skipped the stronger fallback.
- TDP matching uses a small hardcoded heuristic map, not a CPU-model database (for example, CodeCarbon's `cpu_power.csv`).
- There is no packaged CPU-TDP dataset or dedicated resolver layer, so Raspberry Pi and newer CPUs can fall back to generic TDP too often.

## What Is Working Well

### 1) Pipeline Architecture Is Clean

- Orchestration flow is explicit and staged: build, execute, aggregate, combine, carbon, GreenScore.
- Path handling is `pathlib`-first and generally deterministic.
- Methodology labels flow through aggregation to GreenScore (`hardware_rapl_linux` vs estimated tags).

### 2) Fallback Chain Exists and Is Correctly Ordered

Current implementation in `measurement/energy.py`:

1. Use pyRAPL only when Linux x86_64 and pyRAPL setup succeeds.
2. If not, try CodeCarbon tracker and recover `energy_consumed` where available.
3. If CodeCarbon data is missing/invalid, fallback to CPU-time/TDP estimator.

### 3) Good Test Coverage on Energy Core

Focused tests pass:

- `tests/test_energy_crossplatform.py`
- `tests/test_estimators.py`
- `tests/test_platform.py`

Result on this audit run: **65 passed**.

### 4) Cross-Platform Abstractions Exist

- Platform detection and hardware capability checks are centralized.
- Non-Linux environments gracefully enter estimation path.
- Warnings inform user when hardware counters are unavailable.

## Findings (Ranked)

## High

- **CodeCarbon is not in base dependencies.**
  - In `pyproject.toml`, CodeCarbon is optional (`[project.optional-dependencies].energy`).
  - Impact: users installing plain `pgsi-analyzer` may not get CodeCarbon fallback and will frequently drop to TDP estimation.
  - Risk: lower accuracy and inconsistent user expectation versus documentation.

- **No CPU model database integration for TDP resolution.**
  - TDP estimator relies on small heuristic dictionary in `measurement/estimators.py`.
  - Impact: modern Intel/AMD SKUs, ARM variants, and Raspberry Pi boards are often mapped to rough defaults.
  - Risk: significant estimation error and weaker reproducibility.

## Medium

- **CodeCarbon integration only uses runtime tracker output, not static hardware DB.**
  - Current logic tries `final_emissions_data.energy_consumed` and tracker internals.
  - When unavailable, it falls straight to heuristic TDP model.
  - Opportunity: recover TDP from curated CPU database before generic defaults.

- **Raspberry Pi OS is "supported" by fallback, but not specifically calibrated.**
  - Platform fallback works functionally, but accuracy for Pi models depends on coarse defaults.
  - Need explicit ARM/RPi mapping strategy using dataset-based lookup.

## Low

- **Documentation could be clearer on installation profiles.**
  - Some docs imply cross-platform CodeCarbon path broadly, but installation defaults may not include it.
  - A single "recommended install profile" for serious energy studies would reduce confusion.

## Cross-Platform Status

### Windows

- Functional: yes (estimation path).
- Accurate fallback quality: medium (depends on CodeCarbon presence and CPU model match).

### Linux x86_64

- Functional: yes.
- Best path: pyRAPL where permissions/hardware permit; fallback chain present.

### macOS

- Functional: yes.
- Accuracy: medium; better if CodeCarbon active, otherwise heuristic TDP.

### Raspberry Pi OS (Linux ARM)

- Functional: yes (estimation path).
- Accuracy: currently medium-to-low for many models due to heuristic TDP matching.

## Recommendations

1. Make CodeCarbon effectively default for runtime installations intended for benchmarking.
2. Add a packaged CPU power dataset (preferably sourced from CodeCarbon `cpu_power.csv` with attribution/license note).
3. Implement a dedicated CPU model resolver:
   - normalize `py-cpuinfo` strings
   - regex/fuzzy match against dataset
   - confidence score + fallback tiers
4. Keep TDP heuristic map only as last-resort fallback.
5. Add platform matrix tests that assert resolver behavior for:
   - Intel/AMD desktop/mobile SKUs
   - Apple Silicon labels
   - Raspberry Pi ARM labels

## Final Judgment

The codebase is in good shape operationally. The critical next step is improving fallback data quality, not rebuilding architecture. With CodeCarbon-first install posture plus dataset-backed TDP lookup, PGSI can achieve the cross-platform reliability and auditability target for Windows, Linux, macOS, and Raspberry Pi OS.
