# pgsi-analyzer

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Development Status](https://img.shields.io/badge/status-beta-yellow.svg)](https://pypi.org/project/pgsi-analyzer/)

**A comprehensive benchmarking and analysis tool for comparing energy consumption, execution time, and carbon footprint of Python execution methods using the GreenScore metric.**

## What is pgsi-analyzer?

`pgsi-analyzer` (Python GreenScore and Sustainability Analyzer) is a production-grade Python package that operationalizes the **GreenScore** metric into a cross-platform tool for project-level sustainability profiling. It enables automated measurement and execution environment analysis across Python environments on user-specific hardware.

### Key Features

- 🔋 **Energy Measurement**: Direct CPU energy measurement using hardware counters (Linux/Intel) with estimation fallback for Windows and macOS
- ⏱️ **Execution Time Tracking**: Precise measurement of execution time across multiple runs
- 🌍 **Carbon Footprint Calculation**: Automatic conversion of energy consumption to CO₂ equivalent emissions
- 📊 **GreenScore Metric**: Composite sustainability score combining energy, time, and carbon with configurable weights
- 📈 **Statistical Analysis**: Built-in statistical tests (ANOVA) for comparing execution methods
- 🎨 **Visualization Tools**: Command-line interface for generating charts and plots
- 🖥️ **Cross-Platform**: Works on Linux, Windows, and macOS with platform-specific optimizations
- 🧪 **Comprehensive Testing**: Full test suite with 88% code coverage

## What Does It Do?

`pgsi-analyzer` helps you:

1. **Measure Energy Consumption**: Track CPU energy usage of your Python code using hardware counters (Linux/Intel) or estimation models (Windows/macOS)
2. **Benchmark Execution Time**: Measure and compare execution times across multiple runs
3. **Calculate Carbon Footprint**: Convert energy measurements to CO₂ equivalent emissions
4. **Compute GreenScore**: Generate a composite sustainability score that ranks execution methods
5. **Visualize Results**: Create charts comparing energy, time, and carbon across different methods
6. **Statistical Analysis**: Perform statistical tests to determine significant differences between methods

### GreenScore Metric

GreenScore is a weighted composite metric that integrates energy consumption, carbon footprint, and execution time:

```
GreenScore = α·Energy_norm + β·Carbon_norm + γ·Time_norm
```

Where:
- `α = 0.4` (energy weight)
- `β = 0.4` (carbon weight)
- `γ = 0.2` (time weight)
- All metrics are normalized per-algorithm (min-max normalization)
- **Lower GreenScore = better sustainability**

## Installation

### Standard Installation

```bash
pip install pgsi-analyzer
```

### With Optional Dependencies

For hardware energy measurement on Linux/Intel systems:
```bash
pip install pgsi-analyzer[energy]
```

For statistical analysis features:
```bash
pip install pgsi-analyzer[analysis]
```

For all optional features:
```bash
pip install pgsi-analyzer[all]
```

### Development Installation

To install in development mode with all dependencies:

```bash
# Clone the repository
git clone https://github.com/FatinShadab/python-energy-microscope.git
cd python-energy-microscope

# Install in editable mode with dev dependencies
pip install -e ".[dev,all]"
```

## Quick Start

### Basic Usage

```python
from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv
from pgsi_analyzer.models import calculate_carbon_footprint, calculate_greenscore
import pandas as pd

# Measure energy consumption
@measure_energy_to_csv(n=5, csv_filename="demo_energy")
def my_function():
    return sum(range(1000000))

result = my_function()

# Measure execution time
@measure_time_to_csv(n=5, csv_filename="demo_time")
def my_function():
    return sum(range(1000000))

result = my_function()

# Calculate carbon footprint
energy_df = pd.read_csv("demo_energy_com.csv")
carbon_df = calculate_carbon_footprint("demo_energy_com.csv", output_path="carbon.csv")

# Calculate GreenScore
time_df = pd.read_csv("demo_time_com.csv")
greenscore_df = calculate_greenscore(
    energy_df, time_df, carbon_df,
    alpha=0.4, beta=0.4, gamma=0.2,
    output_path="greenscore.csv"
)

print(greenscore_df)
```

### Command-Line Interface

```bash
# Show help
pgsi-analyzer --help

# Generate Energy vs Carbon vs Time grouped bar chart
pgsi-analyzer evcvt data.csv -o chart.png

# Generate line charts per algorithm
pgsi-analyzer lcpack --energy energy.csv --time time.csv --carbon carbon.csv

# Generate scatter plot (Energy vs Time)
pgsi-analyzer scatter energy.csv time.csv -o scatter.png

# Generate line comparison chart
pgsi-analyzer line-compare energy.csv time.csv -o line.png

# Generate method metric comparison
pgsi-analyzer etc-compare metrics.csv -o comparison.png

# Run statistical analysis
pgsi-analyzer statistics --energy energy.csv --time time.csv --carbon carbon.csv --greenscore greenscore.csv
```

## Platform Support

### Linux (x86_64/Intel)

- ✅ **Hardware Energy Measurement**: Uses Intel RAPL (Running Average Power Limit) counters via `pyRAPL`
- ✅ **Direct CPU Energy**: Package and DRAM level measurements
- ✅ **High Accuracy**: Hardware-level precision

### Windows

- ✅ **Energy Estimation**: Uses CPU TDP (Thermal Design Power) and utilization models
- ✅ **CPU Time Tracking**: Precise execution time measurement
- ✅ **Carbon Calculation**: Full carbon footprint support

### macOS

- ✅ **Energy Estimation**: Uses CPU TDP models with Apple Silicon support
- ✅ **CPU Time Tracking**: Precise execution time measurement
- ✅ **Carbon Calculation**: Full carbon footprint support

## Development Environment Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (for cloning the repository)

### Step-by-Step Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/FatinShadab/python-energy-microscope.git
   cd python-energy-microscope
   ```

2. **Create a Virtual Environment** (Recommended)
   ```bash
   # On Linux/macOS
   python3 -m venv venv
   source venv/bin/activate

   # On Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install in Development Mode**
   ```bash
   pip install -e ".[dev,all]"
   ```

   This installs:
   - The package in editable mode (`-e`)
   - Development dependencies (`dev`: pytest, pytest-cov, pytest-mock)
   - All optional dependencies (`all`: energy, analysis)

4. **Verify Installation**
   ```bash
   python -c "import pgsi_analyzer; print(pgsi_analyzer.__version__)"
   pgsi-analyzer --help
   ```

## Testing in Development Environment

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_platform.py

# Run with coverage report
pytest --cov=pgsi_analyzer --cov-report=html

# Run with coverage in terminal
pytest --cov=pgsi_analyzer --cov-report=term
```

### Test Structure

```
tests/
├── test_platform.py      # Platform detection and path resolution tests
├── test_measurement.py    # Energy and time measurement tests
├── test_models.py         # Carbon, GreenScore, aggregation tests
├── test_cli.py            # Command-line interface tests
├── test_utils.py          # Error handling and validation tests
├── test_config.py         # Configuration module tests
└── test_statistics.py     # Statistical analysis tests
```

### Test Coverage

Current test coverage: **88%**

```bash
# Generate detailed HTML coverage report
pytest --cov=pgsi_analyzer --cov-report=html:test_result/coverage_all

# View coverage report
# Open test_result/coverage_all/index.html in your browser
```

### Running Specific Test Suites

```bash
# Test platform module
pytest tests/test_platform.py -v

# Test measurement module
pytest tests/test_measurement.py -v

# Test models module
pytest tests/test_models.py -v

# Test CLI module
pytest tests/test_cli.py -v

# Test utils module
pytest tests/test_utils.py -v

# Test config module
pytest tests/test_config.py -v

# Test statistics module
pytest tests/test_statistics.py -v
```

### Continuous Integration

The package includes pytest configuration in `pyproject.toml`. Tests can be run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -e ".[dev,all]"
    pytest --cov=pgsi_analyzer --cov-report=xml
```

## Package Structure

```
pgsi_analyzer/
├── __init__.py           # Package metadata
├── cli/                  # Command-line interface
│   ├── main.py          # CLI entry point
│   └── visualization.py # Chart generation functions
├── config/               # Configuration management
│   └── defaults.py      # Default benchmark parameters
├── measurement/          # Energy and time measurement
│   ├── energy.py        # Energy measurement decorator
│   ├── time.py          # Time measurement decorator
│   └── estimators.py    # Energy estimation (Windows/macOS)
├── models/               # Analysis and modeling
│   ├── carbon.py        # Carbon footprint calculation
│   ├── greenscore.py    # GreenScore calculation
│   ├── aggregation.py   # Data aggregation
│   ├── combination.py   # Result combination
│   └── statistics.py    # Statistical analysis
├── platform/             # Platform abstraction
│   ├── detection.py     # OS and architecture detection
│   ├── hardware.py      # Hardware information
│   └── paths.py         # Cross-platform path resolution
└── utils/                # Utilities
    ├── errors.py        # Custom exceptions
    └── validation.py    # Input validation
```

## API Documentation

### Measurement

```python
from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv

@measure_energy_to_csv(n=10, csv_filename="energy_results")
def my_function():
    # Your code here
    pass

@measure_time_to_csv(n=10, csv_filename="time_results")
def my_function():
    # Your code here
    pass
```

### Analysis

```python
from pgsi_analyzer.models import (
    calculate_carbon_footprint,
    calculate_greenscore,
    aggregate_energy,
    aggregate_time,
    combine_energy_results,
    combine_time_results,
)

# Calculate carbon footprint
carbon_df = calculate_carbon_footprint(
    energy_csv_path="energy.csv",
    output_path="carbon.csv",
    carbon_intensity=0.000475  # gCO₂e/J
)

# Calculate GreenScore
greenscore_df = calculate_greenscore(
    energy_df, time_df, carbon_df,
    alpha=0.4, beta=0.4, gamma=0.2,
    output_path="greenscore.csv"
)
```

### Platform Detection

```python
from pgsi_analyzer.platform import (
    detect_platform,
    is_linux_intel,
    get_system_info,
    check_rapl_support,
)

platform = detect_platform()  # 'linux', 'windows', 'macos', or 'unknown'
is_supported = is_linux_intel()  # True if Linux x86_64
system_info = get_system_info()  # CPU, RAM, OS information
has_rapl = check_rapl_support()  # True if RAPL available
```

### Validation

```python
from pgsi_analyzer.utils import (
    validate_file_path,
    validate_dataframe,
    validate_weights,
    PGSIAnalyzerError,
)

# Validate file path
path = validate_file_path("data.csv", must_exist=True)

# Validate DataFrame
validate_dataframe(df, required_columns=["algorithm", "method"])

# Validate GreenScore weights
validate_weights(alpha=0.4, beta=0.4, gamma=0.2)  # Must sum to 1.0
```

## Configuration

### Environment Variables

- `PGSI_ANALYZER_DATA_DIR`: Custom data directory path
- `PGSI_ANALYZER_BENCHMARKS_DIR`: Custom benchmarks directory path
- `PGSI_ANALYZER_DNA_FILE`: Path to DNA sequence file for K-Nucleotide benchmark

### Default Parameters

Default benchmark parameters are available via the config module:

```python
from pgsi_analyzer.config import get_default_params

params = get_default_params("hanoi")
# Returns: {'test_n': 50, 'n': 18}
```

## Examples

See the `benchmarks/` directory for example algorithm implementations and the `test_result/` directory for example outputs and visualizations.

## Contributing

Contributions are welcome! Please see the repository's contributing guidelines for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this work in your research, please cite:

```bibtex
@article{shadab2025microscope,
  title   = {Python Under the Microscope: A Comparative Energy Analysis of Execution Methods},
  author  = {Turja, Md Fatin Shadab and Others},
  journal = {IEEE Access},
  year    = {2025}
}
```

## Support

- **Issues**: [GitHub Issues](https://github.com/FatinShadab/python-energy-microscope/issues)
- **Documentation**: [GitHub Repository](https://github.com/FatinShadab/python-energy-microscope)
- **Author**: Md Fatin Shadab Turja

## Acknowledgments

This research was conducted as part of **EEE 4261 (Green Computing)** offered at United International University in Spring 2025. All code, data, and visualization tools are released for reproducibility and open sustainability research.

---

**Made with ❤️ for sustainable software development**
