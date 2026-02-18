import ctypes
import sys
import time
import os
import tempfile
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv

from pgsi_analyzer.config import DEFAULT_PARAMS as __default__, get_measurement_runs

# Load shared library (name matches builder: lib{first_c_stem}.so)
_bench_dir = Path(__file__).resolve().parent
_c_files = sorted(_bench_dir.glob("*.c"))
_stem = _c_files[0].stem if _c_files else "regex_redux"
_lib_path = _bench_dir / (f"{_stem}.dll" if os.name == "nt" else f"lib{_stem}.so")
lib = ctypes.CDLL(str(_lib_path))

# Define argument types for the function
lib.regex_redux.argtypes = [ctypes.c_char_p]
lib.regex_redux.restype = None

# Minimal dummy FASTA when no input file is provided (C library requires a valid path)
_DUMMY_FASTA_CONTENT = "agggtaaa|tttaccct" * 100


def run_regex_redux(file_path: str):
    """Run regex-redux; if file_path is empty or missing, use a temporary dummy FASTA file."""
    path = file_path
    if not path or not os.path.isfile(path):
        fd, path = tempfile.mkstemp(suffix=".fasta", prefix="regex_redux_")
        try:
            os.write(fd, _DUMMY_FASTA_CONTENT.encode("utf-8"))
        finally:
            os.close(fd)
        try:
            print("Running Regex Redux from C:")
            lib.regex_redux(path.encode("utf-8"))
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
        return
    print("Running Regex Redux from C:")
    lib.regex_redux(path.encode("utf-8"))
    
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
    file_path = __default__["regex_redux"].get("file_path", "") or ""

    # You can change this to driver(file_path) if you want plain output
    run_energy_benchmark(file_path)
    run_time_benchmark(file_path)
