# Cross-Platform Compliance Matrix (Energy Fallback)

## Current Matrix

| Platform | pyRAPL path | CodeCarbon path | TDP fallback | Overall status |
|---|---|---|---|---|
| Windows | Not applicable | Supported if installed | Supported | Functional, medium confidence |
| Linux x86_64 (Intel/AMD64) | Supported when permission/hardware available | Supported if installed | Supported | Functional, high/medium confidence |
| macOS | Not applicable | Supported if installed | Supported | Functional, medium confidence |
| Raspberry Pi OS (Linux ARM) | Not applicable | Supported if installed | Supported | Functional, medium/low confidence |

## Key Gaps to Close

1. Ensure CodeCarbon is available in default user path (installation/profile guidance or dependency move).
2. Replace small heuristic TDP table with dataset-backed resolver.
3. Add explicit ARM/Raspberry Pi CPU model fixtures for regression testing.

## Proposed Compliance Targets

## Target A (Short Term)

- Keep current order: `pyRAPL -> CodeCarbon -> TDP`.
- Add clear runtime log line showing selected method.
- Add docs with install command that includes energy extras.

## Target B (Medium Term)

- Integrate `cpu_power.csv`-style dataset into package.
- Implement robust model normalization and matching.
- Emit method provenance metadata in outputs.

## Target C (Release Gate)

All below must pass before calling energy fallback fully compliant:

- Windows smoke benchmark run passes.
- Linux x86_64 run passes with and without RAPL permissions.
- macOS run passes.
- Raspberry Pi OS run passes.
- In non-RAPL scenarios, at least one of:
  - `estimated_codecarbon`, or
  - dataset-backed TDP methodology tag
  appears in energy outputs.

## Concrete Next Actions

1. Add `cpu_power_resolver.py` with tests.
2. Add packaged dataset + source metadata.
3. Expand methodology tags to include dataset-backed TDP explicitly.
4. Add CI jobs or documented local matrix scripts for:
   - Windows
   - Linux
   - macOS
   - Raspberry Pi OS (manual job or device-run script)

This matrix can be used as the release checklist for cross-platform energy fallback quality.
