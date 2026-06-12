#!/usr/bin/env python3
"""
Generate publication-quality figures for the PGSI paper.

Outputs static PDF/PNG/SVG and interactive HTML (Plotly) under paper/figures/.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import pandas as pd
import seaborn as sns

from _paper_common import (
    DEFAULT_ALPHA,
    DEFAULT_BETA,
    DEFAULT_GAMMA,
    METHOD_COLORS,
    METHOD_LABELS,
    METHODS,
    PLATFORM_META,
    apply_plot_style,
    bootstrap_greenscore_ci,
    load_raw_metric_runs,
    paper_figures_dir,
    platform_dirs,
    repo_root,
)

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


def _save_static(fig: plt.Figure, base: Path) -> None:
    fig.savefig(base.with_suffix(".pdf"))
    fig.savefig(base.with_suffix(".png"))
    fig.savefig(base.with_suffix(".svg"))


def fig01_greenscore_comparison(root: Path, n_boot: int, seed: int) -> None:
    """GreenScore bar charts with bootstrap CI per platform."""
    apply_plot_style()
    records = []
    for plat in platform_dirs(root):
        ci_df = bootstrap_greenscore_ci(plat.base, n_boot=n_boot, seed=seed)
        for _, row in ci_df.iterrows():
            records.append(
                {
                    "platform": plat.meta["short"],
                    "platform_full": plat.meta["label"],
                    "method": row["method"],
                    "green_score": row["green_score"],
                    "ci_low": row["ci_low"],
                    "ci_high": row["ci_high"],
                }
            )
    df = pd.DataFrame(records)
    df["method_label"] = df["method"].map(METHOD_LABELS)

    fig, axes = plt.subplots(1, 2, figsize=(8.5, 3.5), sharey=True)
    for ax, plat in zip(axes, platform_dirs(root)):
        sub = df[df["platform"] == plat.meta["short"]].sort_values("green_score")
        y = sub["green_score"]
        yerr = np.vstack([y - sub["ci_low"], sub["ci_high"] - y])
        colors = [METHOD_COLORS[m] for m in sub["method"]]
        ax.bar(
            sub["method_label"],
            y,
            yerr=yerr,
            capsize=3,
            color=colors,
            edgecolor="black",
            linewidth=0.4,
        )
        ax.set_title(plat.meta["label"])
        ax.set_ylabel("GreenScore" if ax is axes[0] else "")
        ax.tick_params(axis="x", rotation=30)
    fig.suptitle(
        "GreenScore with 95\\% bootstrap CI (block bootstrap over 15 algorithms)",
        fontsize=10,
    )
    fig.text(
        0.5,
        -0.02,
        "Linux: RAPL measured  |  Windows: TDP estimated  |  Cross-host bars are not comparable.",
        ha="center",
        fontsize=7,
        style="italic",
    )
    fig.tight_layout()
    _save_static(fig, paper_figures_dir() / "fig01_greenscore_comparison")
    plt.close(fig)

    if HAS_PLOTLY:
        fig_p = make_subplots(rows=1, cols=2, subplot_titles=[p.meta["label"] for p in platform_dirs(root)])
        for col, plat in enumerate(platform_dirs(root), start=1):
            sub = df[df["platform"] == plat.meta["short"]].sort_values("green_score")
            fig_p.add_trace(
                go.Bar(
                    x=sub["method_label"],
                    y=sub["green_score"],
                    error_y=dict(
                        type="data",
                        symmetric=False,
                        array=sub["ci_high"] - sub["green_score"],
                        arrayminus=sub["green_score"] - sub["ci_low"],
                    ),
                    marker_color=[METHOD_COLORS[m] for m in sub["method"]],
                    name=plat.meta["label"],
                ),
                row=1,
                col=col,
            )
        fig_p.update_layout(
            title_text="GreenScore with bootstrap CI",
            template="plotly_white",
            height=420,
            showlegend=False,
        )
        fig_p.write_html(str(paper_figures_dir() / "fig01_greenscore_comparison.html"))


def fig02_energy_distributions(root: Path) -> None:
    apply_plot_style()
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.2), sharey=False)
    for ax, plat in zip(axes, platform_dirs(root)):
        long = load_raw_metric_runs(plat.base, "energy")
        long["method_label"] = long["method"].map(METHOD_LABELS)
        long["log_energy"] = np.log10(long["value"].clip(lower=1.0))
        sns.violinplot(
            data=long,
            x="method_label",
            y="log_energy",
            order=[METHOD_LABELS[m] for m in METHODS],
            palette=[METHOD_COLORS[m] for m in METHODS],
            inner="quartile",
            cut=0,
            ax=ax,
        )
        sns.stripplot(
            data=long.sample(min(800, len(long)), random_state=42),
            x="method_label",
            y="log_energy",
            order=[METHOD_LABELS[m] for m in METHODS],
            color="black",
            alpha=0.12,
            size=1.5,
            jitter=0.25,
            ax=ax,
        )
        ax.set_title(plat.meta["label"])
        ax.set_xlabel("Execution method")
        ax.set_ylabel(r"$\log_{10}$ energy ($\mu$J)")
        ax.tick_params(axis="x", rotation=25)
    fig.suptitle(
        "Per-run energy distributions (all workloads pooled; $R{=}50$ per workload--method)",
        fontsize=10,
    )
    fig.tight_layout()
    _save_static(fig, paper_figures_dir() / "fig02_energy_distributions")
    plt.close(fig)

    if HAS_PLOTLY:
        for plat in platform_dirs(root):
            long = load_raw_metric_runs(plat.base, "energy")
            long["method_label"] = long["method"].map(METHOD_LABELS)
            fig_p = go.Figure()
            for m in METHODS:
                sub = long[long["method"] == m]
                fig_p.add_trace(
                    go.Violin(
                        y=sub["value"],
                        name=METHOD_LABELS[m],
                        box_visible=True,
                        meanline_visible=True,
                        marker_color=METHOD_COLORS[m],
                    )
                )
            fig_p.update_layout(
                title=f"Energy distribution — {plat.meta['label']}",
                yaxis_title="Energy (μJ)",
                yaxis_type="log",
                template="plotly_white",
            )
            fig_p.write_html(
                str(paper_figures_dir() / f"fig02_energy_{plat.key}.html")
            )


def fig03_runtime_distributions(root: Path) -> None:
    apply_plot_style()
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.2))
    for ax, plat in zip(axes, platform_dirs(root)):
        long = load_raw_metric_runs(plat.base, "time")
        long["method_label"] = long["method"].map(METHOD_LABELS)
        sns.boxplot(
            data=long,
            x="method_label",
            y="value",
            order=[METHOD_LABELS[m] for m in METHODS],
            palette=[METHOD_COLORS[m] for m in METHODS],
            fliersize=2,
            ax=ax,
        )
        ax.set_title(plat.meta["label"])
        ax.set_xlabel("Execution method")
        ax.set_ylabel("Execution time (s)")
        ax.tick_params(axis="x", rotation=25)
    fig.suptitle("Per-run runtime distributions (Friedman input data)", fontsize=10)
    fig.tight_layout()
    _save_static(fig, paper_figures_dir() / "fig03_runtime_distributions")
    plt.close(fig)


def fig04_component_decomposition(root: Path) -> None:
    apply_plot_style()
    fig, axes = plt.subplots(1, 2, figsize=(8.5, 3.8), sharey=True)
    components = [
        ("energy_norm_mean", r"$\bar{E}'$", DEFAULT_ALPHA),
        ("carbon_norm_mean", r"$\bar{C}'$", DEFAULT_BETA),
        ("time_norm_mean", r"$\bar{T}'$", DEFAULT_GAMMA),
    ]
    comp_colors = ["#332288", "#88CCEE", "#CC6677"]
    for ax, plat in zip(axes, platform_dirs(root)):
        gs = pd.read_csv(plat.base / "GreenScore.csv").sort_values("green_score")
        methods = gs["method"].tolist()
        bottom = np.zeros(len(methods))
        for (col, label, _w), color in zip(components, comp_colors):
            vals = gs.set_index("method").reindex(methods)[col].values
            ax.bar(
                [METHOD_LABELS[m] for m in methods],
                vals,
                bottom=bottom,
                label=label,
                color=color,
                edgecolor="white",
                linewidth=0.3,
            )
            bottom += vals
        ax.set_title(plat.meta["label"])
        ax.set_ylabel("Stacked normalized component means")
        ax.tick_params(axis="x", rotation=25)
        ax.set_ylim(0, max(bottom) * 1.05)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.02))
    fig.suptitle(
        "GreenScore component decomposition (weights: "
        rf"$\alpha={DEFAULT_ALPHA}$, $\beta={DEFAULT_BETA}$, $\gamma={DEFAULT_GAMMA}$)",
        fontsize=10,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    _save_static(fig, paper_figures_dir() / "fig04_greenscore_components")
    plt.close(fig)


def fig05_methodology_flow(root: Path) -> None:
    apply_plot_style()
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")

    def box(x, y, text, color="#E8F4EA", width=2.2, height=0.55):
        rect = FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle="round,pad=0.03",
            facecolor=color,
            edgecolor="#333333",
            linewidth=0.8,
        )
        ax.add_patch(rect)
        ax.text(x + width / 2, y + height / 2, text, ha="center", va="center", fontsize=7)

    def arrow(x1, y1, x2, y2):
        ax.add_patch(
            FancyArrowPatch(
                (x1, y1),
                (x2, y2),
                arrowstyle="-|>",
                mutation_scale=10,
                color="#444444",
                linewidth=0.9,
            )
        )

    # Linux row
    ax.text(0.2, 5.3, "Linux (x86\\_64)", fontsize=9, fontweight="bold")
    lx = [0.3, 2.7, 5.1, 7.5]
    labels_l = ["Benchmark\n(subprocess)", "pyRAPL / RAPL\n(measured $\\mu$J)", "Carbon model\n($E \\times CI$)", "GreenScore\n(normalize + WLC)"]
    for i, (x, lab) in enumerate(zip(lx, labels_l)):
        box(x, 4.5, lab, color="#D4EDDA")
        if i < len(lx) - 1:
            arrow(x + 2.2, 4.78, lx[i + 1], 4.78)

    # Windows row
    ax.text(0.2, 2.8, "Windows / non-RAPL", fontsize=9, fontweight="bold")
    labels_w = ["Benchmark\n(subprocess)", "Wall time +\nTDP lookup", "Estimated $\\mu$J", "Carbon model", "GreenScore"]
    wx = [0.3, 2.3, 4.3, 6.3, 8.1]
    for i, (x, lab) in enumerate(zip(wx, labels_w)):
        w = 1.7 if i == 2 else 1.9
        box(x, 2.0, lab, color="#FFF3CD", width=w)
        if i < len(wx) - 1:
            arrow(x + w, 2.28, wx[i + 1], 2.28)

    ax.text(
        5,
        0.4,
        "Measurement mode is logged per sample (\\texttt{hardware\\_rapl\\_linux} vs.\\ \\texttt{generic\\_tdp}).\n"
        "Do not compare absolute energy across hosts.",
        ha="center",
        fontsize=7.5,
        style="italic",
    )
    ax.set_title("PGSI measurement pipelines by platform", fontsize=10)
    _save_static(fig, paper_figures_dir() / "fig05_methodology_flow")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate PGSI publication figures")
    parser.add_argument("--data-root", type=Path, default=None)
    parser.add_argument("--n-boot", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--skip-plotly", action="store_true")
    args = parser.parse_args()
    global HAS_PLOTLY
    if args.skip_plotly:
        HAS_PLOTLY = False

    root = args.data_root or repo_root()
    print("Generating figures...")
    fig01_greenscore_comparison(root, args.n_boot, args.seed)
    fig02_energy_distributions(root)
    fig03_runtime_distributions(root)
    fig04_component_decomposition(root)
    fig05_methodology_flow(root)
    print(f"Done. Output: {paper_figures_dir()} (tables: paper/tables/ via generate_latex_tables.py)")


if __name__ == "__main__":
    main()
