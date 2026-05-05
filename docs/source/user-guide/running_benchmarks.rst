Running Benchmarks
==================

PGSI supports both quick sanity runs and full-scale comparison suites.

List Available Targets
----------------------

.. code-block:: bash

   pgsi-analyzer benchmark list --algorithms --benchmarks-dir my-benchmarks
   pgsi-analyzer benchmark list --methods --benchmarks-dir my-benchmarks

Run a Focused Comparison
------------------------

Use this during setup and debugging:

.. code-block:: bash

   pgsi-analyzer benchmark run \
     --algorithms hanoi \
     --methods cpython pypy \
     --runs 5 \
     --benchmarks-dir my-benchmarks \
     --output results_quick

Run a Full Suite
----------------

.. code-block:: bash

   pgsi-analyzer benchmark run \
     --algorithms all \
     --methods all \
     --runs 30 \
     --benchmarks-dir my-benchmarks \
     --output results_full

Use Per-Algorithm Run Overrides
-------------------------------

Some algorithms are slower by design. Tune per algorithm:

.. code-block:: bash

   pgsi-analyzer benchmark run \
     --algorithms hanoi fasta binary-trees \
     --methods cpython pypy \
     --runs 10 \
     --algorithm-runs hanoi=30 fasta=8 binary-trees=15 \
     --benchmarks-dir my-benchmarks

Control Carbon/GreenScore Weights
---------------------------------

You can adjust weighting and carbon intensity:

.. code-block:: bash

   pgsi-analyzer benchmark run \
     --algorithms all \
     --methods all \
     --runs 20 \
     --alpha 0.4 \
     --beta 0.4 \
     --gamma 0.2 \
     --carbon-intensity 0.000475 \
     --benchmarks-dir my-benchmarks

Input and Output Expectations
-----------------------------

- Input benchmark project should include ``pgsi_registry.json`` and method folders.
- Output includes:
  - ``energy_combined.csv``
  - ``time_combined.csv``
  - ``carbon_footprint.csv``
  - ``GreenScore.csv``
  - ``audit_report.json``

Related Pages
-------------

- For tool installation (GCC/PyPy), see :doc:`prerequisites_and_tooling`.
- For output interpretation, see :doc:`interpreting_results`.
- For GreenScore methodology details, see :doc:`../methodology/greenscore_reference`.
