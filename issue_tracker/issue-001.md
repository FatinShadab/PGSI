# [Setup] Create pyproject.toml and src/ directory structure

**Labels:** `setup`, `packaging`, `priority:high`

## Description

Create the foundational package structure and build configuration for `pgsi-analyzer`.

## Tasks

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

## Files to Create

- `pyproject.toml`
- `src/pgsi_analyzer/__init__.py`
- `src/pgsi_analyzer/measurement/__init__.py`
- `src/pgsi_analyzer/platform/__init__.py`
- `src/pgsi_analyzer/models/__init__.py`
- `src/pgsi_analyzer/cli/__init__.py`
- `src/pgsi_analyzer/utils/__init__.py`
- `.gitignore` (or update existing)

## Definition of Done

- [ ] `pyproject.toml` exists with correct package name and dependencies
- [ ] `src/pgsi_analyzer/` directory structure created
- [ ] All `__init__.py` files created
- [ ] Package can be installed in development mode: `pip install -e .`
- [ ] `import pgsi_analyzer` works without errors
- [ ] `.gitignore` properly configured

