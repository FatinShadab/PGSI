"""
Results collection and filesystem layout for the benchmark pipeline.

Delegates file movement and path resolution so the orchestrator can focus on
pipeline coordination. Ensures the output directory structure matches the
contract expected by combination models (method name = parent directory of
aggregated files).
"""

import shutil
from pathlib import Path
from typing import Dict, List, Any


# File type constants for get_output_path
ENERGY_AGGREGATED = "energy_aggregated"
TIME_AGGREGATED = "time_aggregated"
ENERGY_COMBINED = "energy_combined"
TIME_COMBINED = "time_combined"
CARBON_FOOTPRINT = "carbon_footprint"
GREENSCORE = "GreenScore"


class ResultsCollector:
    """
    Handles grouping of raw CSV paths by method and preparation of aggregation
    workspaces. Centralizes output path naming so the pipeline layout is
    consistent and the combination models receive paths under output_dir/<method>/.
    """

    def collect_paths(
        self,
        execution_results: Dict[str, Dict[str, Dict[str, Any]]],
    ) -> Dict[str, Dict[str, List[Path]]]:
        """
        Group energy and time CSV paths by execution method.

        execution_results is expected to be:
          { algorithm: { method: { "energy_csv": Path, "time_csv": Path, ... } } }

        Returns:
          {
            "energy": { method: [dir, ...] },  # unique dirs containing energy CSVs
            "time": { method: [dir, ...] },
          }
        """
        energy_by_method: Dict[str, List[Path]] = {}
        time_by_method: Dict[str, List[Path]] = {}

        for _algorithm, methods_dict in execution_results.items():
            for method, results in methods_dict.items():
                if results.get("energy_csv"):
                    energy_csv = Path(results["energy_csv"])
                    energy_dir = energy_csv.parent
                    if method not in energy_by_method:
                        energy_by_method[method] = []
                    if energy_dir not in energy_by_method[method]:
                        energy_by_method[method].append(energy_dir)

                if results.get("time_csv"):
                    time_csv = Path(results["time_csv"])
                    time_dir = time_csv.parent
                    if method not in time_by_method:
                        time_by_method[method] = []
                    if time_dir not in time_by_method[method]:
                        time_by_method[method].append(time_dir)

        return {"energy": energy_by_method, "time": time_by_method}

    def prepare_aggregation_workspace(
        self,
        output_dir: Path,
        method: str,
        raw_dirs: List[Path],
        kind: str,
    ) -> Path:
        """
        Create a workspace directory and copy all raw CSVs from raw_dirs into it.
        Used so aggregate_energy / aggregate_time can read from a single folder.

        Args:
            output_dir: Base output directory (e.g. results/).
            method: Execution method name (e.g. cpython, pypy).
            raw_dirs: List of directories that contain raw CSV files.
            kind: "energy" or "time" (used for temp dir naming).

        Returns:
            Path to the created directory containing the copied CSV files.
        """
        workspace = output_dir / f"temp_{kind}_{method}"
        workspace.mkdir(parents=True, exist_ok=True)
        for dir_path in raw_dirs:
            dir_path = Path(dir_path)
            if not dir_path.is_dir():
                continue
            for csv_file in dir_path.glob("*.csv"):
                shutil.copy2(csv_file, workspace / csv_file.name)
        return workspace

    def get_output_path(
        self,
        output_dir: Path,
        method: str = None,
        file_type: str = None,
    ) -> Path:
        """
        Centralize output path for aggregated and combined files.

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
