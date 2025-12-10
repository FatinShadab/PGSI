# [Refactor] Move configuration to config module

**Labels:** `refactoring`, `config`, `priority:medium`

## Description

Move default benchmark parameters from `input/__init__.py` to a proper configuration module, removing hardcoded paths and making it extensible.

## Tasks

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

## Files to Create

- `src/pgsi_analyzer/config/defaults.py`

## Files to Modify

- All benchmark files that import from `input` (update imports)

## Files to Reference (source)

- `input/__init__.py`

## Definition of Done

- [ ] Configuration module created
- [ ] Default parameters moved and refactored
- [ ] Hardcoded paths removed
- [ ] Environment variable support added
- [ ] All imports updated throughout codebase
- [ ] Path resolution uses platform abstraction
- [ ] Clear error messages for missing files

