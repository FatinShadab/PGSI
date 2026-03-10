"""
File-system provider for the benchmark pipeline.

Separates pipeline coordination from filesystem I/O: workspace preparation,
path resolution, and aggregated path collection. The orchestrator uses this
provider so that I/O can be mocked in tests without touching disk.
"""

import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from .results_collector import (
    ENERGY_AGGREGATED,
    TIME_AGGREGATED,
    ENERGY_COMBINED,
    TIME_COMBINED,
    CARBON_FOOTPRINT,
    GREENSCORE,
    ENERGY_CSV_PATTERN,
    TIME_CSV_PATTERN,
    GARBAGE_ENTRIES,
)


class FileSystemProvider:
    """
    Handles filesystem operations for the benchmark pipeline: creating workspaces,
    copying raw CSVs by pattern, resolving output paths, and collecting aggregated paths.
    """

    def prepare_aggregation_workspace(
        self,
        output_dir: Path,
        method: str,
        raw_dirs: List[Path],
        kind: str,
    ) -> Path:
        """
        Create a workspace directory and copy raw CSVs from raw_dirs into it.

        Args:
            output_dir: Base output directory (e.g. results/).
            method: Execution method name (e.g. cpython, pypy).
            raw_dirs: List of directories that contain raw CSV files.
            kind: "energy" or "time" (used for temp dir naming and pattern).

        Returns:
            Path to the created directory containing the copied CSV files.
        """
        workspace = Path(output_dir) / f"temp_{kind}_{method}"
        workspace.mkdir(parents=True, exist_ok=True)
        pattern = ENERGY_CSV_PATTERN if kind == "energy" else TIME_CSV_PATTERN
        for dir_path in raw_dirs:
            dir_path = Path(dir_path)
            if not dir_path.is_dir():
                continue
            for entry in dir_path.iterdir():
                if entry.name in GARBAGE_ENTRIES:
                    continue
                if not entry.is_file():
                    continue
                if pattern.match(entry.name):
                    shutil.copy2(entry, workspace / entry.name)
        return workspace

    def get_output_path(
        self,
        output_dir: Path,
        method: Optional[str] = None,
        file_type: Optional[str] = None,
    ) -> Path:
        """
        Return the canonical path for an output file (aggregated, combined, or final).

        Creates method subdirectories when file_type is energy_aggregated or time_aggregated.

        Args:
            output_dir: Base output directory.
            method: Execution method (required for energy_aggregated, time_aggregated).
            file_type: One of energy_aggregated, time_aggregated, energy_combined,
                       time_combined, carbon_footprint, GreenScore.

        Returns:
            Path where the file should be written.
        """
        output_dir = Path(output_dir)
        if file_type == ENERGY_AGGREGATED or file_type == TIME_AGGREGATED:
            if not method:
                raise ValueError("method required for energy_aggregated / time_aggregated")
            method_dir = output_dir / method
            method_dir.mkdir(parents=True, exist_ok=True)
            if file_type == ENERGY_AGGREGATED:
                return method_dir / "energy_aggregated.csv"
            return method_dir / "time_aggregated.csv"
        if file_type == ENERGY_COMBINED:
            return output_dir / "energy_combined.csv"
        if file_type == TIME_COMBINED:
            return output_dir / "time_combined.csv"
        if file_type == CARBON_FOOTPRINT:
            return output_dir / "carbon_footprint.csv"
        if file_type == GREENSCORE:
            return output_dir / "GreenScore.csv"
        raise ValueError(f"Unknown file_type: {file_type}")

    def collect_aggregated_paths(
        self,
        output_dir: Path,
        methods: List[str],
    ) -> Dict[str, Dict[str, Path]]:
        """
        Return paths to energy_aggregated.csv and time_aggregated.csv for each method.

        Args:
            output_dir: Base output directory.
            methods: List of method names (e.g. cpython, pypy).

        Returns:
            {"energy": {method: path}, "time": {method: path}}
        """
        output_dir = Path(output_dir)
        energy_paths: Dict[str, Path] = {}
        time_paths: Dict[str, Path] = {}
        for method in methods:
            energy_paths[method] = self.get_output_path(output_dir, method=method, file_type=ENERGY_AGGREGATED)
            time_paths[method] = self.get_output_path(output_dir, method=method, file_type=TIME_AGGREGATED)
        return {"energy": energy_paths, "time": time_paths}
