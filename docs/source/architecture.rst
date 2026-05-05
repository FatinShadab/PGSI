Architecture
============

PGSI Analyzer is structured as a layered benchmarking and analysis pipeline that prioritizes
repeatability, cross-method comparability, and transparent auditability.

For setup and first-run commands, see :doc:`getting_started`.
For module-level reference details, see :doc:`api/index`.

System Layers
-------------

CLI Layer
~~~~~~~~~

The CLI entrypoint (``pgsi_analyzer.cli.main``) parses user intent, resolves runtime configuration,
and dispatches to benchmark operations. It is intentionally thin: orchestration and analytics logic
live in dedicated modules so they remain reusable and testable.

Orchestration Layer
~~~~~~~~~~~~~~~~~~~

The orchestration package (``pgsi_analyzer.benchmark``) coordinates the benchmark lifecycle:

- input normalization (algorithms/methods/runs),
- method-specific build steps,
- benchmark process execution,
- artifact collection and placement.

This layer enforces execution ordering and minimizes coupling between benchmark implementations and result models.

Measurement Layer
~~~~~~~~~~~~~~~~~

The measurement package provides decorators and estimation utilities:

- ``measure_time_to_csv`` for repeated runtime capture,
- energy measurement/fallback logic (hardware-dependent primary paths with estimator fallback),
- CPU-power resolution utilities backed by packaged data.

The design goal is graceful degradation: obtain usable energy estimates even when hardware counters or optional
dependencies are unavailable.

Modeling Layer
~~~~~~~~~~~~~~

Model modules transform raw artifacts into comparative analytics:

- aggregation per method,
- combination across methods,
- carbon footprint derivation from energy,
- GreenScore computation using weighted components.

This separation keeps analytics formulas isolated from execution mechanics and simplifies experimentation.

Benchmark Content Layer
~~~~~~~~~~~~~~~~~~~~~~~

Built-in benchmarks are shipped with the package, while user benchmarks can be scaffolded and merged through discovery.
Both flows conform to a shared directory contract so the orchestrator can treat them uniformly.

Core Execution Flow
-------------------

At a high level, ``pgsi-analyzer benchmark run`` performs:

1. Parse and validate CLI arguments.
2. Resolve tool paths from flags, environment, and optional ``.env``.
3. Build a unified benchmark registry (built-ins + user project).
4. Build method prerequisites where needed (for example Cython extensions).
5. Execute benchmark workloads for requested algorithms/methods.
6. Collect raw energy/time files into normalized workspace/output structure.
7. Aggregate, combine, compute carbon metrics, and produce GreenScore.
8. Write audit metadata and final report artifacts.

Data Contracts and File Semantics
---------------------------------

Benchmark output collection depends on naming conventions that communicate artifact intent:

- time outputs follow ``time_*.csv``,
- energy outputs follow ``energy_*.csv``,
- combined outputs live at output root for downstream analysis stages.

These conventions are implementation-level contracts between decorators, collector/provider modules, and model transforms.

Configuration Resolution Strategy
---------------------------------

Runtime executables (Python, PyPy, C compiler) are resolved using precedence logic so users can balance convenience and determinism:

1. Explicit CLI flags (strongest),
2. environment variables,
3. optional ``.env`` file,
4. fallback defaults.

This strategy enables both ad-hoc local runs and strict CI reproducibility.

Extensibility Model
-------------------

PGSI is designed for extension along two axes:

- **Benchmark extension**: add new algorithms via scaffold + registry update.
- **Analysis extension**: add or modify model formulas while preserving existing CSV contracts.

The architecture keeps these concerns decoupled so analytical evolution does not require runner rewrites.

Quality and Reliability
-----------------------

Reliability is supported by a broad test surface (CLI behavior, execution orchestration, measurements,
model computations, and audit integrity checks). Audit artifacts are emitted alongside results to support
traceability and post-run diagnostics.

Related Pages
-------------

- For first-run setup and command examples, see :doc:`getting_started`.
- For benchmark interpretation guidance, see :doc:`user-guide/interpreting_results`.
- For API-level module details, see :doc:`api/index`.

