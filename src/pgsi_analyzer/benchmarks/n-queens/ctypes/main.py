import sys
import os
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv

from pgsi_analyzer.config import DEFAULT_PARAMS as __default__, get_measurement_runs

import ctypes
from ctypes import POINTER, c_int, byref

# Load shared library (name matches builder: lib{first_c_stem}.so)
_bench_dir = Path(__file__).resolve().parent
_c_files = sorted(_bench_dir.glob("*.c"))
_stem = _c_files[0].stem if _c_files else "n_queens"
_lib_path = _bench_dir / (f"{_stem}.dll" if os.name == "nt" else f"lib{_stem}.so")
lib = ctypes.CDLL(str(_lib_path))

# Setup return and argument types
lib.solve_n_queens.argtypes = [c_int, POINTER(POINTER(POINTER(POINTER(c_int))))]
lib.solve_n_queens.restype = c_int

lib.free_solutions.argtypes = [POINTER(POINTER(POINTER(c_int))), c_int, c_int]

def solve_n_queens(n):
    out_solutions = POINTER(POINTER(POINTER(c_int)))()
    count = lib.solve_n_queens(n, byref(out_solutions))

    result = []
    for i in range(count):
        solution = []
        for j in range(n):
            row = [out_solutions[i][j][k] for k in range(n)]
            solution.append(row)
        result.append(solution)

    # Free C memory
    lib.free_solutions(out_solutions, count, n)

    return result

def main(n):
    solutions = solve_n_queens(n)
    print(f"Total solutions: {len(solutions)}")
    for sol in solutions:
        for row in sol:
            print(" ".join("Q" if x else "." for x in row))
        print()
        
@measure_energy_to_csv(n=get_measurement_runs("n-queens"), csv_filename="n_queens_ctypes")
def run_energy_benchmark(n: int) -> None:
    main(n)

@measure_time_to_csv(n=get_measurement_runs("n-queens"), csv_filename="n_queens_ctypes")
def run_time_benchmark(n: int) -> None:
    main(n)


if __name__ == "__main__":
    N = __default__["n-queens"]["n"]
   
    # Run the energy benchmark
    run_energy_benchmark(N)
    # Run the time benchmark
    run_time_benchmark(N)
