# [Documentation] Update README and create user documentation

**Labels:** `documentation`, `priority:medium`

## Description

Create comprehensive user-facing documentation for the `pgsi-analyzer` package.

## Tasks

1. **Update `README.md`**:
   - Package name: `pgsi-analyzer`
   - Installation instructions: `pip install pgsi-analyzer`
   - Quick start examples
   - Platform support (Linux hardware counters, Windows/macOS estimation)
   - Usage examples for:
     - Energy measurement decorator
     - Time measurement decorator
     - GreenScore calculation
     - CLI usage
   - Configuration options
   - Environment variables
   - Platform-specific notes

2. **Create `docs/` directory** (optional, for future expansion):
   - `docs/API.md`: API reference
   - `docs/CONTRIBUTING.md`: Contribution guidelines
   - `docs/CHANGELOG.md`: Version history

3. **Add docstrings** to all public functions:
   - Use Google or NumPy docstring style
   - Include parameter descriptions
   - Include return value descriptions
   - Include usage examples where appropriate

4. **Update `pyproject.toml`**:
   - Ensure `readme = "README.md"` is set
   - Add project URLs (repository, documentation, etc.)

## Files to Modify

- `README.md`
- All Python files (add docstrings)

## Files to Create (optional)

- `docs/API.md`
- `docs/CONTRIBUTING.md`
- `docs/CHANGELOG.md`

## Definition of Done

- [ ] README.md updated with package information
- [ ] Installation instructions clear
- [ ] Usage examples provided
- [ ] Platform support documented
- [ ] All public functions have docstrings
- [ ] Documentation is clear and accurate

