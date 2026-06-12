"""Regenerate empirical statistics for the PGSI paper from archived datasets."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

METHODS = ["cpython", "pypy", "cython", "ctypes", "py_compile"]
PY_COMPILE_SUFFIX = "_pycompile"


def _algo_from_energy_filename(stem: str) -> str | None:
    """Map energy_<algo>_<method>.csv stem to registry-style algorithm name."""
    if not stem.startswith("energy_"):
        return None
    body = stem[len("energy_") :]
    for method in METHODS:
        suffix = f"_{method}"
        if body.endswith(suffix):
            return body[: -len(suffix)]
    if body.endswith(PY_COMPILE_SUFFIX):
        return body[: -len(PY_COMPILE_SUFFIX)]
    return None


def load_platform(base: Path) -> tuple[list[str], np.ndarray, np.ndarray]:
    """Return algorithm list and energy/time matrices (rows=algorithms, cols=methods)."""
    by_algo: dict[str, dict[str, tuple[float, float]]] = {}
    for method in METHODS:
        energy_dir = base / f"temp_energy_{method}"
        time_dir = base / f"temp_time_{method}"
        if not energy_dir.exists() or not time_dir.exists():
            continue
        for energy_file in energy_dir.glob("energy_*.csv"):
            algo = _algo_from_energy_filename(energy_file.stem)
            if not algo:
                continue
            time_file = time_dir / energy_file.name.replace("energy_", "time_")
            if not time_file.exists():
                continue
            e_df = pd.read_csv(energy_file)
            t_df = pd.read_csv(time_file)
            e_col = "package (uJ)" if "package (uJ)" in e_df.columns else e_df.columns[3]
            t_col = (
                "execution_time (s)"
                if "execution_time (s)" in t_df.columns
                else "time (s)"
            )
            by_algo.setdefault(algo, {})[method] = (
                float(pd.to_numeric(e_df[e_col], errors="coerce").mean()),
                float(pd.to_numeric(t_df[t_col], errors="coerce").mean()),
            )
    algos = sorted(a for a, vals in by_algo.items() if len(vals) == len(METHODS))
    energy = np.array([[by_algo[a][m][0] for m in METHODS] for a in algos])
    time = np.array([[by_algo[a][m][1] for m in METHODS] for a in algos])
    return algos, energy, time


def friedman_block(energy: np.ndarray, time: np.ndarray) -> dict:
    n, k = energy.shape[0], energy.shape[1]
    stat_e, p_e = stats.friedmanchisquare(*[energy[:, i] for i in range(k)])
    stat_t, p_t = stats.friedmanchisquare(*[time[:, i] for i in range(k)])
    return {
        "n_blocks": n,
        "energy_chi2": float(stat_e),
        "energy_p": float(p_e),
        "energy_W": float(stat_e / (n * (k - 1))),
        "time_chi2": float(stat_t),
        "time_p": float(p_t),
        "time_W": float(stat_t / (n * (k - 1))),
    }


def summarize_platform(base: Path, label: str) -> str:
    algos, energy, time = load_platform(base)
    friedman = friedman_block(energy, time)
    gs = pd.read_csv(base / "GreenScore.csv")
    audit = json.loads((base / "audit_report.json").read_text(encoding="utf-8"))
    meth = audit.get("data_methodology_summary", {})
    lines = [
        f"## {label}",
        f"- Path: `{base.as_posix()}`",
        f"- Complete Friedman blocks: {friedman['n_blocks']} / {len(algos)} algorithms with all five methods",
        f"- Energy Friedman: $\\chi^2$={friedman['energy_chi2']:.4f}, $p$={friedman['energy_p']:.6f}, $W$={friedman['energy_W']:.4f}",
        f"- Time Friedman: $\\chi^2$={friedman['time_chi2']:.4f}, $p$={friedman['time_p']:.6f}, $W$={friedman['time_W']:.4f}",
        f"- Hardware-measured points: {meth.get('hardware_percentage', 'n/a')}\\%",
        f"- Estimated points: {meth.get('estimation_percentage', 'n/a')}\\%",
        "",
        "### GreenScore ranking (lower is better)",
        "",
        "| Method | GreenScore | $\\bar{{E}}'$ | $\\bar{{C}}'$ | $\\bar{{T}}'$ |",
        "|--------|------------|-------------|-------------|-------------|",
    ]
    for _, row in gs.iterrows():
        lines.append(
            f"| `{row['method']}` | {row['green_score']:.4f} | "
            f"{row['energy_norm_mean']:.3f} | {row['carbon_norm_mean']:.3f} | "
            f"{row['time_norm_mean']:.3f} |"
        )
    return "\n".join(lines)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out = root / "pgsi_statistics_summary.md"
    boot_path = root / "paper" / "tables" / "bootstrap_greenscore_ci.csv"
    boot_note = ""
    if boot_path.exists():
        boot_note = (
            f"\n\nBootstrap 95% CIs: see `{boot_path.relative_to(root)}` "
            "(from `scripts/bootstrap_confidence_intervals.py`)."
        )
    sections = [
        "# PGSI empirical statistics summary",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Regenerate all figures: `python scripts/run_paper_analysis.py`",
        "",
        summarize_platform(root / "data" / "linux-intel-pc", "Linux Intel PC (hardware RAPL)"),
        "",
        summarize_platform(root / "data" / "windows-amd-laptop", "Windows AMD laptop (TDP estimation)"),
        boot_note,
    ]
    out.write_text("\n".join(sections), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
