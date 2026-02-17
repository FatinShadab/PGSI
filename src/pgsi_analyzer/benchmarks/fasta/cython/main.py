from raw import fasta_alignment
import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv

from pgsi_analyzer.config import DEFAULT_PARAMS as __default__, get_measurement_runs

def driver(k, query, target):
    """
        Driver function to perform the alignment and print results.
    """
    
    score, alignment, aligned_q, aligned_t = fasta_alignment(query, target, k)

    print("Score:", score)
    print("Alignment starts at:", alignment)
    print("Query:", aligned_q)
    print("Target:", aligned_t)
    

# Benchmarking functions for energy
@measure_energy_to_csv(n=get_measurement_runs("fasta"), csv_filename="fasta_cython")
def run_energy_benchmark(k: int, query_sequence: str, target_sequence: str) -> None:
    driver(k, query_sequence, target_sequence)
    time.sleep(0.01)

# Benchmarking function for time
@measure_time_to_csv(n=get_measurement_runs("fasta"), csv_filename="fasta_cython")
def run_time_benchmark(k: int, query_sequence: str, target_sequence: str) -> None:
    driver(k, query_sequence, target_sequence)
    time.sleep(0.01)


if __name__ == "__main__":
    k = __default__["fasta"]["k"]
    query_sequence = __default__["fasta"]["query_sequence"]
    target_sequence = __default__["fasta"]["target_sequence"]
    
    # Run the energy benchmark
    run_energy_benchmark(k, query_sequence, target_sequence)
    # Run the time benchmark
    run_time_benchmark(k, query_sequence, target_sequence)
