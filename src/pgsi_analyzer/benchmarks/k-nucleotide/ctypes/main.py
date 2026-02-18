import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv

from pgsi_analyzer.config import DEFAULT_PARAMS as __default__, get_measurement_runs

from typing import Dict

import ctypes
from ctypes import c_char_p, c_int, POINTER, Structure

# Adjust for your platform
lib = ctypes.CDLL('./libkmer.so')  # or libkmer.dylib / kmer.dll

class KmerCount(Structure):
    _fields_ = [("kmer", c_char_p), ("count", c_int)]

class KmerMap(Structure):
    _fields_ = [("data", POINTER(KmerCount)), ("size", c_int), ("capacity", c_int)]

lib.count_kmers.restype = POINTER(KmerMap)
lib.count_kmers.argtypes = [c_char_p, c_int]

# Minimal dummy DNA when no input file is provided
_DUMMY_DNA_SEQUENCE = "ACGT" * 500


def read_sequence(file_path: str) -> str:
    """Reads the DNA sequence from a file, ignoring headers.
    If file_path is empty or the file is missing, returns a minimal dummy sequence.
    
    Args:
        file_path (str): Path to the input file containing the DNA sequence.
    
    Returns:
        str: The processed DNA sequence as a single string.
    """
    if not file_path or not os.path.isfile(file_path):
        return _DUMMY_DNA_SEQUENCE
    sequence: list[str] = []
    with open(file_path, 'r') as file:
        for line in file:
            if not line.startswith('>'):
                sequence.append(line.strip().upper())  # Convert to uppercase for consistency
    return ''.join(sequence)

def print_kmer_frequencies(kmers: Dict[str, int]) -> None:
    """Prints k-mer frequencies sorted by frequency (descending), then alphabetically.
    
    Args:
        kmers (Dict[str, int]): Dictionary of k-mer counts.
    """
    sorted_kmers = sorted(kmers.items(), key=lambda item: (-item[1], item[0]))
    for kmer, freq in sorted_kmers:
        print(f"{kmer}: {freq}")


def count_kmers(sequence: str, k: int):
    seq_bytes = sequence.encode('utf-8')
    result = lib.count_kmers(seq_bytes, k)
    kmer_map = result.contents

    counts = {}
    for i in range(kmer_map.size):
        kmer = kmer_map.data[i].kmer.decode('utf-8')
        count = kmer_map.data[i].count
        counts[kmer] = count

    return counts

def main() -> None:
    """Main function to execute the K-Nucleotide frequency analysis."""    
    file_path: str = __default__["K_Nucleotide"].get("nucleotide_sequence_file", "") or ""
    k: int = __default__["K_Nucleotide"].get("k", 2)
    
    sequence: str = read_sequence(file_path)
    kmers: Dict[str, int] = count_kmers(sequence, k)
    print_kmer_frequencies(kmers)

@measure_energy_to_csv(n=get_measurement_runs("K_Nucleotide"), csv_filename="K_Nucleotide_ctypes")
def run_energy_benchmark() -> None:
    main()
    time.sleep(0.01)

@measure_time_to_csv(n=get_measurement_runs("K_Nucleotide"), csv_filename="K_Nucleotide_ctypes")
def run_time_benchmark() -> None:
    main()
    time.sleep(0.01)


if __name__ == "__main__":
    run_energy_benchmark()
    run_time_benchmark()
