import os
from pathlib import Path

from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv
from pgsi_analyzer.config import DEFAULT_PARAMS as __default__, get_measurement_runs

import ctypes

# Load the shared library (names must match benchmark/builder.py build_ctypes)
_bench_dir = Path(__file__).resolve().parent
_c_files = sorted(_bench_dir.glob("*.c"))
_stem = _c_files[0].stem if _c_files else "binary_tree"
_lib_path = _bench_dir / (f"{_stem}.dll" if os.name == "nt" else f"lib{_stem}.so")
lib = ctypes.CDLL(str(_lib_path))

# Define TreeNode struct (forward declaration)
class TreeNode(ctypes.Structure):
    pass

TreeNodePtr = ctypes.POINTER(TreeNode)

TreeNode._fields_ = [("left", TreeNodePtr),
                     ("right", TreeNodePtr)]

# Set argument and return types
lib.make_tree.argtypes = [ctypes.c_int]
lib.make_tree.restype = TreeNodePtr

lib.check_tree.argtypes = [TreeNodePtr]
lib.check_tree.restype = ctypes.c_int

lib.free_tree.argtypes = [TreeNodePtr]
lib.free_tree.restype = None

def run_binary_trees(n: int):
    min_depth = 4
    max_depth = max(min_depth + 2, n)
    stretch_depth = max_depth + 1

    # Stretch tree
    stretch_tree = lib.make_tree(stretch_depth)
    print(f"stretch tree of depth {stretch_depth}\t check: {lib.check_tree(stretch_tree)}")
    lib.free_tree(stretch_tree)

    # Long-lived tree
    long_lived_tree = lib.make_tree(max_depth)

    for depth in range(min_depth, max_depth + 1, 2):
        iterations = 2 ** (max_depth - depth + min_depth)
        check = 0
        for _ in range(iterations):
            temp_tree = lib.make_tree(depth)
            check += lib.check_tree(temp_tree)
            lib.free_tree(temp_tree)
        print(f"{iterations}\t trees of depth {depth}\t check: {check}")

    print(f"long lived tree of depth {max_depth}\t check: {lib.check_tree(long_lived_tree)}")
    lib.free_tree(long_lived_tree)

@measure_energy_to_csv(n=get_measurement_runs("binary-trees"), csv_filename="binary_trees_ctypes")
def run_energy_benchmark(n: int) -> None:
    run_binary_trees(n)

@measure_time_to_csv(n=get_measurement_runs("binary-trees"), csv_filename="binary_trees_ctypes")
def run_time_benchmark(n: int) -> None:
    run_binary_trees(n)


if __name__ == "__main__":
    n = __default__["binary-trees"]["depth"]
    
    run_energy_benchmark(n)
    run_time_benchmark(n)
