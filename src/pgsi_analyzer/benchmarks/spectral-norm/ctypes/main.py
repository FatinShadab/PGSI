import sys
import os
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv

from pgsi_analyzer.config import DEFAULT_PARAMS as __default__, get_measurement_runs

import ctypes
from typing import List

# Load shared library (name matches builder: lib{first_c_stem}.so)
_bench_dir = Path(__file__).resolve().parent
_c_files = sorted(_bench_dir.glob("*.c"))
_stem = _c_files[0].stem if _c_files else "spectralnorm"
_lib_path = _bench_dir / (f"{_stem}.dll" if os.name == "nt" else f"lib{_stem}.so")
lib = ctypes.CDLL(str(_lib_path))

# Define argument and return types
lib.spectral_norm.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int]
lib.spectral_norm.restype = ctypes.c_double

def flatten(matrix: List[List[int]]) -> List[float]:
    return [float(val) for row in matrix for val in row]

def spectral_norm(matrix: List[List[int]], iterations: int = 10) -> float:
    n = len(matrix)
    flat_matrix = flatten(matrix)
    c_matrix = (ctypes.c_double * (n * n))(*flat_matrix)
    return lib.spectral_norm(c_matrix, n, iterations)

@measure_energy_to_csv(n=get_measurement_runs("spectral-norm"), csv_filename="spectral_norm_ctypes")
def run_energy_benchmark(matrix: List[List[int]], iterations=10) -> None:
    spectral_norm(matrix, iterations)

@measure_time_to_csv(n=get_measurement_runs("spectral-norm"), csv_filename="spectral_norm_ctypes")
def run_time_benchmark(matrix: List[List[int]], iterations=10) -> None:
    spectral_norm(matrix, iterations)


if __name__ == "__main__":
    # Example matrix
    A = __default__["spectral-norm"].get("matrix", [])
    itr = __default__["spectral-norm"].get("iterations", 10)

    # Run the benchmarks
    run_energy_benchmark(A, itr)
    run_time_benchmark(A, itr)
