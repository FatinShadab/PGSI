import sys
import os
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv

from pgsi_analyzer.config import DEFAULT_PARAMS as __default__, get_measurement_runs

import ctypes

# Load shared library (name matches builder: lib{first_c_stem}.so)
_bench_dir = Path(__file__).resolve().parent
_c_files = sorted(_bench_dir.glob("*.c"))
_stem = _c_files[0].stem if _c_files else "fannkuch"
_lib_path = _bench_dir / (f"{_stem}.dll" if os.name == "nt" else f"lib{_stem}.so")
lib = ctypes.CDLL(str(_lib_path))

# Prepare argument types
lib.fannkuch_redux.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]

# Prepare return values
max_flips = ctypes.c_int()
count_max_flips = ctypes.c_int()

def driver(n: int) -> None:
    """
    Driver function to call the C function and print results.
    
    :param n: The size of the permutation.
    """
    # Call the C function
    lib.fannkuch_redux(n, ctypes.byref(max_flips), ctypes.byref(count_max_flips))
    
    print(f"Max flips: {max_flips.value}")
    print(f"Count of max flips: {count_max_flips.value}")
    
    
@measure_energy_to_csv(n=get_measurement_runs("fannkuch_redux"), csv_filename="fannkuch_redux_ctypes")
def run_energy_benchmark(n: int) -> None:
    driver(n)

@measure_time_to_csv(n=get_measurement_runs("fannkuch_redux"), csv_filename="fannkuch_redux_ctypes")
def run_time_benchmark(n: int) -> None:
    driver(n)
    

if __name__ == "__main__":
    n = __default__["fannkuch_redux"].get("n", 7)
    run_energy_benchmark(n)
    run_time_benchmark(n)
