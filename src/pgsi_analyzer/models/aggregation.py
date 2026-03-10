"""
Energy and time aggregation from raw measurement logs.

This module provides functions to aggregate energy and time measurements
from raw CSV logs, computing averages across multiple runs.
"""

import re
import pandas as pd
from pathlib import Path
from typing import Union, Optional, List

# Allowed filename patterns for audit (strict regex; partial/temp files excluded)
ALLOWED_ENERGY_CSV_PATTERN = re.compile(r"^energy_.*\.csv$")
ALLOWED_TIME_CSV_PATTERN = re.compile(r"^time_.*\.csv$")
# Partial/temp files to ignore (do not match *.csv.tmp, *.csv.bak, etc.)
PARTIAL_CSV_SUFFIXES = (".csv.tmp", ".csv.bak", ".csv.part", ".csv~")


def _is_partial_or_temp(path: Path) -> bool:
    """True if path looks like a partial/temp file (e.g. file.csv.tmp)."""
    name = path.name
    return any(name.endswith(s) for s in PARTIAL_CSV_SUFFIXES)


def _allowed_energy_csv_files(folder: Path) -> List[Path]:
    """Return paths to CSV files that match ^energy_.*\\.csv$ and are not partial/temp."""
    out = []
    for p in folder.iterdir():
        if not p.is_file():
            continue
        if _is_partial_or_temp(p):
            continue
        if ALLOWED_ENERGY_CSV_PATTERN.match(p.name):
            out.append(p)
    return out


def _allowed_time_csv_files(folder: Path) -> List[Path]:
    """Return paths to CSV files that match ^time_.*\\.csv$ and are not partial/temp."""
    out = []
    for p in folder.iterdir():
        if not p.is_file():
            continue
        if _is_partial_or_temp(p):
            continue
        if ALLOWED_TIME_CSV_PATTERN.match(p.name):
            out.append(p)
    return out


def stress_test_aggregation_regex(
    folder_path: Union[str, Path],
    kind: str = "energy",
) -> dict:
    """
    Regex stress test: attempt to process folder with various filenames.
    Returns counts of accepted, rejected (wrong pattern), and skipped (partial/temp).
    """
    folder = Path(folder_path) if isinstance(folder_path, str) else folder_path
    if not folder.exists() or not folder.is_dir():
        return {"accepted": 0, "rejected_pattern": 0, "skipped_partial": 0}
    accepted, rejected, skipped = 0, 0, 0
    for p in folder.iterdir():
        if not p.is_file():
            continue
        if _is_partial_or_temp(p):
            skipped += 1
            continue
        if kind == "energy":
            if ALLOWED_ENERGY_CSV_PATTERN.match(p.name):
                accepted += 1
            elif p.suffix == ".csv":
                rejected += 1
        else:
            if ALLOWED_TIME_CSV_PATTERN.match(p.name):
                accepted += 1
            elif p.suffix == ".csv":
                rejected += 1
    return {"accepted": accepted, "rejected_pattern": rejected, "skipped_partial": skipped}


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
    
    # Only process files matching ^energy_.*\\.csv$ (exclude partial/temp)
    csv_files = _allowed_energy_csv_files(folder)
    
    if not csv_files:
        raise ValueError(f"No valid energy CSV files found in folder: {folder}")
    
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
            
            # Preserve methodology: use mode (most common) per file
            methodology = "unknown"
            if "methodology" in df.columns:
                mode_vals = df["methodology"].dropna().mode()
                methodology = mode_vals.iloc[0] if len(mode_vals) > 0 else (
                    df["methodology"].iloc[0] if len(df) > 0 else "unknown"
                )
                if pd.isna(methodology):
                    methodology = "unknown"
            
            # Store result with filename (without extension) and methodology
            results.append({
                'filename': csv_file.stem,
                'average_package (uJ)': avg_energy,
                'methodology': methodology,
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
    
    # Only process files matching ^time_.*\\.csv$ (exclude partial/temp)
    csv_files = _allowed_time_csv_files(folder)
    
    if not csv_files:
        raise ValueError(f"No valid time CSV files found in folder: {folder}")
    
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

