from pgsi_analyzer.measurement.cpu_power_resolver import resolve_cpu_power


def test_resolve_cpu_power_exact_match():
    resolution = resolve_cpu_power("Intel Core i7-11370H")
    assert resolution.match_type == "exact"
    assert resolution.source == "codecarbon_cpu_power_csv"
    assert resolution.tdp_watts > 0


def test_resolve_cpu_power_regex_match():
    resolution = resolve_cpu_power("Intel(R) Core(TM) i7-12700H @ 2.30GHz")
    assert resolution.match_type in ("exact", "regex", "fuzzy")
    assert resolution.source == "codecarbon_cpu_power_csv"
    assert resolution.tdp_watts > 0


def test_resolve_cpu_power_known_amd_match():
    resolution = resolve_cpu_power("AMD Ryzen 9 5900X")
    assert resolution.source == "codecarbon_cpu_power_csv"
    assert resolution.tdp_watts > 0


def test_resolve_cpu_power_default_fallback():
    resolution = resolve_cpu_power("Unknown Quantum CPU")
    assert resolution.match_type == "default"
    assert resolution.source == "generic_tdp_default"
    assert resolution.tdp_watts == 65.0
