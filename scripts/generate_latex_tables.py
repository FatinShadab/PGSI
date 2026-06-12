#!/usr/bin/env python3
"""Generate LaTeX tables for paper content (replaces table-as-figure exports)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from _paper_common import (
    METHOD_LABELS,
    friedman_tests,
    load_audit,
    paper_tables_dir,
    per_algorithm_winners,
    platform_dirs,
    repo_root,
)

METHOD_ABBR = {
    "cpython": "CPy",
    "pypy": "PyPy",
    "cython": "Cy",
    "ctypes": "ct",
    "py_compile": "pyc",
}


def _abbr(method: str) -> str:
    return METHOD_ABBR.get(method, method)


def _tex_escape(text: str) -> str:
    return (
        str(text)
        .replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def _texttt_identifier(name: str) -> str:
    return "\\texttt{" + _tex_escape(name) + "}"


def write_measurement_fidelity_tex(root: Path, path: Path) -> None:
    rows = []
    for plat in platform_dirs(root):
        audit = load_audit(plat.base)
        m = audit.get("data_methodology_summary", {})
        rows.append(
            f"{plat.meta['short']} & "
            f"{m.get('hardware_percentage', 0):.0f}\\% & "
            f"{m.get('estimation_percentage', 0):.0f}\\% & "
            f"{_texttt_identifier(plat.meta['methodology'])} \\\\"
        )
    body = "\n".join(rows)
    tex = rf"""\begin{{table}}[t]
\centering
\caption{{Measurement fidelity: share of algorithm--method energy points ($15 \times 5$) by acquisition mode.}}
\label{{tab:measurement_fidelity}}
\renewcommand{{\arraystretch}}{{1.1}}
\begin{{tabular}}{{@{{}}lrrl@{{}}}}
\toprule
\textbf{{Host}} & \textbf{{Hardware-measured}} & \textbf{{Estimated}} & \textbf{{Primary tag}} \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\end{{table}}
"""
    path.write_text(tex, encoding="utf-8")


def write_significance_tex(root: Path, path: Path) -> None:
    rows = []
    for plat in platform_dirs(root):
        f = friedman_tests(plat.base)
        label = plat.meta["short"]
        for metric_name, chi2, p, w, key in [
            ("Energy", f["energy_chi2"], f["energy_p"], f["energy_W"], "energy"),
            ("Runtime", f["time_chi2"], f["time_p"], f["time_W"], "time"),
        ]:
            sig = "Yes" if p < 0.05 else "No"
            rows.append(
                f"{label} & {metric_name} & {f['n_blocks']} & {chi2:.2f} & {p:.4f} & {w:.3f} & {sig} \\\\"
            )
    body = "\n".join(rows)
    tex = rf"""\begin{{table}}[t]
\centering
\caption{{Friedman tests by host (algorithms as blocks, five methods as treatments; $\alpha=0.05$). Linux contrasts are significant for energy and runtime; Windows contrasts are not in this artifact.}}
\label{{tab:significance}}
\renewcommand{{\arraystretch}}{{1.08}}
\footnotesize
\begin{{tabular}}{{@{{}}llrrrrl@{{}}}}
\toprule
\textbf{{Host}} & \textbf{{Metric}} & $n$ & $\chi^2$ & $p$ & $W$ & \textbf{{Sig.}} \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\end{{table}}
"""
    path.write_text(tex, encoding="utf-8")


def write_algorithm_winners_tex(root: Path, path: Path) -> None:
    by_key = {p.key: p for p in platform_dirs(root)}
    linux = per_algorithm_winners(by_key["linux-intel-pc"].base)
    win = per_algorithm_winners(by_key["windows-amd-laptop"].base)
    merged = linux.merge(
        win,
        on="algorithm",
        suffixes=("_linux", "_windows"),
    )
    merged["algorithm"] = merged["algorithm"].str.replace("_", "-")

    rows = []
    for _, r in merged.iterrows():
        rows.append(
            f"{r['algorithm']} & "
            f"\\texttt{{{_abbr(r['winner_energy_linux'])}}} & "
            f"\\texttt{{{_abbr(r['winner_time_linux'])}}} & "
            f"\\texttt{{{_abbr(r['winner_greenscore_linux'])}}} & "
            f"\\texttt{{{_abbr(r['winner_energy_windows'])}}} & "
            f"\\texttt{{{_abbr(r['winner_time_windows'])}}} & "
            f"\\texttt{{{_abbr(r['winner_greenscore_windows'])}}} \\\\"
        )
    body = "\n".join(rows)
    tex = rf"""\begin{{table*}}[t]
\centering
\caption{{Per-algorithm winning execution method by metric and host (lower raw energy/time or lower per-row GreenScore). Abbreviations: ct=ctypes, Cy=cython, PyPy, CPy=cpython, pyc=py\_compile. No method wins all workloads on either host.}}
\label{{tab:algorithm_winners}}
\renewcommand{{\arraystretch}}{{1.05}}
\footnotesize
\begin{{tabular}}{{@{{}}l|ccc|ccc@{{}}}}
\toprule
& \multicolumn{{3}}{{c|}}{{\textbf{{Linux (RAPL)}}}} & \multicolumn{{3}}{{c}}{{\textbf{{Windows (TDP est.)}}}} \\
\cmidrule(lr){{2-4}} \cmidrule(lr){{5-7}}
\textbf{{Algorithm}} & $\bar{{E}}$ & $\bar{{T}}$ & GS & $\bar{{E}}$ & $\bar{{T}}$ & GS \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\end{{table*}}
"""
    path.write_text(tex, encoding="utf-8")
    merged.to_csv(path.with_suffix(".csv"), index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=None)
    args = parser.parse_args()
    root = args.data_root or repo_root()
    out = paper_tables_dir()

    write_measurement_fidelity_tex(root, out / "measurement_fidelity.tex")
    write_significance_tex(root, out / "significance_summary.tex")
    write_algorithm_winners_tex(root, out / "algorithm_winners_combined.tex")

    # CSV for significance (same data as before)
    rows = []
    for plat in platform_dirs(root):
        f = friedman_tests(plat.base)
        for metric, chi2, p, w in [
            ("Energy", f["energy_chi2"], f["energy_p"], f["energy_W"]),
            ("Runtime", f["time_chi2"], f["time_p"], f["time_W"]),
        ]:
            rows.append(
                {
                    "Platform": plat.meta["short"],
                    "Metric": metric,
                    "Blocks (n)": f["n_blocks"],
                    "chi2": chi2,
                    "p": p,
                    "W": w,
                    "Significant": p < 0.05,
                }
            )
    pd.DataFrame(rows).to_csv(out / "significance_summary.csv", index=False)

    print(f"Wrote LaTeX tables to {out}")


if __name__ == "__main__":
    main()
