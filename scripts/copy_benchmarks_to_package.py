"""
Script to copy benchmarks from repository root to package structure.

This script normalizes benchmark directory names and copies them to
src/pgsi_analyzer/benchmarks/ with the correct structure.
"""

import sys
import shutil
from pathlib import Path

# Mapping from repository names to normalized package names
ALGORITHM_MAPPING = {
    "Binary-trees": "binary-trees",
    "Fannkuch-Redux": "fannkuch-redux",
    "FASTA": "fasta",
    "K-Nucleotide": "k-nucleotide",
    "KNN": "knn",
    "Mandelbrot": "mandelbrot",
    "N-Body": "n-body",
    "N-Queens": "n-queens",
    "Pi-Digits": "pi-digits",
    "Regex-Redux": "regex-redux",
    "Reverse-Complement": "reverse-complement",
    "Sieve-of-Eratosthenes": "sieve",
    "Spectral-Norm": "spectral-norm",
    "Strassen": "strassen",
    "Towers-of-Hanoi": "hanoi",
}

# Method name mapping
METHOD_MAPPING = {
    "Cpython": "cpython",
    "PyPy": "pypy",
    "Cython": "cython",
    "Ctypes": "ctypes",
    "py_compile": "py_compile",
}


def copy_benchmarks():
    """Copy benchmarks from repository to package structure."""
    repo_root = Path(__file__).parent.parent
    benchmarks_src = repo_root / "benchmarks"
    benchmarks_dst = repo_root / "src" / "pgsi_analyzer" / "benchmarks"
    
    if not benchmarks_src.exists():
        print(f"❌ Source benchmarks directory not found: {benchmarks_src}")
        return False
    
    benchmarks_dst.mkdir(parents=True, exist_ok=True)
    
    print(f"Copying benchmarks from {benchmarks_src} to {benchmarks_dst}")
    print()
    
    copied_count = 0
    
    for algo_src_name, algo_dst_name in ALGORITHM_MAPPING.items():
        algo_src = benchmarks_src / algo_src_name
        if not algo_src.exists():
            print(f"⚠ Skipping {algo_src_name} (not found)")
            continue
        
        algo_dst = benchmarks_dst / algo_dst_name
        algo_dst.mkdir(parents=True, exist_ok=True)
        
        print(f"Copying {algo_src_name} → {algo_dst_name}")
        
        # Copy each method
        for method_src_name, method_dst_name in METHOD_MAPPING.items():
            method_src = algo_src / method_src_name
            if not method_src.exists():
                continue
            
            method_dst = algo_dst / method_dst_name
            if method_dst.exists():
                shutil.rmtree(method_dst)
            
            shutil.copytree(method_src, method_dst)
            copied_count += 1
            print(f"  ✓ {method_src_name} → {method_dst_name}")
        
        # Copy README if exists
        readme_src = algo_src / "README.md"
        if readme_src.exists():
            shutil.copy2(readme_src, algo_dst / "README.md")
        
        # Copy special files (e.g., dna.txt for k-nucleotide)
        for special_file in ["dna.txt", "input_fasta.txt"]:
            special_src = algo_src / special_file
            if special_src.exists():
                shutil.copy2(special_src, algo_dst / special_file)
    
    print()
    print(f"✅ Copied {copied_count} benchmark method directories")
    print(f"   Destination: {benchmarks_dst}")
    return True


if __name__ == "__main__":
    success = copy_benchmarks()
    sys.exit(0 if success else 1)

