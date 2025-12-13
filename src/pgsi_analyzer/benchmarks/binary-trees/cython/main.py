from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv
from pgsi_analyzer.config import DEFAULT_PARAMS as __default__

import raw  # Import the compiled Cython module

@measure_energy_to_csv(n=__default__["binary-trees"]["test_n"], csv_filename="binary_trees_cython")
def run_energy_benchmark(n: int) -> None:
    raw.main(n)

@measure_time_to_csv(n=__default__["binary-trees"]["test_n"], csv_filename="binary_trees_cython")
def run_time_benchmark(n: int) -> None:
    raw.main(n)


if __name__ == "__main__":
    n = __default__["binary-trees"]["depth"]
    
    run_energy_benchmark(n)
    run_time_benchmark(n)
