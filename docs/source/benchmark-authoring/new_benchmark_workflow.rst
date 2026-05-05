Extending and Registering New Benchmarks
========================================

This guide shows how to add a new benchmark algorithm and make it discoverable by PGSI.

Option A: Create a Full Project Scaffold
----------------------------------------

Generate a benchmark project skeleton:

.. code-block:: bash

   pgsi-analyzer startproject my-benchmarks --algorithms all

This creates a ready structure and registry file.

Option B: Add One Benchmark to Existing Project
-----------------------------------------------

Create and register a benchmark in an existing benchmark project:

.. code-block:: bash

   pgsi-analyzer create benchmark \
     --name my_algo \
     --benchmarks-dir my-benchmarks

This command:

- creates method folders (``cpython``, ``pypy``, ``cython``, ``ctypes``, ``py_compile``),
- adds starter files (``main.py`` and method-specific stubs),
- updates ``pgsi_registry.json`` with the new benchmark entry.

Implement the Workload
----------------------

Edit the generated files, especially:

- ``my-benchmarks/my_algo/cpython/main.py``
- and equivalent method directories as needed.

Keep the measurement decorators so PGSI can collect outputs:

.. code-block:: python

   @measure_energy_to_csv(n=get_measurement_runs("my_algo"), csv_filename="my_algo_cpython")
   def run_energy_benchmark():
       run_workload()

   @measure_time_to_csv(n=get_measurement_runs("my_algo"), csv_filename="my_algo_cpython")
   def run_time_benchmark():
       run_workload()

Validate Discovery
------------------

.. code-block:: bash

   pgsi-analyzer benchmark list --algorithms --benchmarks-dir my-benchmarks

You should see ``my_algo`` in the output.

Run Only the New Benchmark
--------------------------

.. code-block:: bash

   pgsi-analyzer benchmark run \
     --algorithms my_algo \
     --methods cpython \
     --runs 5 \
     --benchmarks-dir my-benchmarks \
     --output results_my_algo

Best Practices
--------------

- Keep workloads deterministic where possible.
- Start with ``cpython`` baseline, then add other methods.
- Add enough runs to reduce random variance.
- Keep input sizes representative of your real workload category.

Related Pages
-------------

- For execution commands, see :doc:`../user-guide/running_benchmarks`.
- For API details of scaffold utilities, see :doc:`../api/benchmarks`.
- For benchmark discovery and output validation, see :doc:`../development/troubleshooting`.
