import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv

from raw import strassen_multiplication
from pgsi_analyzer.config import DEFAULT_PARAMS as __default__, get_measurement_runs

from typing import List

def main(A, B) -> None:
    """
    Main function to perform Strassen's matrix multiplication.
    
    Args:
        A (List[List[int]]): First matrix.
        B (List[List[int]]): Second matrix.
    """
    result = strassen_multiplication(A, B)
    for row in result:
        print(row)
        
@measure_energy_to_csv(n=get_measurement_runs("strassen"), csv_filename="strassen_cython")
def run_energy_benchmark(A: List[List[int]], B: List[List[int]]) -> None:
    """
    Run the energy benchmark for Strassen's matrix multiplication.
    
    Args:
        A (List[List[int]]): First matrix.
        B (List[List[int]]): Second matrix.
    """
    main(A, B)
    
@measure_time_to_csv(n=get_measurement_runs("strassen"), csv_filename="strassen_cython")
def run_time_benchmark(A: List[List[int]], B: List[List[int]]) -> None:
    """
    Run the time benchmark for Strassen's matrix multiplication.
    
    Args:
        A (List[List[int]]): First matrix.
        B (List[List[int]]): Second matrix.
    """
    main(A, B)


if __name__ == "__main__":
    A = __default__["strassen"].get("A", [[0]])
    B = __default__["strassen"].get("B", [[0]])
    
    # Run the benchmarks
    run_energy_benchmark(A, B)
    run_time_benchmark(A, B)
