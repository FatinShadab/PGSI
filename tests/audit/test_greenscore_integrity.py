"""
Audit tests: GreenScore computation integrity and methodology.

Validates GreenScore math, zero-variance normalization, methodology counts,
and that points_measured/points_estimated are correctly mapped from methodology.
"""

import pandas as pd
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from pgsi_analyzer.models.greenscore import (
    calculate_greenscore,
    normalize_metrics,
    _methodology_counts_from_aggregated,
    METHODOLOGY_MEASURED,
)


class TestNormalizationZeroVariance:
    """Zero-variance: identical values must not cause division by zero; score is stable."""

    def test_normalize_metrics_constant_row_produces_zeros(self):
        """Constant row (all methods same value) normalizes to zeros, no div-by-zero."""
        df = pd.DataFrame({
            "algorithm": ["a1", "a2"],
            "cpython": [100.0, 10.0],
            "pypy": [100.0, 20.0],
        })
        # First row is constant (100, 100)
        out = normalize_metrics(df)
        assert out["algorithm"].tolist() == ["a1", "a2"]
        # a1 row: constant -> 0, 0
        assert (out.drop(columns=["algorithm"]).iloc[0] == 0).all()
        # a2 row: min=10 max=20 -> 0, 1
        assert out.iloc[1]["cpython"] == 0.0
        assert out.iloc[1]["pypy"] == 1.0

    def test_calculate_greenscore_all_identical_energy_time_stable_score(self):
        """All methods have identical energy and time -> GreenScore is stable (no div-by-zero)."""
        # Same value for every method in every metric -> constant rows -> normalized to 0
        energy_df = pd.DataFrame({
            "algorithm": ["hanoi", "sieve"],
            "cpython": [50.0, 50.0],
            "pypy": [50.0, 50.0],
        })
        time_df = pd.DataFrame({
            "algorithm": ["hanoi", "sieve"],
            "cpython": [1.0, 1.0],
            "pypy": [1.0, 1.0],
        })
        carbon_df = pd.DataFrame({
            "algorithm": ["hanoi", "sieve"],
            "cpython_CO2e_g": [0.1, 0.1],
            "pypy_CO2e_g": [0.1, 0.1],
        })
        result = calculate_greenscore(energy_df, time_df, carbon_df)
        # All rows constant -> all normalized 0 -> green_score = 0 for all
        assert "green_score" in result.columns
        assert (result["green_score"] == 0.0).all()
        assert len(result) == 2


class TestMethodologyCounts:
    """points_measured and points_estimated correctly mapped from methodology column."""

    def test_methodology_count_three_hardware_one_fallback(self):
        """Mock 3 hardware rows and 1 fallback row -> points_measured=3, points_estimated=1."""
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "energy_aggregated.csv"
            df = pd.DataFrame({
                "filename": ["a", "b", "c", "d"],
                "average_package (uJ)": [100, 200, 300, 400],
                "methodology": [
                    METHODOLOGY_MEASURED,
                    METHODOLOGY_MEASURED,
                    METHODOLOGY_MEASURED,
                    "estimated_cpu_tdp",
                ],
            })
            df.to_csv(path, index=False)
            counts = _methodology_counts_from_aggregated({"cpython": path})
            assert counts["cpython"]["points_measured"] == 3
            assert counts["cpython"]["points_estimated"] == 1

    def test_greenscore_includes_points_measured_and_estimated_from_aggregated(self):
        """GreenScore.csv includes points_measured and points_estimated from methodology."""
        with TemporaryDirectory() as tmp:
            agg_path = Path(tmp) / "energy_aggregated.csv"
            pd.DataFrame({
                "filename": ["hanoi", "sieve"],
                "average_package (uJ)": [100, 200],
                "methodology": [METHODOLOGY_MEASURED, "estimated_cpu_tdp"],
            }).to_csv(agg_path, index=False)
            energy_df = pd.DataFrame({
                "algorithm": ["hanoi", "sieve"],
                "cpython": [100.0, 200.0],
            })
            time_df = pd.DataFrame({
                "algorithm": ["hanoi", "sieve"],
                "cpython": [1.0, 2.0],
            })
            carbon_df = pd.DataFrame({
                "algorithm": ["hanoi", "sieve"],
                "cpython_CO2e_g": [0.1, 0.2],
            })
            result = calculate_greenscore(
                energy_df, time_df, carbon_df,
                aggregated_energy_paths={"cpython": agg_path},
            )
            assert "points_measured" in result.columns
            assert "points_estimated" in result.columns
            row = result[result["method"] == "cpython"].iloc[0]
            assert row["points_measured"] == 1
            assert row["points_estimated"] == 1


class TestGreenScoreStress:
    """Stress-test GreenScore model: weights, ordering, bounds."""

    def test_weights_must_sum_to_one(self):
        """Weights not summing to 1.0 raise ValueError."""
        energy_df = pd.DataFrame({"algorithm": ["a"], "cpython": [1.0]})
        time_df = pd.DataFrame({"algorithm": ["a"], "cpython": [1.0]})
        carbon_df = pd.DataFrame({"algorithm": ["a"], "cpython_CO2e_g": [1.0]})
        with pytest.raises(ValueError, match="Weights must sum"):
            calculate_greenscore(
                energy_df, time_df, carbon_df,
                alpha=0.5, beta=0.5, gamma=0.5,
            )

    def test_lower_energy_lower_score(self):
        """Method with lower normalized energy gets lower (better) green_score when others equal."""
        energy_df = pd.DataFrame({
            "algorithm": ["a", "b"],
            "cpython": [10.0, 100.0],
            "pypy": [100.0, 100.0],
        })
        time_df = pd.DataFrame({
            "algorithm": ["a", "b"],
            "cpython": [1.0, 1.0],
            "pypy": [1.0, 1.0],
        })
        carbon_df = pd.DataFrame({
            "algorithm": ["a", "b"],
            "cpython_CO2e_g": [0.1, 0.1],
            "pypy_CO2e_g": [0.1, 0.1],
        })
        result = calculate_greenscore(energy_df, time_df, carbon_df)
        cpy_score = result[result["method"] == "cpython"]["green_score"].iloc[0]
        pypy_score = result[result["method"] == "pypy"]["green_score"].iloc[0]
        assert cpy_score < pypy_score

    def test_normalized_means_in_zero_one(self):
        """Normalized component means are in [0, 1] (or constant 0)."""
        energy_df = pd.DataFrame({
            "algorithm": ["a", "b", "c"],
            "m1": [1.0, 2.0, 3.0],
            "m2": [4.0, 5.0, 6.0],
        })
        time_df = pd.DataFrame({
            "algorithm": ["a", "b", "c"],
            "m1": [0.5, 1.0, 1.5],
            "m2": [2.0, 2.5, 3.0],
        })
        carbon_df = pd.DataFrame({
            "algorithm": ["a", "b", "c"],
            "m1_CO2e_g": [0.01, 0.02, 0.03],
            "m2_CO2e_g": [0.04, 0.05, 0.06],
        })
        result = calculate_greenscore(energy_df, time_df, carbon_df)
        for col in ["energy_mean", "time_mean", "carbon_mean"]:
            assert (result[col] >= 0).all() and (result[col] <= 1).all()


class TestMethodologyConsistency:
    """Methodology consistency: mixed hardware/estimation is flagged."""

    def test_inconsistent_data_source_column_when_mixed(self):
        """When a method has both points_measured and points_estimated > 0, flag Inconsistent."""
        with TemporaryDirectory() as tmp:
            agg_path = Path(tmp) / "energy_aggregated.csv"
            pd.DataFrame({
                "filename": ["hanoi", "sieve"],
                "average_package (uJ)": [100, 200],
                "methodology": [METHODOLOGY_MEASURED, "estimated_cpu_tdp"],
            }).to_csv(agg_path, index=False)
            energy_df = pd.DataFrame({
                "algorithm": ["hanoi", "sieve"],
                "cpython": [100.0, 200.0],
            })
            time_df = pd.DataFrame({
                "algorithm": ["hanoi", "sieve"],
                "cpython": [1.0, 2.0],
            })
            carbon_df = pd.DataFrame({
                "algorithm": ["hanoi", "sieve"],
                "cpython_CO2e_g": [0.1, 0.2],
            })
            result = calculate_greenscore(
                energy_df, time_df, carbon_df,
                aggregated_energy_paths={"cpython": agg_path},
            )
            assert "data_source_consistency" in result.columns
            row = result[result["method"] == "cpython"].iloc[0]
            assert row["data_source_consistency"] == "Inconsistent Data Source"

    def test_consistent_all_hardware(self):
        """All hardware -> Consistent."""
        with TemporaryDirectory() as tmp:
            agg_path = Path(tmp) / "energy_aggregated.csv"
            pd.DataFrame({
                "filename": ["hanoi", "sieve"],
                "average_package (uJ)": [100, 200],
                "methodology": [METHODOLOGY_MEASURED, METHODOLOGY_MEASURED],
            }).to_csv(agg_path, index=False)
            energy_df = pd.DataFrame({
                "algorithm": ["hanoi", "sieve"],
                "cpython": [100.0, 200.0],
            })
            time_df = pd.DataFrame({
                "algorithm": ["hanoi", "sieve"],
                "cpython": [1.0, 2.0],
            })
            carbon_df = pd.DataFrame({
                "algorithm": ["hanoi", "sieve"],
                "cpython_CO2e_g": [0.1, 0.2],
            })
            result = calculate_greenscore(
                energy_df, time_df, carbon_df,
                aggregated_energy_paths={"cpython": agg_path},
            )
            row = result[result["method"] == "cpython"].iloc[0]
            assert row["data_source_consistency"] == "Consistent"
