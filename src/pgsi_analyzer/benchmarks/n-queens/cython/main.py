import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv

from pgsi_analyzer.config import DEFAULT_PARAMS as __default__, get_measurement_runs

from raw import n_queens

def print_board(board):
    """
    Prints the N-Queens board in a human-readable format.
    
    Args:
        board (list): The N-Queens board to print.
    """
    for row in board:
        print(" ".join("Q" if cell else "." for cell in row))
    print()

def main(n):
    """
    Main function to solve the N-Queens problem.
    
    Args:
        n (int): The size of the board (N).
    
    Returns:
        list: A list of all possible solutions.
    """
    solutions = n_queens(n)
    print(f"Total solutions for {n}-Queens: {len(solutions)}")
    for sol in solutions:
        print_board(sol)
        
@measure_energy_to_csv(n=get_measurement_runs("n-queens"), csv_filename="n_queens_cython")
def run_energy_benchmark(n: int) -> None:
    main(n)

@measure_time_to_csv(n=get_measurement_runs("n-queens"), csv_filename="n_queens_cython")
def run_time_benchmark(n: int) -> None:
    main(n)

if __name__ == "__main__":
    N = __default__["n-queens"]["n"]
   
    # Run the energy benchmark
    run_energy_benchmark(N)
    # Run the time benchmark
    run_time_benchmark(N)

