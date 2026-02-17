import ctypes
import sys
import time
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv

from pgsi_analyzer.config import DEFAULT_PARAMS as __default__, get_measurement_runs


# Load the shared library
lib = ctypes.CDLL("./libregexredux.so")  # Or "regexredux.dll" on Windows

# Define argument types for the function
lib.regex_redux.argtypes = [ctypes.c_char_p]
lib.regex_redux.restype = None

def run_regex_redux(file_path: str):
    print("Running Regex Redux from C:")
    lib.regex_redux(file_path.encode('utf-8'))
    
@measure_time_to_csv(n=get_measurement_runs("regex_redux"), csv_filename="regex_redux_ctypes")
def run_time_benchmark(file_path: str) -> None:
    """
    Measure and log the time it takes to run the Regex-Redux benchmark.
    """
    run_regex_redux(file_path)
    time.sleep(0.01)

@measure_energy_to_csv(n=get_measurement_runs("regex_redux"), csv_filename="regex_redux_ctypes")
def run_energy_benchmark(file_path: str) -> None:
    """
    Measure and log the energy consumption of the Regex-Redux benchmark.
    """
    run_regex_redux(file_path)
    time.sleep(0.01)


if __name__ == "__main__":
    file_path = __default__["regex_redux"]["file_path"]

    # You can change this to driver(file_path) if you want plain output
    run_energy_benchmark(file_path)
    run_time_benchmark(file_path)
