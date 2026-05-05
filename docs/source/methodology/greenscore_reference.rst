GreenScore Methodology and Reference
====================================

GreenScore in PGSI is a composite metric that summarizes performance and sustainability signals into one ranking value.

What GreenScore Combines
------------------------

PGSI computes GreenScore from:

- energy metrics,
- carbon footprint metrics,
- execution time metrics.

The score uses configurable weights:

- ``alpha`` for energy,
- ``beta`` for carbon,
- ``gamma`` for time.

Default CLI values are set to:

- ``alpha = 0.4``
- ``beta = 0.4``
- ``gamma = 0.2``

Why a Composite Score Exists
----------------------------

Single-metric decisions can be misleading. A method can be fast but energy-inefficient, or low-energy but too slow for production use.
GreenScore provides a tunable, decision-oriented summary while keeping source metrics visible for transparent interpretation.

Academic Reference
------------------

Reference publication:

- `GreenScore paper (IEEE Xplore) <https://ieeexplore.ieee.org/document/11231789>`_

When documenting or publishing benchmark findings, include:

1. the GreenScore reference,
2. your selected weight values,
3. carbon intensity factor,
4. hardware/runtime environment details.

Interpretation Guidance
-----------------------

- Use GreenScore for ranking and coarse prioritization.
- Use raw energy/time/carbon tables for root-cause analysis and final technical decisions.
- Re-run critical comparisons with higher run counts to reduce statistical noise.

Related Pages
-------------

- For output files and interpretation flow, see :doc:`../user-guide/interpreting_results`.
- For execution details, see :doc:`../user-guide/running_benchmarks`.
- For architecture and pipeline context, see :doc:`../architecture`.
