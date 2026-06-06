"""
visualize.py
============
Figure generation for the analysis: DEM hillshade, flow accumulation, stream
network, the three LULC epochs, the curve-number map, and a results summary.
All figures are written to outputs/figures/.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource, ListedColormap, BoundaryNorm
from landcover import CLASS_NAMES, EPOCHS

plt.rcParams.update({"figure.dpi": 130, "font.size": 9,
                     "axes.titlesize": 10, "savefig.bbox": "tight"})

LC_COLORS = ["#3b7dd8", "#d6313b", "#e8c33a", "#2e7d32", "#9ccc65", "#bcaaa4"]
LC_CMAP = ListedColormap(LC_COLORS)


def _mask_outside(arr, catch_mask):
    a = np.array(arr, dtype=float)
    a[~catch_mask] = np.nan
    return a


def dem_hillshade(dem, catch_mask, stream_mask, outdir):
    ls = LightSource(azdeg=315, altdeg=45)
    hs = ls.hillshade(dem, vert_exag=2.0, dx=30, dy=30)
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.imshow(hs, cmap="gray")
    ax.imshow(dem, cmap="terrain", alpha=0.55)
    ax.contour(catch_mask, levels=[0.5], colors="black", linewidths=1.4)
    ys, xs = np.where(stream_mask)
    ax.scatter(xs, ys, s=0.15, c="#1565c0")
    ax.set_title("Synthetic DEM with hillshade, catchment boundary and streams")
    ax.axis("off")
    fig.savefig(f"{outdir}/01_dem_hillshade.png")
    plt.close(fig)


def flow_accumulation(acc, catch_mask, outdir):
    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(np.log1p(_mask_outside(acc, catch_mask)), cmap="cubehelix_r")
    ax.set_title("Flow accumulation (log scale)")
    ax.axis("off")
    fig.colorbar(im, ax=ax, shrink=0.7, label="log(1 + upstream cells)")
    fig.savefig(f"{outdir}/02_flow_accumulation.png")
    plt.close(fig)


def stream_network(dem, stream_mask, catch_mask, branches, area_km2, outdir):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.imshow(dem, cmap="Greys_r")
    ys, xs = np.where(stream_mask)
    ax.scatter(xs, ys, s=0.4, c="#0d47a1")
    ax.contour(catch_mask, levels=[0.5], colors="#d6313b", linewidths=1.6)
    ax.set_title(f"Extracted stream network\n"
                 f"catchment {area_km2:.0f} km^2, {branches} river segments")
    ax.axis("off")
    fig.savefig(f"{outdir}/03_stream_network.png")
    plt.close(fig)


def landcover_epochs(lulc, catch_mask, outdir):
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.6))
    norm = BoundaryNorm(np.arange(-0.5, 6.5, 1), LC_CMAP.N)
    for ax, epoch in zip(axes, EPOCHS):
        layer = _mask_outside(lulc[epoch], catch_mask)
        ax.imshow(layer, cmap=LC_CMAP, norm=norm)
        ax.set_title(f"Land cover {epoch}")
        ax.axis("off")
    handles = [plt.Rectangle((0, 0), 1, 1, color=LC_COLORS[c])
               for c in CLASS_NAMES]
    fig.legend(handles, list(CLASS_NAMES.values()), loc="lower center",
               ncol=6, frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("Land-use / land-cover across three epochs "
                 "(built-up expands on the valley floor)")
    fig.savefig(f"{outdir}/04_landcover_epochs.png")
    plt.close(fig)


def curve_number_map(cn_last, epoch, outdir):
    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(cn_last, cmap="YlOrRd", vmin=65, vmax=100)
    ax.set_title(f"Curve number map ({epoch})")
    ax.axis("off")
    fig.colorbar(im, ax=ax, shrink=0.7, label="SCS Curve Number")
    fig.savefig(f"{outdir}/05_curve_number_map.png")
    plt.close(fig)


def results_summary(rows, outdir):
    epochs = [r["epoch"] for r in rows]
    cn = [r["weighted_cn"] for r in rows]
    q = [r["Q_mm"] for r in rows]
    built = [r["Built-up"] for r in rows]

    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    axes[0].plot(epochs, built, "o-", color="#d6313b")
    axes[0].set_title("Built-up area (% of catchment)")
    axes[0].set_ylabel("%")
    axes[1].plot(epochs, cn, "o-", color="#6a1b9a")
    axes[1].set_title("Area-weighted curve number")
    bars = axes[2].bar(epochs, q, color="#1565c0")
    axes[2].set_title(f"Direct runoff depth Q (mm)\nfor {rows[0]['rainfall_mm']:.0f} mm storm")
    axes[2].set_ylabel("mm")
    for b, val in zip(bars, q):
        axes[2].text(b.get_x() + b.get_width() / 2, val + 0.6, f"{val:.1f}",
                     ha="center", va="bottom", fontsize=8)
    axes[2].set_ylim(0, max(q) * 1.12)
    for ax in axes:
        ax.tick_params(axis="x", rotation=20)
        ax.grid(alpha=0.3)
    fig.suptitle("Land-use change drives rising runoff potential")
    fig.savefig(f"{outdir}/06_results_summary.png")
    plt.close(fig)
