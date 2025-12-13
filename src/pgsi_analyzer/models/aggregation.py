"""
Energy and time aggregation from raw measurement logs.

This module provides functions to aggregate energy and time measurements
from raw CSV logs, computing averages across multiple runs.
"""

import pandas as pd
from pathlib import Path
from typing import Union, Optional


def aggregate_energy(
    folder_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None
) -> pd.DataFrame:
    """
    Compute average energy consumption from raw CSV logs in a folder.

    Reads all CSV files in the specified folder and computes the average
    'package (uJ)' value for each file.

    Args:
        folder_path: Path to folder containing energy CSV files.
                    Each CSV should have a 'package (uJ)' column.
        output_path: Optional path to save the aggregated results CSV.

    Returns:
        DataFrame with columns:
        - 'filename': Base name of the CSV file (without extension)
        - 'average_package (uJ)': Average energy in microjoules

    Examples:
        >>> df = aggregate_energy('energy_benchmark/')
        >>> df.head()
    """
    # Convert to Path if string
    folder = Path(folder_path) if isinstance(folder_path, str) else folder_path
    
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")
    
    if not folder.is_dir():
        raise ValueError(f"Path is not a directory: {folder}")
    
    # Find all CSV files
    csv_files = list(folder.glob('*.csv'))
    
    if not csv_files:
        raise ValueError(f"No CSV files found in folder: {folder}")
    
    results = []
    
    for csv_file in csv_files:
        try:
            # Read CSV
            df = pd.read_csv(csv_file)
            
            # Check for required column
            if 'package (uJ)' not in df.columns:
                continue  # Skip files without the required column
            
            # Compute average
            avg_energy = df['package (uJ)'].mean()
            
            # Store result with filename (without extension)
            results.append({
                'filename': csv_file.stem,
                'average_package (uJ)': avg_energy
            })
        except Exception as e:
            # Skip files that can't be read
            continue
    
    if not results:
        raise ValueError(f"No valid energy data found in folder: {folder}")
    
    # Create DataFrame
    result_df = pd.DataFrame(results)
    
    # Save to file if output path provided
    if output_path is not None:
        output = Path(output_path) if isinstance(output_path, str) else output_path
        output.parent.mkdir(parents=True, exist_ok=True)
        result_df.to_csv(output, index=False)
    
    return result_df


def aggregate_time(
    folder_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None
) -> pd.DataFrame:
    """
    Compute average execution time from raw CSV logs in a folder.

    Reads all CSV files in the specified folder and computes the average
    'execution_time (s)' value for each file.

    Args:
        folder_path: Path to folder containing time CSV files.
                    Each CSV should have an 'execution_time (s)' column.
        output_path: Optional path to save the aggregated results CSV.

    Returns:
        DataFrame with columns:
        - 'filename': Base name of the CSV file (without extension)
        - 'execution_time (s)': Average execution time in seconds

    Examples:
        >>> df = aggregate_time('time_benchmark/')
        >>> df.head()
    """
    # Convert to Path if string
    folder = Path(folder_path) if isinstance(folder_path, str) else folder_path
    
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")
    
    if not folder.is_dir():
        raise ValueError(f"Path is not a directory: {folder}")
    
    # Find all CSV files
    csv_files = list(folder.glob('*.csv'))
    
    if not csv_files:
        raise ValueError(f"No CSV files found in folder: {folder}")
    
    results = []
    
    for csv_file in csv_files:
        try:
            # Read CSV
            df = pd.read_csv(csv_file)
            
            # Check for required column
            if 'execution_time (s)' not in df.columns:
                continue  # Skip files without the required column
            
            # Compute average
            avg_time = df['execution_time (s)'].mean()
            
            # Store result with filename (without extension)
            results.append({
                'filename': csv_file.stem,
                'execution_time (s)': avg_time
            })
        except Exception as e:
            # Skip files that can't be read
            continue
    
    if not results:
        raise ValueError(f"No valid time data found in folder: {folder}")
    
    # Create DataFrame
    result_df = pd.DataFrame(results)
    
    # Save to file if output path provided
    if output_path is not None:
        output = Path(output_path) if isinstance(output_path, str) else output_path
        output.parent.mkdir(parents=True, exist_ok=True)
        result_df.to_csv(output, index=False)
    
    return result_df

