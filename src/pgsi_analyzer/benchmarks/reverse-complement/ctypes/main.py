import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv

from pgsi_analyzer.config import DEFAULT_PARAMS as __default__, get_measurement_runs

import ctypes
from ctypes import c_char_p, POINTER, c_char

# Load the shared library
lib = ctypes.CDLL('./libreverse.so')

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
