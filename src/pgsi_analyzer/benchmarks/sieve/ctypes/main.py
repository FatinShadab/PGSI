import sys
import os
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv

from pgsi_analyzer.config import DEFAULT_PARAMS as __default__, get_measurement_runs

import ctypes
from typing import List

# Load shared library (name matches builder: lib{first_c_stem}.so)
_bench_dir = Path(__file__).resolve().parent
_c_files = sorted(_bench_dir.glob("*.c"))
_stem = _c_files[0].stem if _c_files else "sieve"
_lib_path = _bench_dir / (f"{_stem}.dll" if os.name == "nt" else f"lib{_stem}.so")
lib = ctypes.CDLL(str(_lib_path))

# Configure the C function
lib.sieve.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
lib.sieve.restype = ctypes.POINTER(ctypes.c_int)
lib.free_array.argtypes = [ctypes.POINTER(ctypes.c_int)]

def get_primes(n: int) -> List[int]:
    count = ctypes.c_int()
    primes_ptr = lib.sieve(n, ctypes.byref(count))
    
    if not primes_ptr:
        raise MemoryError("Failed to allocate primes")

    # Copy the result to a Python list
    primes = [primes_ptr[i] for i in range(count.value)]

    # Free C memory
    lib.free_array(primes_ptr)

    return primes

@measure_energy_to_csv(n=get_measurement_runs("sieve"), csv_filename="sieve_ctypes")
def run_energy_benchmark(n: int) -> None:
    print(f"Primes up to {n}: {get_primes(n)}")

@measure_time_to_csv(n=get_measurement_runs("sieve"), csv_filename="sieve_ctypes")
def run_time_benchmark(n: int) -> None:
    print(f"Primes up to {n}: {get_primes(n)}")


if __name__ == "__main__":
    n = __default__["sieve"]["n"]
    
    run_energy_benchmark(n)
    run_time_benchmark(n)