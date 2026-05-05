"""
Main CLI entry point for pgsi-analyzer package.

This module provides the command-line interface for benchmark execution
and listing operations.
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Optional

from ..utils import PGSIAnalyzerError
from ..benchmark import orchestrator
from ..benchmarks.discovery import build_registry, list_algorithms_from_registry, list_methods_from_registry
from ..benchmarks.template import generate_benchmark_template, create_benchmark_scaffold
from ..benchmarks.registry import list_algorithms as list_builtin_algorithms
from ..benchmarks.discovery import USER_REGISTRY_FILENAME
from ..config import load_tool_paths


def _parse_algorithm_runs(values: Optional[list]) -> Dict[str, int]:
    """Parse CLI --algorithm-runs values formatted as algorithm=runs."""
    if not values:
        return {}
    parsed: Dict[str, int] = {}
    for item in values:
        if "=" not in item:
            raise ValueError(f"Invalid --algorithm-runs value '{item}'. Expected format: algorithm=runs")
        algorithm, run_text = item.split("=", 1)
        algorithm = algorithm.strip()
        run_text = run_text.strip()
        if not algorithm:
            raise ValueError(f"Invalid --algorithm-runs value '{item}': missing algorithm")
        try:
            run_count = int(run_text)
        except ValueError as exc:
            raise ValueError(f"Invalid run count '{run_text}' for algorithm '{algorithm}'") from exc
        if run_count <= 0:
            raise ValueError(f"Run count for algorithm '{algorithm}' must be positive")
        parsed[algorithm] = run_count
    return parsed


def _resolve_benchmarks_dir(cli_value: Optional[str]) -> Optional[Path]:
    """
    Resolve benchmark directory from CLI value or auto-detect ./benchmarks.

    Priority:
    1) Explicit --benchmarks-dir
    2) Auto-detect ./benchmarks when pgsi_registry.json exists
    3) None (built-ins only)
    """
    if cli_value:
        return Path(cli_value)
    candidate = Path.cwd() / "benchmarks"
    if (candidate / USER_REGISTRY_FILENAME).exists():
        return candidate
    return None


def _bootstrap_default_project() -> Path:
    """
    Create default benchmark project in ./benchmarks when running pgsi-analyzer
    with no command.
    """
    target = Path.cwd() / "benchmarks"
    if target.exists() and any(target.iterdir()):
        return target
    return generate_benchmark_template(
        output_dir=target,
        algorithms=list_builtin_algorithms(),
        force=False,
    )


def main(argv: Optional[list] = None) -> int:
    """
    Main CLI entry point.

    Args:
        argv: Optional command-line arguments. If None, uses sys.argv.

    Returns:
        Exit code: 0 for success, non-zero for errors.

    Examples:
        >>> main(['--help'])
        0
    """
    parser = argparse.ArgumentParser(
        description="PGSI Analyzer: Python GreenScore and Sustainability Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available benchmarks
  pgsi-analyzer benchmark list

  # Run a single benchmark
  pgsi-analyzer benchmark run --algorithms hanoi --methods cpython --runs 5

  # Create a user benchmark project scaffold (Django-style)
  pgsi-analyzer startproject my-benchmarks --algorithms all

  # Run full benchmark suite
  pgsi-analyzer benchmark run --algorithms all --methods all --runs 50
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # startproject (Django-style scaffold)
    startproject_parser = subparsers.add_parser(
        'startproject',
        help='Generate user benchmark project scaffold (Django-style)'
    )
    startproject_parser.add_argument(
        'name',
        type=str,
        help='Project directory to create (e.g. my-benchmarks)'
    )
    startproject_parser.add_argument(
        '--algorithms',
        type=str,
        nargs='+',
        default=['all'],
        help='Algorithms to scaffold (default: all built-ins)'
    )
    startproject_parser.add_argument(
        '--force',
        action='store_true',
        help='Allow generation in non-empty output directory'
    )

    # create benchmark (single benchmark scaffold + registry update)
    create_parser = subparsers.add_parser(
        'create',
        help='Create project resources (e.g., benchmark scaffold)'
    )
    create_subparsers = create_parser.add_subparsers(dest='create_command', help='Create commands')
    create_benchmark_parser = create_subparsers.add_parser(
        'benchmark',
        help='Create one benchmark scaffold and register it'
    )
    create_benchmark_parser.add_argument(
        '--name',
        type=str,
        required=True,
        help='Benchmark name (e.g. my_algo)'
    )
    create_benchmark_parser.add_argument(
        '--benchmarks-dir',
        type=str,
        default='benchmarks',
        help='Target benchmark directory (default: ./benchmarks)'
    )
    create_benchmark_parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing benchmark files if present'
    )
    
    # benchmark: run benchmark suite
    benchmark_parser = subparsers.add_parser(
        'benchmark',
        help='Benchmark execution commands'
    )
    benchmark_subparsers = benchmark_parser.add_subparsers(dest='benchmark_command', help='Benchmark commands')
    
    # benchmark run
    run_parser = benchmark_subparsers.add_parser(
        'run',
        help='Execute benchmark suite and generate GreenScore'
    )
    run_parser.add_argument(
        '--algorithms',
        type=str,
        nargs='+',
        default=['all'],
        help='Algorithm names to run (default: all). Use "all" for all algorithms.'
    )
    run_parser.add_argument(
        '--methods',
        type=str,
        nargs='+',
        default=['all'],
        help='Execution methods to run (default: all). Use "all" for all methods.'
    )
    run_parser.add_argument(
        '--runs',
        type=int,
        default=50,
        help='Number of runs per benchmark (default: 50)'
    )
    run_parser.add_argument(
        '--algorithm-runs',
        type=str,
        nargs='*',
        help='Optional per-algorithm run overrides in format algorithm=runs (e.g. hanoi=20 sieve=10)'
    )
    run_parser.add_argument(
        '--output',
        type=str,
        default='results',
        help='Output directory for results (default: results/)'
    )
    run_parser.add_argument(
        '--carbon-intensity',
        type=float,
        default=0.000475,
        help='Carbon intensity factor in gCO₂e/J (default: 0.000475)'
    )
    run_parser.add_argument(
        '--alpha',
        type=float,
        default=0.4,
        help='Energy weight for GreenScore (default: 0.4)'
    )
    run_parser.add_argument(
        '--beta',
        type=float,
        default=0.4,
        help='Carbon weight for GreenScore (default: 0.4)'
    )
    run_parser.add_argument(
        '--gamma',
        type=float,
        default=0.2,
        help='Time weight for GreenScore (default: 0.2)'
    )
    run_parser.add_argument(
        '--env-file',
        type=str,
        help='Path to .env file containing tool paths (PGSI_PYPY_PATH, PGSI_CC_PATH, PGSI_PYTHON_PATH)'
    )
    run_parser.add_argument(
        '--python-path',
        type=str,
        help='Path to Python executable for benchmarks (overrides PGSI_PYTHON_PATH and .env)'
    )
    run_parser.add_argument(
        '--pypy-path',
        type=str,
        help='Path to PyPy executable (overrides PGSI_PYPY_PATH and .env)'
    )
    run_parser.add_argument(
        '--cc-path',
        type=str,
        help='Path to C compiler executable (gcc/cl.exe) (overrides PGSI_CC_PATH and .env)'
    )
    run_parser.add_argument(
        '--benchmarks-dir',
        type=str,
        help='Optional path to user benchmark directory (<algorithm>/<method>/main.py). '
             'Discovered benchmarks are merged with built-ins.'
    )
    
    # benchmark list
    list_parser = benchmark_subparsers.add_parser(
        'list',
        help='List available algorithms and methods'
    )
    list_parser.add_argument(
        '--algorithms',
        action='store_true',
        help='List available algorithms'
    )
    list_parser.add_argument(
        '--methods',
        action='store_true',
        help='List available execution methods'
    )
    list_parser.add_argument(
        '--benchmarks-dir',
        type=str,
        help='Optional path to user benchmark directory (<algorithm>/<method>/main.py). '
             'Discovered benchmarks are merged with built-ins.'
    )

    # benchmark init-template
    init_parser = benchmark_subparsers.add_parser(
        'init-template',
        help='Generate user benchmark template project (Django-style scaffold)'
    )
    init_parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Output directory where template tree will be generated'
    )
    init_parser.add_argument(
        '--algorithms',
        type=str,
        nargs='+',
        default=['all'],
        help='Algorithms to scaffold (default: all built-ins)'
    )
    init_parser.add_argument(
        '--force',
        action='store_true',
        help='Allow generation in non-empty output directory'
    )
    
    # Parse arguments
    args = parser.parse_args(argv)
    
    # If no command provided, bootstrap default project
    if not args.command:
        created = _bootstrap_default_project()
        print(f"PGSI project ready at: {created}")
        print("Next step:")
        print("  pgsi-analyzer create benchmark --name A1 --benchmarks-dir ./benchmarks")
        print("  pgsi-analyzer benchmark run --algorithms all --methods all")
        return 0
    
    try:
        if args.command == 'benchmark':
            if not args.benchmark_command:
                benchmark_parser.print_help()
                return 1
            
            if args.benchmark_command == 'list':
                benchmarks_dir = _resolve_benchmarks_dir(getattr(args, "benchmarks_dir", None))
                registry = build_registry(benchmarks_dir)
                if args.algorithms:
                    algorithms = list_algorithms_from_registry(registry)
                    print("Available algorithms:")
                    for algo in algorithms:
                        print(f"  - {algo}")
                elif args.methods:
                    methods = list_methods_from_registry(registry)
                    print("Available execution methods:")
                    for method in methods:
                        print(f"  - {method}")
                else:
                    algorithms = list_algorithms_from_registry(registry)
                    methods = list_methods_from_registry(registry)
                    print("Available algorithms:")
                    for algo in algorithms:
                        print(f"  - {algo}")
                    print()
                    print("Available execution methods:")
                    for method in methods:
                        print(f"  - {method}")
                return 0
            
            elif args.benchmark_command == 'run':
                # Load tool paths and path sources (for audit report)
                env_file = Path(args.env_file) if args.env_file else None
                tool_paths, path_sources = load_tool_paths(
                    env_file=env_file,
                    cli_python=args.python_path,
                    cli_pypy=args.pypy_path,
                    cli_cc=args.cc_path,
                )
                
                output_path = Path(args.output)
                algorithm_runs = _parse_algorithm_runs(args.algorithm_runs)
                greenscore_path = orchestrator.run_benchmark_suite(
                    algorithms=args.algorithms,
                    methods=args.methods,
                    runs=args.runs,
                    algorithm_runs=algorithm_runs,
                    output_dir=output_path,
                    carbon_intensity=args.carbon_intensity,
                    alpha=args.alpha,
                    beta=args.beta,
                    gamma=args.gamma,
                    tool_paths=tool_paths,
                    path_sources=path_sources,
                    benchmarks_dir=_resolve_benchmarks_dir(args.benchmarks_dir),
                )
                print("Benchmark suite completed successfully!")
                print(f"   GreenScore results: {greenscore_path}")
                return 0

            elif args.benchmark_command == 'init-template':
                selected_algorithms = (
                    list_builtin_algorithms() if "all" in args.algorithms else args.algorithms
                )
                generated = generate_benchmark_template(
                    output_dir=Path(args.output),
                    algorithms=selected_algorithms,
                    force=bool(args.force),
                )
                print(f"Benchmark template generated at: {generated}")
                print("Next step:")
                print(f"  pgsi-analyzer benchmark run --algorithms all --methods all --benchmarks-dir {generated}")
                return 0
        elif args.command == 'startproject':
            selected_algorithms = (
                list_builtin_algorithms() if "all" in args.algorithms else args.algorithms
            )
            generated = generate_benchmark_template(
                output_dir=Path(args.name),
                algorithms=selected_algorithms,
                force=bool(args.force),
            )
            print(f"Project scaffold created at: {generated}")
            print("Next step:")
            print(f"  pgsi-analyzer benchmark run --algorithms all --methods all --benchmarks-dir {generated}")
            return 0
        elif args.command == 'create':
            if not args.create_command:
                create_parser.print_help()
                return 1
            if args.create_command == 'benchmark':
                created = create_benchmark_scaffold(
                    benchmarks_dir=Path(args.benchmarks_dir),
                    benchmark_name=args.name,
                    force=bool(args.force),
                    register=True,
                )
                print(f"Benchmark scaffold created: {created}")
                print(f"Registry updated: {Path(args.benchmarks_dir) / 'pgsi_registry.json'}")
                print("Next step:")
                print(f"  pgsi-analyzer benchmark run --algorithms {args.name} --methods cpython --benchmarks-dir {Path(args.benchmarks_dir)}")
                return 0
        
        return 0
        
    except PGSIAnalyzerError as e:
        print(f"ERROR: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

