"""
Visualization functions for generating charts and plots.

This module provides functions to create various visualizations from
energy, time, and carbon footprint data.
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import List, Optional, Union


def generate_grouped_bar_chart(
    csv_file: Union[str, Path],
    metrics: List[str],
    x_column: str,
    title: str,
    ylabel: str,
    output_file: Optional[Union[str, Path]] = None,
    normalize: bool = True
) -> None:
    """
    Generate a grouped bar chart comparing multiple metrics.

    Args:
        csv_file: Path to CSV file containing the data.
        metrics: List of metric column names to plot.
        x_column: Column name to use for x-axis categories.
        title: Chart title.
        ylabel: Y-axis label.
        output_file: Optional path to save the chart. If None, displays the chart.
        normalize: Whether to normalize values by maximum (default: True).

    Examples:
        >>> generate_grouped_bar_chart(
        ...     'data.csv',
        ...     ['energy_mean_μJ', 'time_mean_s'],
        ...     'method',
        ...     'Comparison Chart',
        ...     'Values',
        ...     'output.png'
        ... )
    """
    csv_path = Path(csv_file) if isinstance(csv_file, str) else csv_file
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    if normalize:
        df[metrics] = df[metrics] / df[metrics].max()
        fig, ax = plt.subplots()
        ax.text(1.5, 22, r"Values normalized: $x_{norm} = \frac{x}{\max(x)}$", fontsize=12, color='red')
    
    categories = df[x_column]
    bar_width = 0.2
    index = np.arange(len(categories))
    
    plt.figure(figsize=(10, 6))
    
    for i, metric in enumerate(metrics):
        plt.bar(index + i * bar_width, df[metric], width=bar_width, label=metric.replace('_', ' ').title())
    
    plt.xlabel(x_column.title())
    plt.ylabel("Normalized Value " + r" [$x_{norm} = \frac{x}{\max(x)}, x_{norm} \in [0, 1]$]" if normalize else ylabel)
    plt.title(title)
    plt.xticks(index + bar_width, categories)
    plt.legend()
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    
    if output_file:
        output_path = Path(output_file) if isinstance(output_file, str) else output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.tight_layout()
        plt.savefig(output_path)
        print(f"✅ Chart saved to: {output_path}")
    else:
        plt.show()
    plt.close()


def plot_metric_line_chart(
    file_path: Union[str, Path],
    metric_unit: str,
    title: str,
    ylabel: str,
    output_file: Union[str, Path]
) -> None:
    """
    Plot a line chart showing metric values per algorithm for different methods.

    Args:
        file_path: Path to CSV file with 'algorithm' column and method columns.
        metric_unit: Unit for the metric (e.g., 'μJ', 's', 'gCO₂eq').
        title: Chart title.
        ylabel: Y-axis label.
        output_file: Path to save the chart.

    Examples:
        >>> plot_metric_line_chart(
        ...     'energy_com.csv',
        ...     'μJ',
        ...     'Energy Consumption',
        ...     'Energy',
        ...     'energy_chart.png'
        ... )
    """
    file = Path(file_path) if isinstance(file_path, str) else file_path
    if not file.exists():
        raise FileNotFoundError(f"File not found: {file}")
    
    df = pd.read_csv(file)
    algorithms = df['algorithm']
    methods = df.columns[1:]
    
    # Transpose for line plotting: each line is a method across algorithms
    df_transposed = df.set_index('algorithm').T
    
    plt.figure(figsize=(14, 6))
    for method in df_transposed.index:
        plt.plot(algorithms, df_transposed.loc[method], marker='o', label=method.replace('_', r'\_'))
    
    plt.title(title)
    plt.xlabel('Algorithm')
    plt.ylabel(f'{ylabel} ({metric_unit})')
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(title='Method', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    output = Path(output_file) if isinstance(output_file, str) else output_file
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output)
    print(f"✅ Saved chart: {output}")
    plt.close()


def plot_execution_vs_energy_scatter(
    energy_file: Union[str, Path],
    time_file: Union[str, Path],
    output_file: Union[str, Path]
) -> None:
    """
    Create a scatter plot comparing execution time vs energy consumption.

    Args:
        energy_file: Path to CSV file with energy data.
        time_file: Path to CSV file with time data.
        output_file: Path to save the scatter plot.

    Examples:
        >>> plot_execution_vs_energy_scatter(
        ...     'energy_com.csv',
        ...     'time_com.csv',
        ...     'scatter.png'
        ... )
    """
    energy_path = Path(energy_file) if isinstance(energy_file, str) else energy_file
    time_path = Path(time_file) if isinstance(time_file, str) else time_file
    
    if not energy_path.exists():
        raise FileNotFoundError(f"Energy file not found: {energy_path}")
    if not time_path.exists():
        raise FileNotFoundError(f"Time file not found: {time_path}")
    
    # Load and reshape data
    energy_df = pd.read_csv(energy_path)
    time_df = pd.read_csv(time_path)
    
    energy_long = energy_df.melt(id_vars=["algorithm"], var_name="method", value_name="energy_μJ")
    time_long = time_df.melt(id_vars=["algorithm"], var_name="method", value_name="time_s")
    
    merged = pd.merge(energy_long, time_long, on=["algorithm", "method"])
    merged["energy_J"] = merged["energy_μJ"] / 1e6  # Convert μJ to J
    
    # Plotting
    plt.figure(figsize=(10, 6))
    scatter = plt.scatter(
        merged["time_s"],
        merged["energy_J"],
        c=merged["method"].astype("category").cat.codes,
        cmap="tab10",
        alpha=0.8,
        edgecolors="k"
    )
    
    # Add algorithm labels
    for _, row in merged.iterrows():
        plt.text(row["time_s"] + 0.02, row["energy_J"], row["algorithm"], fontsize=7, alpha=0.7)
    
    # Add legend
    handles, _ = scatter.legend_elements(prop="colors", alpha=0.6)
    labels = merged["method"].unique()
    plt.legend(handles, labels, title="Method", bbox_to_anchor=(1.05, 1), loc="upper left")
    
    plt.title("Execution Time vs Energy Consumption (Per Algorithm × Method)")
    plt.xlabel("Execution Time (s)")
    plt.ylabel("Energy Consumption (J)")
    plt.grid(True)
    plt.tight_layout()
    
    output = Path(output_file) if isinstance(output_file, str) else output_file
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output)
    print(f"✅ Saved scatter plot: {output}")
    plt.close()


def plot_time_vs_energy_line_chart(
    energy_file: Union[str, Path],
    time_file: Union[str, Path],
    output_file: Union[str, Path]
) -> None:
    """
    Create a line chart comparing energy and time trends per method.

    Args:
        energy_file: Path to CSV file with energy data.
        time_file: Path to CSV file with time data.
        output_file: Path to save the line chart.

    Examples:
        >>> plot_time_vs_energy_line_chart(
        ...     'energy_com.csv',
        ...     'time_com.csv',
        ...     'line_chart.png'
        ... )
    """
    energy_path = Path(energy_file) if isinstance(energy_file, str) else energy_file
    time_path = Path(time_file) if isinstance(time_file, str) else time_file
    
    if not energy_path.exists():
        raise FileNotFoundError(f"Energy file not found: {energy_path}")
    if not time_path.exists():
        raise FileNotFoundError(f"Time file not found: {time_path}")
    
    # Read CSVs
    energy_df = pd.read_csv(energy_path)
    time_df = pd.read_csv(time_path)
    
    # Convert energy to Joules
    for col in energy_df.columns[1:]:
        energy_df[col] = energy_df[col] / 1e6  # μJ → J
    
    algorithms = energy_df["algorithm"]
    methods = energy_df.columns[1:]
    
    # Set up subplots
    plt.figure(figsize=(14, 6))
    
    for method in methods:
        plt.plot(
            algorithms,
            energy_df[method],
            marker='o',
            label=f"{method} - Energy (J)",
            linestyle='--'
        )
        plt.plot(
            algorithms,
            time_df[method],
            marker='x',
            label=f"{method} - Time (s)",
            linestyle='-'
        )
    
    # Formatting
    plt.title("Execution Time and Energy Consumption Trends per Method")
    plt.xlabel("Algorithm")
    plt.ylabel("Value (Joules / Seconds)")
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    output = Path(output_file) if isinstance(output_file, str) else output_file
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output)
    print(f"✅ Saved line chart: {output}")
    plt.close()


def plot_method_metric_line_chart(
    csv_file: Union[str, Path],
    output_file: Union[str, Path]
) -> None:
    """
    Create a line chart comparing energy and time metrics across methods.

    Args:
        csv_file: Path to CSV file with method metrics.
                 Expected columns: 'method', 'energy_mean_μJ', 'time_mean_s'.
        output_file: Path to save the line chart.

    Examples:
        >>> plot_method_metric_line_chart(
        ...     'greenscore_components.csv',
        ...     'method_comparison.png'
        ... )
    """
    csv_path = Path(csv_file) if isinstance(csv_file, str) else csv_file
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    # Load the CSV
    df = pd.read_csv(csv_path)
    
    # Check for required columns
    if 'energy_mean_μJ' not in df.columns or 'time_mean_s' not in df.columns:
        raise ValueError("CSV must contain 'energy_mean_μJ' and 'time_mean_s' columns")
    
    # Convert energy from μJ to J
    df['energy_mean_J'] = df['energy_mean_μJ'] / 1e6
    
    # Plotting setup
    plt.figure(figsize=(10, 6))
    methods = df['method']
    
    # Plot energy
    plt.plot(methods, df['energy_mean_J'], marker='o', linestyle='-', label='Energy (J)', color='tab:blue')
    
    # Plot time
    plt.plot(methods, df['time_mean_s'], marker='s', linestyle='--', label='Time (s)', color='tab:orange')
    
    # Styling
    plt.title('Comparison of Energy and Time Footprint by Execution Method')
    plt.xlabel('Execution Method')
    plt.ylabel('Metric Value')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    
    output = Path(output_file) if isinstance(output_file, str) else output_file
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output)
    print(f"✅ Saved line chart: {output}")
    plt.close()

