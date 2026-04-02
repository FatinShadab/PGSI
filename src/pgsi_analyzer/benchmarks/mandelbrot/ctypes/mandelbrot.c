// mandelbrot.c
#include <stdlib.h>

// Generate the Mandelbrot set and fill a pre-allocated 2D array
void generate_mandelbrot(int width, int height, int max_iter,
                         double x_min, double x_max,
                         double y_min, double y_max,
                         int* output) {
    double aspect_ratio = (double)width / height;
    y_min /= aspect_ratio;
    y_max /= aspect_ratio;

    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            double cr = x_min + ((double)x / width) * (x_max - x_min);
            double ci = y_min + ((double)y / height) * (y_max - y_min);
            double zr = 0.0;
            double zi = 0.0;
            int iter;
            for (iter = 0; iter < max_iter; iter++) {
                double zr2 = zr * zr;
                double zi2 = zi * zi;
                if ((zr2 + zi2) > 4.0)
                    break;
                double new_zi = 2.0 * zr * zi + ci;
                double new_zr = zr2 - zi2 + cr;
                zr = new_zr;
                zi = new_zi;
            }
            output[y * width + x] = iter;
        }
    }
}
