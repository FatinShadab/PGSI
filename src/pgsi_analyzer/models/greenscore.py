"""
GreenScore calculation and metric normalization.

This module provides functions to calculate GreenScore, a composite metric
combining energy consumption, execution time, and carbon footprint with
configurable weights.
"""

import pandas as pd
from pathlib import Path
from typing import Union, Optional


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
    
    # Select only numeric method columns
    method_cols = df.columns.drop('algorithm')
    numeric_df = df[method_cols]
    
    # Apply row-wise normalization (min-max per algorithm)
    normalized_df = numeric_df.apply(
        lambda row: (row - row.min()) / (row.max() - row.min())
        if row.max() != row.min() else row * 0,  # Handle constant rows
        axis=1
    )
    
    # Add back the algorithm column
    normalized_df.insert(0, 'algorithm', algorithm_names)
    
    # Save to file if output path provided
    if output_path is not None:
        output = Path(output_path) if isinstance(output_path, str) else output_path
        output.parent.mkdir(parents=True, exist_ok=True)
        normalized_df.to_csv(output, index=False)
    
    return normalized_df


def calculate_greenscore(
    energy_df: pd.DataFrame,
    time_df: pd.DataFrame,
    carbon_df: pd.DataFrame,
    alpha: float = 0.4,
    beta: float = 0.4,
    gamma: float = 0.2,
    output_path: Optional[Union[str, Path]] = None
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

    Returns:
        DataFrame sorted by green score (ascending, lower is better):
        - 'method': Method name
        - 'energy_mean': Mean normalized energy
        - 'time_mean': Mean normalized time
        - 'carbon_mean': Mean normalized carbon
        - 'green_score': Composite GreenScore

    Examples:
        >>> energy_df = pd.read_csv('energy.csv')
        >>> time_df = pd.read_csv('time.csv')
        >>> carbon_df = pd.read_csv('carbon.csv')
        >>> ranking = calculate_greenscore(energy_df, time_df, carbon_df)
    """
    # Validate weights sum to 1.0
    if abs(alpha + beta + gamma - 1.0) > 1e-6:
        raise ValueError(f"Weights must sum to 1.0, got: alpha={alpha}, beta={beta}, gamma={gamma}")
    
    # Step 1: Normalize each DataFrame
    energy_norm = normalize_metrics(energy_df)
    time_norm = normalize_metrics(time_df)
    carbon_norm = normalize_metrics(carbon_df)
    
    # Step 2: Drop algorithm column and compute column-wise means
    energy_mean = energy_norm.drop(columns=['algorithm']).mean()
    time_mean = time_norm.drop(columns=['algorithm']).mean()
    carbon_mean = carbon_norm.drop(columns=['algorithm']).mean()
    
    # Step 3: Method names from energy columns (already plain: cpython, py_compile, etc.)
    # Carbon columns have '_CO2e_g' suffix but we use energy index so names stay correct
    method_names = energy_mean.index
    
    # Step 4: Combine into a single DataFrame
    mean_df = pd.DataFrame({
        'method': method_names,
        'energy_mean': energy_mean.values,
        'time_mean': time_mean.values,
        'carbon_mean': carbon_mean.values
    })
    
    # Step 5: Compute GreenScore = α·energy + β·carbon + γ·time
    mean_df['green_score'] = (
        alpha * mean_df['energy_mean'] +
        beta * mean_df['carbon_mean'] +
        gamma * mean_df['time_mean']
    )
    
    # Step 6: Sort methods by green score (lower is better)
    green_score_df = mean_df.sort_values(by='green_score').reset_index(drop=True)
    
    # Step 7: Save to file if output path provided
    if output_path is not None:
        output = Path(output_path) if isinstance(output_path, str) else output_path
        output.parent.mkdir(parents=True, exist_ok=True)
        green_score_df.to_csv(output, index=False)
    
    return green_score_df

