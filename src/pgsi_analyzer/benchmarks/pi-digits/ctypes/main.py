import sys
import time
import os
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv

from pgsi_analyzer.config import DEFAULT_PARAMS as __default__, get_measurement_runs

import ctypes

# Load shared library (name matches builder: lib{first_c_stem}.so)
_bench_dir = Path(__file__).resolve().parent
_c_files = sorted(_bench_dir.glob("*.c"))
_stem = _c_files[0].stem if _c_files else "pi_gauss_legendre"
_lib_path = _bench_dir / (f"{_stem}.dll" if os.name == "nt" else f"lib{_stem}.so")
lib = ctypes.CDLL(str(_lib_path))

# Define return type and argument type for the function
lib.compute_pi_gauss_legendre.argtypes = [ctypes.c_int]
lib.compute_pi_gauss_legendre.restype = ctypes.c_double

def driver(iterations):
    """
    Driver function to call the C function for computing Pi using Gauss-Legendre algorithm.
    
    :param iterations: Number of iterations for the algorithm
    :return: Computed value of Pi
    """
    pi_approx : float = lib.compute_pi_gauss_legendre(iterations)
    print(f"Computed Pi: {pi_approx}")
    
    return pi_approx

@measure_energy_to_csv(n=get_measurement_runs("pi_digits"), csv_filename="pi_digits_ctypes")
def run_energy_benchmark(iterations: int) -> None:
    driver(iterations)
    time.sleep(0.01)

@measure_time_to_csv(n=get_measurement_runs("pi_digits"), csv_filename="pi_digits_ctypes")
def run_time_benchmark(iterations: int) -> None:
    driver(iterations)
    time.sleep(0.01)
    
    
if __name__ == "__main__":
    ITERATIONS = __default__["pi_digits"]["iterations"]
    
    # Run benchmarks
    run_energy_benchmark(ITERATIONS)
    run_time_benchmark(ITERATIONS)
