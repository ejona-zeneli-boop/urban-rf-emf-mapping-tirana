# -*- coding: utf-8 -*-
"""Generate six interpolated RF-EMF exposure maps for MKA Square, Tirana."""

from pathlib import Path

import contextily as ctx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.path import Path as MplPath
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd
from scipy.interpolate import griddata
from scipy.spatial import ConvexHull


PROJECT_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_DIR / "data" / "mka_square_anonymized.xlsx"
OUTPUT_DIR = PROJECT_DIR / "outputs" / "figures" / "mka_square"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BANDS = [
    ("LTE800", 791, 862),
    ("GSM900", 880, 960),
    ("LTE1800", 1710, 1880),
    ("UMTS2100", 1920, 2170),
    ("LTE2600", 2500, 2690),
    ("5G_NR3600", 3400, 3800),
]
HOTSPOT_PERCENTILE = 85
BASEMAP = ctx.providers.Esri.WorldImagery


df = pd.read_excel(INPUT_FILE)
df.columns = df.columns.astype(str).str.strip()
required = ["point_id", "lat", "lon"] + [band[0] for band in BANDS]
missing = [column for column in required if column not in df.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")

for column in required[1:]:
    df[column] = pd.to_numeric(df[column], errors="coerce")
df = df.dropna(subset=required).copy()

lat = df["lat"].to_numpy()
lon = df["lon"].to_numpy()
number_of_points = len(df)

points = np.column_stack([lon, lat])
hull = ConvexHull(points)
hull_points = points[hull.vertices]
boundary = np.vstack([hull_points, hull_points[0]])
hull_path = MplPath(boundary)

grid_size = 500
grid_x, grid_y = np.meshgrid(
    np.linspace(lon.min(), lon.max(), grid_size),
    np.linspace(lat.min(), lat.max(), grid_size),
)
inside = hull_path.contains_points(
    np.column_stack([grid_x.ravel(), grid_y.ravel()])
).reshape(grid_x.shape)

mean_latitude = lat.mean()
aspect = 1.0 / np.cos(np.deg2rad(mean_latitude))
dx = lon.max() - lon.min()
dy = lat.max() - lat.min()
metres_per_degree_longitude = 111_320 * np.cos(np.deg2rad(mean_latitude))
scale_bar_degrees = 100.0 / metres_per_degree_longitude

for band_name, low_mhz, high_mhz in BANDS:
    electric_field = df[band_name].to_numpy()
    hotspot = np.percentile(electric_field, HOTSPOT_PERCENTILE)
    interpolated = griddata(points, electric_field, (grid_x, grid_y), method="linear")
    interpolated = np.where(inside, interpolated, np.nan)

    fig, ax = plt.subplots(figsize=(9.2, 8.6))
    image = ax.pcolormesh(
        grid_x, grid_y, interpolated, cmap="jet", shading="auto",
        vmin=np.nanmin(interpolated), vmax=np.nanmax(interpolated),
        alpha=0.75, zorder=3,
    )
    ax.contour(
        grid_x, grid_y, interpolated, levels=[hotspot],
        colors="cyan", linewidths=1.6, zorder=4,
    )
    ax.plot(boundary[:, 0], boundary[:, 1], color="#00008B", lw=2.4, zorder=5)
    ax.scatter(
        lon, lat, s=22, facecolors="white", edgecolors="#333366",
        linewidths=0.7, zorder=6,
    )

    ax.set_aspect(aspect)
    ax.set_xlim(lon.min() - 0.08 * dx, lon.max() + 0.08 * dx)
    ax.set_ylim(lat.min() - 0.10 * dy, lat.max() + 0.10 * dy)
    try:
        ctx.add_basemap(
            ax, crs="EPSG:4326", source=BASEMAP,
            attribution_size=5, zorder=1,
        )
    except Exception as error:
        print(f"Basemap unavailable: {error}")

    ax.set_xlabel("Longitude", fontsize=10)
    ax.set_ylabel("Latitude", fontsize=10)
    ax.set_title(
        f"{band_name} ({low_mhz}\u2013{high_mhz} MHz) \u2013 "
        "Interpolated electric field exposure (V/m)\n"
        f"MKA Square, Tirana (N = {number_of_points} measurement locations)",
        fontsize=12, fontweight="bold",
    )
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:.4f}\u00b0E"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:.4f}\u00b0N"))
    ax.tick_params(labelsize=8)

    colorbar = fig.colorbar(image, ax=ax, fraction=0.042, pad=0.03)
    colorbar.set_label("Electric field strength, E (V/m)", fontsize=10)
    colorbar.ax.tick_params(labelsize=8)

    x0 = lon.min() - 0.05 * dx
    y0 = lat.min() - 0.055 * dy
    ax.add_patch(plt.Rectangle(
        (x0 - 0.02 * dx, y0 - 0.03 * dy),
        scale_bar_degrees + 0.09 * dx, 0.10 * dy,
        facecolor="white", edgecolor="black", lw=0.8, alpha=0.9, zorder=7,
    ))
    ax.plot([x0, x0 + scale_bar_degrees], [y0, y0], color="black", lw=3, zorder=8)
    for x_value in (x0, x0 + scale_bar_degrees):
        ax.plot(
            [x_value, x_value], [y0 - 0.008 * dy, y0 + 0.008 * dy],
            color="black", lw=1.5, zorder=8,
        )
    ax.text(
        x0 + scale_bar_degrees / 2, y0 + 0.022 * dy, "100 m",
        ha="center", va="bottom", fontsize=9, zorder=8,
    )

    north_x = lon.max() + 0.05 * dx
    north_y = lat.max() + 0.02 * dy
    ax.annotate(
        "", xy=(north_x, north_y + 0.07 * dy), xytext=(north_x, north_y),
        arrowprops={"arrowstyle": "-|>", "color": "black", "lw": 1.8}, zorder=8,
    )
    ax.text(
        north_x, north_y - 0.015 * dy, "N", ha="center", va="top",
        fontsize=11, fontweight="bold",
        bbox={"boxstyle": "square,pad=0.25", "fc": "white", "ec": "black", "lw": 0.8},
        zorder=8,
    )

    legend_items = [
        Line2D([0], [0], color="#00008B", lw=2.4, label="Study area boundary"),
        Line2D(
            [0], [0], marker="o", color="none", markerfacecolor="white",
            markeredgecolor="#333366", markersize=7, label="Measurement points",
        ),
        Line2D(
            [0], [0], color="cyan", lw=1.8,
            label=(
                f"Hotspot threshold\n{HOTSPOT_PERCENTILE}th percentile "
                f"({hotspot:.2f} V/m)"
            ),
        ),
    ]
    ax.legend(
        handles=legend_items, loc="upper center", bbox_to_anchor=(0.5, -0.10),
        ncol=3, fontsize=8.5, framealpha=0.95, edgecolor="#cccccc",
    )

    plt.tight_layout()
    output_file = OUTPUT_DIR / f"{band_name}_MKA_square_Tirana_satellite.png"
    fig.savefig(output_file, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {output_file}")

print(f"Completed: generated {len(BANDS)} maps.")
