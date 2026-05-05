Interpreting Results
====================

PGSI generates multiple output layers so users can inspect raw behavior, normalized comparisons, and ranking outcomes.

Core Output Files
-----------------

``energy_combined.csv``
~~~~~~~~~~~~~~~~~~~~~~~

- Combined energy metrics across methods.
- Values are normalized into a shared table for cross-method comparison.

``time_combined.csv``
~~~~~~~~~~~~~~~~~~~~~

- Execution-time aggregates across methods.
- Use this to verify whether an energy-efficient method also meets latency goals.

``carbon_footprint.csv``
~~~~~~~~~~~~~~~~~~~~~~~~

- Derived from energy metrics and carbon intensity factor.
- Represents estimated gCO2e outcomes.

``GreenScore.csv``
~~~~~~~~~~~~~~~~~~

- Final weighted score used for ranking method sustainability/performance trade-offs.
- Uses configured weights (``alpha``, ``beta``, ``gamma``).

``audit_report.json``
~~~~~~~~~~~~~~~~~~~~~

- Provenance artifact for run settings, tool path sourcing, and execution integrity checks.
- Use this file when sharing or reproducing results in team environments.

How to Read GreenScore Safely
-----------------------------

1. Validate benchmark stability first (enough runs, low variance).
2. Confirm methods all completed successfully (audit report + file presence).
3. Compare energy/time/carbon jointly, not GreenScore alone.
4. Document your chosen carbon intensity and weights in reports.

Common Analysis Pattern
-----------------------

1. Start with ``time_combined.csv`` to detect extreme outliers.
2. Cross-check with ``energy_combined.csv`` for energy/latency trade-offs.
3. Use ``carbon_footprint.csv`` to communicate environmental impact.
4. Use ``GreenScore.csv`` as a summary metric for decision-making.

Related Pages
-------------

- For score methodology and academic reference, see :doc:`../methodology/greenscore_reference`.
- For architecture and data flow internals, see :doc:`../architecture`.
