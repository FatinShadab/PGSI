"""
Statistical analysis utilities for pgsi_analyzer.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import pandas as pd

from ..utils import AnalysisError, validate_dataframe, validate_file_path


def _require_scipy():
    try:
        import scipy.stats as stats  # noqa: F401
    except ImportError as exc:  # pragma: no cover
        raise AnalysisError("scipy is required for statistical analysis (install pgsi-analyzer[analysis])") from exc


def calculate_standard_deviation(df: pd.DataFrame) -> pd.Series:
    """
    Calculate standard deviation across methods (per column).
    """
    validate_dataframe(df, ["algorithm"])
    return df.drop(columns=["algorithm"]).std()


def perform_statistical_tests(
    energy_df: pd.DataFrame,
    time_df: pd.DataFrame,
    carbon_df: pd.DataFrame,
) -> dict:
    """
    Perform simple paired statistical tests across methods.
    Returns a dictionary of p-values for energy/time/carbon using one-way ANOVA.
    """
    _require_scipy()
    import scipy.stats as stats

    results = {}
    for label, df in [("energy", energy_df), ("time", time_df), ("carbon", carbon_df)]:
        validate_dataframe(df, ["algorithm"])
        cols = [c for c in df.columns if c != "algorithm"]
        if len(cols) < 2:
            raise AnalysisError(f"Need at least two methods to compare for {label}")
        groups = [df[c].values for c in cols]
        stat, pvalue = stats.f_oneway(*groups)
        results[label] = {"f_stat": stat, "p_value": pvalue}
    return results


def oneway_anova_greenscore(greenscore_df: pd.DataFrame) -> dict:
    """
    Run one-way ANOVA on GreenScore results across methods.
    Expects columns: method, green_score.
    """
    _require_scipy()
    import scipy.stats as stats

    validate_dataframe(greenscore_df, ["method", "green_score"])
    grouped = greenscore_df.groupby("method")["green_score"].apply(list)
    if len(grouped) < 2:
        raise AnalysisError("Need at least two methods for ANOVA")
    stat, pvalue = stats.f_oneway(*grouped.tolist())
    return {"f_stat": stat, "p_value": pvalue}


def load_csv(path: Union[str, Path]) -> pd.DataFrame:
    """Utility to load a CSV with validation."""
    p = validate_file_path(path, must_exist=True)
    return pd.read_csv(p)

