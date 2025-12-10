# [Refactor] Create CLI module from visualization

**Labels:** `refactoring`, `cli`, `priority:medium`

## Description

Refactor the visualization module into a proper CLI interface, removing hardcoded paths and making it the main entry point for the package.

## Tasks

1. **Create `src/pgsi_analyzer/cli/__init__.py`** with export:
   ```python
   from .main import main
   ```

2. **Create `src/pgsi_analyzer/cli/main.py`**:
   - Move and refactor logic from `visualization/__main__.py`
   - Implement `main(argv=None)` function that:
     - Accepts optional `argv` parameter for testability
     - Uses `argparse` with subcommands for different chart types
     - Returns exit code (0 for success, non-zero for errors)
   - Subcommands:
     - `evcvt`: Grouped bar chart (Energy vs Carbon vs Time)
     - `lcpack`: Line charts per algorithm
     - `scatter`: Scatter plot (Energy vs Time)
     - `line-compare`: Overlayed line chart
     - `etc-compare`: Method metric comparison line chart
   - Remove all hardcoded absolute paths
   - Accept file paths as command-line arguments
   - Use `pathlib.Path` for all path operations
   - Use `pgsi_analyzer.platform.paths.resolve_data_path()` for default paths

3. **Create `src/pgsi_analyzer/cli/visualization.py`**:
   - Move all plotting functions from `visualization/__main__.py`
   - Functions:
     - `generate_grouped_bar_chart()`
     - `plot_metric_line_chart()`
     - `plot_execution_vs_energy_scatter()`
     - `plot_time_vs_energy_line_chart()`
     - `plot_method_metric_line_chart()`
   - Update all functions to accept `Path` objects
   - Remove hardcoded paths

4. **Update `pyproject.toml`** entry point:
   - Ensure `pgsi-analyzer = "pgsi_analyzer.cli:main"` is configured

## Files to Create

- `src/pgsi_analyzer/cli/main.py`
- `src/pgsi_analyzer/cli/visualization.py`

## Files to Reference (source)

- `visualization/__main__.py`

## Definition of Done

- [ ] CLI module created with proper structure
- [ ] `main()` function accepts `argv` parameter
- [ ] All subcommands implemented
- [ ] All hardcoded paths removed
- [ ] File paths accepted as CLI arguments
- [ ] Entry point works: `pgsi-analyzer --help`
- [ ] All visualization functions moved and refactored
- [ ] Functions use `pathlib.Path`
- [ ] Exit codes returned correctly

