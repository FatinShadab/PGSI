"""
Verification demo script for models module.

This script demonstrates the functionality of the models module functions
including carbon footprint, GreenScore, aggregation, and combination.
"""

import pandas as pd
from pathlib import Path
from tempfile import TemporaryDirectory

from pgsi_analyzer.models import (
    calculate_carbon_footprint,
    normalize_metrics,
    calculate_greenscore,
    aggregate_energy,
    aggregate_time,
    combine_energy_results,
    combine_time_results,
)

def demo_carbon_footprint():
    """Demonstrate carbon footprint calculation."""
    print("=" * 60)
    print("Carbon Footprint Calculation Demo")
    print("=" * 60)
    
    with TemporaryDirectory() as tmpdir:
        # Create sample energy data
        energy_data = {
            'algorithm': ['bubble_sort', 'quick_sort'],
            'cpython': [1000000, 2000000],  # μJ
            'pypy': [500000, 1500000],
        }
        energy_df = pd.DataFrame(energy_data)
        energy_path = Path(tmpdir) / "energy.csv"
        energy_df.to_csv(energy_path, index=False)
        
        print(f"Energy data saved to: {energy_path}")
        print(energy_df)
        print()
        
        # Calculate carbon footprint
        carbon_df = calculate_carbon_footprint(energy_path)
        print("Carbon footprint calculated:")
        print(carbon_df)
        print()
        
        # Save to file
        carbon_path = Path(tmpdir) / "carbon.csv"
        carbon_df = calculate_carbon_footprint(energy_path, output_path=carbon_path)
        print(f"[OK] Carbon footprint saved to: {carbon_path}")
        print()

def demo_normalization():
    """Demonstrate metric normalization."""
    print("=" * 60)
    print("Metric Normalization Demo")
    print("=" * 60)
    
    df = pd.DataFrame({
        'algorithm': ['algo1', 'algo2'],
        'cpython': [100, 200],
        'pypy': [50, 150],
    })
    
    print("Original data:")
    print(df)
    print()
    
    normalized = normalize_metrics(df)
    print("Normalized data:")
    print(normalized)
    print()

def demo_greenscore():
    """Demonstrate GreenScore calculation."""
    print("=" * 60)
    print("GreenScore Calculation Demo")
    print("=" * 60)
    
    energy_df = pd.DataFrame({
        'algorithm': ['bubble_sort', 'quick_sort'],
        'cpython': [100, 200],
        'pypy': [50, 150],
    })
    
    time_df = pd.DataFrame({
        'algorithm': ['bubble_sort', 'quick_sort'],
        'cpython': [1.0, 2.0],
        'pypy': [0.5, 1.5],
    })
    
    carbon_df = pd.DataFrame({
        'algorithm': ['bubble_sort', 'quick_sort'],
        'cpython_CO2e_g': [0.1, 0.2],
        'pypy_CO2e_g': [0.05, 0.15],
    })
    
    print("Energy data:")
    print(energy_df)
    print()
    print("Time data:")
    print(time_df)
    print()
    print("Carbon data:")
    print(carbon_df)
    print()
    
    greenscore_df = calculate_greenscore(energy_df, time_df, carbon_df)
    print("GreenScore ranking (lower is better):")
    print(greenscore_df)
    print()

def demo_aggregation():
    """Demonstrate energy and time aggregation."""
    print("=" * 60)
    print("Aggregation Demo")
    print("=" * 60)
    
    with TemporaryDirectory() as tmpdir:
        energy_folder = Path(tmpdir) / "energy"
        energy_folder.mkdir()
        
        # Create sample energy CSV files
        for i, name in enumerate(['bubble_sort_cpython', 'quick_sort_cpython']):
            df = pd.DataFrame({
                'package (uJ)': [1000000 + i*100000, 2000000 + i*100000],
            })
            (energy_folder / f"{name}.csv").write_text(df.to_csv(index=False))
        
        print(f"Created energy CSV files in: {energy_folder}")
        print()
        
        # Aggregate energy
        energy_avg = aggregate_energy(energy_folder)
        print("Aggregated energy:")
        print(energy_avg)
        print()
        
        # Aggregate time
        time_folder = Path(tmpdir) / "time"
        time_folder.mkdir()
        
        for i, name in enumerate(['bubble_sort_cpython', 'quick_sort_cpython']):
            df = pd.DataFrame({
                'execution_time (s)': [1.0 + i*0.1, 2.0 + i*0.1],
            })
            (time_folder / f"{name}.csv").write_text(df.to_csv(index=False))
        
        time_avg = aggregate_time(time_folder)
        print("Aggregated time:")
        print(time_avg)
        print()

def demo_combination():
    """Demonstrate combining results from multiple methods."""
    print("=" * 60)
    print("Combination Demo")
    print("=" * 60)
    
    with TemporaryDirectory() as tmpdir:
        # Create aggregated files in method subdirectories
        cpython_dir = Path(tmpdir) / "cpython"
        pypy_dir = Path(tmpdir) / "pypy"
        cpython_dir.mkdir()
        pypy_dir.mkdir()
        
        # Energy averages
        cpython_energy = pd.DataFrame({
            'filename': ['bubble_sort_cpython', 'quick_sort_cpython'],
            'average_package (uJ)': [1000000, 2000000],
        })
        cpython_energy.to_csv(cpython_dir / "energy_avg.csv", index=False)
        
        pypy_energy = pd.DataFrame({
            'filename': ['bubble_sort_pypy', 'quick_sort_pypy'],
            'average_package (uJ)': [500000, 1500000],
        })
        pypy_energy.to_csv(pypy_dir / "energy_avg.csv", index=False)
        
        # Combine energy results
        file_paths = [
            cpython_dir / "energy_avg.csv",
            pypy_dir / "energy_avg.csv",
        ]
        output_path = Path(tmpdir) / "energy_com.csv"
        
        combined = combine_energy_results(file_paths, output_path)
        print("Combined energy results:")
        print(combined)
        print()
        print(f"[OK] Combined results saved to: {output_path}")
        print()

def main():
    print()
    print("Models Module - Verification Demo")
    print("=" * 60)
    print()
    
    demo_carbon_footprint()
    demo_normalization()
    demo_greenscore()
    demo_aggregation()
    demo_combination()
    
    print("=" * 60)
    print("[OK] Models module verification complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()

