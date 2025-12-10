# [Cleanup] Remove unnecessary files and update package structure

**Labels:** `cleanup`, `maintenance`, `priority:low`

## Description

Remove old files and directories that are no longer needed after the refactoring, and ensure the package structure is clean.

## Tasks

1. **Identify files to remove:**
   - `energy_module/` directory (moved to `src/pgsi_analyzer/measurement/`)
   - `time_modules/` directory (moved to `src/pgsi_analyzer/measurement/`)
   - `scripts/` directory (moved to `src/pgsi_analyzer/models/`)
   - `visualization/` directory (moved to `src/pgsi_analyzer/cli/`)
   - `input/` directory (moved to `src/pgsi_analyzer/config/`)
   - `m.md` (internal documentation, can be archived or moved to `docs/`)
   - `README_PACKAGE_CONVERSION_PLAN.md` (conversion complete, can be archived)

2. **Update `.gitignore`** if needed:
   - Ensure old directories are not accidentally committed

3. **Create `MANIFEST.in`** (optional):
   - Specify which files to include in package distribution
   - Exclude `benchmarks/` and `data/` directories (research artifacts)

4. **Verify package structure:**
   - Only `src/pgsi_analyzer/` should contain package code
   - `benchmarks/` and `data/` should remain (excluded from package)
   - Documentation files in root are acceptable

## Files to Remove

- `energy_module/` (entire directory)
- `time_modules/` (entire directory)
- `scripts/` (entire directory)
- `visualization/` (entire directory)
- `input/` (entire directory)

## Files to Archive (move to `docs/archive/` or delete)

- `m.md`
- `README_PACKAGE_CONVERSION_PLAN.md`

## Definition of Done

- [ ] Old directories removed
- [ ] No broken imports (all code uses new structure)
- [ ] `.gitignore` updated
- [ ] `MANIFEST.in` created (if needed)
- [ ] Package structure is clean
- [ ] `benchmarks/` and `data/` remain (excluded from package)
- [ ] Documentation files organized

