import sys
import os
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv

from pgsi_analyzer.config import DEFAULT_PARAMS as __default__, get_measurement_runs

import ctypes
from ctypes import c_char_p, POINTER, c_char

# Load shared library (name matches builder: lib{first_c_stem}.so)
_bench_dir = Path(__file__).resolve().parent
_c_files = sorted(_bench_dir.glob("*.c"))
_stem = _c_files[0].stem if _c_files else "reverse_comlement"
_lib_path = _bench_dir / (f"{_stem}.dll" if os.name == "nt" else f"lib{_stem}.so")
lib = ctypes.CDLL(str(_lib_path))

lib.reverse_complement.argtypes = [c_char_p]
lib.reverse_complement.restype = POINTER(c_char)
lib.free_result.argtypes = [POINTER(c_char)]      
lib.free_result.restype = None

def reverse_complement(dna: str) -> str:
    dna_bytes = dna.encode('utf-8')
    result_ptr = lib.reverse_complement(dna_bytes)
    result = ctypes.string_at(result_ptr).decode('utf-8')
    lib.free_result(result_ptr)  # Clean up the raw malloc memory
    return result

@measure_energy_to_csv(n=get_measurement_runs("reverse_complement"), csv_filename="reverse_complement_ctypes")
def run_energy_benchmark(dna: str) -> None:
    reverse_complement(dna)

@measure_time_to_csv(n=get_measurement_runs("reverse_complement"), csv_filename="reverse_complement_ctypes")
def run_time_benchmark(dna: str) -> None:
    reverse_complement(dna)


if __name__ == "__main__":
    # Example DNA sequence
    dna = __default__["reverse_complement"]["dna_sequence"]
    
    # Run benchmarks
    run_energy_benchmark(dna)
    run_time_benchmark(dna)
