# [Refactor] Move analysis scripts to models module

**Labels:** `refactoring`, `analysis`, `priority:medium`

## Description

Consolidate all analysis and data processing scripts into the `models` module, refactoring them to use `pathlib.Path` and removing hardcoded paths.

## Tasks

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

## Files to Create

- `src/pgsi_analyzer/models/carbon.py`
- `src/pgsi_analyzer/models/greenscore.py`
- `src/pgsi_analyzer/models/aggregation.py`
- `src/pgsi_analyzer/models/combination.py`

## Files to Reference (source)

- `scripts/carbon.py`
- `scripts/greenscore.py`
- `scripts/energy_avg.py`
- `scripts/time_avg.py`
- `scripts/combine_energy.py`
- `scripts/combine_time.py`

## Definition of Done

- [ ] All analysis functions moved to models module
- [ ] All hardcoded paths removed
- [ ] All functions use `pathlib.Path`
- [ ] Functions accept paths as parameters
- [ ] Functions return DataFrames (file writing optional)
- [ ] No relative path assumptions remain
- [ ] Carbon intensity is configurable
- [ ] GreenScore weights are configurable

