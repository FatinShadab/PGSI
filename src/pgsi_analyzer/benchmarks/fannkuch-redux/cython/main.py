from raw import fannkuch_redux
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv

from pgsi_analyzer.config import DEFAULT_PARAMS as __default__, get_measurement_runs


def driver(n: int) -> None:
    max_flips, count_max_flips = fannkuch_redux(n)
    print(f"Max flips: {max_flips}")
    print(f"Count of max flips: {count_max_flips}")

@measure_energy_to_csv(n=get_measurement_runs("fannkuch_redux"), csv_filename="fannkuch_redux_cython")
def run_energy_benchmark(n: int) -> None:
    driver(n)

@measure_time_to_csv(n=get_measurement_runs("fannkuch_redux"), csv_filename="fannkuch_redux_cython")
def run_time_benchmark(n: int) -> None:
    driver(n)

    
if __name__ == "__main__":
    n = __default__["fannkuch_redux"].get("n", 7)
    run_energy_benchmark(n)
    run_time_benchmark(n)
