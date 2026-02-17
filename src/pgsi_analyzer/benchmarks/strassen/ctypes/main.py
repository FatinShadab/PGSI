import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

import ctypes
import numpy as np
from pgsi_analyzer.config import DEFAULT_PARAMS as __default__, get_measurement_runs
import argparse
from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv


from typing import List

# Load the shared library
lib = ctypes.CDLL("./libstrassen.so")  # or "strassen.dll" on Windows

# Define the function signature
lib.strassen.argtypes = [
    ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int),
    ctypes.c_int
]

def flatten(matrix: List[List[int]]) -> np.ndarray:
    return np.array(matrix, dtype=np.int32).flatten()

def strassen_ctypes(A: List[List[int]], B: List[List[int]]) -> List[List[int]]:
    n = len(A)
    flat_A = flatten(A)
    flat_B = flatten(B)
    flat_C = np.zeros((n * n,), dtype=np.int32)

    lib.strassen(
        flat_A.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
        flat_B.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
        flat_C.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
        ctypes.c_int(n)
    )

    return flat_C.reshape((n, n)).tolist()

def main(A, B):
    C = strassen_ctypes(A, B)
    print("Resultant matrix C:")
    for row in C:
        print(row)

@measure_energy_to_csv(n=get_measurement_runs("strassen"), csv_filename="strassen_ctypes")
def run_energy_benchmark(A: List[List[int]], B: List[List[int]]) -> None:
    """
    Run the energy benchmark for Strassen's matrix multiplication.
    
    Args:
        A (List[List[int]]): First matrix.
        B (List[List[int]]): Second matrix.
    """
    main(A, B)
    
@measure_time_to_csv(n=get_measurement_runs("strassen"), csv_filename="strassen_ctypes")
def run_time_benchmark(A: List[List[int]], B: List[List[int]]) -> None:
    """
    Run the time benchmark for Strassen's matrix multiplication.
    
    Args:
        A (List[List[int]]): First matrix.
        B (List[List[int]]): Second matrix.
    """
    main(A, B)

if __name__ == "__main__":
    A = __default__["strassen"]["A"]
    B = __default__["strassen"]["B"]
    
    # Run the benchmarks
    run_energy_benchmark(A, B)
    run_time_benchmark(A, B)
