import re
from typing import List, Tuple
import time
import tempfile
from raw import regex_redux
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv

from pgsi_analyzer.config import DEFAULT_PARAMS as __default__, get_measurement_runs

# Minimal dummy FASTA when no input file is provided (Cython raw reads from path)
_DUMMY_FASTA_CONTENT = "agggtaaa|tttaccct" * 100


def _resolve_file_path(file_path: str) -> str:
    """Return a valid path: use file_path if it exists, else a temp file with dummy content."""
    if file_path and os.path.isfile(file_path):
        return file_path
    fd, path = tempfile.mkstemp(suffix=".fasta", prefix="regex_redux_")
    try:
        os.write(fd, _DUMMY_FASTA_CONTENT.encode("utf-8"))
    finally:
        os.close(fd)
    return path


@measure_time_to_csv(n=get_measurement_runs("regex_redux"), csv_filename="regex_redux_cython")
def run_time_benchmark(file_path: str) -> None:
    """
    Measure and log the time it takes to run the Regex-Redux benchmark.
    """
    path = _resolve_file_path(file_path)
    try:
        regex_redux(path)
    finally:
        if path != file_path:
            try:
                os.unlink(path)
            except OSError:
                pass
    time.sleep(0.01)

@measure_energy_to_csv(n=get_measurement_runs("regex_redux"), csv_filename="regex_redux_cython")
def run_energy_benchmark(file_path: str) -> None:
    """
    Measure and log the energy consumption of the Regex-Redux benchmark.
    """
    path = _resolve_file_path(file_path)
    try:
        regex_redux(path)
    finally:
        if path != file_path:
            try:
                os.unlink(path)
            except OSError:
                pass
    time.sleep(0.01)


if __name__ == "__main__":
    file_path = __default__["regex_redux"].get("file_path", "") or ""

    # You can change this to driver(file_path) if you want plain output
    run_energy_benchmark(file_path)
    run_time_benchmark(file_path)
