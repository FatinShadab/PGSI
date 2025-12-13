"""
Models module for carbon footprint, GreenScore, and data aggregation.

This module provides functions for:
- Carbon footprint calculation
- GreenScore computation and normalization
- Energy and time aggregation
- Combining results from multiple methods
"""

from .carbon import calculate_carbon_footprint
from .greenscore import calculate_greenscore, normalize_metrics
from .aggregation import aggregate_energy, aggregate_time
from .combination import combine_energy_results, combine_time_results

__all__ = [
    "calculate_carbon_footprint",
    "calculate_greenscore",
    "normalize_metrics",
    "aggregate_energy",
    "aggregate_time",
    "combine_energy_results",
    "combine_time_results",
]
