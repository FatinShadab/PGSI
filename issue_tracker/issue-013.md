# [Enhancement] Add statistical analysis and advanced features

**Labels:** `enhancement`, `feature`, `priority:low`

## Description

Add advanced statistical analysis features and optional enhancements to the package.

## Tasks

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

## Files to Create

- `src/pgsi_analyzer/models/statistics.py`

## Files to Modify

- `src/pgsi_analyzer/cli/main.py` (add statistics subcommand)
- `pyproject.toml` (verify optional dependencies)

## Files to Reference (source)

- `scripts/std.py`
- `scripts/stat_test.py`
- `scripts/greenscore_oneway_anova.py`

## Definition of Done

- [ ] Statistical functions moved and refactored
- [ ] Functions use `pathlib.Path`
- [ ] Optional dependencies work correctly
- [ ] CLI subcommand added
- [ ] Statistical tests produce correct results
- [ ] Functions handle missing optional dependencies gracefully

