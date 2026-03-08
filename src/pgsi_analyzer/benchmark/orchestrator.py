"""
Benchmark orchestration module.

Coordinates the full benchmark execution pipeline:
1. Build benchmarks (if needed)
2. Execute benchmarks
3. Aggregate results
4. Combine methods
5. Calculate carbon
6. Calculate GreenScore

File and path logistics are delegated to ResultsCollector.
"""

import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict

from .results_collector import (
    ResultsCollector,
    ENERGY_AGGREGATED,
    TIME_AGGREGATED,
    ENERGY_COMBINED,
    TIME_COMBINED,
    CARBON_FOOTPRINT,
    GREENSCORE,
)
from ..benchmarks.registry import (
    BENCHMARKS,
    list_algorithms,
    list_methods,
    get_benchmark_path,
    validate_algorithm,
    validate_method,
)
from .builder import build_benchmark, requires_build
from .executor import execute_benchmark, AuditLogger, AUDIT_REPORT_FILENAME
from ..models import (
    aggregate_energy,
    aggregate_time,
    combine_energy_results,
    combine_time_results,
    calculate_carbon_footprint,
    calculate_greenscore,
)
from ..utils import AnalysisError, ConfigurationError
from ..config import ToolPaths


def resolve_algorithms(algorithms: List[str]) -> List[str]:
    """
    Resolve algorithm list, expanding 'all' to all available algorithms.
    
    Args:
        algorithms: List of algorithm names or ['all']
        
    Returns:
        Sorted list of algorithm names
    """
    if "all" in algorithms:
        return list_algorithms()
    
    # Validate all algorithms
    invalid = [a for a in algorithms if not validate_algorithm(a)]
    if invalid:
        raise ValueError(
            f"Invalid algorithms: {invalid}. Available: {list_algorithms()}"
        )
    
    return sorted(set(algorithms))  # Deduplicate and sort


def resolve_methods(methods: List[str], algorithm: Optional[str] = None) -> List[str]:
    """
    Resolve method list, expanding 'all' to all available methods.
    
    Args:
        methods: List of method names or ['all']
        algorithm: Optional algorithm name for validation
        
    Returns:
        List of method names in deterministic order
    """
    if "all" in methods:
        return list_methods(algorithm)
    
    # Validate methods
    if algorithm:
        invalid = [m for m in methods if not validate_method(algorithm, m)]
        if invalid:
            raise ValueError(
                f"Invalid methods for {algorithm}: {invalid}. "
                f"Available: {list_methods(algorithm)}"
            )
    else:
        valid_methods = list_methods()
        invalid = [m for m in methods if m not in valid_methods]
        if invalid:
            raise ValueError(
                f"Invalid methods: {invalid}. Available: {valid_methods}"
            )
    
    # Return in deterministic order
    valid_order = list_methods()
    return [m for m in valid_order if m in methods]


def run_benchmark_suite(
    algorithms: List[str],
    methods: List[str],
    runs: int = 50,
    output_dir: Path = None,
    carbon_intensity: float = 0.000475,
    alpha: float = 0.4,
    beta: float = 0.4,
    gamma: float = 0.2,
    tool_paths: Optional[ToolPaths] = None,
    path_sources: Optional[dict] = None,
) -> Path:
    """
    Execute full benchmark suite and generate GreenScore CSV.
    
    This is the main orchestration function that:
    1. Resolves algorithm and method lists
    2. Builds benchmarks that require compilation
    3. Executes all benchmark × method combinations
    4. Aggregates raw CSVs
    5. Combines results across methods
    6. Calculates carbon footprint
    7. Calculates GreenScore
    8. Writes final GreenScore.csv
    
    Args:
        algorithms: List of algorithm names or ['all']
        methods: List of method names or ['all']
        runs: Number of runs per benchmark (default: 50)
        output_dir: Base directory for all outputs (defaults to ./results)
        carbon_intensity: Carbon intensity factor in gCO₂e/J (default: 0.000475)
        alpha: Energy weight for GreenScore (default: 0.4)
        beta: Carbon weight for GreenScore (default: 0.4)
        gamma: Time weight for GreenScore (default: 0.2)
        tool_paths: Optional ToolPaths configuration for Python/PyPy/C compiler
        
    Returns:
        Path to final GreenScore.csv file
        
    Raises:
        ValueError: If algorithms or methods are invalid
        ConfigurationError: If build fails
        AnalysisError: If data processing fails
    """
    # Resolve algorithm and method lists
    algorithm_list = resolve_algorithms(algorithms)
    method_list = resolve_methods(methods)
    
    if output_dir is None:
        output_dir = Path.cwd() / "results"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Running benchmark suite:")
    print(f"  Algorithms: {len(algorithm_list)} ({', '.join(algorithm_list[:3])}...)")
    print(f"  Methods: {len(method_list)} ({', '.join(method_list)})")
    print(f"  Runs per benchmark: {runs}")
    print(f"  Output directory: {output_dir}")
    print()
    
    # Track execution results and audit (path identity verification)
    execution_results: Dict[str, Dict[str, Dict[str, Path]]] = defaultdict(dict)
    audit_logger = AuditLogger()
    if path_sources is None:
        path_sources = {
            "python": {"path": str(tool_paths.python.resolve()) if tool_paths else None, "source": "system_default"},
            "pypy": {"path": str(tool_paths.pypy.resolve()) if tool_paths and tool_paths.pypy else None, "source": "system_default"},
            "c_compiler": {"path": str(tool_paths.c_compiler.resolve()) if tool_paths and tool_paths.c_compiler else None, "source": "system_default"},
        }
    
    # Phase 1: Build benchmarks that require compilation
    print("Phase 1: Building benchmarks...")
    built_benchmarks: Dict[str, Dict[str, Path]] = {}
    
    for algorithm in algorithm_list:
        for method in method_list:
            if requires_build(method):
                print(f"  Building {algorithm}/{method}...", end=" ", flush=True)
                try:
                    benchmark_path = get_benchmark_path(algorithm, method)
                    built_path = build_benchmark(algorithm, method, benchmark_path, tool_paths=tool_paths)
                    built_benchmarks.setdefault(algorithm, {})[method] = built_path
                    print("✓")
                except Exception as e:
                    print(f"✗ Error: {e}")
                    # Continue with other benchmarks
                    continue
    
    print()
    
    # Phase 2: Execute benchmarks
    print("Phase 2: Executing benchmarks...")
    total_combinations = len(algorithm_list) * len(method_list)
    current = 0
    
    for algorithm in algorithm_list:
        for method in method_list:
            current += 1
            print(f"  [{current}/{total_combinations}] {algorithm}/{method}...", end=" ", flush=True)
            
            try:
                # Get benchmark path (use built path if available)
                if algorithm in built_benchmarks and method in built_benchmarks[algorithm]:
                    benchmark_path = built_benchmarks[algorithm][method]
                else:
                    benchmark_path = get_benchmark_path(algorithm, method)
                
                # Execute benchmark
                # Note: The benchmark script itself handles runs via decorators
                # We just need to execute it once - decorators will run n times
                results = execute_benchmark(
                    algorithm=algorithm,
                    method=method,
                    benchmark_path=benchmark_path,
                    runs=runs,
                    output_dir=output_dir,
                    tool_paths=tool_paths,
                    audit_logger=audit_logger,
                )
                
                execution_results[algorithm][method] = results
                print("✓")
                
            except Exception as e:
                print(f"✗ Error: {e}")
                # Continue with other benchmarks
                continue
    
    print()

    # Write audit_report.json (path identity and requested/resolved/runtime-reported)
    try:
        report = audit_logger.to_report_dict(path_sources)
        report_path = output_dir / AUDIT_REPORT_FILENAME
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        if report.get("severity") == "HIGH":
            print(f"  ⚠ Audit report: path mismatch detected — see {report_path}")
    except Exception:
        pass  # Do not fail the run if report write fails
    
    collector = ResultsCollector()

    # Phase 3: Collect and organize raw CSVs (delegate to ResultsCollector)
    print("Phase 3: Collecting raw measurement data...")
    collected = collector.collect_paths(execution_results)
    method_energy_dirs = collected["energy"]
    method_time_dirs = collected["time"]

    # Phase 4: Aggregate per method (workspace and paths via ResultsCollector)
    print("Phase 4: Aggregating results per method...")
    aggregated_energy_files: Dict[str, Path] = {}
    aggregated_time_files: Dict[str, Path] = {}

    for method in method_list:
        if method in method_energy_dirs and method_energy_dirs[method]:
            workspace_energy = collector.prepare_aggregation_workspace(
                output_dir, method, method_energy_dirs[method], "energy"
            )
            agg_energy_path = collector.get_output_path(
                output_dir, method=method, file_type=ENERGY_AGGREGATED
            )
            aggregate_energy(workspace_energy, output_path=agg_energy_path)
            aggregated_energy_files[method] = agg_energy_path

        if method in method_time_dirs and method_time_dirs[method]:
            workspace_time = collector.prepare_aggregation_workspace(
                output_dir, method, method_time_dirs[method], "time"
            )
            agg_time_path = collector.get_output_path(
                output_dir, method=method, file_type=TIME_AGGREGATED
            )
            aggregate_time(workspace_time, output_path=agg_time_path)
            aggregated_time_files[method] = agg_time_path

    print()
    
    # Phase 5: Combine methods
    print("Phase 5: Combining results across methods...")

    if not aggregated_energy_files or not aggregated_time_files:
        raise AnalysisError(
            "No aggregated data available. Check benchmark execution results."
        )

    energy_combined_path = collector.get_output_path(output_dir, file_type=ENERGY_COMBINED)
    combine_energy_results(
        list(aggregated_energy_files.values()),
        output_path=energy_combined_path,
    )

    time_combined_path = collector.get_output_path(output_dir, file_type=TIME_COMBINED)
    combine_time_results(
        list(aggregated_time_files.values()),
        output_path=time_combined_path,
    )
    
    print(f"  Energy combined: {energy_combined_path}")
    print(f"  Time combined: {time_combined_path}")
    print()
    
    # Phase 6: Calculate carbon footprint
    print("Phase 6: Calculating carbon footprint...")

    carbon_path = collector.get_output_path(output_dir, file_type=CARBON_FOOTPRINT)
    carbon_df = calculate_carbon_footprint(
        energy_combined_path,
        output_path=carbon_path,
        carbon_intensity=carbon_intensity,
    )
    
    print(f"  Carbon footprint: {carbon_path}")
    print()
    
    # Phase 7: Calculate GreenScore
    print("Phase 7: Calculating GreenScore...")

    energy_df = pd.read_csv(energy_combined_path)
    time_df = pd.read_csv(time_combined_path)

    greenscore_path = collector.get_output_path(output_dir, file_type=GREENSCORE)
    greenscore_df = calculate_greenscore(
        energy_df,
        time_df,
        carbon_df,
        alpha=alpha,
        beta=beta,
        gamma=gamma,
        output_path=greenscore_path,
        aggregated_energy_paths=aggregated_energy_files,
    )
    
    print(f"  GreenScore: {greenscore_path}")
    print()

    # Augment audit_report.json with data_methodology_summary and normalization_bounds
    try:
        report_path = output_dir / AUDIT_REPORT_FILENAME
        if report_path.exists():
            report = json.loads(report_path.read_text(encoding="utf-8"))
            if "points_measured" in greenscore_df.columns and "points_estimated" in greenscore_df.columns:
                total_measured = int(greenscore_df["points_measured"].sum())
                total_estimated = int(greenscore_df["points_estimated"].sum())
                total_points = total_measured + total_estimated
                report["data_methodology_summary"] = {
                    "total_points": total_points,
                    "hardware_percentage": round(100.0 * total_measured / total_points, 2) if total_points else 0.0,
                    "estimation_percentage": round(100.0 * total_estimated / total_points, 2) if total_points else 0.0,
                }
            else:
                report["data_methodology_summary"] = {"total_points": 0, "hardware_percentage": 0.0, "estimation_percentage": 0.0}
            numeric_energy = energy_df.drop(columns=["algorithm"], errors="ignore").select_dtypes(include="number")
            numeric_time = time_df.drop(columns=["algorithm"], errors="ignore").select_dtypes(include="number")
            numeric_carbon = carbon_df.drop(columns=["algorithm"], errors="ignore").select_dtypes(include="number")
            report["normalization_bounds"] = {
                "energy": {"min": float(numeric_energy.min().min()), "max": float(numeric_energy.max().max())} if not numeric_energy.empty else {"min": None, "max": None},
                "time": {"min": float(numeric_time.min().min()), "max": float(numeric_time.max().max())} if not numeric_time.empty else {"min": None, "max": None},
                "carbon": {"min": float(numeric_carbon.min().min()), "max": float(numeric_carbon.max().max())} if not numeric_carbon.empty else {"min": None, "max": None},
            }
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    except Exception:
        pass

    # Final summary
    print("=" * 70)
    print("Benchmark Suite Execution Complete")
    print("=" * 70)
    print(f"Final GreenScore ranking saved to: {greenscore_path}")
    print()
    print("Top 3 methods by GreenScore (lower is better):")
    print(greenscore_df.head(3).to_string(index=False))
    print()
    
    return greenscore_path
