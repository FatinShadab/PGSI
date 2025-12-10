# GitHub Issues: pgsi-analyzer Package Conversion

This document contains a sequential set of GitHub issues for converting the current codebase into a production-grade, cross-platform Python package named `pgsi-analyzer` ready for PyPI distribution.

**Package Name:** `pgsi-analyzer`  
**Import Name:** `pgsi_analyzer`  
**Target:** PyPI-ready package with cross-platform support (Linux hardware counters, Windows/macOS estimation)

---

## Issue #1: [Setup] Create pyproject.toml and src/ directory structure

**Labels:** `setup`, `packaging`, `priority:high`

### Body

Create the foundational package structure and build configuration for `pgsi-analyzer`.

**Tasks:**

1. **Create `pyproject.toml`** with the following configuration:
   - Package name: `pgsi-analyzer`
   - Import name: `pgsi_analyzer`
   - Version: `1.0.0`
   - Python requirement: `>=3.8`
   - Core dependencies: `pandas>=2.0.0`, `matplotlib>=3.7.0`, `numpy>=1.24.0`, `psutil>=5.9.0`
   - Optional dependencies:
     - `[energy]`: `pyRAPL>=0.2.3; sys_platform == 'linux' and platform_machine == 'x86_64'`
     - `[analysis]`: `scipy>=1.10.0`, `statsmodels>=0.14.0`
   - Entry point: `pgsi-analyzer = "pgsi_analyzer.cli:main"`
   - Use `setuptools` as build backend with `src/` layout

2. **Create `src/pgsi_analyzer/` directory structure:**
   ```
   src/pgsi_analyzer/
   ├── __init__.py          # Package initialization with __version__
   ├── measurement/         # Energy and time measurement modules
   ├── platform/            # OS-specific abstraction layer
   ├── models/              # Carbon modeling and normalization
   ├── cli/                 # Command-line interface
   └── utils/               # Shared utilities
   ```

3. **Create `src/pgsi_analyzer/__init__.py`** with:
   - `__version__ = "1.0.0"`
   - Package metadata
   - Top-level imports for common functions

4. **Create empty `__init__.py` files** in all subdirectories

5. **Create `.gitignore`** if it doesn't exist, adding:
   - `__pycache__/`, `*.pyc`, `*.pyo`
   - `dist/`, `build/`, `*.egg-info/`
   - `.pytest_cache/`, `.coverage`
   - Virtual environment directories

**Files to Create:**
- `pyproject.toml`
- `src/pgsi_analyzer/__init__.py`
- `src/pgsi_analyzer/measurement/__init__.py`
- `src/pgsi_analyzer/platform/__init__.py`
- `src/pgsi_analyzer/models/__init__.py`
- `src/pgsi_analyzer/cli/__init__.py`
- `src/pgsi_analyzer/utils/__init__.py`
- `.gitignore` (or update existing)

**Definition of Done:**
- [ ] `pyproject.toml` exists with correct package name and dependencies
- [ ] `src/pgsi_analyzer/` directory structure created
- [ ] All `__init__.py` files created
- [ ] Package can be installed in development mode: `pip install -e .`
- [ ] `import pgsi_analyzer` works without errors
- [ ] `.gitignore` properly configured

---

## Issue #2: [Refactor] Implement platform abstraction module

**Labels:** `refactoring`, `platform`, `priority:high`

### Body

Create a cross-platform abstraction layer to handle OS-specific differences, path resolution, and hardware detection. This module will enable the package to work on Linux (with hardware counters), Windows, and macOS (with estimation).

**Tasks:**

1. **Create `src/pgsi_analyzer/platform/__init__.py`** with exports:
   ```python
   from .detection import detect_platform, is_linux_intel, is_windows, is_macos
   from .paths import get_user_data_dir, resolve_data_path, resolve_benchmark_path
   from .hardware import get_cpu_info, get_system_info, check_rapl_support
   ```

2. **Create `src/pgsi_analyzer/platform/detection.py`**:
   - `detect_platform()`: Returns platform identifier ('linux', 'windows', 'macos', 'unknown')
   - `is_linux_intel()`: Checks if running on Linux with x86_64 architecture
   - `is_windows()`: Checks if running on Windows
   - `is_macos()`: Checks if running on macOS
   - Use `platform` and `sys` modules for detection

3. **Create `src/pgsi_analyzer/platform/paths.py`**:
   - Replace all `os.path` usage with `pathlib.Path`
   - `get_user_data_dir()`: Returns platform-specific user data directory
     - Windows: `%APPDATA%/pgsi_analyzer`
     - Linux/macOS: `~/.local/share/pgsi_analyzer`
   - `resolve_data_path(base=None)`: Resolves data directory path
     - Checks `PGSI_ANALYZER_DATA_DIR` environment variable
     - Falls back to `get_user_data_dir() / "data"`
   - `resolve_benchmark_path(algorithm, method)`: Resolves benchmark file paths
     - Checks `PGSI_ANALYZER_BENCHMARKS_DIR` environment variable
   - All functions return `pathlib.Path` objects

4. **Create `src/pgsi_analyzer/platform/hardware.py`**:
   - `get_cpu_info()`: Returns CPU information using `psutil` and `platform`
   - `get_system_info(result_file_path)`: Returns comprehensive system info dictionary
     - CPU, RAM, OS, Architecture
     - Test result file path
     - Platform-specific metadata
   - `check_rapl_support()`: Checks if Intel RAPL is available (Linux/Intel only)
     - Returns `True` if pyRAPL can be used, `False` otherwise
     - Handles import errors gracefully

**Files to Create:**
- `src/pgsi_analyzer/platform/detection.py`
- `src/pgsi_analyzer/platform/paths.py`
- `src/pgsi_analyzer/platform/hardware.py`

**Files to Reference (for understanding current implementation):**
- `energy_module/decorator.py` (get_system_info function)
- `time_modules/decorator.py` (get_system_info function)

**Definition of Done:**
- [ ] All platform detection functions work correctly on Linux, Windows, and macOS
- [ ] Path resolution functions use `pathlib.Path` exclusively
- [ ] Environment variable support implemented
- [ ] Hardware detection functions return correct information
- [ ] RAPL support detection works correctly
- [ ] Unit tests pass (if tests exist)
- [ ] No `os.path` imports remain in platform module

---

## Issue #3: [Refactor] Move and refactor measurement modules to use pathlib

**Labels:** `refactoring`, `measurement`, `priority:high`

### Body

Move energy and time measurement decorators to the new package structure and refactor them to use `pathlib.Path` and the platform abstraction layer.

**Tasks:**

1. **Create `src/pgsi_analyzer/measurement/__init__.py`** with exports:
   ```python
   from .energy import measure_energy_to_csv
   from .time import measure_time_to_csv
   ```

2. **Create `src/pgsi_analyzer/measurement/energy.py`**:
   - Move logic from `energy_module/decorator.py`
   - Replace `os.path.join()` with `pathlib.Path` operations
   - Replace `os.makedirs()` with `Path.mkdir(parents=True, exist_ok=True)`
   - Replace `os.path.isfile()` with `Path.exists()`
   - Import and use `pgsi_analyzer.platform.hardware.get_system_info`
   - Import and use `pgsi_analyzer.platform.detection.is_linux_intel`
   - Make pyRAPL import conditional (only on Linux/Intel)
   - Add graceful fallback for non-Linux systems (return mock/estimated values or raise informative error)
   - Update function signature to accept `Path` objects where appropriate
   - Update CSV file I/O to use `Path.open()` or `Path.write_text()`

3. **Create `src/pgsi_analyzer/measurement/time.py`**:
   - Move logic from `time_modules/decorator.py`
   - Apply same pathlib refactoring as energy module
   - Import and use platform abstraction functions
   - Update file I/O to use `Path` operations

4. **Update imports** in both modules:
   - Remove `import os`
   - Add `from pathlib import Path`
   - Add imports from `pgsi_analyzer.platform`

**Files to Create:**
- `src/pgsi_analyzer/measurement/energy.py`
- `src/pgsi_analyzer/measurement/time.py`

**Files to Modify/Reference:**
- `energy_module/decorator.py` (source)
- `time_modules/decorator.py` (source)

**Definition of Done:**
- [ ] Energy decorator moved and refactored
- [ ] Time decorator moved and refactored
- [ ] All `os.path` usage replaced with `pathlib.Path`
- [ ] Platform abstraction functions used
- [ ] pyRAPL import is conditional and handles errors gracefully
- [ ] File I/O uses `Path` operations
- [ ] Decorators maintain same external API (backward compatible)
- [ ] No `os.path` or `os.makedirs` calls remain

---

## Issue #4: [Refactor] Create cross-platform energy measurement with estimation fallback

**Labels:** `feature`, `measurement`, `platform`, `priority:high`

### Body

Implement a cross-platform energy measurement system that uses hardware counters on Linux (Intel RAPL) and provides estimation methods for Windows and macOS.

**Tasks:**

1. **Create `src/pgsi_analyzer/measurement/estimators.py`**:
   - `estimate_energy_cpu_time(cpu_time_seconds, cpu_info)`: Estimates energy based on CPU time and CPU model
     - Uses CPU TDP (Thermal Design Power) and utilization models
     - Returns energy in microjoules (μJ)
   - `estimate_energy_from_psutil()`: Uses `psutil` to estimate energy
     - Monitors CPU percent and time
     - Applies power models based on CPU type
   - `get_cpu_tdp(cpu_model)`: Returns TDP for common CPU models (dictionary lookup)
   - Platform-specific estimation functions:
     - `estimate_windows()`: Windows-specific estimation
     - `estimate_macos()`: macOS-specific estimation

2. **Update `src/pgsi_analyzer/measurement/energy.py`**:
   - Modify `measure_energy_to_csv` to:
     - Check platform using `pgsi_analyzer.platform.detection.is_linux_intel()`
     - If Linux/Intel: Use pyRAPL (existing behavior)
     - If Windows/macOS: Use estimation methods from `estimators.py`
     - Log measurement method in CSV (add column: `measurement_method`)
   - Ensure CSV format remains consistent across platforms
   - Add warning messages when using estimation (inform user that hardware counters are not available)

3. **Update system info** to include:
   - `measurement_method`: 'hardware' or 'estimation'
   - `platform`: Detected platform
   - `estimation_model`: Model used for estimation (if applicable)

**Files to Create:**
- `src/pgsi_analyzer/measurement/estimators.py`

**Files to Modify:**
- `src/pgsi_analyzer/measurement/energy.py`

**Definition of Done:**
- [ ] Estimation functions implemented for Windows and macOS
- [ ] Energy decorator automatically selects measurement method based on platform
- [ ] CSV output includes measurement method indicator
- [ ] System info includes measurement metadata
- [ ] Warning messages displayed when using estimation
- [ ] Estimation provides reasonable energy values (within order of magnitude)
- [ ] Linux/Intel still uses pyRAPL (no regression)

---

## Issue #5: [Refactor] Move analysis scripts to models module

**Labels:** `refactoring`, `analysis`, `priority:medium`

### Body

Consolidate all analysis and data processing scripts into the `models` module, refactoring them to use `pathlib.Path` and removing hardcoded paths.

**Tasks:**

1. **Create `src/pgsi_analyzer/models/__init__.py`** with exports:
   ```python
   from .carbon import calculate_carbon_footprint
   from .greenscore import calculate_greenscore, normalize_metrics
   from .aggregation import aggregate_energy, aggregate_time
   from .combination import combine_energy_results, combine_time_results
   ```

2. **Create `src/pgsi_analyzer/models/carbon.py`**:
   - Move logic from `scripts/carbon.py`
   - Refactor to:
     - Accept file paths as `Path` objects or strings (convert to `Path`)
     - Remove hardcoded paths
     - Accept carbon intensity factor as parameter (default: 0.000475 gCO₂e/J)
     - Return DataFrame instead of writing to file (write as optional parameter)
   - Function signature: `calculate_carbon_footprint(energy_csv_path, output_path=None, carbon_intensity=0.000475)`

3. **Create `src/pgsi_analyzer/models/greenscore.py`**:
   - Move logic from `scripts/greenscore.py`
   - Refactor to:
     - Remove hardcoded Windows/Linux paths
     - Accept file paths as parameters
     - Use `pathlib.Path` for all file operations
     - Make weights configurable (default: alpha=0.4, beta=0.4, gamma=0.2)
   - Functions:
     - `normalize_metrics(df)`: Row-wise min-max normalization
     - `calculate_greenscore(energy_df, time_df, carbon_df, alpha=0.4, beta=0.4, gamma=0.2)`: Full pipeline
   - Remove hardcoded file paths from `read_csv_files()` function

4. **Create `src/pgsi_analyzer/models/aggregation.py`**:
   - Move logic from `scripts/energy_avg.py` and `scripts/time_avg.py`
   - Functions:
     - `aggregate_energy(folder_path, output_path=None)`: Computes average energy from raw CSV logs
     - `aggregate_time(folder_path, output_path=None)`: Computes average execution time
   - Use `pathlib.Path` for all operations
   - Accept folder paths as `Path` objects

5. **Create `src/pgsi_analyzer/models/combination.py`**:
   - Move logic from `scripts/combine_energy.py` and `scripts/combine_time.py`
   - Functions:
     - `combine_energy_results(file_paths, output_path)`: Merges energy results from all methods
     - `combine_time_results(file_paths, output_path)`: Merges time results from all methods
   - Accept `file_paths` as list of `Path` objects
   - Remove relative path assumptions

6. **Update all functions** to:
   - Use `pathlib.Path` exclusively
   - Remove hardcoded paths
   - Accept paths as function parameters
   - Return DataFrames (write to file as optional)

**Files to Create:**
- `src/pgsi_analyzer/models/carbon.py`
- `src/pgsi_analyzer/models/greenscore.py`
- `src/pgsi_analyzer/models/aggregation.py`
- `src/pgsi_analyzer/models/combination.py`

**Files to Reference (source):**
- `scripts/carbon.py`
- `scripts/greenscore.py`
- `scripts/energy_avg.py`
- `scripts/time_avg.py`
- `scripts/combine_energy.py`
- `scripts/combine_time.py`

**Definition of Done:**
- [ ] All analysis functions moved to models module
- [ ] All hardcoded paths removed
- [ ] All functions use `pathlib.Path`
- [ ] Functions accept paths as parameters
- [ ] Functions return DataFrames (file writing optional)
- [ ] No relative path assumptions remain
- [ ] Carbon intensity is configurable
- [ ] GreenScore weights are configurable

---

## Issue #6: [Refactor] Create CLI module from visualization

**Labels:** `refactoring`, `cli`, `priority:medium`

### Body

Refactor the visualization module into a proper CLI interface, removing hardcoded paths and making it the main entry point for the package.

**Tasks:**

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

**Files to Create:**
- `src/pgsi_analyzer/cli/main.py`
- `src/pgsi_analyzer/cli/visualization.py`

**Files to Reference (source):**
- `visualization/__main__.py`

**Definition of Done:**
- [ ] CLI module created with proper structure
- [ ] `main()` function accepts `argv` parameter
- [ ] All subcommands implemented
- [ ] All hardcoded paths removed
- [ ] File paths accepted as CLI arguments
- [ ] Entry point works: `pgsi-analyzer --help`
- [ ] All visualization functions moved and refactored
- [ ] Functions use `pathlib.Path`
- [ ] Exit codes returned correctly

---

## Issue #7: [Refactor] Move configuration to config module

**Labels:** `refactoring`, `config`, `priority:medium`

### Body

Move default benchmark parameters from `input/__init__.py` to a proper configuration module, removing hardcoded paths and making it extensible.

**Tasks:**

1. **Create `src/pgsi_analyzer/config/__init__.py`** with exports:
   ```python
   from .defaults import get_default_params, DEFAULT_PARAMS
   from .paths import resolve_config_path
   ```

2. **Create `src/pgsi_analyzer/config/defaults.py`**:
   - Move content from `input/__init__.py`
   - Refactor to:
     - Remove hardcoded absolute path for `nucleotide_sequence_file`
     - Use `pathlib.Path` and `pgsi_analyzer.platform.paths` for path resolution
     - Make paths relative to package or configurable via environment variables
     - Function: `get_default_params(algorithm_name)`: Returns default parameters for an algorithm
     - Constant: `DEFAULT_PARAMS`: Dictionary of all default parameters
   - For `K_Nucleotide` nucleotide_sequence_file:
     - Check `PGSI_ANALYZER_DNA_FILE` environment variable
     - Fall back to package data directory or user config directory
     - Provide clear error if file not found

3. **Create `src/pgsi_analyzer/config/paths.py`** (if not already created in Issue #2):
   - Move path resolution utilities here
   - Or ensure platform/paths.py is imported/used

4. **Update all imports** in codebase that reference `input.__default__`:
   - Change to `from pgsi_analyzer.config import get_default_params`
   - Update usage: `get_default_params("hanoi")` instead of `__default__["hanoi"]`

**Files to Create:**
- `src/pgsi_analyzer/config/defaults.py`

**Files to Modify:**
- All benchmark files that import from `input` (update imports)

**Files to Reference (source):**
- `input/__init__.py`

**Definition of Done:**
- [ ] Configuration module created
- [ ] Default parameters moved and refactored
- [ ] Hardcoded paths removed
- [ ] Environment variable support added
- [ ] All imports updated throughout codebase
- [ ] Path resolution uses platform abstraction
- [ ] Clear error messages for missing files

---

## Issue #8: [Cleanup] Remove unnecessary files and update package structure

**Labels:** `cleanup`, `maintenance`, `priority:low`

### Body

Remove old files and directories that are no longer needed after the refactoring, and ensure the package structure is clean.

**Tasks:**

1. **Identify files to remove:**
   - `energy_module/` directory (moved to `src/pgsi_analyzer/measurement/`)
   - `time_modules/` directory (moved to `src/pgsi_analyzer/measurement/`)
   - `scripts/` directory (moved to `src/pgsi_analyzer/models/`)
   - `visualization/` directory (moved to `src/pgsi_analyzer/cli/`)
   - `input/` directory (moved to `src/pgsi_analyzer/config/`)
   - `m.md` (internal documentation, can be archived or moved to `docs/`)
   - `README_PACKAGE_CONVERSION_PLAN.md` (conversion complete, can be archived)

2. **Update `.gitignore`** if needed:
   - Ensure old directories are not accidentally committed

3. **Create `MANIFEST.in`** (optional):
   - Specify which files to include in package distribution
   - Exclude `benchmarks/` and `data/` directories (research artifacts)

4. **Verify package structure:**
   - Only `src/pgsi_analyzer/` should contain package code
   - `benchmarks/` and `data/` should remain (excluded from package)
   - Documentation files in root are acceptable

**Files to Remove:**
- `energy_module/` (entire directory)
- `time_modules/` (entire directory)
- `scripts/` (entire directory)
- `visualization/` (entire directory)
- `input/` (entire directory)

**Files to Archive (move to `docs/archive/` or delete):**
- `m.md`
- `README_PACKAGE_CONVERSION_PLAN.md`

**Definition of Done:**
- [ ] Old directories removed
- [ ] No broken imports (all code uses new structure)
- [ ] `.gitignore` updated
- [ ] `MANIFEST.in` created (if needed)
- [ ] Package structure is clean
- [ ] `benchmarks/` and `data/` remain (excluded from package)
- [ ] Documentation files organized

---

## Issue #9: [Feature] Add comprehensive error handling and validation

**Labels:** `feature`, `quality`, `priority:medium`

### Body

Add robust error handling, input validation, and user-friendly error messages throughout the package.

**Tasks:**

1. **Create `src/pgsi_analyzer/utils/__init__.py`** with exports:
   ```python
   from .validation import validate_file_path, validate_dataframe
   from .errors import PGSIAnalyzerError, MeasurementError, AnalysisError
   ```

2. **Create `src/pgsi_analyzer/utils/errors.py`**:
   - Define custom exception classes:
     - `PGSIAnalyzerError`: Base exception
     - `MeasurementError`: For measurement-related errors
     - `AnalysisError`: For analysis-related errors
     - `PlatformError`: For platform-specific errors
     - `ConfigurationError`: For configuration errors

3. **Create `src/pgsi_analyzer/utils/validation.py`**:
   - `validate_file_path(path, must_exist=True)`: Validates file path exists
   - `validate_dataframe(df, required_columns)`: Validates DataFrame structure
   - `validate_weights(alpha, beta, gamma)`: Validates GreenScore weights sum to 1.0
   - `validate_platform()`: Validates platform support and provides helpful errors

4. **Update measurement modules** to:
   - Raise `MeasurementError` with helpful messages
   - Validate inputs before processing
   - Handle missing pyRAPL gracefully (informative error)

5. **Update analysis modules** to:
   - Raise `AnalysisError` for data processing errors
   - Validate CSV structure before processing
   - Handle division by zero in normalization
   - Validate DataFrame columns

6. **Update CLI** to:
   - Catch exceptions and display user-friendly messages
   - Return appropriate exit codes
   - Validate file paths before processing

**Files to Create:**
- `src/pgsi_analyzer/utils/errors.py`
- `src/pgsi_analyzer/utils/validation.py`

**Files to Modify:**
- `src/pgsi_analyzer/measurement/energy.py`
- `src/pgsi_analyzer/measurement/time.py`
- `src/pgsi_analyzer/models/*.py`
- `src/pgsi_analyzer/cli/main.py`

**Definition of Done:**
- [ ] Custom exception classes defined
- [ ] Validation functions implemented
- [ ] Error handling added to all modules
- [ ] User-friendly error messages
- [ ] Input validation before processing
- [ ] Graceful handling of missing dependencies
- [ ] CLI returns appropriate exit codes

---

## Issue #10: [Testing] Create test suite structure and initial tests

**Labels:** `testing`, `quality`, `priority:medium`

### Body

Create a comprehensive test suite to ensure package functionality and prevent regressions.

**Tasks:**

1. **Create `tests/` directory structure:**
   ```
   tests/
   ├── __init__.py
   ├── conftest.py          # Pytest configuration and fixtures
   ├── test_platform.py     # Platform detection tests
   ├── test_measurement.py  # Measurement decorator tests
   ├── test_models.py       # Analysis function tests
   ├── test_cli.py          # CLI tests
   └── fixtures/            # Test data fixtures
       └── sample_data.csv
   ```

2. **Create `tests/conftest.py`**:
   - Pytest fixtures for:
     - Sample CSV data
     - Temporary directories
     - Mock system info
     - Mock platform detection

3. **Create `tests/test_platform.py`**:
   - Test platform detection functions
   - Test path resolution functions
   - Test hardware detection functions
   - Mock different platforms

4. **Create `tests/test_measurement.py`**:
   - Test energy decorator (mock pyRAPL)
   - Test time decorator
   - Test estimation functions
   - Test cross-platform behavior

5. **Create `tests/test_models.py`**:
   - Test carbon calculation
   - Test GreenScore calculation
   - Test normalization functions
   - Test aggregation functions

6. **Create `tests/test_cli.py`**:
   - Test CLI argument parsing
   - Test subcommands
   - Test file path handling
   - Mock file operations

7. **Update `pyproject.toml`**:
   - Add `pytest>=7.0.0` to `[project.optional-dependencies]` under `dev` or `test`
   - Add `pytest-cov>=4.0.0` for coverage
   - Add `pytest-mock>=3.10.0` for mocking

**Files to Create:**
- `tests/__init__.py`
- `tests/conftest.py`
- `tests/test_platform.py`
- `tests/test_measurement.py`
- `tests/test_models.py`
- `tests/test_cli.py`
- `tests/fixtures/sample_data.csv`

**Definition of Done:**
- [ ] Test directory structure created
- [ ] Pytest fixtures configured
- [ ] Platform tests implemented
- [ ] Measurement tests implemented
- [ ] Model tests implemented
- [ ] CLI tests implemented
- [ ] Tests can be run with `pytest`
- [ ] Test coverage > 70% (aim for higher)

---

## Issue #11: [Documentation] Update README and create user documentation

**Labels:** `documentation`, `priority:medium`

### Body

Create comprehensive user-facing documentation for the `pgsi-analyzer` package.

**Tasks:**

1. **Update `README.md`**:
   - Package name: `pgsi-analyzer`
   - Installation instructions: `pip install pgsi-analyzer`
   - Quick start examples
   - Platform support (Linux hardware counters, Windows/macOS estimation)
   - Usage examples for:
     - Energy measurement decorator
     - Time measurement decorator
     - GreenScore calculation
     - CLI usage
   - Configuration options
   - Environment variables
   - Platform-specific notes

2. **Create `docs/` directory** (optional, for future expansion):
   - `docs/API.md`: API reference
   - `docs/CONTRIBUTING.md`: Contribution guidelines
   - `docs/CHANGELOG.md`: Version history

3. **Add docstrings** to all public functions:
   - Use Google or NumPy docstring style
   - Include parameter descriptions
   - Include return value descriptions
   - Include usage examples where appropriate

4. **Update `pyproject.toml`**:
   - Ensure `readme = "README.md"` is set
   - Add project URLs (repository, documentation, etc.)

**Files to Modify:**
- `README.md`
- All Python files (add docstrings)

**Files to Create (optional):**
- `docs/API.md`
- `docs/CONTRIBUTING.md`
- `docs/CHANGELOG.md`

**Definition of Done:**
- [ ] README.md updated with package information
- [ ] Installation instructions clear
- [ ] Usage examples provided
- [ ] Platform support documented
- [ ] All public functions have docstrings
- [ ] Documentation is clear and accurate

---

## Issue #12: [Packaging] Finalize package metadata and prepare for PyPI

**Labels:** `packaging`, `release`, `priority:high`

### Body

Finalize all package metadata, ensure build system is correct, and prepare the package for PyPI distribution.

**Tasks:**

1. **Finalize `pyproject.toml`**:
   - Verify all metadata is correct (name, version, description, authors)
   - Ensure all dependencies are specified
   - Verify entry points are correct
   - Add project URLs (repository, issues, documentation)
   - Add license information
   - Add classifiers

2. **Create `LICENSE` file** (if not exists):
   - Use MIT License (recommended) or maintain existing license
   - Ensure license matches `pyproject.toml`

3. **Create `CHANGELOG.md`**:
   - Document version 1.0.0 release
   - List major features
   - Document breaking changes (if any)

4. **Test package build**:
   - Run: `python -m build`
   - Verify `dist/` contains wheel and source distribution
   - Test installation from wheel: `pip install dist/pgsi_analyzer-*.whl`

5. **Test installation**:
   - Create fresh virtual environment
   - Install package: `pip install pgsi-analyzer`
   - Test import: `python -c "import pgsi_analyzer; print(pgsi_analyzer.__version__)"`
   - Test CLI: `pgsi-analyzer --help`

6. **Create `.github/workflows/publish.yml`** (optional, for CI/CD):
   - GitHub Actions workflow for automated PyPI publishing
   - Test on multiple Python versions
   - Test on multiple platforms

**Files to Create/Modify:**
- `pyproject.toml` (finalize)
- `LICENSE` (create/verify)
- `CHANGELOG.md` (create)
- `.github/workflows/publish.yml` (optional)

**Definition of Done:**
- [ ] `pyproject.toml` is complete and correct
- [ ] LICENSE file exists and matches metadata
- [ ] Package builds successfully: `python -m build`
- [ ] Package installs from wheel
- [ ] Import works: `import pgsi_analyzer`
- [ ] CLI works: `pgsi-analyzer --help`
- [ ] All metadata is accurate
- [ ] Ready for PyPI upload (or TestPyPI for testing)

---

## Issue #13: [Enhancement] Add statistical analysis and advanced features

**Labels:** `enhancement`, `feature`, `priority:low`

### Body

Add advanced statistical analysis features and optional enhancements to the package.

**Tasks:**

1. **Create `src/pgsi_analyzer/models/statistics.py`**:
   - Move logic from `scripts/std.py` (standard deviation calculation)
   - Move logic from `scripts/stat_test.py` (statistical tests)
   - Move logic from `scripts/greenscore_oneway_anova.py` (ANOVA analysis)
   - Functions:
     - `calculate_standard_deviation(df)`: Calculate std dev across methods
     - `perform_statistical_tests(energy_df, time_df, carbon_df)`: Statistical significance tests
     - `oneway_anova_greenscore(greenscore_df)`: ANOVA for GreenScore comparison
   - Use `scipy` and `statsmodels` (optional dependencies)

2. **Update `pyproject.toml`**:
   - Ensure `[analysis]` optional dependencies include `scipy` and `statsmodels`

3. **Add to CLI**:
   - New subcommand: `statistics` for running statistical analysis
   - Options for different statistical tests

**Files to Create:**
- `src/pgsi_analyzer/models/statistics.py`

**Files to Modify:**
- `src/pgsi_analyzer/cli/main.py` (add statistics subcommand)
- `pyproject.toml` (verify optional dependencies)

**Files to Reference (source):**
- `scripts/std.py`
- `scripts/stat_test.py`
- `scripts/greenscore_oneway_anova.py`

**Definition of Done:**
- [ ] Statistical functions moved and refactored
- [ ] Functions use `pathlib.Path`
- [ ] Optional dependencies work correctly
- [ ] CLI subcommand added
- [ ] Statistical tests produce correct results
- [ ] Functions handle missing optional dependencies gracefully

---

## Summary

This set of 13 issues provides a complete roadmap for converting the codebase into the `pgsi-analyzer` package. The issues are ordered to:

1. **Establish foundation** (Issues #1-2): Package structure and platform abstraction
2. **Refactor core functionality** (Issues #3-7): Move and refactor all modules
3. **Add cross-platform support** (Issue #4): Energy estimation for Windows/macOS
4. **Clean up and quality** (Issues #8-10): Remove old files, add error handling, create tests
5. **Documentation and release** (Issues #11-12): User docs and PyPI preparation
6. **Enhancements** (Issue #13): Advanced features

**Estimated Total Effort:** 40-60 hours of development work

**Critical Path:** Issues #1, #2, #3, #4, #5, #12 (must be completed for basic functionality)

**Dependencies:**
- Issue #2 depends on Issue #1
- Issue #3 depends on Issue #2
- Issue #4 depends on Issue #3
- Issue #5 depends on Issue #2
- Issue #6 depends on Issue #2
- Issue #7 depends on Issue #2
- Issue #8 depends on Issues #3, #5, #6, #7
- Issue #9 depends on Issues #3, #5, #6
- Issue #10 depends on all previous issues
- Issue #11 depends on all previous issues
- Issue #12 depends on all previous issues
- Issue #13 depends on Issue #5

