Prerequisites and Tooling
=========================

This page focuses on practical environment setup for accurate, reproducible benchmark runs.

Python and Virtual Environment
------------------------------

Use Python 3.8+ and isolate dependencies in a virtual environment:

.. code-block:: bash

   python -m venv .venv
   # Linux/macOS
   source .venv/bin/activate
   # Windows PowerShell
   .venv\Scripts\Activate.ps1

   pip install -U pip
   pip install -e .

PyPy Setup for Method Comparison
--------------------------------

PGSI compares ``cpython`` and ``pypy`` execution paths. Install PyPy and provide its executable path.

Windows
~~~~~~~

1. Download the latest PyPy3 Windows build from the official downloads page.
2. Extract it to a stable location (example: ``C:\tools\pypy3``).
3. Set environment variable:

.. code-block:: powershell

   $env:PGSI_PYPY_PATH="C:\tools\pypy3\pypy3.exe"

Linux/macOS
~~~~~~~~~~~

Install via package manager or download binary release, then point PGSI to the executable:

.. code-block:: bash

   export PGSI_PYPY_PATH=/opt/pypy/bin/pypy3

GCC / C Compiler Setup for ``ctypes`` and ``cython``
-----------------------------------------------------

To benchmark native paths (``ctypes``/``cython``), a C compiler must be available.

Windows (recommended: MSYS2 MinGW-w64 GCC)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Install `MSYS2 <https://www.msys2.org/>`_.
2. Open MSYS2 UCRT64 shell and install toolchain:

.. code-block:: bash

   pacman -S --needed mingw-w64-ucrt-x86_64-gcc

3. Set compiler path for PGSI:

.. code-block:: powershell

   $env:PGSI_CC_PATH="C:\msys64\ucrt64\bin\gcc.exe"

Alternative on Windows: Visual Studio Build Tools (``cl.exe``), then set ``PGSI_CC_PATH`` to the compiler path.

Linux
~~~~~

.. code-block:: bash

   sudo apt update
   sudo apt install -y build-essential
   export PGSI_CC_PATH=/usr/bin/gcc

macOS
~~~~~

.. code-block:: bash

   xcode-select --install
   export PGSI_CC_PATH=/usr/bin/clang

Quick Verification
------------------

Before full runs, verify detected tools by running a small benchmark slice:

.. code-block:: bash

   pgsi-analyzer benchmark run \
     --algorithms hanoi \
     --methods cpython pypy ctypes cython \
     --runs 2 \
     --benchmarks-dir my-benchmarks \
     --output results_sanity

If one method fails, run per-method first to isolate setup issues.

Related Pages
-------------

- For first-run flow, see :doc:`../getting_started`.
- For pyRAPL method details and permissions, see :doc:`../methodology/measurement_methods`.
- For benchmark authoring and registry setup, see :doc:`../benchmark-authoring/new_benchmark_workflow`.
