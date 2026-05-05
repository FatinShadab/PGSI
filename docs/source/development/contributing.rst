Contributing
============

This page describes a practical contribution workflow aligned with the current PGSI codebase and tooling.

Repository Layout
-----------------

- Core package code: ``src/pgsi_analyzer``
- Tests: ``tests``
- Sphinx docs source: ``docs/source``

Set Up a Local Dev Environment
------------------------------

.. code-block:: bash

   python -m venv .venv
   # Linux/macOS
   source .venv/bin/activate
   # Windows PowerShell
   .venv\Scripts\Activate.ps1

   pip install -U pip
   pip install -e .

Run the Test Suite
------------------

PGSI uses ``pytest`` with test discovery configured from ``pyproject.toml``.

.. code-block:: bash

   pytest

To run a narrower subset during iteration:

.. code-block:: bash

   pytest tests/test_cli_benchmark.py

Code Style and Static Checks
----------------------------

Project configuration includes Black, isort, and mypy sections in ``pyproject.toml``.

.. code-block:: bash

   python -m black src tests
   python -m isort src tests
   python -m mypy src

Build Documentation Locally
---------------------------

From the ``docs`` directory:

.. code-block:: bash

   python -m pip install -r requirements.txt
   python -m sphinx -M clean source _build
   python -m sphinx -M html source _build

Generated HTML will be available in ``docs/_build/html``.

Contribution Focus Areas
------------------------

- Benchmark execution pipeline: ``pgsi_analyzer.benchmark``
- Measurement and fallback logic: ``pgsi_analyzer.measurement``
- Scoring and analytics models: ``pgsi_analyzer.models``
- CLI and user workflows: ``pgsi_analyzer.cli``

When changing behavior, update tests and relevant documentation pages in the same change.

Related Pages
-------------

- For system design context, see :doc:`../architecture`.
- For benchmark authoring flow, see :doc:`../benchmark-authoring/new_benchmark_workflow`.
- For common setup/runtime issues, see :doc:`troubleshooting`.
