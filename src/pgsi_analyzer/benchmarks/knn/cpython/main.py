import math
import random
import sys
from collections import Counter
from pathlib import Path
from typing import List, Sequence, Tuple

sys.path.append(str(Path(__file__).resolve().parents[3]))

from pgsi_analyzer.config import DEFAULT_PARAMS as __default__, get_measurement_runs
from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv


class KNN:
    """Minimal KNN implementation used for pgsi-analyzer benchmarking."""

    def __init__(self, k: int = 3, mode: str = "classification") -> None:
        if k <= 0:
            raise ValueError("k must be a positive integer")
        if mode not in ("classification", "regression"):
            raise ValueError("mode must be either 'classification' or 'regression'")

        self.k = k
        self.mode = mode
        self.data: List[Tuple[List[float], float]] = []

    def fit(self, X: List[List[float]], y: List[float]) -> None:
        if len(X) != len(y):
            raise ValueError("Feature and label lists must have the same length")

        self.data = list(zip(X, y))

    def _euclidean_distance(self, point1: List[float], point2: List[float]) -> float:
        return math.sqrt(sum((p1 - p2) ** 2 for p1, p2 in zip(point1, point2)))

    def predict(self, X: List[List[float]]) -> List[float]:
        return [self._predict_single(x) for x in X]

    def _predict_single(self, x: List[float]) -> float:
        distances: List[Tuple[float, float]] = [
            (self._euclidean_distance(x, features), label) for features, label in self.data
        ]
        distances.sort(key=lambda d: d[0])
        k_nearest_neighbors = distances[:self.k]

        if self.mode == "classification":
            labels = [label for _, label in k_nearest_neighbors]
            return Counter(labels).most_common(1)[0][0]
        return sum(label for _, label in k_nearest_neighbors) / self.k


def _build_dataset(
    rng: random.Random, num_samples: int, num_features: int
) -> Tuple[List[List[float]], List[float], List[float], Sequence[float]]:
    X_train = [
        [rng.uniform(0.0, 100.0) for _ in range(num_features)]
        for _ in range(num_samples)
    ]
    y_train_classification = [rng.randint(0, 1) for _ in range(num_samples)]
    y_train_regression = [rng.uniform(0.0, 100.0) for _ in range(num_samples)]
    query = [rng.uniform(0.0, 100.0) for _ in range(num_features)]
    return X_train, y_train_classification, y_train_regression, query


def run_knn_workload(num_samples: int, num_features: int, k: int) -> Tuple[float, float]:
    """
    Developer-facing benchmark workload.

    This function is intentionally plain Python so users can copy this pattern
    and only wrap their own workload with the PGSI decorators below.
    """
    rng = random.Random(42)
    X_train, y_train_classification, y_train_regression, query = _build_dataset(
        rng, num_samples, num_features
    )

    knn_classifier = KNN(k=k, mode="classification")
    knn_classifier.fit(X_train, y_train_classification)
    prediction_classification = float(knn_classifier.predict([list(query)])[0])

    knn_regressor = KNN(k=k, mode="regression")
    knn_regressor.fit(X_train, y_train_regression)
    prediction_regression = float(knn_regressor.predict([list(query)])[0])

    return prediction_classification, prediction_regression


# These decorators are the only integration a developer needs for measurement.
@measure_energy_to_csv(n=get_measurement_runs("knn"), csv_filename="knn_cpython")
def run_energy_benchmark(num_samples: int, num_features: int, k: int) -> None:
    run_knn_workload(num_samples, num_features, k)


@measure_time_to_csv(n=get_measurement_runs("knn"), csv_filename="knn_cpython")
def run_time_benchmark(num_samples: int, num_features: int, k: int) -> None:
    run_knn_workload(num_samples, num_features, k)


if __name__ == "__main__":
    num_samples = __default__["knn"].get("num_samples", 1000)
    num_features = __default__["knn"].get("num_features", 10)
    k = __default__["knn"].get("k", 5)

    run_energy_benchmark(num_samples, num_features, k)
    run_time_benchmark(num_samples, num_features, k)
