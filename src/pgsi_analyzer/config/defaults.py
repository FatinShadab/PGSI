"""
Default benchmark parameters and helpers for resolving benchmark assets.
"""
from __future__ import annotations

import os
import random
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

from ..platform.paths import resolve_data_path

DNA_ENV_VAR = "PGSI_ANALYZER_DNA_FILE"


def _resolve_dna_path() -> Path:
    """
    Resolve the DNA sequence file for the K-Nucleotide benchmark.

    Order of precedence:
    1. Environment variable PGSI_ANALYZER_DNA_FILE (must exist)
    2. Data directory resolved via resolve_data_path() / "K-Nucleotide"/"dna.txt"
    3. Repository benchmarks fallback: ../benchmarks/K-Nucleotide/dna.txt
    """
    env_path = os.getenv(DNA_ENV_VAR)
    if env_path:
        candidate = Path(env_path).expanduser()
        if candidate.exists():
            return candidate
        raise FileNotFoundError(
            f"{DNA_ENV_VAR} is set but file does not exist: {candidate}"
        )

    # Preferred data location (user/configurable data dir)
    data_candidate = resolve_data_path() / "K-Nucleotide" / "dna.txt"
    if data_candidate.exists():
        return data_candidate

    # Fallback to repository benchmarks directory (developer convenience)
    repo_root = Path(__file__).resolve().parents[2]
    repo_candidate = repo_root / "benchmarks" / "K-Nucleotide" / "dna.txt"
    if repo_candidate.exists():
        return repo_candidate

    raise FileNotFoundError(
        "dna.txt not found. Set PGSI_ANALYZER_DNA_FILE to the DNA sequence file "
        "or place dna.txt in the data directory (K-Nucleotide) or benchmarks/K-Nucleotide."
    )


def _build_defaults() -> Dict[str, Any]:
    dna_path = _resolve_dna_path()

    return {
        "hanoi": {
            "test_n": 50,
            "n": 18,
        },
        "strassen": {
            "test_n": 50,
            "A": [[random.randint(0, 10) for _ in range(128)] for _ in range(128)],
            "B": [[random.randint(0, 10) for _ in range(128)] for _ in range(128)],
        },
        "spectral-norm": {
            "test_n": 50,
            "iterations": 1000,
            "matrix": [[random.randint(0, 10) for _ in range(128)] for _ in range(128)],
        },
        "sieve": {
            "test_n": 50,
            "n": 10_000_000,
        },
        "n-queens": {
            "test_n": 50,
            "n": 12,
        },
        "reverse_complement": {
            "test_n": 50,
            "dna_sequence": "ATGC" * 10_000_000,
        },
        "binary-trees": {
            "test_n": 50,
            "depth": 18,
        },
        "knn": {
            "test_n": 50,
            "num_samples": 10_000,
            "num_features": 100,
            "k": 5,
        },
        "pi_digits": {
            "test_n": 50,
            "iterations": 1000,
        },
        "K_Nucleotide": {
            "test_n": 50,
            "k": 6,
            "nucleotide_sequence_file": dna_path,
        },
        "fannkuch_redux": {
            "test_n": 50,
            "n": 10,
            "perm": list(range(1, 11)),
        },
        "fasta": {
            "test_n": 50,
            "k": 8,
            "query_sequence": "ACGTAGCTAGCTAGTACGATCGATCGTACGATCGATCGTAGCTAGCTGACGATCGATCGTACGATCGTAGCTAGCATCG",
            "target_sequence": "GATCGATCGTAGCTAGCATCGATCGTACGATCGATCGTAGCTAGCTGACGATCGATCGTACGATCGTAGCTAGCATCG",
        },
        "mandelbrot": {
            "test_n": 50,
            "width": 100,
            "height": 100,
            "max_iter": 100,
            "x_min": -2.0,
            "x_max": 1.0,
            "y_min": -1.5,
            "y_max": 1.5,
        },
        "nbody": {
            "test_n": 50,
            "num_bodies": 100,
            "time_steps": 1000,
            "G": 6.67430e-11,
            "dt": 1000,
            "bodies": [
                {
                    "mass": random.uniform(1e24, 1e30),
                    "position": [random.uniform(-1e11, 1e11) for _ in range(3)],
                    "velocity": [random.uniform(-1e4, 1e4) for _ in range(3)],
                }
                for _ in range(100)
            ],
        },
        "regex_redux": {
            "file_path": "input_fasta.txt",
            "test_n": 50,
        },
    }


DEFAULT_PARAMS: Dict[str, Any] = _build_defaults()


def get_default_params(algorithm_name: str) -> Dict[str, Any]:
    """
    Return a copy of the default parameters for the given algorithm.
    """
    if algorithm_name not in DEFAULT_PARAMS:
        raise KeyError(f"Unknown algorithm '{algorithm_name}'. Available: {list(DEFAULT_PARAMS.keys())}")
    return deepcopy(DEFAULT_PARAMS[algorithm_name])


__all__ = ["DEFAULT_PARAMS", "get_default_params", "DNA_ENV_VAR"]

