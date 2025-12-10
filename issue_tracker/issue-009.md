# [Feature] Add comprehensive error handling and validation

**Labels:** `feature`, `quality`, `priority:medium`

## Description

Add robust error handling, input validation, and user-friendly error messages throughout the package.

## Tasks

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

## Files to Create

- `src/pgsi_analyzer/utils/errors.py`
- `src/pgsi_analyzer/utils/validation.py`

## Files to Modify

- `src/pgsi_analyzer/measurement/energy.py`
- `src/pgsi_analyzer/measurement/time.py`
- `src/pgsi_analyzer/models/*.py`
- `src/pgsi_analyzer/cli/main.py`

## Definition of Done

- [ ] Custom exception classes defined
- [ ] Validation functions implemented
- [ ] Error handling added to all modules
- [ ] User-friendly error messages
- [ ] Input validation before processing
- [ ] Graceful handling of missing dependencies
- [ ] CLI returns appropriate exit codes

