#!/usr/bin/env python3
"""Build hardware and experiment summary tables for the PGSI paper."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from _paper_common import load_audit, paper_tables_dir, platform_dirs, repo_root


def _load_system_info(base: Path) -> dict:
    path = base / "system_info_pyrapl.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def build_summary_table(root: Path) -> pd.DataFrame:
    rows = []
    for plat in platform_dirs(root):
        sysinfo = _load_system_info(plat.base)
        audit = load_audit(plat.base)
        meth = audit.get("data_methodology_summary", {})
        rows.append(
            {
                "Platform ID": plat.key,
                "Host label": plat.meta["label"],
                "CPU": sysinfo.get("CPU", "—"),
                "Physical cores": sysinfo.get("Cores_Physical", "—"),
                "Logical cores": sysinfo.get("Cores_Logical", "—"),
                "RAM (GB)": sysinfo.get("RAM_GB", "—"),
                "OS": sysinfo.get("OS", "—"),
                "Architecture": sysinfo.get("Architecture", "—"),
                "Measurement": plat.meta["measurement_note"],
                "Methodology tag": plat.meta["methodology"],
                "Benchmark runs ($R$)": 50,
                "Algorithms": 15,
                "Methods": 5,
                "Hardware-measured (\\%)": meth.get("hardware_percentage", 0),
                "Estimated (\\%)": meth.get("estimation_percentage", 0),
                "PGSI version": "1.0.2",
            }
        )
    return pd.DataFrame(rows)


def _tex_escape(text: str) -> str:
    return (
        str(text)
        .replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def to_latex(df: pd.DataFrame, path: Path) -> None:
    """Write a compact IEEE-friendly LaTeX table."""
    rows = []
    for _, r in df.iterrows():
        cpu = _tex_escape(str(r["CPU"]))
        if len(cpu) > 38:
            cpu = cpu[:35] + "..."
        rows.append(
            " & ".join(
                [
                    _tex_escape(r["Platform ID"]),
                    cpu,
                    f"{r['Physical cores']}/{r['Logical cores']}",
                    f"{r['RAM (GB)']}",
                    _tex_escape(str(r["OS"])[:24]),
                    _tex_escape("RAPL" if "RAPL" in str(r["Measurement"]) else "TDP model"),
                    f"{int(r['Hardware-measured (\\%)'])}\\%/{int(r['Estimated (\\%)'])}\\%",
                    str(int(r["Benchmark runs ($R$)"])),
                ]
            )
            + r" \\"
        )
    body = "\n".join(rows)
    latex = rf"""\begin{{table*}}[t]
\centering
\caption{{Experimental platforms and measurement configuration (PGSI {df['PGSI version'].iloc[0]}).}}
\label{{tab:hardware_summary}}
\renewcommand{{\arraystretch}}{{1.1}}
\footnotesize
\begin{{tabular}}{{@{{}}llllllcc@{{}}}}
\toprule
\textbf{{ID}} & \textbf{{CPU}} & \textbf{{Cores (P/L)}} & \textbf{{RAM}} & \textbf{{OS}} & \textbf{{Energy path}} & \textbf{{Meas./Est.}} & \textbf{{$R$}} \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\end{{table*}}
"""
    path.write_text(latex, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=None)
    args = parser.parse_args()
    root = args.data_root or repo_root()
    out = paper_tables_dir()
    df = build_summary_table(root)
    csv_path = out / "hardware_summary.csv"
    tex_path = out / "hardware_summary.tex"
    df.to_csv(csv_path, index=False)
    to_latex(df, tex_path)
    print(f"Wrote {csv_path} and {tex_path}")


if __name__ == "__main__":
    main()
