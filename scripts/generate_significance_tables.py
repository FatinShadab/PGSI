#!/usr/bin/env python3
"""Generate Friedman significance LaTeX table (deprecated: use generate_latex_tables.py)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    script = Path(__file__).resolve().parent / "generate_latex_tables.py"
    subprocess.run([sys.executable, str(script), *sys.argv[1:]], check=True)


if __name__ == "__main__":
    main()
