"""
Main CLI entry point for pgsi-analyzer package.

This module provides the command-line interface with subcommands for
different visualization and analysis operations.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

from .visualization import (
    generate_grouped_bar_chart,
    plot_metric_line_chart,
    plot_execution_vs_energy_scatter,
    plot_time_vs_energy_line_chart,
    plot_method_metric_line_chart,
)
from ..platform.paths import resolve_data_path
from ..utils import validate_file_path, PGSIAnalyzerError
from ..models.statistics import (
    load_csv,
    perform_statistical_tests,
    oneway_anova_greenscore,
)
from ..benchmark.orchestrator import run_benchmark_suite
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
  # Generate Energy vs Carbon vs Time grouped bar chart
  pgsi-analyzer evcvt data.csv -o chart.png

  # Generate line charts per algorithm
  pgsi-analyzer lcpack --energy energy.csv --time time.csv --carbon carbon.csv

  # Generate scatter plot
  pgsi-analyzer scatter energy.csv time.csv -o scatter.png

  # Generate line comparison chart
  pgsi-analyzer line-compare energy.csv time.csv -o line.png

  # Generate method metric comparison
  pgsi-analyzer etc-compare metrics.csv -o comparison.png
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # evcvt: Energy vs Carbon vs Time grouped bar chart
    evcvt_parser = subparsers.add_parser(
        'evcvt',
        help='Generate grouped bar chart (Energy vs Carbon vs Time)'
    )
    evcvt_parser.add_argument('csv_file', type=str, help='Path to CSV file with metrics')
    evcvt_parser.add_argument('-o', '--output', type=str, help='Output image path')
    
    # lcpack: Line charts per algorithm
    lcpack_parser = subparsers.add_parser(
        'lcpack',
        help='Generate line charts per algorithm for energy, time, and carbon'
    )
    lcpack_parser.add_argument('--energy', type=str, required=True, help='Path to energy CSV file')
    lcpack_parser.add_argument('--time', type=str, required=True, help='Path to time CSV file')
    lcpack_parser.add_argument('--carbon', type=str, required=True, help='Path to carbon CSV file')
    lcpack_parser.add_argument('-o', '--output-dir', type=str, help='Output directory for charts')
    
    # scatter: Scatter plot (Energy vs Time)
    scatter_parser = subparsers.add_parser(
        'scatter',
        help='Generate scatter plot (Energy vs Time)'
    )
    scatter_parser.add_argument('energy_csv', type=str, help='Path to energy CSV file')
    scatter_parser.add_argument('time_csv', type=str, help='Path to time CSV file')
    scatter_parser.add_argument('-o', '--output', type=str, help='Output image path')
    
    # line-compare: Overlayed line chart
    line_compare_parser = subparsers.add_parser(
        'line-compare',
        help='Generate overlayed line chart comparing energy and time trends'
    )
    line_compare_parser.add_argument('energy_csv', type=str, help='Path to energy CSV file')
    line_compare_parser.add_argument('time_csv', type=str, help='Path to time CSV file')
    line_compare_parser.add_argument('-o', '--output', type=str, help='Output image path')
    
    # etc-compare: Method metric comparison line chart
    etc_compare_parser = subparsers.add_parser(
        'etc-compare',
        help='Generate method metric comparison line chart'
    )
    etc_compare_parser.add_argument('csv_file', type=str, help='Path to CSV file with method metrics')
    etc_compare_parser.add_argument('-o', '--output', type=str, help='Output image path')
    
    # statistics: basic statistical tests
    stats_parser = subparsers.add_parser(
        'statistics',
        help='Run basic statistical analysis (ANOVA) on results'
    )
    stats_parser.add_argument('--energy', type=str, help='Energy comparison CSV (algorithm columns)')
    stats_parser.add_argument('--time', type=str, help='Time comparison CSV (algorithm columns)')
    stats_parser.add_argument('--carbon', type=str, help='Carbon comparison CSV (algorithm columns)')
    stats_parser.add_argument('--greenscore', type=str, help='Greenscore CSV with columns method,green_score')
    
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
        if args.command == 'evcvt':
            csv_path = Path(args.csv_file)
            if not csv_path.exists():
                print(f"❌ Error: CSV file not found: {csv_path}")
                return 1
            
            output_path = Path(args.output) if args.output else None
            if output_path is None:
                output_path = csv_path.parent / f"{csv_path.stem}_evcvt.png"
            
            metrics = ["energy_mean_μJ", "time_mean_s", "carbon_mean_gCO2eq"]
            generate_grouped_bar_chart(
                csv_file=csv_path,
                metrics=metrics,
                x_column="method",
                title="Energy, Time, and Carbon Footprint Across Python Execution Methods",
                ylabel="Metric Values (μJ, s, gCO₂e)",
                output_file=output_path
            )
            
        elif args.command == 'lcpack':
            energy_path = Path(args.energy)
            time_path = Path(args.time)
            carbon_path = Path(args.carbon)
            
            if not energy_path.exists():
                print(f"❌ Error: Energy file not found: {energy_path}")
                return 1
            if not time_path.exists():
                print(f"❌ Error: Time file not found: {time_path}")
                return 1
            if not carbon_path.exists():
                print(f"❌ Error: Carbon file not found: {carbon_path}")
                return 1
            
            output_dir = Path(args.output_dir) if args.output_dir else Path.cwd()
            output_dir.mkdir(parents=True, exist_ok=True)
            
            plot_metric_line_chart(
                file_path=energy_path,
                metric_unit="μJ",
                title="Energy Consumption per Algorithm",
                ylabel="Energy",
                output_file=output_dir / "line_energy_per_algorithm.png"
            )
            
            plot_metric_line_chart(
                file_path=time_path,
                metric_unit="s",
                title="Execution Time per Algorithm",
                ylabel="Time",
                output_file=output_dir / "line_time_per_algorithm.png"
            )
            
            plot_metric_line_chart(
                file_path=carbon_path,
                metric_unit="gCO₂eq",
                title="Carbon Footprint per Algorithm",
                ylabel="Carbon Emission",
                output_file=output_dir / "line_carbon_per_algorithm.png"
            )
            
        elif args.command == 'scatter':
            energy_path = Path(args.energy_csv)
            time_path = Path(args.time_csv)
            
            if not energy_path.exists():
                print(f"❌ Error: Energy file not found: {energy_path}")
                return 1
            if not time_path.exists():
                print(f"❌ Error: Time file not found: {time_path}")
                return 1
            
            output_path = Path(args.output) if args.output else Path.cwd() / "scatter_energy_vs_time.png"
            
            plot_execution_vs_energy_scatter(
                energy_file=energy_path,
                time_file=time_path,
                output_file=output_path
            )
            
        elif args.command == 'line-compare':
            energy_path = Path(args.energy_csv)
            time_path = Path(args.time_csv)
            
            if not energy_path.exists():
                print(f"❌ Error: Energy file not found: {energy_path}")
                return 1
            if not time_path.exists():
                print(f"❌ Error: Time file not found: {time_path}")
                return 1
            
            output_path = Path(args.output) if args.output else Path.cwd() / "line_energy_vs_time_trends.png"
            
            plot_time_vs_energy_line_chart(
                energy_file=energy_path,
                time_file=time_path,
                output_file=output_path
            )
            
        elif args.command == 'etc-compare':
            csv_path = Path(args.csv_file)
            if not csv_path.exists():
                print(f"❌ Error: CSV file not found: {csv_path}")
                return 1
            
            output_path = Path(args.output) if args.output else Path.cwd() / "method_metric_comparison_linechart.png"
            
            plot_method_metric_line_chart(
                csv_file=csv_path,
                output_file=output_path
            )
        
        elif args.command == 'statistics':
            results = {}
            if args.energy and args.time and args.carbon:
                energy_df = load_csv(args.energy)
                time_df = load_csv(args.time)
                carbon_df = load_csv(args.carbon)
                results["anova_energy_time_carbon"] = perform_statistical_tests(
                    energy_df, time_df, carbon_df
                )
            if args.greenscore:
                gs_df = load_csv(args.greenscore)
                results["anova_greenscore"] = oneway_anova_greenscore(gs_df)
            if not results:
                print("ℹ️ Provide --energy/--time/--carbon and/or --greenscore for analysis.")
                return 1
            for key, value in results.items():
                print(f"{key}: {value}")
        
        elif args.command == 'benchmark':
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
                # Load tool paths from configuration
                env_file = Path(args.env_file) if args.env_file else None
                tool_paths = load_tool_paths(
                    env_file=env_file,
                    cli_python=args.python_path,
                    cli_pypy=args.pypy_path,
                    cli_cc=args.cc_path,
                )
                
                output_path = Path(args.output)
                greenscore_path = run_benchmark_suite(
                    algorithms=args.algorithms,
                    methods=args.methods,
                    runs=args.runs,
                    output_dir=output_path,
                    carbon_intensity=args.carbon_intensity,
                    alpha=args.alpha,
                    beta=args.beta,
                    gamma=args.gamma,
                    tool_paths=tool_paths,
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

