# PGSI Release Readiness Checklist

Use this checklist before production release.

## Priority 0 and 1 Verification

- [ ] Default install includes `codecarbon` (`pip install pgsi-analyzer`).
- [ ] CPU power fallback uses packaged dataset (`src/pgsi_analyzer/config/cpu_power.csv`).
- [ ] Per-run energy CSV includes:
  - [ ] `methodology`
  - [ ] `provenance_source`
  - [ ] `provenance_match_type`
  - [ ] `provenance_matched_model`
- [ ] `system_info_pyrapl.json` includes estimation provenance when estimation path is used.
- [ ] Tests pass:
  - [ ] `pytest -q tests/test_cpu_power_resolver.py tests/test_estimators.py tests/test_energy_crossplatform.py tests/test_measurement.py`

## Cross-Platform Release Matrix (Priority 2)

Each platform should run a smoke benchmark:

```bash
pgsi-analyzer benchmark run --algorithms hanoi --methods cpython --runs 3 --output release_smoke/
```

### Windows

- [ ] Smoke run passes.
- [ ] Non-RAPL run methodology includes either `estimated_codecarbon` or `dataset_tdp`.

### Linux x86_64 (with RAPL permissions)

- [ ] Smoke run passes.
- [ ] Methodology includes `hardware_rapl_linux`.

### Linux x86_64 (without RAPL permissions)

- [ ] Smoke run passes.
- [ ] Methodology includes either `estimated_codecarbon` or `dataset_tdp`.

### macOS

- [ ] Smoke run passes.
- [ ] Methodology includes either `estimated_codecarbon` or `dataset_tdp`.

### Raspberry Pi OS

- [ ] Smoke run passes.
- [ ] Methodology includes either `estimated_codecarbon` or `dataset_tdp`.
- [ ] `generic_tdp` is rare and only appears when model resolution fails.

## Release Gate Rule

For all non-RAPL runs, at least one of the following must be true:

- `methodology == estimated_codecarbon`, or
- `methodology == dataset_tdp`

`generic_tdp` should be treated as last-resort fallback and investigated when frequent.
