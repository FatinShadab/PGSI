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
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

