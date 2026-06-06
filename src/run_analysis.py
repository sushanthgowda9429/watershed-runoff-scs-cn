"""
run_analysis.py
===============
End-to-end pipeline:

    DEM  ->  watershed delineation  ->  land-use scenarios  ->
    SCS-CN runoff  ->  figures + results table

Run from the repo root:

    python src/run_analysis.py

Outputs land in data/ (the DEM) and outputs/ (figures + results.csv).
"""

import os
import csv
import json
import numpy as np

import terrain
import hydrology
import landcover
import runoff
import visualize

DATA_DIR = "data"
OUT_DIR = "outputs"
FIG_DIR = f"{OUT_DIR}/figures"
SEED = 42


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(FIG_DIR, exist_ok=True)
    dem_path = f"{DATA_DIR}/dem.tif"

    print("1. Generating synthetic DEM ...")
    dem = terrain.generate_dem(dem_path, seed=SEED)
    print(f"   DEM {dem.shape}, elevation {dem.min():.0f}-{dem.max():.0f} m")

    print("2. Delineating catchment and streams ...")
    h = hydrology.delineate(dem_path)
    print(f"   catchment {h['area_km2']:.0f} km^2, {h['branches']} river segments")

    print("3. Building land-cover scenarios and soil groups ...")
    lulc, hsg, slope = landcover.build_layers(
        dem, h["catch_mask"], h["stream_mask"], h["res"])

    print("4. SCS-CN runoff analysis ...")
    rows = runoff.analyse(lulc, hsg, h["catch_mask"], h["area_km2"])

    print("5. Writing figures ...")
    visualize.dem_hillshade(dem, h["catch_mask"], h["stream_mask"], FIG_DIR)
    visualize.flow_accumulation(h["acc"], h["catch_mask"], FIG_DIR)
    visualize.stream_network(dem, h["stream_mask"], h["catch_mask"],
                             h["branches"], h["area_km2"], FIG_DIR)
    visualize.landcover_epochs(lulc, h["catch_mask"], FIG_DIR)
    last = landcover.EPOCHS[-1]
    cn_last = runoff.cn_grid(lulc[last], hsg, h["catch_mask"])
    cn_last[~h["catch_mask"]] = np.nan
    visualize.curve_number_map(cn_last, last, FIG_DIR)
    visualize.results_summary(rows, FIG_DIR)

    print("6. Writing results table ...")
    fieldnames = list(rows[0].keys())
    with open(f"{OUT_DIR}/results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    with open(f"{OUT_DIR}/results.json", "w") as f:
        json.dump({"catchment_km2": round(h["area_km2"], 1),
                   "river_segments": h["branches"],
                   "elevation_m": [round(float(dem.min())), round(float(dem.max()))],
                   "epochs": rows}, f, indent=2)

    print("\nSummary (the headline result):")
    print(f"   {'epoch':<12}{'built-up %':>11}{'weighted CN':>13}{'runoff Q mm':>13}")
    for r in rows:
        print(f"   {r['epoch']:<12}{r['Built-up']:>11.2f}"
              f"{r['weighted_cn']:>13.2f}{r['Q_mm']:>13.1f}")
    delta = rows[-1]["Q_mm"] - rows[0]["Q_mm"]
    print(f"\n   Runoff rose {delta:.1f} mm "
          f"(+{100*delta/rows[0]['Q_mm']:.1f}%) as built-up land expanded.")
    print("Done. See outputs/figures/ and outputs/results.csv")


if __name__ == "__main__":
    main()
