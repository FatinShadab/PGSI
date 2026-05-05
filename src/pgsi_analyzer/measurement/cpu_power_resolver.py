"""
CPU power resolver backed by a packaged dataset.
"""

from __future__ import annotations

import csv
import statistics
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path
from typing import List, Dict, Any


DEFAULT_TDP_WATTS = 65.0
_FUZZY_THRESHOLD = 0.72


@dataclass(frozen=True)
class CpuPowerResolution:
    tdp_watts: float
    match_type: str
    matched_model: str
    source: str
    normalized_query: str


def _normalize_cpu_name(cpu_name: str) -> str:
    text = (cpu_name or "").lower().strip()
    text = re.sub(r"\(r\)|\(tm\)|®|™", " ", text)
    text = re.sub(r"@\s*\d+(\.\d+)?\s*ghz", " ", text)
    text = re.sub(r"\d+(\.\d+)?\s*ghz", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parse_tdp_watts(raw_value: str) -> float:
    """Parse TDP values that may be scalar or range-like strings."""
    numbers = re.findall(r"\d+(?:\.\d+)?", raw_value or "")
    if not numbers:
        raise ValueError(f"Unable to parse TDP from value: {raw_value!r}")
    values = [float(n) for n in numbers]
    if len(values) == 1:
        return values[0]
    return float(statistics.mean(values))


@lru_cache(maxsize=1)
def _load_dataset() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    dataset_path = Path(__file__).resolve().parents[1] / "config" / "cpu_power.csv"
    with dataset_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Support both PGSI-curated and upstream CodeCarbon schemas.
            model = (row.get("model") or row.get("Name") or "").strip()
            tdp_raw = (row.get("tdp_watts") or row.get("TDP") or "").strip()
            aliases_raw = (row.get("aliases") or "").strip()
            if not model or not tdp_raw:
                continue
            aliases = [a.strip() for a in aliases_raw.split("|") if a.strip()]
            rows.append(
                {
                    "model": model,
                    "normalized_model": _normalize_cpu_name(model),
                    "tdp_watts": _parse_tdp_watts(tdp_raw),
                    "aliases": aliases,
                    "normalized_aliases": [_normalize_cpu_name(a) for a in aliases],
                }
            )
    return rows


def resolve_cpu_power(cpu_name: str) -> CpuPowerResolution:
    normalized = _normalize_cpu_name(cpu_name)
    dataset = _load_dataset()

    if normalized:
        for row in dataset:
            names = [row["normalized_model"], *row["normalized_aliases"]]
            if normalized in names:
                return CpuPowerResolution(
                    tdp_watts=row["tdp_watts"],
                    match_type="exact",
                    matched_model=row["model"],
                    source="codecarbon_cpu_power_csv",
                    normalized_query=normalized,
                )

        for row in dataset:
            names = [row["normalized_model"], *row["normalized_aliases"]]
            if any(name and (name in normalized or normalized in name) for name in names):
                return CpuPowerResolution(
                    tdp_watts=row["tdp_watts"],
                    match_type="regex",
                    matched_model=row["model"],
                    source="codecarbon_cpu_power_csv",
                    normalized_query=normalized,
                )

        best_ratio = 0.0
        best_row = None
        for row in dataset:
            names = [row["normalized_model"], *row["normalized_aliases"]]
            ratio = max((SequenceMatcher(None, normalized, name).ratio() for name in names if name), default=0.0)
            if ratio > best_ratio:
                best_ratio = ratio
                best_row = row

        if best_row is not None and best_ratio >= _FUZZY_THRESHOLD:
            return CpuPowerResolution(
                tdp_watts=best_row["tdp_watts"],
                match_type="fuzzy",
                matched_model=best_row["model"],
                source="codecarbon_cpu_power_csv",
                normalized_query=normalized,
            )

    return CpuPowerResolution(
        tdp_watts=DEFAULT_TDP_WATTS,
        match_type="default",
        matched_model="generic_default",
        source="generic_tdp_default",
        normalized_query=normalized or "unknown",
    )
