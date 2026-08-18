"""Generate band-specific IDW RF-EMF maps from the public workbooks."""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.path import Path as MplPath
from scipy.spatial import ConvexHull

ROOT = Path(__file__).resolve().parents[1]
BANDS = [
    ("a", "LTE 800", "LTE800"),
    ("b", "900 MHz Mobile Band", "GSM900"),
    ("c", "LTE 1800", "LTE1800"),
    ("d", "2100 MHz Mobile Band", "UMTS2100"),
    ("e", "LTE 2600", "LTE2600"),
    ("f", "5G NR 3600", "5G"),
]


def load_site(site: str) -> tuple[pd.DataFrame, str, int]:
    if site == "mka":
        frame = pd.read_excel(ROOT / "data/mka_square_anonymized.xlsx")
        frame = frame.rename(columns={"lat": "latitude", "lon": "longitude", "5G_NR3600": "5G"})
        return frame, "MKA Square", 85
    frame = pd.read_excel(ROOT / "data/kt_square_anonymized.xlsx")
    frame = frame.rename(columns={"lat_round": "latitude", "long_round": "longitude",
                                  "5G_3500": "5G", "5G_NR3600": "5G"})
    return frame, "KT Square", 86


def idw(lon: np.ndarray, lat: np.ndarray, values: np.ndarray, n: int = 400):
    gx = np.linspace(lon.min(), lon.max(), n)
    gy = np.linspace(lat.min(), lat.max(), n)
    xx, yy = np.meshgrid(gx, gy)
    lat0 = float(lat.mean())
    scale_x = 111_320.0 * math.cos(math.radians(lat0))
    px = (lon - lon.mean()) * scale_x
    py = (lat - lat.mean()) * 110_540.0
    qx = (xx.ravel() - lon.mean()) * scale_x
    qy = (yy.ravel() - lat.mean()) * 110_540.0
    result = np.empty(qx.size)
    for start in range(0, qx.size, 5000):
        stop = min(start + 5000, qx.size)
        d2 = (qx[start:stop, None] - px) ** 2 + (qy[start:stop, None] - py) ** 2
        weights = 1.0 / np.maximum(d2, 1e-12)
        result[start:stop] = (weights @ values) / weights.sum(axis=1)
    points = np.column_stack([lon, lat])
    hull = points[ConvexHull(points).vertices]
    polygon = MplPath(np.vstack([hull, hull[0]]))
    inside = polygon.contains_points(np.column_stack([xx.ravel(), yy.ravel()]))
    surface = result.reshape(xx.shape)
    surface[~inside.reshape(xx.shape)] = np.nan
    return xx, yy, surface, hull


def render(site: str, basemap: bool = True) -> None:
    df, site_label, expected = load_site(site)
    if len(df) != expected:
        raise ValueError(f"Expected {expected} points, found {len(df)}")
    out = ROOT / "outputs/generated" / site
    out.mkdir(parents=True, exist_ok=True)
    lon = df["longitude"].to_numpy(float)
    lat = df["latitude"].to_numpy(float)
    for letter, label, column in BANDS:
        values = df[column].to_numpy(float)
        xx, yy, surface, hull = idw(lon, lat, values)
        p85 = float(np.percentile(values, 85))
        fig, ax = plt.subplots(figsize=(8, 9), dpi=200)
        ax.set_xlim(lon.min(), lon.max()); ax.set_ylim(lat.min(), lat.max())
        ax.set_aspect(1 / math.cos(math.radians(float(lat.mean()))))
        if basemap:
            try:
                import contextily as ctx
                ctx.add_basemap(ax, crs="EPSG:4326", source=ctx.providers.Esri.WorldImagery,
                                attribution=True, reset_extent=False)
            except Exception as exc:
                print(f"Basemap unavailable: {exc}")
        mesh = ax.pcolormesh(xx, yy, surface, cmap="turbo", shading="auto", alpha=.80)
        ax.contour(xx, yy, surface, levels=[p85], colors="#00F5FF", linewidths=2)
        closed = np.vstack([hull, hull[0]])
        ax.plot(closed[:, 0], closed[:, 1], color="#0A2292", lw=2.5)
        ax.scatter(lon, lat, s=20, facecolor="white", edgecolor="#34406A", lw=.7)
        ax.set(title=f"({letter}) {label} IDW-Interpolated Electric Field Exposure (V/m)\n"
                     f"{site_label}, Tirana · N = {expected}", xlabel="Longitude", ylabel="Latitude")
        fig.colorbar(mesh, ax=ax, label="Electric field strength, E (V/m)")
        fig.tight_layout()
        target = out / f"{site.upper()}_IDW_{letter}_{column.lower()}.png"
        fig.savefig(target, dpi=300, facecolor="white")
        plt.close(fig)
        print(f"{target.name}: P85={p85:.2f} V/m")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", choices=("kt", "mka"), required=True)
    parser.add_argument("--no-basemap", action="store_true")
    args = parser.parse_args()
    render(args.site, not args.no_basemap)
