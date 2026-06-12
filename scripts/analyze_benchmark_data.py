"""Analyze PGSI benchmark datasets for paper statistics."""
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

METHODS = ["cpython", "pypy", "cython", "ctypes", "py_compile"]


def load_platform(base: Path):
    algos = set()
    for m in METHODS:
        d = base / f"temp_energy_{m}"
        if d.exists():
            for f in d.glob("energy_*.csv"):
                stem = f.stem.replace("energy_", "")
                algo = stem.rsplit("_", 1)[0]
                algos.add(algo)
    algos = sorted(algos)
    energy = {a: {} for a in algos}
    time = {a: {} for a in algos}
    for m in METHODS:
        ed = base / f"temp_energy_{m}"
        td = base / f"temp_time_{m}"
        if not ed.exists():
            continue
        for f in ed.glob("energy_*.csv"):
            algo = f.stem.replace("energy_", "").rsplit("_", 1)[0]
            df = pd.read_csv(f)
            col = "package (uJ)" if "package (uJ)" in df.columns else df.columns[3]
            energy[algo][m] = df[col].mean()
            energy[algo][f"{m}_std"] = df[col].std()
            energy[algo][f"{m}_n"] = len(df)
        for f in td.glob("time_*.csv"):
            algo = f.stem.replace("time_", "").rsplit("_", 1)[0]
            df = pd.read_csv(f)
            if "execution_time (s)" in df.columns:
                col = "execution_time (s)"
            elif "time (s)" in df.columns:
                col = "time (s)"
            else:
                numeric_cols = [
                    c for c in df.columns
                    if c not in ("timestamp", "function", "run") and pd.api.types.is_numeric_dtype(df[c])
                ]
                col = numeric_cols[0] if numeric_cols else df.columns[-1]
            time[algo][m] = pd.to_numeric(df[col], errors="coerce").mean()
    return algos, energy, time


def friedman_analysis(base: Path, label: str):
    algos, energy, time = load_platform(base)
    print(f"\n=== {label} ===")
    print(f"Algorithms: {len(algos)}")
    e_rows, t_rows = [], []
    valid_algos = []
    for a in algos:
        if all(m in energy[a] for m in METHODS) and all(m in time[a] for m in METHODS):
            e_rows.append([energy[a][m] for m in METHODS])
            t_rows.append([time[a][m] for m in METHODS])
            valid_algos.append(a)
    e_arr = np.array(e_rows)
    t_arr = np.array(t_rows)
    print(f"Complete blocks: {len(valid_algos)}")
    stat_e, p_e = stats.friedmanchisquare(*[e_arr[:, i] for i in range(5)])
    stat_t, p_t = stats.friedmanchisquare(*[t_arr[:, i] for i in range(5)])
    n, k = len(valid_algos), 5
    W_e = stat_e / (n * (k - 1))
    W_t = stat_t / (n * (k - 1))
    print(f"Energy Friedman: chi2={stat_e:.4f}, p={p_e:.6f}, W={W_e:.4f}")
    print(f"Time Friedman: chi2={stat_t:.4f}, p={p_t:.6f}, W={W_t:.4f}")
    ranks_e = np.apply_along_axis(lambda row: stats.rankdata(row), 1, e_arr)
    mean_ranks_e = ranks_e.mean(axis=0)
    ranks_t = np.apply_along_axis(lambda row: stats.rankdata(row), 1, t_arr)
    mean_ranks_t = ranks_t.mean(axis=0)
    print("Energy mean ranks (lower=better):")
    for m, r in sorted(zip(METHODS, mean_ranks_e), key=lambda x: x[1]):
        print(f"  {m}: {r:.3f}")
    print("Time mean ranks (lower=better):")
    for m, r in sorted(zip(METHODS, mean_ranks_t), key=lambda x: x[1]):
        print(f"  {m}: {r:.3f}")
    gs = pd.read_csv(base / "GreenScore.csv")
    print("GreenScore ranking (lower=better):")
    for _, row in gs.iterrows():
        print(
            f"  {row['method']}: green_score={row['green_score']:.4f}, "
            f"E'={row['energy_norm_mean']:.3f}, C'={row['carbon_norm_mean']:.3f}, "
            f"T'={row['time_norm_mean']:.3f}"
        )
    sample = next((base / "temp_energy_cpython").glob("*.csv"))
    df = pd.read_csv(sample, nrows=5)
    if "methodology" in df.columns:
        print(f"Methodology: {df['methodology'].unique()}")
    if "cpython_n" in energy.get(valid_algos[0], {}):
        print(f"Runs per file (sample): {energy[valid_algos[0]].get('cpython_n')}")
    return valid_algos


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    friedman_analysis(root / "data" / "windows-amd-laptop", "Windows AMD Laptop")
    friedman_analysis(root / "data" / "linux-intel-pc", "Linux Intel PC")
