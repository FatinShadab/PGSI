import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv

from pgsi_analyzer.config import DEFAULT_PARAMS as __default__, get_measurement_runs

from raw import driver

@measure_energy_to_csv(n=get_measurement_runs("sieve"), csv_filename="sieve_cython")
def run_energy_benchmark(n: int) -> None:
    driver(n)

@measure_time_to_csv(n=get_measurement_runs("sieve"), csv_filename="sieve_cython")
def run_time_benchmark(n: int) -> None:
    driver(n)


if __name__ == "__main__":
    n = __default__["sieve"]["n"]
    
    run_energy_benchmark(n)
    run_time_benchmark(n)