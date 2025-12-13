import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv

from pgsi_analyzer.config import DEFAULT_PARAMS as __default__

from raw import compute_pi_gauss_legendre

@measure_energy_to_csv(n=__default__["pi_digits"]["test_n"], csv_filename="pi_digits_cython")
def run_energy_benchmark(iterations: int) -> None:
    pi_approx : float = compute_pi_gauss_legendre(iterations)
    print(f"Computed Pi: {pi_approx}")
    time.sleep(0.01)

@measure_time_to_csv(n=__default__["pi_digits"]["test_n"], csv_filename="pi_digits_cython")
def run_time_benchmark(iterations: int) -> None:
    pi_approx : float = compute_pi_gauss_legendre(iterations)
    print(f"Computed Pi: {pi_approx}")
    time.sleep(0.01)


if __name__ == "__main__":
    ITERATIONS = __default__["pi_digits"]["iterations"]
    
    # Run benchmarks
    run_energy_benchmark(ITERATIONS)
    run_time_benchmark(ITERATIONS)
