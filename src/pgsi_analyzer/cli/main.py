"""
Main CLI entry point for pgsi-analyzer package.

This module provides the command-line interface for benchmark execution
and listing operations.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

from ..utils import PGSIAnalyzerError
from ..benchmark import orchestrator
from ..benchmarks.registry import list_algorithms, list_methods
from ..config import load_tool_paths


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

  # Run full benchmark suite
  pgsi-analyzer benchmark run --algorithms all --methods all --runs 50
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
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
    
    # Parse arguments
    args = parser.parse_args(argv)
    
    # If no command provided, show help
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'benchmark':
            if not args.benchmark_command:
                benchmark_parser.print_help()
                return 1
            
            if args.benchmark_command == 'list':
                if args.algorithms:
                    algorithms = list_algorithms()
                    print("Available algorithms:")
                    for algo in algorithms:
                        print(f"  - {algo}")
                elif args.methods:
                    methods = list_methods()
                    print("Available execution methods:")
                    for method in methods:
                        print(f"  - {method}")
                else:
                    algorithms = list_algorithms()
                    methods = list_methods()
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
                greenscore_path = orchestrator.run_benchmark_suite(
                    algorithms=args.algorithms,
                    methods=args.methods,
                    runs=args.runs,
                    output_dir=output_path,
                    carbon_intensity=args.carbon_intensity,
                    alpha=args.alpha,
                    beta=args.beta,
                    gamma=args.gamma,
                    tool_paths=tool_paths,
                    path_sources=path_sources,
                )
                print(f"✅ Benchmark suite completed successfully!")
                print(f"   GreenScore results: {greenscore_path}")
                return 0
        
        return 0
        
    except PGSIAnalyzerError as e:
        print(f"❌ {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

