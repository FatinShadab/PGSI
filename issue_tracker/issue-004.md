# [Refactor] Create cross-platform energy measurement with estimation fallback

**Labels:** `feature`, `measurement`, `platform`, `priority:high`

## Description

Implement a cross-platform energy measurement system that uses hardware counters on Linux (Intel RAPL) and provides estimation methods for Windows and macOS.

## Tasks

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

## Files to Create

- `src/pgsi_analyzer/measurement/estimators.py`

## Files to Modify

- `src/pgsi_analyzer/measurement/energy.py`

## Definition of Done

- [ ] Estimation functions implemented for Windows and macOS
- [ ] Energy decorator automatically selects measurement method based on platform
- [ ] CSV output includes measurement method indicator
- [ ] System info includes measurement metadata
- [ ] Warning messages displayed when using estimation
- [ ] Estimation provides reasonable energy values (within order of magnitude)
- [ ] Linux/Intel still uses pyRAPL (no regression)

