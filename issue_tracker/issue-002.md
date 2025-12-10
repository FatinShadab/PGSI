# [Refactor] Implement platform abstraction module

**Labels:** `refactoring`, `platform`, `priority:high`

## Description

Create a cross-platform abstraction layer to handle OS-specific differences, path resolution, and hardware detection. This module will enable the package to work on Linux (with hardware counters), Windows, and macOS (with estimation).

## Tasks

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

## Files to Create

- `src/pgsi_analyzer/platform/detection.py`
- `src/pgsi_analyzer/platform/paths.py`
- `src/pgsi_analyzer/platform/hardware.py`

## Files to Reference (for understanding current implementation)

- `energy_module/decorator.py` (get_system_info function)
- `time_modules/decorator.py` (get_system_info function)

## Definition of Done

- [ ] All platform detection functions work correctly on Linux, Windows, and macOS
- [ ] Path resolution functions use `pathlib.Path` exclusively
- [ ] Environment variable support implemented
- [ ] Hardware detection functions return correct information
- [ ] RAPL support detection works correctly
- [ ] Unit tests pass (if tests exist)
- [ ] No `os.path` imports remain in platform module

