"""
GreenScore calculation and metric normalization.

This module provides functions to calculate GreenScore, a composite metric
combining energy consumption, execution time, and carbon footprint with
configurable weights.
"""

import pandas as pd
from pathlib import Path
from typing import Union, Optional, Dict

# Methodology tag for "measured" (hardware); all others count as "estimated"
METHODOLOGY_MEASURED = "hardware_rapl_linux"


def normalize_metrics(df: pd.DataFrame, output_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """
    Normalize metrics across methods (row-wise) per algorithm.

    Applies min-max normalization to each row, normalizing values between 0 and 1.
    This allows fair comparison across different algorithms with different scales.

    Args:
        df: DataFrame with one row per algorithm, 'algorithm' column, and metric columns.
        output_path: Optional path to save the normalized DataFrame as CSV.

    Returns:
        DataFrame with 'algorithm' and normalized method columns.

    Examples:
        >>> df = pd.DataFrame({
        ...     'algorithm': ['algo1', 'algo2'],
        ...     'method1': [100, 200],
        ...     'method2': [50, 150]
        ... })
        >>> normalized = normalize_metrics(df)
    """
    # Copy to avoid modifying original
    df = df.copy()
    
    # Extract algorithm names
    algorithm_names = df['algorithm']
    
    # Select only numeric method columns (missing methods may be '' / NaN)
    method_cols = df.columns.drop('algorithm')
    numeric_df = df[method_cols].apply(pd.to_numeric, errors='coerce')

    def _normalize_row(row: pd.Series) -> pd.Series:
        valid = row.dropna()
        if valid.empty:
            return row * 0.0
        row_min = valid.min()
        row_max = valid.max()
        if row_max == row_min:
            return row.apply(lambda v: 0.0 if pd.notna(v) else v)
        return (row - row_min) / (row_max - row_min)

    # Apply row-wise normalization (min-max per algorithm, ignoring NaN)
    normalized_df = numeric_df.apply(_normalize_row, axis=1)
    
    # Add back the algorithm column
    normalized_df.insert(0, 'algorithm', algorithm_names)
    
    # Save to file if output path provided
    if output_path is not None:
        output = Path(output_path) if isinstance(output_path, str) else output_path
        output.parent.mkdir(parents=True, exist_ok=True)
        normalized_df.to_csv(output, index=False)
    
    return normalized_df


def _methodology_counts_from_aggregated(aggregated_energy_paths: Dict[str, Path]) -> Dict[str, Dict[str, int]]:
    """For each method, count points_measured (hardware_rapl_linux) and points_estimated (else)."""
    out = {}
    for method, path in aggregated_energy_paths.items():
        path = Path(path)
        if not path.exists():
            out[method] = {"points_measured": 0, "points_estimated": 0}
            continue
        df = pd.read_csv(path)
        if "methodology" not in df.columns:
            out[method] = {"points_measured": 0, "points_estimated": len(df)}
            continue
        measured = (df["methodology"] == METHODOLOGY_MEASURED).sum()
        out[method] = {"points_measured": int(measured), "points_estimated": int(len(df) - measured)}
    return out


def calculate_greenscore(
    energy_df: pd.DataFrame,
    time_df: pd.DataFrame,
    carbon_df: pd.DataFrame,
    alpha: float = 0.4,
    beta: float = 0.4,
    gamma: float = 0.2,
    output_path: Optional[Union[str, Path]] = None,
    aggregated_energy_paths: Optional[Dict[str, Union[str, Path]]] = None,
) -> pd.DataFrame:
    """
    Compute the GreenScore for each method by combining normalized
    energy, time, and carbon scores with weighted averaging.

    GreenScore = α·energy + β·carbon + γ·time

    Lower scores indicate better sustainability (lower energy, time, and carbon).

    Args:
        energy_df: Raw energy DataFrame (with 'algorithm' column).
        time_df: Raw time DataFrame (with 'algorithm' column).
        carbon_df: Raw carbon DataFrame (with 'algorithm' column).
        alpha: Weight for energy component (default: 0.4).
        beta: Weight for carbon component (default: 0.4).
        gamma: Weight for time component (default: 0.2).
        output_path: Optional path to save the final ranking CSV.
        aggregated_energy_paths: Optional dict method -> path to method's energy_aggregated.csv
                                used to add points_measured / points_estimated to the output.

    Returns:
        DataFrame sorted by green score (ascending, lower is better):
        - 'method': Method name
        - 'energy_uJ_mean', 'time_s_mean', 'carbon_g_mean': Raw averages across algorithms
        - 'energy_norm_mean', 'time_norm_mean', 'carbon_norm_mean': Normalized 0–1 means (0 = best)
        - 'green_score': Composite GreenScore
        - 'points_measured': (if aggregated_energy_paths given) Count of hardware-measured points
        - 'points_estimated': (if aggregated_energy_paths given) Count of estimated points
        - 'data_source_consistency': "Consistent" or "Inconsistent Data Source" (when method has both hardware and estimation)

    Examples:
        >>> energy_df = pd.read_csv('energy.csv')
        >>> time_df = pd.read_csv('time.csv')
        >>> carbon_df = pd.read_csv('carbon.csv')
        >>> ranking = calculate_greenscore(energy_df, time_df, carbon_df)
    """
    # Validate weights sum to 1.0
    if abs(alpha + beta + gamma - 1.0) > 1e-6:
        raise ValueError(f"Weights must sum to 1.0, got: alpha={alpha}, beta={beta}, gamma={gamma}")
    
    # Step 1: Raw means (μJ / seconds / g CO2e) for reporting
    energy_numeric = energy_df.drop(columns=['algorithm']).apply(pd.to_numeric, errors='coerce')
    time_numeric = time_df.drop(columns=['algorithm']).apply(pd.to_numeric, errors='coerce')
    carbon_cols = [c for c in carbon_df.columns if c != 'algorithm']
    carbon_numeric = carbon_df[carbon_cols].apply(pd.to_numeric, errors='coerce')
    carbon_numeric.columns = [c.removesuffix('_CO2e_g') for c in carbon_numeric.columns]

    energy_raw_mean = energy_numeric.mean(skipna=True)
    time_raw_mean = time_numeric.mean(skipna=True)
    carbon_raw_mean = carbon_numeric.mean(skipna=True)

    # Step 2: Normalize each DataFrame (0 = best among methods for that algorithm)
    energy_norm = normalize_metrics(energy_df)
    time_norm = normalize_metrics(time_df)
    carbon_norm = normalize_metrics(carbon_df)

    # Step 3: Normalized column-wise means (components of GreenScore)
    energy_norm_mean = energy_norm.drop(columns=['algorithm']).mean(skipna=True)
    time_norm_mean = time_norm.drop(columns=['algorithm']).mean(skipna=True)
    carbon_norm_cols = carbon_norm.drop(columns=['algorithm'])
    carbon_norm_cols.columns = [c.removesuffix('_CO2e_g') for c in carbon_norm_cols.columns]
    carbon_norm_mean = carbon_norm_cols.mean(skipna=True)

    method_names = energy_raw_mean.index

    # Step 4: Combine into a single DataFrame
    mean_df = pd.DataFrame({
        'method': method_names,
        'energy_uJ_mean': energy_raw_mean.reindex(method_names).values,
        'time_s_mean': time_raw_mean.reindex(method_names).values,
        'carbon_g_mean': carbon_raw_mean.reindex(method_names).values,
        'energy_norm_mean': energy_norm_mean.reindex(method_names).values,
        'time_norm_mean': time_norm_mean.reindex(method_names).values,
        'carbon_norm_mean': carbon_norm_mean.reindex(method_names).values,
    })

    # Step 4b: Add methodology summary (points_measured vs points_estimated)
    if aggregated_energy_paths:
        paths_as_path = {k: Path(v) for k, v in aggregated_energy_paths.items()}
        counts = _methodology_counts_from_aggregated(paths_as_path)
        mean_df["points_measured"] = mean_df["method"].map(lambda m: counts.get(m, {}).get("points_measured", 0))
        mean_df["points_estimated"] = mean_df["method"].map(lambda m: counts.get(m, {}).get("points_estimated", 0))
    else:
        mean_df["points_measured"] = 0
        mean_df["points_estimated"] = 0

    # Step 4c: Methodology consistency — flag "Inconsistent Data Source" when a method has both hardware and estimation
    mean_df["data_source_consistency"] = mean_df.apply(
        lambda r: "Inconsistent Data Source" if (r["points_measured"] > 0 and r["points_estimated"] > 0) else "Consistent",
        axis=1,
    )
    
    # Step 5: Compute GreenScore = α·energy_norm + β·carbon_norm + γ·time_norm
    mean_df['green_score'] = (
        alpha * mean_df['energy_norm_mean'] +
        beta * mean_df['carbon_norm_mean'] +
        gamma * mean_df['time_norm_mean']
    )
    
    # Step 6: Sort methods by green score (lower is better)
    green_score_df = mean_df.sort_values(by='green_score').reset_index(drop=True)
    
    # Step 7: Save to file if output path provided
    if output_path is not None:
        output = Path(output_path) if isinstance(output_path, str) else output_path
        output.parent.mkdir(parents=True, exist_ok=True)
        green_score_df.to_csv(output, index=False)
    
    return green_score_df

