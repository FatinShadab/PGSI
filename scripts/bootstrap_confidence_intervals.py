#!/usr/bin/env python3
"""Compute bootstrap confidence intervals for GreenScore and per-method metrics."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _paper_common import (
    bootstrap_greenscore_ci,
    bootstrap_metric_ci,
    load_raw_metric_runs,
    paper_tables_dir,
    platform_dirs,
    repo_root,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap CIs for PGSI paper metrics")
    parser.add_argument("--data-root", type=Path, default=None)
    parser.add_argument("--n-boot", type=int, default=5000)
    parser.add_argument("--ci", type=float, default=0.95)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    root = args.data_root or repo_root()
    out_dir = paper_tables_dir()
    all_gs: list[pd.DataFrame] = []
    all_energy: list[pd.DataFrame] = []
    all_time: list[pd.DataFrame] = []

    for plat in platform_dirs(root):
        gs_ci = bootstrap_greenscore_ci(
            plat.base, n_boot=args.n_boot, ci=args.ci, seed=args.seed
        )
        gs_ci.insert(0, "platform", plat.key)
        all_gs.append(gs_ci)

        energy_long = load_raw_metric_runs(plat.base, "energy")
        time_long = load_raw_metric_runs(plat.base, "time")
        e_ci = bootstrap_metric_ci(
            energy_long, ["method"], n_boot=min(args.n_boot, 2000), ci=args.ci, seed=args.seed
        )
        t_ci = bootstrap_metric_ci(
            time_long, ["method"], n_boot=min(args.n_boot, 2000), ci=args.ci, seed=args.seed
        )
        e_ci.insert(0, "platform", plat.key)
        t_ci.insert(0, "platform", plat.key)
        all_energy.append(e_ci)
        all_time.append(t_ci)

    gs_path = out_dir / "bootstrap_greenscore_ci.csv"
    pd.concat(all_gs, ignore_index=True).to_csv(gs_path, index=False)
    pd.concat(all_energy, ignore_index=True).to_csv(
        out_dir / "bootstrap_energy_ci.csv", index=False
    )
    pd.concat(all_time, ignore_index=True).to_csv(
        out_dir / "bootstrap_time_ci.csv", index=False
    )
    print(f"Wrote {gs_path}")


if __name__ == "__main__":
    main()
