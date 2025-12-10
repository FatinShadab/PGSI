"""
Verification demo script for cross-platform energy estimation.

This script demonstrates the functionality of the energy measurement decorator
with estimation fallback on Windows/macOS.
"""

import warnings
from pathlib import Path
from tempfile import TemporaryDirectory
from pgsi_analyzer.measurement import measure_energy_to_csv
from pgsi_analyzer.platform.detection import detect_platform

def demo_energy_estimation():
    """Demonstrate energy measurement with estimation."""
    print("=" * 60)
    print("Cross-Platform Energy Measurement Demo")
    print("=" * 60)
    print(f"Platform: {detect_platform()}")
    print()
    
    with TemporaryDirectory() as tmpdir:
        folder_path = Path(tmpdir) / "energy_demo"
        
        @measure_energy_to_csv(n=3, csv_filename="demo_energy", folder_name=folder_path)
        def sample_function(x, y):
            """A sample function that performs CPU work."""
            # Some CPU-intensive work
            result = 0
            for i in range(100000):
                result += i * x + y
            return result
        
        print("Running function with energy measurement...")
        print("(Warning about estimation is expected on Windows/macOS)")
        print()
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = sample_function(5, 3)
            
            if w:
                print(f"Warning received: {w[0].message}")
                print()
        
        print(f"Function result: {result}")
        print(f"Output folder: {folder_path}")
        print()
        
        # Check CSV file
        csv_file = folder_path / "demo_energy.csv"
        json_file = folder_path / "system_info_pyrapl.json"
        
        if csv_file.exists():
            print(f"[OK] CSV file created: {csv_file}")
            with csv_file.open('r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"   CSV has {len(lines)} lines (including header)")
                
                # Show first data row
                if len(lines) > 1:
                    print(f"   First measurement: {lines[1].strip()}")
        else:
            print("[ERROR] CSV file not created")
        
        if json_file.exists():
            print(f"[OK] System info JSON created: {json_file}")
            import json
            with json_file.open('r', encoding='utf-8') as f:
                system_info = json.load(f)
                print(f"   Measurement method: {system_info.get('measurement_method', 'N/A')}")
                if 'estimation_model' in system_info:
                    print(f"   Estimation model: {system_info['estimation_model']}")
        else:
            print("[ERROR] System info JSON not created")
    
    print()

def main():
    print()
    print("Energy Estimation - Verification Demo")
    print("=" * 60)
    print()
    
    demo_energy_estimation()
    
    print("=" * 60)
    print("[OK] Energy estimation verification complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()

