# [Testing] Create test suite structure and initial tests

**Labels:** `testing`, `quality`, `priority:medium`

## Description

Create a comprehensive test suite to ensure package functionality and prevent regressions.

## Tasks

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

## Files to Create

- `tests/__init__.py`
- `tests/conftest.py`
- `tests/test_platform.py`
- `tests/test_measurement.py`
- `tests/test_models.py`
- `tests/test_cli.py`
- `tests/fixtures/sample_data.csv`

## Definition of Done

- [ ] Test directory structure created
- [ ] Pytest fixtures configured
- [ ] Platform tests implemented
- [ ] Measurement tests implemented
- [ ] Model tests implemented
- [ ] CLI tests implemented
- [ ] Tests can be run with `pytest`
- [ ] Test coverage > 70% (aim for higher)

