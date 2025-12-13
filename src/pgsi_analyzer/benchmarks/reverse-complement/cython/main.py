import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv

from pgsi_analyzer.config import DEFAULT_PARAMS as __default__

from raw import reverse_complement

@measure_energy_to_csv(n=__default__["reverse_complement"]["test_n"], csv_filename="reverse_complement_cython")
def run_energy_benchmark(dna_sequence: str) -> None:
    reverse_complement(dna_sequence.encode("utf-8"))
    
@measure_time_to_csv(n=__default__["reverse_complement"]["test_n"], csv_filename="reverse_complement_cython")
def run_time_benchmark(dna_sequence: str) -> None:
    reverse_complement(dna_sequence.encode("utf-8"))


if __name__ == "__main__":
    # Example DNA sequence
    dna = __default__["reverse_complement"]["dna_sequence"]
    
    # Run benchmarks
    run_energy_benchmark(dna)
    run_time_benchmark(dna)
