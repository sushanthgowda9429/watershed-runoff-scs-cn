"""
hydrology.py
============
Watershed delineation from a DEM, following the same workflow the source
publication used in QGIS/QSWAT, but implemented as reproducible Python:

  1. Fill pits and depressions, resolve flats   (conditioning the DEM)
  2. D8 flow direction                           (Fig. 2 in the paper)
  3. Flow accumulation
  4. Pour-point selection + catchment delineation
  5. Stream-network extraction

Uses the `pysheds` library. A small shim keeps it working on NumPy >= 2,
where `np.in1d` / `np.bool` were removed.
"""

import numpy as np

if not hasattr(np, "in1d"):
    np.in1d = np.isin          # pysheds 0.5 / NumPy 2 compatibility
if not hasattr(np, "bool"):
    np.bool = bool

from pysheds.grid import Grid

# D8 direction map (E, NE, N, NW, W, SW, S, SE) -> pysheds default
DIRMAP = (64, 128, 1, 2, 4, 8, 16, 32)


def delineate(dem_path, stream_threshold=1500):
    """
    Run the full delineation pipeline.

    Returns a dict with: grid, fdir, acc (arrays), catch_mask (bool array on
    the full grid), stream_mask (bool array), outlet (row, col), branches
    (number of river segments), and area_km2.
    """
    grid = Grid.from_raster(dem_path)
    dem = grid.read_raster(dem_path)

    # 1. Condition the DEM
    pit_filled = grid.fill_pits(dem)
    flooded = grid.fill_depressions(pit_filled)
    inflated = grid.resolve_flats(flooded)

    # 2-3. Flow direction and accumulation
    fdir = grid.flowdir(inflated, dirmap=DIRMAP)
    acc = grid.accumulation(fdir, dirmap=DIRMAP)
    acc_arr = np.asarray(acc)

    # 4. Robust outlet: highest-accumulation cell along the bottom edge
    edge = acc_arr[-6:, :]
    col = int(edge.max(axis=0).argmax())
    row = int(acc_arr[-6:, col].argmax()) + (acc_arr.shape[0] - 6)
    x_coord, y_coord = grid.affine * (col, row)
    x_snap, y_snap = grid.snap_to_mask(acc > stream_threshold, (x_coord, y_coord))

    catch = grid.catchment(x=x_snap, y=y_snap, fdir=fdir,
                           dirmap=DIRMAP, xytype="coordinate")
    catch_mask = np.asarray(catch).astype(bool)

    res = abs(grid.affine.a)
    area_km2 = float(catch_mask.sum()) * (res * res) / 1e6

    # 5. Stream network (raster mask within the catchment) + branch count
    stream_mask = (acc_arr > stream_threshold) & catch_mask
    grid.clip_to(catch)
    branches = grid.extract_river_network(fdir, acc > stream_threshold,
                                          dirmap=DIRMAP)
    n_branches = len(branches["features"])

    return dict(grid=grid, fdir=np.asarray(fdir), acc=acc_arr,
                catch_mask=catch_mask, stream_mask=stream_mask,
                outlet=(row, col), branches=n_branches,
                area_km2=area_km2, res=res)
