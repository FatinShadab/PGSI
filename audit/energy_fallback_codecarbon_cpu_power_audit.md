# Energy Fallback Audit: pyRAPL -> CodeCarbon -> TDP

## User Requirement Interpreted

Primary requirement:

- if pyRAPL is unavailable, fallback should prioritize CodeCarbon
- TDP should still exist as last fallback
- leverage CodeCarbon CPU power database (`cpu_power.csv`) for model-specific TDP lookup
- must run on Windows, Linux, macOS, and Raspberry Pi OS

## Current Compliance

## Pass

- **Fallback order is already correct in code path**:
  - pyRAPL first (Linux x86_64 only)
  - CodeCarbon second (when import/tracker works)
  - TDP estimation third

- **Methodology labeling exists**:
  - `hardware_rapl_linux`
  - `estimated_codecarbon`
  - `estimated_cpu_tdp` / `estimated_fallback_generic`

## Partial

- CodeCarbon is optional dependency, so practical fallback may become:
  - pyRAPL unavailable -> CodeCarbon missing -> TDP
- This is functionally valid but does not guarantee the desired "must use CodeCarbon when possible" behavior for normal installs.

## Fail / Gap

- No integration with a CPU power database equivalent to CodeCarbon `cpu_power.csv`.
- TDP lookup is currently a compact hardcoded dictionary with partial string matching.

## Risk Analysis

- **Accuracy risk**: generic TDP values for unknown CPUs can materially skew energy and carbon estimates.
- **Portability risk**: ARM boards and newer CPUs are underrepresented in static map.
- **Auditability risk**: no confidence signal for model matching quality (exact vs fuzzy vs default).

## Recommended Target Design

## 1) Resolver Layer

Add a dedicated CPU power resolver module:

- `src/pgsi_analyzer/measurement/cpu_power_resolver.py`
- Input: `py-cpuinfo`/platform CPU name string
- Output:
  - `tdp_watts`
  - `match_type` (`exact`, `regex`, `fuzzy`, `default`)
  - `matched_model`
  - `source` (`codecarbon_cpu_power_csv` or `internal_default`)

## 2) Dataset Strategy

Bundle curated CPU dataset in package data, for example:

- `src/pgsi_analyzer/config/cpu_power.csv`

Implementation options:

- **Preferred**: import from CodeCarbon upstream dataset during release refresh process.
- Maintain attribution/version metadata in an adjacent file:
  - `cpu_power.source.json` with commit hash/date/license note.

## 3) Fallback Decision Matrix

1. pyRAPL available and functional -> use hardware.
2. Else if CodeCarbon tracker yields energy -> use CodeCarbon energy directly.
3. Else if CPU model matches dataset -> use dataset-backed TDP estimator.
4. Else use conservative generic TDP fallback.

## 4) Cross-Platform Guarantees

The above works on:

- Windows: no pyRAPL, CodeCarbon + dataset TDP fallback.
- macOS: no pyRAPL, CodeCarbon + dataset TDP fallback.
- Linux x86_64: pyRAPL preferred; if denied/unavailable, same fallback.
- Raspberry Pi OS: no pyRAPL; CodeCarbon first, then dataset TDP.

## 5) Test Additions Required

Add tests for:

- exact dataset match (`Intel Core i9-13900K` style)
- normalized match with suffixes and frequency text
- ARM/Raspberry Pi examples
- unknown CPU -> default TDP with explicit methodology tag
- CodeCarbon import missing -> dataset TDP still deterministic

## Suggested Acceptance Criteria

- `pgsi-analyzer` run on all target OSes completes without pyRAPL dependency.
- On non-pyRAPL runs:
  - CodeCarbon path is attempted and logged.
  - If unavailable, dataset-backed TDP path is attempted and logged.
- `system_info_pyrapl.json` (or equivalent system metadata) records:
  - measurement method
  - fallback model
  - data source (`codecarbon`, `cpu_power_csv`, or `generic_tdp`)

## Bottom Line

PGSI already follows the right fallback order. To satisfy the requirement strongly (especially for Windows/macOS/Raspberry Pi), the missing piece is CPU power dataset integration and default-install posture that keeps CodeCarbon available in typical user environments.
