"""
landcover.py
============
Build three Land-Use / Land-Cover (LULC) scenarios over the catchment and a
hydrologic-soil-group (HSG) layer.

The publication's central finding is that built-up area expanded across three
epochs (1985-95, 1995-2005, 2005-15), raising the runoff curve number. This
module reproduces that *mechanism*: built-up land grows over three epochs by
encroaching on the valley floor (low elevation, near the stream), converting
agriculture and then forest. The class fractions here are emergent from the
generated terrain, not the paper's measured values.

Classes
-------
0 water, 1 built-up, 2 agriculture, 3 forest, 4 shrub/pasture, 5 barren

Soil
----
Sandy-clay-loam dominates the source study, which maps to Hydrologic Soil
Group C, with a wetter group-D zone on the low valley floor (~25% of area),
echoing the paper's ~76/24 two-unit soil split.
"""

import numpy as np
from scipy.ndimage import distance_transform_edt

WATER, BUILT, AGRI, FOREST, SHRUB, BARREN = range(6)
CLASS_NAMES = {WATER: "Water", BUILT: "Built-up", AGRI: "Agriculture",
               FOREST: "Forest", SHRUB: "Shrub/Pasture", BARREN: "Barren"}
EPOCHS = ["1985-1995", "1995-2005", "2005-2015"]


def _slope_pct(dem, res):
    gy, gx = np.gradient(dem, res, res)
    return np.hypot(gx, gy) * 100.0


def build_layers(dem, catch_mask, stream_mask, res):
    """
    Returns
    -------
    lulc : dict[str, np.ndarray]   one int LULC raster per epoch (catchment only)
    hsg  : np.ndarray              hydrologic soil group ('C'/'D' as 2/3 codes)
    slope: np.ndarray
    """
    slope = _slope_pct(dem, res)
    dist_stream = distance_transform_edt(~stream_mask) * res  # metres to stream
    elev = dem.copy()

    # Normalised "valley proximity": low elevation + close to stream
    e_lo, e_hi = np.percentile(elev[catch_mask], [5, 95])
    elev_n = np.clip((elev - e_lo) / (e_hi - e_lo), 0, 1)
    valley_score = (1 - elev_n) * np.exp(-dist_stream / 1500.0)

    # Per-epoch land-use change, mirroring the paper's pattern:
    #   forest retreats to higher/steeper ground, agriculture expands into it,
    #   and a small built-up core grows on the valley floor.
    #   (forest_elev, forest_slope, built_score_threshold)
    epoch_params = {
        0: (0.42, 10, 0.93),   # substantial forest, tiny built-up core
        1: (0.58, 14, 0.86),   # forest retreats, built-up grows
        2: (0.72, 19, 0.80),   # least forest, largest built-up core
    }
    lulc = {}
    for ep, name in enumerate(EPOCHS):
        f_elev, f_slope, b_thresh = epoch_params[ep]
        layer = np.full(dem.shape, AGRI, dtype=np.uint8)              # default
        layer[(slope > f_slope) & (elev_n > f_elev)] = FOREST        # highlands
        layer[(slope > 9) & (elev_n > 0.40) & (layer == AGRI)] = SHRUB
        layer[elev_n > 0.90] = BARREN                                # bare ridgetops
        layer[(valley_score > b_thresh)] = BUILT                     # built core
        layer[stream_mask] = WATER
        layer[~catch_mask] = 255                                     # nodata
        lulc[name] = layer

    # Hydrologic soil group: D on the low valley floor, C elsewhere
    hsg = np.full(dem.shape, 2, dtype=np.uint8)            # 2 -> 'C'
    hsg[(1 - elev_n) * np.exp(-dist_stream / 1200.0) > 0.55] = 3   # 3 -> 'D'
    hsg[~catch_mask] = 255

    return lulc, hsg, slope


def class_fractions(layer, catch_mask):
    """Percentage of catchment area in each class for one LULC layer."""
    inside = layer[catch_mask]
    total = inside.size
    out = {}
    for code, nm in CLASS_NAMES.items():
        out[nm] = 100.0 * np.count_nonzero(inside == code) / total
    return out
