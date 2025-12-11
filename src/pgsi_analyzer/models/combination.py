"""
Combine energy and time results from multiple execution methods.

This module provides functions to merge aggregated results from different
execution methods (e.g., CPython, PyPy, Cython) into comparison tables.
"""

import pandas as pd
from pathlib import Path
from typing import Union, List
from collections import defaultdict

from ..utils import validate_file_path, AnalysisError


def extract_algorithm_name(full_name: str) -> str:
    """
    Extract algorithm name from full filename.

    Extracts everything before the last underscore, assuming format:
    'algorithm_method' or 'algorithm_run_method'.

    Args:
        full_name: Full filename (e.g., 'bubble_sort_cpython')

    Returns:
        Algorithm name (e.g., 'bubble_sort')

    Examples:
        >>> extract_algorithm_name('bubble_sort_cpython')
        'bubble_sort'
    """
    return '_'.join(full_name.split('_')[:-1])


def combine_energy_results(
    file_paths: List[Union[str, Path]],
    output_path: Union[str, Path]
) -> pd.DataFrame:
    """
    Merge energy results from multiple execution methods.

    Combines aggregated energy results from different methods (e.g., CPython, PyPy)
    into a single comparison table with algorithms as rows and methods as columns.

    Args:
        file_paths: List of paths to aggregated energy CSV files.
                   Method name is extracted from the parent directory name.
        output_path: Path to save the combined results CSV.

    Returns:
        DataFrame with:
        - 'algorithm' column
        - One column per method with average energy values

    Examples:
        >>> paths = [
        ...     'cpython/energy_avg.csv',
        ...     'pypy/energy_avg.csv'
        ... ]
        >>> df = combine_energy_results(paths, 'energy_com.csv')
    """
    energy_data = defaultdict(dict)  # {algorithm: {method: value}}
    
    for file_path in file_paths:
        # Convert to Path if string
        path = validate_file_path(file_path, must_exist=True)
        
        # Extract method name from parent directory
        method_name = path.parent.name
        
        # Read CSV
        df = pd.read_csv(path)
        
        if 'filename' not in df.columns or 'average_package (uJ)' not in df.columns:
            raise AnalysisError(f"CSV must contain 'filename' and 'average_package (uJ)' columns: {path}")
        
        # Process each row
        for _, row in df.iterrows():
            full_filename = row['filename']
            algorithm = extract_algorithm_name(full_filename)
            
            try:
                avg_energy = float(row['average_package (uJ)'])
                energy_data[algorithm][method_name] = avg_energy
            except (ValueError, KeyError):
                continue
    
    if not energy_data:
        raise AnalysisError("No valid energy data found in input files")
    
    # Get all unique methods
    all_methods = sorted({method for algo_data in energy_data.values() for method in algo_data})
    
    # Build DataFrame
    rows = []
    for algorithm in sorted(energy_data):
        row = {'algorithm': algorithm}
        for method in all_methods:
            row[method] = energy_data[algorithm].get(method, '')
        rows.append(row)
    
    result_df = pd.DataFrame(rows)
    
    # Save to file
    output = Path(output_path) if isinstance(output_path, str) else output_path
    output.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(output, index=False)
    
    return result_df


def combine_time_results(
    file_paths: List[Union[str, Path]],
    output_path: Union[str, Path]
) -> pd.DataFrame:
    """
    Merge execution time results from multiple execution methods.

    Combines aggregated time results from different methods (e.g., CPython, PyPy)
    into a single comparison table with algorithms as rows and methods as columns.

    Args:
        file_paths: List of paths to aggregated time CSV files.
                   Method name is extracted from the parent directory name.
        output_path: Path to save the combined results CSV.

    Returns:
        DataFrame with:
        - 'algorithm' column
        - One column per method with average execution time values

    Examples:
        >>> paths = [
        ...     'cpython/time_avg.csv',
        ...     'pypy/time_avg.csv'
        ... ]
        >>> df = combine_time_results(paths, 'time_com.csv')
    """
    time_data = defaultdict(dict)  # {algorithm: {method: time}}
    
    for file_path in file_paths:
        # Convert to Path if string
        path = validate_file_path(file_path, must_exist=True)
        
        # Extract method name from parent directory
        method_name = path.parent.name
        
        # Read CSV
        df = pd.read_csv(path)
        
        if 'filename' not in df.columns or 'execution_time (s)' not in df.columns:
            raise AnalysisError(f"CSV must contain 'filename' and 'execution_time (s)' columns: {path}")
        
        # Process each row
        for _, row in df.iterrows():
            full_filename = row['filename']
            algorithm = extract_algorithm_name(full_filename)
            
            try:
                exec_time = float(row['execution_time (s)'])
                time_data[algorithm][method_name] = exec_time
            except (ValueError, KeyError):
                continue
    
    if not time_data:
        raise AnalysisError("No valid time data found in input files")
    
    # Get all unique methods
    all_methods = sorted({method for algo_data in time_data.values() for method in algo_data})
    
    # Build DataFrame
    rows = []
    for algorithm in sorted(time_data):
        row = {'algorithm': algorithm}
        for method in all_methods:
            row[method] = time_data[algorithm].get(method, '')
        rows.append(row)
    
    result_df = pd.DataFrame(rows)
    
    # Save to file
    output = Path(output_path) if isinstance(output_path, str) else output_path
    output.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(output, index=False)
    
    return result_df

