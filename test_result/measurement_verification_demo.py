"""
Verification demo script for measurement modules.

This script demonstrates the functionality of the measurement decorators
and can be run to verify the implementation.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from pgsi_analyzer.measurement import measure_time_to_csv, measure_energy_to_csv

def demo_time_measurement():
    """Demonstrate time measurement decorator."""
    print("=" * 60)
    print("Time Measurement Decorator Demo")
    print("=" * 60)
    
    with TemporaryDirectory() as tmpdir:
        folder_path = Path(tmpdir) / "time_demo"
        
        @measure_time_to_csv(n=3, csv_filename="demo_time", folder_name=folder_path)
        def sample_function(x, y):
            """A sample function that adds two numbers."""
            return x + y
        
        result = sample_function(5, 3)
        print(f"Function result: {result}")
        print(f"Output folder: {folder_path}")
        
        csv_file = folder_path / "demo_time.csv"
        json_file = folder_path / "system_info.json"
        
        if csv_file.exists():
            print(f"[OK] CSV file created: {csv_file}")
            with csv_file.open('r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"   CSV has {len(lines)} lines (including header)")
        else:
            print("[ERROR] CSV file not created")
        
        if json_file.exists():
            print(f"[OK] System info JSON created: {json_file}")
        else:
            print("[ERROR] System info JSON not created")
    
    print()

def demo_energy_measurement():
    """Demonstrate energy measurement decorator (error case on Windows)."""
    print("=" * 60)
    print("Energy Measurement Decorator Demo")
    print("=" * 60)
    
    @measure_energy_to_csv(n=1, csv_filename="demo_energy")
    def sample_function():
        return 42
    
    try:
        result = sample_function()
        print(f"Function result: {result}")
        print("[OK] Energy measurement worked (Linux/Intel with pyRAPL)")
    except RuntimeError as e:
        print(f"[EXPECTED] Energy measurement not available: {e}")
        print("   This is expected on Windows/macOS or without pyRAPL")
    
    print()

def main():
    print()
    print("Measurement Modules - Verification Demo")
    print("=" * 60)
    print()
    
    # Time measurement (works on all platforms)
    demo_time_measurement()
    
    # Energy measurement (Linux/Intel only)
    demo_energy_measurement()
    
    print("=" * 60)
    print("[OK] Measurement module verification complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()

