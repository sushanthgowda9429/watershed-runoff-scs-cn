"""
terrain.py
==========
Generate a synthetic but hydrologically realistic Digital Elevation Model (DEM).

The DEM is built from three components:
  1. A regional downstream gradient (terrain drains toward the south edge).
  2. A sine-curved trunk valley that forces flow to converge into one basin.
  3. Multi-octave smoothed-noise to create realistic ridges and tributaries.

A fixed random seed makes the output fully reproducible. The resulting
catchment area, elevation range, and stream network are emergent properties
of this generated surface -- they are NOT taken from any real-world dataset.
"""

import numpy as np
from scipy.ndimage import gaussian_filter
import rasterio
from rasterio.transform import from_origin


def _octave(n, sigma, seed):
    """One octave of smoothed Gaussian noise."""
    r = np.random.default_rng(seed).standard_normal((n, n))
    return gaussian_filter(r, sigma=sigma)


def generate_dem(path, n=820, res=30.0, seed=42):
    """
    Build a synthetic DEM and write it to `path` as a single-band GeoTIFF.

    Parameters
    ----------
    path : str   output GeoTIFF path
    n    : int   grid size (n x n cells)
    res  : float cell size in metres (30 m mirrors SRTM resolution)
    seed : int   random seed for reproducibility

    Returns
    -------
    dem : np.ndarray  the elevation array (float32)
    """
    # Multi-octave noise for ridges and tributaries
    noise = np.zeros((n, n))
    for i, sigma in enumerate([60, 30, 15, 7]):
        noise += _octave(n, sigma, 100 + i) * (sigma ** 0.9)
    noise = (noise - noise.min()) / np.ptp(noise)

    yy, xx = np.mgrid[0:n, 0:n].astype(float)

    # Sine-curved trunk valley: column position varies with row
    trunk_col = n * 0.5 + n * 0.18 * np.sin(yy / n * np.pi * 1.1)
    dist_trunk = np.abs(xx - trunk_col)          # cells from trunk
    dist_km = dist_trunk * res / 1000.0

    downstream = (1.0 - yy / n)                  # high in north, low in south

    dem = (downstream * 350.0) + (dist_km * 55.0) + (noise * 260.0) + 150.0
    dem -= np.exp(-(dist_trunk / 12.0) ** 2) * 120.0   # carve the trunk channel
    dem = dem.astype("float32")

    transform = from_origin(500000, 7000000 + n * res, res, res)
    profile = dict(driver="GTiff", height=n, width=n, count=1,
                   dtype="float32", crs="EPSG:32643", transform=transform,
                   nodata=-9999)
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(dem, 1)

    return dem


if __name__ == "__main__":
    d = generate_dem("data/dem.tif")
    print(f"DEM written: {d.shape}, elevation {d.min():.0f}-{d.max():.0f} m")
