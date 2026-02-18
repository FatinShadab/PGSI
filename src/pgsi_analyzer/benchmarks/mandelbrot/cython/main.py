# main.py
from raw import generate_mandelbrot
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from pgsi_analyzer.measurement import measure_energy_to_csv, measure_time_to_csv

from pgsi_analyzer.config import DEFAULT_PARAMS as __default__, get_measurement_runs


def render_mandelbrot(data, max_iter):
    chars = " .:-=+*#%@"
    scale = len(chars) - 1

    for row in data:
        print("".join(chars[int(i / max_iter * scale)] for i in row))
        
def driver(width: int, height: int, max_iter: int, 
                         x_min: float, x_max: float, y_min: float, y_max: float):
    data = generate_mandelbrot(width, height, max_iter, x_min, x_max, y_min, y_max)
    render_mandelbrot(data, max_iter)

# Measure energy consumption and time taken for the Mandelbrot set generation
@measure_energy_to_csv(n=get_measurement_runs("mandelbrot"), csv_filename="mandelbrot_cython")
def run_energy_benchmark(width: int, height: int, max_iter: int, 
                         x_min: float, x_max: float, y_min: float, y_max: float) -> None:
    driver(width, height, max_iter, x_min, x_max, y_min, y_max)

# Measure time taken for the Mandelbrot set generation
@measure_time_to_csv(n=get_measurement_runs("mandelbrot"), csv_filename="mandelbrot_cython")
def run_time_benchmark(width: int, height: int, max_iter: int, 
                         x_min: float, x_max: float, y_min: float, y_max: float) -> None:
    driver(width, height, max_iter, x_min, x_max, y_min, y_max)
    

if __name__ == "__main__":
    m = __default__["mandelbrot"]
    width, height = m.get("width", 1000), m.get("height", 1000)
    max_iter = m.get("max_iter", 100)
    x_min, x_max, y_min, y_max = (
        m.get("x_min", -2.5), m.get("x_max", 1.0),
        m.get("y_min", -1.25), m.get("y_max", 1.25)
    )

    # Run energy and time benchmarks
    run_energy_benchmark(width, height, max_iter, x_min, x_max, y_min, y_max)
    run_time_benchmark(width, height, max_iter, x_min, x_max, y_min, y_max)
