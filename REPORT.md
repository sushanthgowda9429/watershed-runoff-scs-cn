# Project Summary Report
## Land-Use Change and Surface-Runoff Potential: a Reproducible SCS-CN Watershed Analysis

**Author:** Sushanth Shivegowda
**Type:** Methods-demonstration project (portfolio)
**Stack:** Python · pysheds · rasterio · NumPy/SciPy · Matplotlib

---

### 1. Scope and relationship to prior work

This project reproduces the **methodology** of a peer-reviewed paper I
co-authored as second author — Lavan Kumar B, Sushanth S Gowda, Manikanta M V,
Mohammed Zaumam Ur Rehman, *"Application of GIS in Investigating the Influence
of Rainfall-Runoff on Landslides,"* IRJET Vol. 08 Issue 06, June 2021,
pp. 3646–3653 — using **synthetic, reproducible data and original code**.

It is deliberately **not** a re-run of the published study:

- The original analysis used real SRTM DEMs, FAO soil rasters and NASA LULC
  data over a 352.88 km² catchment in Kodagu, Karnataka. None of that data is
  used here.
- The original was executed in QGIS with the QSWAT/SWAT interface (a GUI
  workflow). This project re-implements the same hydrological methods —
  watershed delineation by D8 flow routing, and SCS Curve Number runoff — as
  scripted, version-controllable Python.

The purpose is to demonstrate, in a way a reviewer can run and verify, the
same geospatial-hydrology skill set the publication evidences.

### 2. Objective

Show that progressive land-use change — forest loss and a growing built-up
core — increases the area-weighted runoff curve number of a catchment and
therefore the direct runoff produced by a fixed design storm. This is the
central mechanism of the source paper, in which an increasing SCS-CN across
three decadal epochs was linked to rising runoff and landslide susceptibility.

### 3. Methodology

**3.1 Synthetic terrain.** A 820 × 820 cell DEM at 30 m resolution (mirroring
SRTM) is generated from a regional downstream gradient, a sine-curved trunk
valley that forces flow convergence, and four octaves of smoothed Gaussian
noise for realistic ridges and tributaries. A fixed seed (42) makes the
surface fully reproducible. Elevation ranges 130–1445 m.

**3.2 Hydrological conditioning and routing.** Using `pysheds`, the DEM is
pit-filled, depression-filled and its flats resolved, then D8 flow direction
and flow accumulation are computed. The catchment outlet is taken as the
highest-accumulation cell on the southern edge; the catchment is delineated
from it (**508 km²**) and the stream network extracted by an accumulation
threshold (**183 river segments**).

**3.3 Land-use / land-cover epochs.** Three LULC layers are built over the
catchment to represent three decadal epochs. Forest occupies steep, high
ground and retreats across epochs; agriculture (the matrix class) expands into
it; a built-up core grows on the valley floor (low elevation, near the stream).
This mirrors the publication's observation of expanding built-up and
agricultural area at the expense of forest.

**3.4 Hydrologic soil groups.** Sandy-clay-loam dominates the source study,
mapped here to Hydrologic Soil Group C, with a wetter Group-D zone on the low
valley floor — echoing the paper's ~76/24 two-unit soil split.

**3.5 SCS Curve Number runoff.** Each cell receives a curve number from a
USDA-NRCS TR-55 lookup keyed on (land-use class × HSG). The area-weighted
catchment CN gives potential maximum retention and runoff depth:

```
S = 25400 / CN − 254                          (mm)
Q = (P − 0.2S)² / (P + 0.8S)   for P > 0.2S   (mm)
```

A design rainfall of **P = 120 mm** (a heavy single-day monsoon event) is
applied to each epoch.

### 4. Results

| Epoch      | Built-up % | Agriculture % | Forest % | Weighted CN | S (mm) | Q (mm) |
|------------|-----------:|--------------:|---------:|------------:|-------:|-------:|
| 1985–1995  |       1.71 |         65.89 |    17.01 |       81.11 |   59.2 |   69.9 |
| 1995–2005  |       4.22 |         63.38 |     3.37 |       81.83 |   56.4 |   71.6 |
| 2005–2015  |       7.11 |         60.50 |     0.18 |       82.16 |   55.2 |   72.4 |

Across the three epochs the built-up fraction rises from ~1.7% to ~7.1% and
forest falls from ~17% to near zero. The area-weighted curve number rises from
81.1 to 82.2, and direct runoff from the same 120 mm storm increases from 69.9
to 72.4 mm — a **+3.6%** rise driven entirely by land-cover change, since
rainfall and soil are held constant.

The weighted-CN trajectory (81.1 → 82.2) sits in the same band as the
published study's measured SCS-CN (≈80.0 → 81.7) — an independent but
consistent result, not a fitted one.

Figures (in `outputs/figures/`): DEM hillshade, flow accumulation, stream
network, the three land-cover epochs, the curve-number map, and a results
summary.

### 5. Interpretation

The result restates the source paper's core argument in a controlled setting:
when impervious and bare-soil cover replace forest, infiltration capacity
falls, the curve number rises, and a larger share of the same rainfall becomes
surface runoff. Sustained higher runoff is one contributor to slope instability
and landslide risk on steep terrain — the link the original study investigated.

### 6. Limitations (honest)

- **Synthetic data.** Terrain, land cover and soils are generated, not
  observed. The numbers are internally consistent but are not measurements of
  any real place.
- **Not calibrated or validated.** No gauge data; runoff is a design-storm
  estimate from tabulated curve numbers, not a calibrated simulation.
- **Lumped CN method.** The SCS-CN approach ignores rainfall intensity,
  antecedent moisture dynamics, and routing time; it estimates event runoff
  volume, not a hydrograph.
- **Single design storm.** One rainfall depth is applied; a frequency analysis
  would strengthen the runoff conclusion.

### 7. Possible extensions

Calibrate against a real gauged catchment with open SRTM + ESA WorldCover data;
add antecedent-moisture (AMC) adjustment; compute sub-basin-level CN and runoff;
add a simple landslide-susceptibility index combining slope and runoff to more
fully mirror the source study.

### 8. Reproducibility

```bash
pip install -r requirements.txt
python src/run_analysis.py
```

Deterministic from seed 42; the figures and `results.csv`/`results.json` in
this repository were produced by exactly this command.
