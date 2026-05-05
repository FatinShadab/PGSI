Troubleshooting
===============

This page covers frequent setup and runtime issues when building or using PGSI docs and benchmarks.

Docs Build Issues
-----------------

``document isn't included in any toctree``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Cause: A page exists but no index includes it.
- Fix: Add the page to the appropriate section ``index.rst``.

Autodoc import errors
~~~~~~~~~~~~~~~~~~~~~

- Cause: Incorrect module path in ``.. automodule::`` directive.
- Fix: Verify module names against ``src/pgsi_analyzer`` package structure.

Benchmark Runtime Issues
------------------------

``pypy`` method not found
~~~~~~~~~~~~~~~~~~~~~~~~~

- Ensure PyPy is installed.
- Set ``PGSI_PYPY_PATH`` or pass ``--pypy-path``.

Compiler errors for ``ctypes``/``cython``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Install GCC/Clang/MSVC build tools.
- Set ``PGSI_CC_PATH`` or pass ``--cc-path``.

pyRAPL permission failures
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Confirm Linux Intel x86_64 support.
- Ensure required kernel module/device access (for example ``msr``).
- Re-check active Python environment has ``pyRAPL`` installed.

Result Consistency Issues
-------------------------

Large run-to-run variance
~~~~~~~~~~~~~~~~~~~~~~~~~

- Increase ``--runs``.
- Reduce background system load.
- Keep workload inputs deterministic.

Missing expected output files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Inspect CLI stderr.
- Inspect ``audit_report.json`` for failed phases and tool path sources.

Related Pages
-------------

- :doc:`../user-guide/prerequisites_and_tooling`
- :doc:`../user-guide/running_benchmarks`
- :doc:`../methodology/measurement_methods`
