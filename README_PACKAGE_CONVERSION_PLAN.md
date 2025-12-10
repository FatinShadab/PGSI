# Python Energy Microscope: PyPI Package Conversion Plan

**Document Version:** 1.0  
**Target:** Convert repository into a production-ready, OS-independent Python package suitable for PyPI distribution  
**Author:** Senior Python Software Architect  
**Date:** Based on comprehensive repository analysis

---

## Executive Summary

This document provides a prescriptive blueprint for refactoring the `python-energy-microscope` repository into a modern, PyPI-ready Python package. The conversion addresses critical portability issues, standardizes package structure, and establishes proper dependency management following PEP 517/518 standards.

**Current State:** Research codebase with functional components but significant portability and distribution blockers.  
**Target State:** Production-ready package installable via `pip install energy-microscope` with cross-platform support.

---

## 1. Package Structure Proposal

### 1.1 Ideal Directory Structure

The recommended structure follows the **src-layout** pattern (PEP 420 compliant) for better testability and isolation:

```
python-energy-microscope/
│
├── pyproject.toml                    # Modern build system configuration (PEP 517/518)
├── README.md                          # User-facing documentation
├── LICENSE                            # License file (CC-BY-4.0 → MIT conversion recommended)
├── CITATION.cff                       # Citation metadata (preserve)
├── .gitignore                        # Git ignore patterns
│
├── src/                               # Source code directory (src-layout)
│   └── energy_microscope/            # Primary package module
│       ├── __init__.py               # Package initialization with version
│       │
│       ├── energy/                   # Energy measurement module
│       │   ├── __init__.py
│       │   └── decorator.py          # measure_energy_to_csv decorator
│       │
│       ├── time/                     # Time measurement module
│       │   ├── __init__.py
│       │   └── decorator.py          # measure_time_to_csv decorator
│       │
│       ├── visualization/            # Visualization CLI module
│       │   ├── __init__.py
│       │   └── cli.py                # Refactored from __main__.py
│       │
│       ├── analysis/                 # Data processing and analysis
│       │   ├── __init__.py
│       │   ├── aggregation.py        # energy_avg, time_avg logic
│       │   ├── combination.py        # combine_energy, combine_time logic
│       │   ├── carbon.py             # Carbon footprint calculation
│       │   └── greenscore.py         # GreenScore calculation pipeline
│       │
│       ├── survey/                   # Synthetic survey generation (optional)
│       │   ├── __init__.py
│       │   ├── chatgpt.py            # OpenAI integration
│       │   ├── gemini.py             # Google Gemini integration
│       │   └── utils.py               # Shared utilities
│       │
│       ├── config/                    # Configuration management
│       │   ├── __init__.py
│       │   ├── defaults.py           # Default benchmark parameters (from input/)
│       │   └── paths.py               # Path resolution utilities
│       │
│       └── utils/                     # Shared utilities
│           ├── __init__.py
│           └── system_info.py        # System information gathering
│
├── tests/                             # Test suite (NEW)
│   ├── __init__.py
│   ├── test_energy.py
│   ├── test_time.py
│   ├── test_analysis.py
│   ├── test_greenscore.py
│   └── fixtures/                     # Test data fixtures
│
├── benchmarks/                        # Benchmark implementations (EXCLUDED from package)
│   └── [algorithm folders]/          # Keep as separate research artifacts
│
├── data/                              # Research data (EXCLUDED from package)
│   └── [collection folders]/
│
├── docs/                              # Documentation (NEW)
│   ├── conf.py                       # Sphinx configuration
│   ├── index.rst
│   └── api/                           # API documentation
│
└── scripts/                            # Development/utility scripts (EXCLUDED from package)
    └── [development helpers]
```

### 1.2 Package Naming

**PyPI Package Name:** `energy-microscope`  
**Import Name:** `energy_microscope`  
**Installation Command:** `pip install energy-microscope`  
**Usage:** `import energy_microscope` or `from energy_microscope.energy import measure_energy_to_csv`

**Rationale:**
- Hyphens in PyPI names are standard (e.g., `scikit-learn`, `tensor-flow`)
- Underscores in import names follow PEP 8
- Shorter name improves usability
- Avoids confusion with repository name

### 1.3 Module Organization Rationale

1. **`src/` Layout:** Isolates source code from tests and development files, preventing accidental imports of non-installed code.
2. **Flat Module Structure:** `energy/`, `time/`, `analysis/` as top-level submodules improves discoverability.
3. **Separation of Concerns:** Analysis scripts consolidated into `analysis/` module with clear responsibilities.
4. **Configuration Module:** Centralizes default parameters and path resolution for maintainability.

---

## 2. Setup and Metadata Files

### 2.1 Complete `pyproject.toml` Configuration

Create a comprehensive `pyproject.toml` using the modern `[project]` table format (PEP 621):

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "energy-microscope"
version = "1.0.0"
description = "A comprehensive benchmarking and analysis tool for comparing energy consumption, execution time, and carbon footprint of Python execution methods"
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
authors = [
    {name = "Md Fatin Shadab Turja", email = ""},
    {name = "Md Mahmudul Hasan", email = ""},
]
maintainers = [
    {name = "Md Fatin Shadab Turja", email = ""}
]
keywords = [
    "python",
    "energy-efficiency",
    "sustainability",
    "benchmarking",
    "software-performance",
    "green-software",
    "carbon-emissions",
    "energy-consumption",
    "greenscore",
    "cpython",
    "pypy",
    "cython",
    "ctypes",
    "py-compile"
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Science/Research",
    "Intended Audience :: Developers",
    "Topic :: Scientific/Engineering",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: System :: Benchmark",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Operating System :: OS Independent",
    "Environment :: Console"
]

dependencies = [
    "pandas>=2.0.0",
    "matplotlib>=3.7.0",
    "numpy>=1.24.0",
    "psutil>=5.9.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
energy = [
    "pyRAPL>=0.2.3; sys_platform == 'linux' and platform_machine == 'x86_64'",
]
survey = [
    "openai>=1.0.0",
    "google-genai>=0.2.0",
]
analysis = [
    "scipy>=1.10.0",
    "statsmodels>=0.14.0",
]
all = [
    "energy-microscope[energy,survey,analysis]",
]

[project.scripts]
energy-microscope = "energy_microscope.visualization.cli:main"

[project.urls]

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
"energy_microscope" = ["config/*.json", "config/*.yaml"]

[tool.black]
line-length = 100
target-version = ["py38", "py39", "py310", "py311", "py312", "py313"]

[tool.isort]
profile = "black"
src_paths = ["src", "tests"]

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

### 2.2 External Dependencies Analysis

#### Core Dependencies (Always Required)

| Package | Version | Purpose | Notes |
|---------|---------|----------|-------|
| `pandas` | >=2.0.0 | Data manipulation and CSV processing | Used throughout analysis scripts |
| `matplotlib` | >=3.7.0 | Visualization and chart generation | Required for visualization CLI |
| `numpy` | >=1.24.0 | Numerical operations | Used in visualization and analysis |
| `psutil` | >=5.9.0 | System information gathering | Used in decorators for system info |
| `pydantic` | >=2.0.0 | Data validation | Used in synthetic survey module |

#### Optional Dependencies (Platform/Feature-Specific)

| Package | Version | Purpose | Platform Constraint |
|---------|---------|---------|---------------------|
| `pyRAPL` | >=0.2.3 | Intel RAPL energy measurement | Linux + x86_64 only |
| `openai` | >=1.0.0 | OpenAI API client | Optional (survey feature) |
| `google-genai` | >=0.2.0 | Google Gemini API client | Optional (survey feature) |
| `scipy` | >=1.10.0 | Statistical tests | Optional (advanced analysis) |
| `statsmodels` | >=0.14.0 | Statistical modeling | Optional (advanced analysis) |

**Dependency Strategy:**
- Core dependencies are always installed: `pip install energy-microscope`
- Platform-specific dependencies via extras: `pip install energy-microscope[energy]` (for Linux/Intel)
- Feature-specific dependencies: `pip install energy-microscope[survey]` or `energy-microscope[analysis]`
- All-in-one: `pip install energy-microscope[all]`

### 2.3 Minimum Python Version

**Recommended:** Python 3.8+

**Rationale:**
- Python 3.8 introduced `typing.Protocol` and improved type hints
- `pathlib` is mature and stable
- `importlib.metadata` available for version introspection
- Broad compatibility with modern scientific Python stack
- EOL for Python 3.7 is June 2023 (already past)

**Testing Matrix:**
- Test on Python 3.8, 3.9, 3.10, 3.11, 3.12, 3.13
- CI/CD should run tests on all supported versions

---

## 3. OS-Independence and Portability Review

### 3.1 Critical OS-Specific Issues Identified

#### Issue 1: Hardcoded Absolute Paths

**Location:** `visualization/__main__.py` (lines 218, 226, 234, 256)

**Current Code:**
```python
file_path="/home/eaegon/Documents/GITHUB/python-energy-microscope/data/collection_1/combine/energy_com.csv"
```

**Required Fix:**
- Replace with command-line arguments or configuration file paths
- Use `pathlib.Path` for path construction
- Implement path resolution relative to package data or user-provided base directory

**Refactored Pattern:**
```python
from pathlib import Path
from energy_microscope.config.paths import resolve_data_path

# In CLI function:
data_dir = Path(args.data_dir) if args.data_dir else resolve_data_path()
energy_file = data_dir / "combine" / "energy_com.csv"
```

#### Issue 2: Hardcoded Paths in Input Configuration

**Location:** `input/__init__.py` (line 56)

**Current Code:**
```python
'nucleotide_sequence_file': '/home/eaegon/Documents/GITHUB/python-energy-microscope/benchmarks/K-Nucleotide/dna.txt',
```

**Required Fix:**
- Use `pathlib.Path(__file__).parent` to resolve relative to package
- Or use `importlib.resources` (Python 3.9+) for package data files
- Make paths configurable via environment variables or config files

**Refactored Pattern:**
```python
from pathlib import Path
from importlib.resources import files

# For package data:
dna_file = files("energy_microscope.config") / "data" / "dna.txt"

# For user-provided files:
dna_file = Path(os.getenv("K_NUCLEOTIDE_DNA_FILE", default_path))
```

#### Issue 3: Hardcoded Windows Paths

**Location:** `scripts/greenscore.py` (lines 25-27)

**Current Code:**
```python
'C:\\Users\\User\\OneDrive\\Documents\\GitHub\\python-energy-microscope\\data\\collection_1\\combine\\energy_com.csv'
```

**Required Fix:**
- Remove hardcoded paths entirely
- Accept paths as function parameters or CLI arguments
- Use `pathlib.Path` for cross-platform path handling

#### Issue 4: Relative Paths with Backslashes

**Location:** `scripts/combine_energy.py` (lines 46-52), `scripts/stat_test.py` (line 19)

**Current Code:**
```python
file_paths = [
    '../collection_1/cpython/energy_avg.csv',
    # ...
]
```

**Required Fix:**
- Use `pathlib.Path` instead of string concatenation
- Resolve paths relative to a configurable base directory
- Use forward slashes (Python normalizes automatically) or `Path` operations

**Refactored Pattern:**
```python
from pathlib import Path

base_dir = Path(config.get("data_directory", "."))
file_paths = [
    base_dir / "collection_1" / "cpython" / "energy_avg.csv",
    base_dir / "collection_1" / "pypy" / "energy_avg.csv",
    # ...
]
```

### 3.2 Required Standard Library Replacements

#### Replace `os.path` with `pathlib.Path`

**Current Pattern (Throughout Codebase):**
```python
import os
result_file_path = os.path.join(folder_name, f"{csv_filename}.csv")
if not os.path.isfile(system_info_path):
    # ...
```

**Required Replacement:**
```python
from pathlib import Path

result_file_path = Path(folder_name) / f"{csv_filename}.csv"
if not system_info_path.exists():
    # ...
```

**Files Requiring Updates:**
- `energy_module/decorator.py` (lines 43, 46, 47, 50)
- `time_modules/decorator.py` (lines 32, 35, 36, 39)
- `scripts/energy_avg.py` (line 35)
- `scripts/time_avg.py` (line 35)
- `scripts/combine_energy.py` (line 14)
- `scripts/combine_time.py` (line 13)
- `synthetic_survey/utils.py` (lines 218, 221)

#### Replace `os.makedirs` with `pathlib.Path.mkdir`

**Current Pattern:**
```python
os.makedirs(folder_name, exist_ok=True)
```

**Required Replacement:**
```python
Path(folder_name).mkdir(parents=True, exist_ok=True)
```

#### Replace String Path Concatenation

**Current Pattern:**
```python
system_info_path = os.path.join(folder_name, "system_info.json")
```

**Required Replacement:**
```python
system_info_path = Path(folder_name) / "system_info.json"
```

### 3.3 Platform-Specific Command Execution

**Current Status:** No direct `subprocess.run('cmd')` calls found in core modules. However, Cython benchmarks require compilation steps that may use platform-specific commands.

**Recommendation:**
- Document platform-specific build requirements in README
- Provide helper scripts for Cython compilation (optional, not part of package)
- Use `shutil.which()` to detect available compilers
- Provide clear error messages when platform requirements are not met

### 3.4 Path Resolution Strategy

Create a centralized path resolution module (`energy_microscope/config/paths.py`):

```python
"""Path resolution utilities for cross-platform compatibility."""
from pathlib import Path
from typing import Optional
import os

def get_user_data_dir() -> Path:
    """Get platform-specific user data directory."""
    if os.name == "nt":  # Windows
        base = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif os.name == "posix":  # Linux/macOS
        base = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    else:
        base = Path.home()
    return base / "energy_microscope"

def resolve_data_path(base: Optional[Path] = None) -> Path:
    """Resolve data directory path."""
    if base:
        return Path(base)
    env_path = os.getenv("ENERGY_MICROSCOPE_DATA_DIR")
    if env_path:
        return Path(env_path)
    return get_user_data_dir() / "data"

def resolve_benchmark_path(algorithm: str, method: str) -> Path:
    """Resolve benchmark file path (for external benchmarks)."""
    base = Path(os.getenv("ENERGY_MICROSCOPE_BENCHMARKS_DIR", "."))
    return base / algorithm / method
```

---

## 4. Entry Point Configuration

### 4.1 Command-Line Entry Point

**Primary Entry Point:** Visualization CLI tool

**Configuration in `pyproject.toml`:**
```toml
[project.scripts]
energy-microscope = "energy_microscope.visualization.cli:main"
```

**Installation Result:**
- After `pip install energy-microscope`, users can run: `energy-microscope --help`
- Command available in PATH on all platforms

### 4.2 Entry Point Module Structure

**File:** `src/energy_microscope/visualization/cli.py`

**Function Signature:**
```python
def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point for energy-microscope CLI.
    
    Args:
        argv: Optional command-line arguments (defaults to sys.argv)
    
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    # Implementation
```

**Refactoring from `visualization/__main__.py`:**
- Rename `__main__.py` → `cli.py`
- Update function to accept `argv` parameter for testability
- Remove hardcoded paths, accept as CLI arguments
- Return exit codes for proper shell integration

### 4.3 Additional Entry Points (Optional)

For advanced users, consider additional entry points:

```toml
[project.scripts]
energy-microscope-vis = "energy_microscope.visualization.cli:main"
energy-microscope-greenscore = "energy_microscope.analysis.greenscore:main"
energy-microscope-carbon = "energy_microscope.analysis.carbon:main"
```

**Recommendation:** Start with single entry point (`energy-microscope`) to avoid command proliferation. Add subcommands using `argparse` subparsers if needed.

### 4.4 Module-Level Entry Points

**For Programmatic Use:**
```python
# User code:
from energy_microscope.energy import measure_energy_to_csv
from energy_microscope.time import measure_time_to_csv
from energy_microscope.analysis import calculate_greenscore
```

**No entry point required** - these are imported directly.

---

## 5. Critical Refactoring Summary (The Action Plan)

### Priority 1: Path Abstraction and OS Independence

**Task:** Replace all hardcoded paths and `os.path` usage with `pathlib.Path`

**Impact:** **CRITICAL** - Blocks cross-platform functionality

**Actions:**
1. Create `energy_microscope/config/paths.py` with path resolution utilities
2. Replace `os.path.join()` with `Path` operations in:
   - `energy_module/decorator.py`
   - `time_modules/decorator.py`
   - All scripts in `scripts/` directory
3. Remove hardcoded absolute paths from:
   - `visualization/__main__.py` (4 instances)
   - `input/__init__.py` (1 instance)
   - `scripts/greenscore.py` (3 instances)
4. Replace `os.makedirs()` with `Path.mkdir(parents=True, exist_ok=True)`
5. Update file I/O to use `Path.open()` or `Path.read_text()` / `Path.write_text()`

**Estimated Effort:** 4-6 hours  
**Dependencies:** None  
**Testing:** Run on Windows, Linux, macOS

---

### Priority 2: Package Structure Reorganization

**Task:** Reorganize codebase into `src/energy_microscope/` structure with proper module separation

**Impact:** **HIGH** - Required for PyPI distribution and maintainability

**Actions:**
1. Create `src/energy_microscope/` directory structure
2. Move and rename modules:
   - `energy_module/` → `src/energy_microscope/energy/`
   - `time_modules/` → `src/energy_microscope/time/`
   - `visualization/` → `src/energy_microscope/visualization/`
   - `scripts/*.py` → `src/energy_microscope/analysis/*.py` (consolidate related scripts)
   - `input/__init__.py` → `src/energy_microscope/config/defaults.py`
   - `synthetic_survey/` → `src/energy_microscope/survey/` (optional)
3. Update all import statements throughout codebase
4. Create `src/energy_microscope/__init__.py` with:
   - Package version (`__version__`)
   - Top-level imports for common functions
   - Package metadata
5. Update relative imports to absolute imports

**Estimated Effort:** 6-8 hours  
**Dependencies:** Priority 1 (path fixes should be done first)  
**Testing:** Verify all imports resolve correctly, run basic smoke tests

---

### Priority 3: Dependency Management and Configuration

**Task:** Create `pyproject.toml`, implement optional dependencies, and establish configuration system

**Impact:** **HIGH** - Required for PyPI distribution and user experience

**Actions:**
1. Create comprehensive `pyproject.toml` (see Section 2.1)
2. Implement optional dependency groups:
   - `[energy]` for pyRAPL (Linux/Intel only)
   - `[survey]` for LLM APIs
   - `[analysis]` for statistical libraries
3. Create configuration management system:
   - `energy_microscope/config/defaults.py` - Default benchmark parameters
   - Support for environment variables (`ENERGY_MICROSCOPE_DATA_DIR`, etc.)
   - Optional YAML/JSON config file support
4. Update API keys handling:
   - Remove hardcoded API keys from `synthetic_survey/chatgpt_agent.py` and `gemini_agent.py`
   - Use `os.getenv("OPENAI_API_KEY")` and `os.getenv("GEMINI_API_KEY")`
   - Provide clear error messages when keys are missing
5. Add version management:
   - `__version__` in `__init__.py`
   - Single source of truth (read from `pyproject.toml` or `_version.py`)

**Estimated Effort:** 4-5 hours  
**Dependencies:** Priority 2 (structure must be in place)  
**Testing:** Test installation with different dependency combinations, verify optional dependencies work correctly

---

## 6. Additional Recommendations

### 6.1 Testing Infrastructure

**Create test suite:**
- Unit tests for decorators (mock pyRAPL for non-Linux systems)
- Integration tests for analysis functions
- CLI tests using `pytest` and `click.testing` or `argparse` testing utilities
- Test fixtures for sample CSV data

**Tools:**
- `pytest>=7.0.0` (testing framework)
- `pytest-cov>=4.0.0` (coverage reporting)
- `pytest-mock>=3.10.0` (mocking utilities)

### 6.2 Documentation

**Required Documentation:**
1. **User Guide:** Installation, basic usage, API reference
2. **API Documentation:** Generate with Sphinx or mkdocs
3. **Examples:** Jupyter notebooks or example scripts
4. **Contributing Guide:** For open-source contributors

### 6.3 CI/CD Pipeline

**Recommended Services:**
- GitHub Actions (if repository is on GitHub)
- Test on multiple Python versions (3.8-3.13)
- Test on multiple OS (Linux, Windows, macOS)
- Automated PyPI publishing on tags

### 6.4 Version Management

**Strategy:**
- Use semantic versioning (SemVer): `MAJOR.MINOR.PATCH`
- Initial release: `1.0.0`
- Use `setuptools-scm` or `bump2version` for automated versioning

### 6.5 License Consideration

**Current:** CC-BY-4.0 (Creative Commons Attribution)  
**Recommendation:** MIT License for PyPI distribution

**Rationale:**
- MIT is more permissive and standard for Python packages
- CC-BY-4.0 is typically for content/media, not software
- MIT allows commercial use without attribution requirements (though attribution is still appreciated)

**Action:** If keeping CC-BY-4.0, ensure `pyproject.toml` license field matches exactly.

---

## 7. Migration Checklist

### Pre-Conversion
- [ ] Backup current repository
- [ ] Create feature branch: `git checkout -b package-conversion`
- [ ] Review and understand current codebase structure

### Phase 1: Path Abstraction (Priority 1)
- [ ] Create `energy_microscope/config/paths.py`
- [ ] Replace `os.path` with `pathlib.Path` in all files
- [ ] Remove all hardcoded absolute paths
- [ ] Test on Windows, Linux, macOS
- [ ] Commit: `git commit -m "refactor: replace os.path with pathlib for OS independence"`

### Phase 2: Structure Reorganization (Priority 2)
- [ ] Create `src/energy_microscope/` directory
- [ ] Move and rename all modules
- [ ] Update all import statements
- [ ] Create `__init__.py` files with proper exports
- [ ] Test imports: `python -c "import energy_microscope"`
- [ ] Commit: `git commit -m "refactor: reorganize into src-layout package structure"`

### Phase 3: Configuration and Dependencies (Priority 3)
- [ ] Create `pyproject.toml` with complete metadata
- [ ] Implement optional dependency groups
- [ ] Create configuration management system
- [ ] Remove hardcoded API keys
- [ ] Add version management
- [ ] Test installation: `pip install -e .`
- [ ] Commit: `git commit -m "feat: add pyproject.toml and dependency management"`

### Phase 4: Entry Points
- [ ] Refactor `visualization/__main__.py` → `visualization/cli.py`
- [ ] Implement `main()` function with proper argument handling
- [ ] Configure entry point in `pyproject.toml`
- [ ] Test CLI: `energy-microscope --help`
- [ ] Commit: `git commit -m "feat: add CLI entry point"`

### Phase 5: Testing and Documentation
- [ ] Create test suite structure
- [ ] Write unit tests for core functions
- [ ] Write integration tests
- [ ] Update README.md with installation and usage instructions
- [ ] Generate API documentation
- [ ] Commit: `git commit -m "test: add test suite and update documentation"`

### Phase 6: PyPI Preparation
- [ ] Verify `pyproject.toml` is complete
- [ ] Build package: `python -m build`
- [ ] Test installation from built wheel: `pip install dist/energy_microscope-*.whl`
- [ ] Create PyPI account (if not exists)
- [ ] Test on TestPyPI: `twine upload --repository testpypi dist/*`
- [ ] Final release: `twine upload dist/*`

---

## 8. Post-Conversion Validation

### Functional Testing
1. **Installation Test:**
   ```bash
   pip install energy-microscope
   python -c "import energy_microscope; print(energy_microscope.__version__)"
   ```

2. **CLI Test:**
   ```bash
   energy-microscope --help
   ```

3. **Import Test:**
   ```python
   from energy_microscope.energy import measure_energy_to_csv
   from energy_microscope.time import measure_time_to_csv
   from energy_microscope.analysis import calculate_greenscore
   ```

4. **Cross-Platform Test:**
   - Install and run on Windows 10/11
   - Install and run on Linux (Ubuntu/Debian)
   - Install and run on macOS

### Performance Testing
- Verify decorators still function correctly
- Ensure no performance regressions from pathlib migration
- Test with large CSV files (if applicable)

### Documentation Review
- README.md is clear and complete
- API documentation is accurate
- Examples work as documented
- Installation instructions are correct

---

## Conclusion

This conversion plan provides a comprehensive roadmap for transforming the `python-energy-microscope` repository into a production-ready PyPI package. The three critical refactoring tasks (path abstraction, structure reorganization, and dependency management) address the most significant blockers to distribution.

**Estimated Total Effort:** 14-19 hours of development work, plus testing and documentation.

**Success Criteria:**
- Package installs cleanly via `pip install energy-microscope`
- All functionality works on Windows, Linux, and macOS
- No hardcoded paths or OS-specific code
- Clear separation of concerns and maintainable structure
- Comprehensive documentation for users

Following this plan will result in a professional, maintainable Python package that can be distributed on PyPI and used by researchers and developers worldwide.

---

**Document End**

