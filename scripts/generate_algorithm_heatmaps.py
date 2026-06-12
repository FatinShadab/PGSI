#!/usr/bin/env python3
"""
Per-algorithm winner exports.

Primary output: LaTeX table (algorithm_winners_combined.tex) via generate_latex_tables.py.
Optional: heatmap PNG/PDF when --heatmaps is passed (supplementary only).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from _paper_common import (
    METHODS,
    METHOD_LABELS,
    apply_plot_style,
    paper_figures_dir,
    paper_tables_dir,
    per_algorithm_winners,
    platform_dirs,
    repo_root,
)


METRIC_MAP = {
    "winner_energy": "Lowest energy",
    "winner_time": "Fastest runtime",
    "winner_greenscore": "Best per-algorithm GreenScore",
}


def _winner_matrix(winners: pd.DataFrame, col: str) -> pd.DataFrame:
    """Rows=algorithms, columns=methods, 1 if method wins that algorithm."""
    mat = pd.DataFrame(0, index=winners["algorithm"], columns=METHODS)
    for _, row in winners.iterrows():
        mat.loc[row["algorithm"], row[col]] = 1
    mat.index = [a.replace("_", "-") for a in mat.index]
    return mat


def plot_heatmap(mat: pd.DataFrame, title: str, out_path: Path) -> None:
    apply_plot_style()
    fig, ax = plt.subplots(figsize=(6.5, max(4.0, 0.28 * len(mat))))
    sns.heatmap(
        mat,
        cmap="YlGn",
        linewidths=0.5,
        linecolor="#cccccc",
        cbar_kws={"label": "Winner (1=yes)"},
        ax=ax,
        vmin=0,
        vmax=1,
    )
    ax.set_title(title, fontsize=10)
    ax.set_xlabel("Execution method")
    ax.set_ylabel("Algorithm")
    ax.set_xticklabels([METHOD_LABELS[m] for m in METHODS], rotation=30, ha="right")
    fig.savefig(out_path.with_suffix(".pdf"))
    fig.savefig(out_path.with_suffix(".png"))
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=None)
    parser.add_argument(
        "--heatmaps",
        action="store_true",
        help="Also write supplementary heatmap images (not used in the LaTeX paper)",
    )
    args = parser.parse_args()
    root = args.data_root or repo_root()
    out_fig = paper_figures_dir()
    out_tab = paper_tables_dir()

    latex_script = Path(__file__).resolve().parent / "generate_latex_tables.py"
    subprocess.run([sys.executable, str(latex_script), "--data-root", str(root)], check=True)

    if not args.heatmaps:
        print("LaTeX winner table written (use --heatmaps for optional heatmap images).")
        return

    for plat in platform_dirs(root):
        winners = per_algorithm_winners(plat.base)
        winners.to_csv(out_tab / f"algorithm_winners_{plat.key}.csv", index=False)
        for col, label in METRIC_MAP.items():
            mat = _winner_matrix(winners, col)
            fname = out_fig / f"fig06_winners_{col.replace('winner_', '')}_{plat.key}"
            plot_heatmap(
                mat,
                f"{plat.meta['label']}: {label}",
                fname,
            )
    # Combined faceted summary (one figure, three metrics x two platforms = use 2x3 subplots)
    apply_plot_style()
    fig, axes = plt.subplots(2, 3, figsize=(12, 7))
    for i, plat in enumerate(platform_dirs(root)):
        winners = per_algorithm_winners(plat.base)
        for j, (col, label) in enumerate(METRIC_MAP.items()):
            mat = _winner_matrix(winners, col)
            sns.heatmap(
                mat,
                ax=axes[i, j],
                cmap="YlGn",
                cbar=False,
                vmin=0,
                vmax=1,
                linewidths=0.3,
            )
            axes[i, j].set_title(f"{plat.meta['short']}: {label}", fontsize=8)
            if j == 0:
                axes[i, j].set_ylabel("Algorithm")
            else:
                axes[i, j].set_ylabel("")
            axes[i, j].set_xlabel("")
    fig.suptitle("Per-algorithm winning method (1 = winner for that workload)", fontsize=10)
    fig.tight_layout()
    combined = out_fig / "fig06_algorithm_winner_matrix"
    fig.savefig(combined.with_suffix(".pdf"))
    fig.savefig(combined.with_suffix(".png"))
    plt.close(fig)
    print(f"Wrote fig06 heatmaps to {out_fig}")


if __name__ == "__main__":
    main()
