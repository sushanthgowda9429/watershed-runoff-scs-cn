"""
runoff.py
=========
SCS Curve Number (SCS-CN) runoff estimation -- the same empirical method the
source publication used to link land-use change to increased surface runoff.

For each land-use class and hydrologic soil group (HSG) a standard curve
number is looked up (values after USDA-NRCS TR-55, National Engineering
Handbook). The area-weighted catchment CN is then converted to a potential
maximum retention S and a direct-runoff depth Q for a design storm:

    S = 25400 / CN - 254                       (mm)
    Q = (P - 0.2 S)^2 / (P + 0.8 S)   if P > 0.2 S, else 0   (mm)

A higher CN (more impervious / built-up land) yields a smaller S and a larger
Q for the same rainfall -- the mechanism behind the paper's finding that
urbanisation raised runoff potential across the three epochs.
"""

import numpy as np
from landcover import (WATER, BUILT, AGRI, FOREST, SHRUB, BARREN,
                       CLASS_NAMES, class_fractions)

# Curve numbers by class, for HSG C and HSG D (TR-55 representative values)
CN_TABLE = {
    WATER:  {"C": 98, "D": 98},
    BUILT:  {"C": 90, "D": 92},   # residential, ~38% impervious
    AGRI:   {"C": 82, "D": 85},   # row crops, straight row, good condition
    FOREST: {"C": 70, "D": 77},   # woods, good hydrologic condition
    SHRUB:  {"C": 74, "D": 80},   # brush / pasture, fair condition
    BARREN: {"C": 86, "D": 88},   # bare / fallow soil
}

DESIGN_RAINFALL_MM = 120.0   # a heavy single-day monsoon event


def cn_grid(layer, hsg, catch_mask):
    """Per-cell curve number raster for one LULC layer (NaN outside catchment)."""
    cn = np.full(layer.shape, np.nan, dtype=float)
    for code in CLASS_NAMES:
        for hsg_code, key in ((2, "C"), (3, "D")):
            sel = (layer == code) & (hsg == hsg_code) & catch_mask
            cn[sel] = CN_TABLE[code][key]
    return cn


def weighted_cn(cn):
    """Area-weighted mean curve number over the catchment."""
    return float(np.nanmean(cn))


def runoff_depth(cn, rainfall=DESIGN_RAINFALL_MM):
    """SCS-CN direct runoff depth Q (mm) from a curve number and rainfall P."""
    s = 25400.0 / cn - 254.0
    ia = 0.2 * s
    q = np.where(rainfall > ia, (rainfall - ia) ** 2 / (rainfall + 0.8 * s), 0.0)
    return float(q)


def analyse(lulc, hsg, catch_mask, area_km2, rainfall=DESIGN_RAINFALL_MM):
    """
    Build a per-epoch results table.

    Returns list of dicts: epoch, class fractions, weighted_cn, S_mm, Q_mm,
    runoff_volume_Mm3.
    """
    rows = []
    for epoch, layer in lulc.items():
        cn = cn_grid(layer, hsg, catch_mask)
        wcn = weighted_cn(cn)
        s = 25400.0 / wcn - 254.0
        q = runoff_depth(wcn, rainfall)
        vol_Mm3 = q / 1000.0 * area_km2 * 1e6 / 1e6   # mm->m * km2->m2, to Mm^3
        row = dict(epoch=epoch, weighted_cn=round(wcn, 2),
                   S_mm=round(s, 1), Q_mm=round(q, 1),
                   runoff_volume_Mm3=round(vol_Mm3, 2),
                   rainfall_mm=rainfall)
        row.update({k: round(v, 2) for k, v in
                    class_fractions(layer, catch_mask).items()})
        rows.append(row)
    return rows
