"""
Results collection and filesystem layout for the benchmark pipeline.

Groups raw CSV paths by method (collect_paths). Filesystem I/O (workspace
preparation, output path resolution) is delegated to FileSystemProvider;
ResultsCollector retains backward compatibility by delegating to a default
provider when prepare_aggregation_workspace or get_output_path are called.
"""

import re
from pathlib import Path
from typing import Dict, List, Any, TYPE_CHECKING

from ..utils.errors import AuditError
from ..benchmarks.registry import VALID_METHODS

if TYPE_CHECKING:
    from .provider import FileSystemProvider

# Allowed filename patterns (audit): only these are copied into aggregation workspace
ENERGY_CSV_PATTERN = re.compile(r"^energy_.*\.csv$")
TIME_CSV_PATTERN = re.compile(r"^time_.*\.csv$")
# Ignore directory-level garbage
GARBAGE_ENTRIES = {".DS_Store", "__pycache__", ".git", ".env"}


# File type constants for get_output_path
ENERGY_AGGREGATED = "energy_aggregated"
TIME_AGGREGATED = "time_aggregated"
ENERGY_COMBINED = "energy_combined"
TIME_COMBINED = "time_combined"
CARBON_FOOTPRINT = "carbon_footprint"
GREENSCORE = "GreenScore"


class ResultsCollector:
    """
    Handles grouping of raw CSV paths by method. Workspace and path resolution
    delegate to FileSystemProvider (default instance) for backward compatibility.
    """

    def __init__(self, provider: "FileSystemProvider" = None) -> None:
        from .provider import FileSystemProvider as _FS
        self._provider = provider if provider is not None else _FS()

    def collect_paths(
        self,
        execution_results: Dict[str, Dict[str, Dict[str, Any]]],
    ) -> Dict[str, Dict[str, List[Path]]]:
        """
        Group energy and time CSV paths by execution method.

        ``execution_results`` is expected to be a nested mapping in this shape:
        ``{algorithm: {method: {"energy_csv": Path, "time_csv": Path, ...}}}``.

        Returns:
            Dict[str, Dict[str, List[Path]]]: Grouped CSV parent directories:
            ``{"energy": {method: [Path, ...]}, "time": {method: [Path, ...]}}``.

        Raises:
            AuditError: If a method is not in the registry whitelist (``VALID_METHODS``).
        """
        energy_by_method: Dict[str, List[Path]] = {}
        time_by_method: Dict[str, List[Path]] = {}

        for _algorithm, methods_dict in execution_results.items():
            for method, results in methods_dict.items():
                # Verification: method must be in registry whitelist
                if method not in VALID_METHODS:
                    raise AuditError(
                        f"Data file found for method '{method}' which is not registered in "
                        "benchmarks/registry.py (VALID_METHODS). Audit requires all methods to be whitelisted."
                    )
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
        """Delegate to FileSystemProvider. See provider.prepare_aggregation_workspace."""
        return self._provider.prepare_aggregation_workspace(output_dir, method, raw_dirs, kind)

    def get_output_path(
        self,
        output_dir: Path,
        method: str = None,
        file_type: str = None,
    ) -> Path:
        """Delegate to FileSystemProvider. See provider.get_output_path."""
        return self._provider.get_output_path(output_dir, method=method, file_type=file_type)
