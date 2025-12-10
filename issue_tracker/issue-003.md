# [Refactor] Move and refactor measurement modules to use pathlib

**Labels:** `refactoring`, `measurement`, `priority:high`

## Description

Move energy and time measurement decorators to the new package structure and refactor them to use `pathlib.Path` and the platform abstraction layer.

## Tasks

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

## Files to Create

- `src/pgsi_analyzer/measurement/energy.py`
- `src/pgsi_analyzer/measurement/time.py`

## Files to Modify/Reference

- `energy_module/decorator.py` (source)
- `time_modules/decorator.py` (source)

## Definition of Done

- [ ] Energy decorator moved and refactored
- [ ] Time decorator moved and refactored
- [ ] All `os.path` usage replaced with `pathlib.Path`
- [ ] Platform abstraction functions used
- [ ] pyRAPL import is conditional and handles errors gracefully
- [ ] File I/O uses `Path` operations
- [ ] Decorators maintain same external API (backward compatible)
- [ ] No `os.path` or `os.makedirs` calls remain

