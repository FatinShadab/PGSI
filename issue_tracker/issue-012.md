# [Packaging] Finalize package metadata and prepare for PyPI

**Labels:** `packaging`, `release`, `priority:high`

## Description

Finalize all package metadata, ensure build system is correct, and prepare the package for PyPI distribution.

## Tasks

1. **Finalize `pyproject.toml`**:
   - Verify all metadata is correct (name, version, description, authors)
   - Ensure all dependencies are specified
   - Verify entry points are correct
   - Add project URLs (repository, issues, documentation)
   - Add license information
   - Add classifiers

2. **Create `LICENSE` file** (if not exists):
   - Use MIT License (recommended) or maintain existing license
   - Ensure license matches `pyproject.toml`

3. **Create `CHANGELOG.md`**:
   - Document version 1.0.0 release
   - List major features
   - Document breaking changes (if any)

4. **Test package build**:
   - Run: `python -m build`
   - Verify `dist/` contains wheel and source distribution
   - Test installation from wheel: `pip install dist/pgsi_analyzer-*.whl`

5. **Test installation**:
   - Create fresh virtual environment
   - Install package: `pip install pgsi-analyzer`
   - Test import: `python -c "import pgsi_analyzer; print(pgsi_analyzer.__version__)"`
   - Test CLI: `pgsi-analyzer --help`

6. **Create `.github/workflows/publish.yml`** (optional, for CI/CD):
   - GitHub Actions workflow for automated PyPI publishing
   - Test on multiple Python versions
   - Test on multiple platforms

## Files to Create/Modify

- `pyproject.toml` (finalize)
- `LICENSE` (create/verify)
- `CHANGELOG.md` (create)
- `.github/workflows/publish.yml` (optional)

## Definition of Done

- [ ] `pyproject.toml` is complete and correct
- [ ] LICENSE file exists and matches metadata
- [ ] Package builds successfully: `python -m build`
- [ ] Package installs from wheel
- [ ] Import works: `import pgsi_analyzer`
- [ ] CLI works: `pgsi-analyzer --help`
- [ ] All metadata is accurate
- [ ] Ready for PyPI upload (or TestPyPI for testing)

