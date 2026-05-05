Measurement Methods (Including pyRAPL)
======================================

PGSI uses a layered measurement approach to keep runs useful across heterogeneous systems.

Measurement Priority
--------------------

At runtime, PGSI attempts energy measurement in this order:

1. Hardware-assisted path (``pyRAPL``) when available and supported.
2. CodeCarbon-based estimation when available.
3. Deterministic CPU-power/TDP estimation fallback.

This design allows one command interface across Linux, Windows, and macOS while preserving provenance metadata.

pyRAPL Setup and Permissions
----------------------------

``pyRAPL`` typically works on Linux Intel x86_64 systems with Intel RAPL access.

Install
~~~~~~~

.. code-block:: bash

   pip install -e ".[energy]"

Kernel/permission notes
~~~~~~~~~~~~~~~~~~~~~~~

- The ``msr`` kernel module may be required.
- On many systems, reading RAPL counters requires elevated privileges or access to specific device files.

Typical Linux setup commands:

.. code-block:: bash

   sudo modprobe msr
   ls /dev/cpu/0/msr

If permission is denied during measurement, run under a user/session with required access or configure permissions according to your system security policy.

Run with pyRAPL-capable configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pgsi-analyzer benchmark run \
     --algorithms hanoi \
     --methods cpython \
     --runs 10 \
     --benchmarks-dir my-benchmarks \
     --output results_pyrapl

Fallback Behavior
-----------------

When ``pyRAPL`` is unavailable, PGSI falls back to estimation logic. The estimator first attempts
CodeCarbon-derived energy and then falls back to deterministic CPU-power/TDP estimation when needed.
Output metadata indicates the methodology source so users can distinguish measured vs estimated values.

Related Pages
-------------

- For practical setup (PyPy/GCC/etc.), see :doc:`../user-guide/prerequisites_and_tooling`.
- For architecture data flow, see :doc:`../architecture`.
- For score interpretation and trade-off analysis, see :doc:`../user-guide/interpreting_results`.
