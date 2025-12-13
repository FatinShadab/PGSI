"""
Carbon footprint calculation from energy consumption data.

This module provides functions to calculate carbon dioxide equivalent (CO₂e)
emissions from energy consumption data using configurable carbon intensity factors.
"""

import pandas as pd
from pathlib import Path
from typing import Union, Optional


def calculate_carbon_footprint(
    energy_csv_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    carbon_intensity: float = 0.000475
) -> pd.DataFrame:
    """
    Calculate carbon footprint from energy consumption data.

    Converts energy values (in microjoules) to carbon dioxide equivalent (CO₂e)
    in grams using a configurable carbon intensity factor.

    Args:
        energy_csv_path: Path to CSV file containing energy data.
                        Expected format: 'algorithm' column and method columns with energy in μJ.
        output_path: Optional path to save the carbon footprint CSV.
                    If None, file is not written.
        carbon_intensity: Carbon intensity factor in gCO₂e per Joule.
                         Default: 0.000475 (global average).

    Returns:
        DataFrame with carbon footprint data:
        - 'algorithm' column
        - Method columns with '_CO2e_g' suffix (carbon in grams)

    Examples:
        >>> df = calculate_carbon_footprint('energy.csv')
        >>> df.head()
        >>> # Save to file
        >>> df = calculate_carbon_footprint('energy.csv', output_path='carbon.csv')
    """
    # Convert to Path if string
    energy_path = Path(energy_csv_path) if isinstance(energy_csv_path, str) else energy_csv_path
    
    if not energy_path.exists():
        raise FileNotFoundError(f"Energy CSV file not found: {energy_path}")
    
    # Read energy data
    energy_df = pd.read_csv(energy_path)
    
    if 'algorithm' not in energy_df.columns:
        raise ValueError("CSV must contain an 'algorithm' column")
    
    # Create carbon footprint DataFrame
    carbon_df = pd.DataFrame()
    carbon_df['algorithm'] = energy_df['algorithm']
    
    # Calculate carbon for each method column
    method_columns = [col for col in energy_df.columns if col != 'algorithm']
    
    for method_col in method_columns:
        carbon_col = f"{method_col}_CO2e_g"
        # Convert μJ to J, then multiply by carbon intensity
        carbon_df[carbon_col] = (
            energy_df[method_col] * 1e-6 * carbon_intensity
        ).round(6)
    
    # Save to file if output path provided
    if output_path is not None:
        output = Path(output_path) if isinstance(output_path, str) else output_path
        output.parent.mkdir(parents=True, exist_ok=True)
        carbon_df.to_csv(output, index=False)
    
    return carbon_df

