Getting Started
===============

This guide walks through a complete first-run workflow for ``pgsi-analyzer``:
installation, environment setup, benchmark project creation, execution, and result interpretation.

Prerequisites
-------------

- Python 3.8 or newer
- ``pip`` available in your shell
- Optional: PyPy executable for ``pypy`` method benchmarks
- Optional: C compiler for ``ctypes`` and ``cython`` methods

Installation
------------

Install from source (GitHub):

.. code-block:: bash

   git clone https://github.com/FatinShadab/PGSI.git
   cd PGSI
   pip install -e .

Install from your local repository checkout:

.. code-block:: bash

   pip install -e .

Or install from a packaged release:

.. code-block:: bash

   pip install pgsi-analyzer

Verify the CLI is available:

.. code-block:: bash

   pgsi-analyzer --help

For internal execution details, see :doc:`architecture`.
For full Python module references, see :doc:`api/index`.

Configure Tool Paths
--------------------

PGSI can resolve executable locations from CLI flags, environment variables, and optional ``.env`` files.
For reproducible teams and CI, defining paths explicitly is recommended.

Environment variables used by the CLI:

- ``PGSI_PYTHON_PATH``
- ``PGSI_PYPY_PATH``
- ``PGSI_CC_PATH``

Example ``.env``:

.. code-block:: text

   PGSI_PYTHON_PATH=/usr/bin/python3
   PGSI_PYPY_PATH=/opt/pypy/bin/pypy3
   PGSI_CC_PATH=/usr/bin/gcc

pyRAPL Setup (Linux Intel x86_64)
---------------------------------

If you want hardware-assisted energy measurement, install the optional ``energy`` extras.
This enables ``pyRAPL`` on supported Linux Intel x86_64 systems.

Install with extras:

.. code-block:: bash

   pip install -e ".[energy]"

Validate installation:

.. code-block:: bash

   python -c "import pyRAPL; print('pyRAPL available')"

Run a benchmark with the same CLI flow (PGSI will use ``pyRAPL`` when available and supported):

.. code-block:: bash

   pgsi-analyzer benchmark run \
     --algorithms hanoi \
     --methods cpython \
     --runs 10 \
     --output results_pyrapl \
     --benchmarks-dir my-benchmarks

If ``pyRAPL`` is unavailable or unsupported on the host, PGSI falls back to estimator-based energy paths automatically.

First Benchmark Project
-----------------------

Create a benchmark project scaffold (all built-ins):

.. code-block:: bash

   pgsi-analyzer startproject my-benchmarks --algorithms all

Alternative (explicit benchmark subcommand):

.. code-block:: bash

   pgsi-analyzer benchmark init-template --output my-benchmarks --algorithms all

List Available Algorithms and Methods
-------------------------------------

Run from inside the project root (or pass ``--benchmarks-dir``):

.. code-block:: bash

   pgsi-analyzer benchmark list --algorithms --benchmarks-dir my-benchmarks
   pgsi-analyzer benchmark list --methods --benchmarks-dir my-benchmarks

Run Your First Suite
--------------------

Execute a focused run using one algorithm and one method:

.. code-block:: bash

   pgsi-analyzer benchmark run \
     --algorithms hanoi \
     --methods cpython \
     --runs 5 \
     --output results \
     --benchmarks-dir my-benchmarks

Run across all algorithms and all methods:

.. code-block:: bash

   pgsi-analyzer benchmark run \
     --algorithms all \
     --methods all \
     --runs 20 \
     --output results \
     --benchmarks-dir my-benchmarks

Override run counts per algorithm:

.. code-block:: bash

   pgsi-analyzer benchmark run \
     --algorithms hanoi fasta \
     --methods cpython pypy \
     --runs 10 \
     --algorithm-runs hanoi=30 fasta=5 \
     --benchmarks-dir my-benchmarks

Expected Outputs
----------------

After a successful run, the output directory contains:

- ``energy_combined.csv``
- ``time_combined.csv``
- ``carbon_footprint.csv``
- ``GreenScore.csv``
- ``audit_report.json``

Method-specific aggregated files are also created under subdirectories (for example ``results/cpython``).

Minimal Programmatic Usage
--------------------------

You can run key analysis steps from Python for custom pipelines:

.. code-block:: python

   from pathlib import Path
   from pgsi_analyzer.models.carbon import calculate_carbon_footprint

   energy_path = Path("results/energy_combined.csv")
   carbon_df = calculate_carbon_footprint(
       energy_csv_path=energy_path,
       output_path="results/carbon_footprint.csv",
       carbon_intensity=0.000475,
   )
   print(carbon_df.head())

What Happens Internally
-----------------------

The command pipeline follows this sequence:

1. Resolve configuration and runtime tool paths.
2. Build/merge benchmark registry (built-ins + optional user benchmarks).
3. Build method-specific assets (``cython``/``ctypes`` when required).
4. Execute benchmark runners and collect raw time/energy CSV artifacts.
5. Aggregate and combine outputs across methods.
6. Compute carbon footprint and GreenScore ranking.
7. Emit audit metadata for provenance and reproducibility.

Troubleshooting First Runs
--------------------------

- If ``pypy`` or compiler methods fail, run with ``--methods cpython`` first to validate baseline setup.
- If no user benchmark is found, verify ``--benchmarks-dir`` points to a folder containing ``pgsi_registry.json``.
- If output files are missing, inspect CLI stderr and ``audit_report.json`` for execution failures.
- If you expected ``pyRAPL`` usage, confirm Linux Intel x86_64 support and verify installation in the active Python environment.

Related Pages
-------------

- For prerequisite setup (PyPy, GCC/Clang, environment checks), see :doc:`user-guide/prerequisites_and_tooling`.
- For benchmark extension and registry workflow, see :doc:`benchmark-authoring/new_benchmark_workflow`.

