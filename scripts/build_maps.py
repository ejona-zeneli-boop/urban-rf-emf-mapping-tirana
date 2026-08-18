"""Rebuild the 12 publication IDW maps from the two public workbooks."""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.path import Path as MplPath
from matplotlib.ticker import FuncFormatter, MaxNLocator
from scipy.spatial import ConvexHull

ROOT = Path(__file__).resolve().parents[1]
BANDS = [
    ("a", "LTE 800", "LTE800", "lte800"),
    ("b", "900 MHz Mobile Band", "GSM900", "mobile900"),
    ("c", "LTE 1800", "LTE1800", "lte1800"),
    ("d", "2100 MHz Mobile Band", "UMTS2100", "mobile2100"),
    ("e", "LTE 2600", "LTE2600", "lte2600"),
    ("f", "5G NR 3600", "5G_NR3600", "nr3600"),
]
SITES = {
    "mka": {"file": "mka_square_anonymized.xlsx", "prefix": "MKA", "title": "MKA Square",
            "n": 85, "grid": 520, "zoom": 19},
    "kt": {"file": "kt_square_anonymized.xlsx", "prefix": "KT", "title": "KT Square",
           "n": 86, "grid": 200, "zoom": 18},
}


def load_site(site: str):
    cfg = SITES[site]
    df = pd.read_excel(ROOT / "data" / cfg["file"])
    aliases = {"lat": "latitude", "lon": "longitude", "lat_round": "latitude",
               "long_round": "longitude", "5G_3500": "5G_NR3600"}
    df = df.rename(columns=aliases)
    needed = ["latitude", "longitude"] + [x[2] for x in BANDS]
    missing = [c for c in needed if c not in df]
    if missing:
        raise ValueError(f"Missing columns in {cfg['file']}: {missing}")
    if len(df) != cfg["n"]:
        raise ValueError(f"Expected {cfg['n']} points for {site}, found {len(df)}")
    if df[needed].isna().any().any():
        raise ValueError(f"Missing values in {cfg['file']}")
    return df.rename(columns={"latitude": "lat", "longitude": "lon"}), cfg


def idw_surface(lon, lat, values, n, power=2.0):
    pad_x, pad_y = (lon.max()-lon.min())*.025, (lat.max()-lat.min())*.025
    gx = np.linspace(lon.min()-pad_x, lon.max()+pad_x, n)
    gy = np.linspace(lat.min()-pad_y, lat.max()+pad_y, n)
    glon, glat = np.meshgrid(gx, gy)
    lat0 = float(lat.mean())
    xm = (lon-lon.mean())*111320*math.cos(math.radians(lat0)); ym = (lat-lat.mean())*110540
    gxm = (glon-lon.mean())*111320*math.cos(math.radians(lat0)); gym = (glat-lat.mean())*110540
    flat_x, flat_y = gxm.ravel(), gym.ravel(); out = np.empty(flat_x.size)
    for start in range(0, flat_x.size, 5000):
        stop = min(start+5000, flat_x.size)
        d2 = (flat_x[start:stop,None]-xm[None,:])**2 + (flat_y[start:stop,None]-ym[None,:])**2
        weights = 1/np.maximum(d2, 1e-10)**(power/2)
        vals = (weights @ values)/weights.sum(axis=1)
        exact = d2 < 1e-10
        if exact.any():
            rr, cc = np.where(exact); vals[rr] = values[cc]
        out[start:stop] = vals
    grid = out.reshape(glon.shape)
    points = np.column_stack([lon,lat]); hull = points[ConvexHull(points).vertices]
    inside = MplPath(np.vstack([hull,hull[0]])).contains_points(
        np.column_stack([glon.ravel(),glat.ravel()])).reshape(glon.shape)
    grid[~inside] = np.nan
    return glon, glat, grid, hull


def add_scale_bar(ax, lon, lat):
    dx = 100/(111320*math.cos(math.radians(float(lat.mean()))))
    xmin,xmax=ax.get_xlim(); ymin,ymax=ax.get_ylim(); xr,yr=xmax-xmin,ymax-ymin
    x0,y0=xmin+.07*xr,ymin+.035*yr
    ax.add_patch(Rectangle((xmin+.012*xr,ymin+.008*yr),.976*xr,.105*yr,
                 facecolor="white",edgecolor="#111827",linewidth=.7,alpha=.84,zorder=9))
    ax.plot([x0,x0+dx],[y0,y0],color="#111111",lw=3.2,solid_capstyle="butt",zorder=11)
    for xpos in (x0,x0+dx):
        ax.plot([xpos,xpos],[y0-.009*yr,y0+.009*yr],color="#111111",lw=2.2,zorder=11)
    ax.text(x0+dx/2,y0+.024*yr,"100 m",ha="center",va="bottom",fontsize=11,zorder=12)


def add_north_arrow(ax):
    ax.annotate("",xy=(.955,.972),xytext=(.955,.910),xycoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>",mutation_scale=16,lw=2.2,color="#111111"),zorder=15)
    ax.text(.955,.895,"N",transform=ax.transAxes,ha="center",va="center",fontsize=12,fontweight="bold",
            bbox=dict(boxstyle="square,pad=0.20",facecolor="white",edgecolor="#111111"),zorder=15)


def make_map(df, cfg, band, no_basemap=False):
    letter,label,column,slug=band
    lon=df.lon.to_numpy(float); lat=df.lat.to_numpy(float); values=df[column].to_numpy(float)
    glon,glat,grid,hull=idw_surface(lon,lat,values,cfg["grid"]); p85=float(np.percentile(values,85))
    fig,ax=plt.subplots(figsize=(10,10),dpi=300)
    xpad=(lon.max()-lon.min())*.035; ypad=(lat.max()-lat.min())*.035
    ax.set_xlim(lon.min()-xpad,lon.max()+xpad); ax.set_ylim(lat.min()-ypad,lat.max()+ypad)
    ax.set_aspect(1/math.cos(math.radians(float(lat.mean())))); ax.set_facecolor("#d8dee5")
    if not no_basemap:
        try:
            import contextily as ctx
            ctx.add_basemap(ax,crs="EPSG:4326",source=ctx.providers.Esri.WorldImagery,
                            zoom=cfg["zoom"],attribution=False,reset_extent=False,zorder=0)
        except Exception as exc:
            print(f"WARNING: basemap unavailable for {label}: {exc}")
    finite=grid[np.isfinite(grid)]
    mesh=ax.pcolormesh(glon,glat,grid,cmap="turbo",shading="auto",vmin=float(finite.min()),
                       vmax=float(finite.max()),alpha=.80,zorder=2,rasterized=True)
    ax.contour(glon,glat,grid,levels=[p85],colors="#00F5FF",linewidths=2.2,zorder=5)
    closed=np.vstack([hull,hull[0]]); ax.plot(closed[:,0],closed[:,1],color="#0A2292",lw=2.8,zorder=6)
    ax.scatter(lon,lat,s=25,facecolor="white",edgecolor="#34406A",linewidth=.75,zorder=7)
    fig.suptitle(f"({letter}) {label} IDW-Interpolated Electric Field Exposure (V/m)\n{cfg['title']}",
                 fontsize=15.5,fontweight="bold",y=.982,linespacing=1.15)
    ax.set_title(f"{cfg['title']}, Tirana · N = {cfg['n']} measurement points",fontsize=10.5,color="#374151",pad=10)
    ax.set_xlabel("Longitude",fontsize=12,labelpad=8); ax.set_ylabel("Latitude",fontsize=12,labelpad=8)
    ax.tick_params(labelsize=9.5,direction="out",length=4,width=.8)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x,pos:f"{x:.4f}°E")); ax.yaxis.set_major_formatter(FuncFormatter(lambda y,pos:f"{y:.4f}°N"))
    ax.xaxis.set_major_locator(MaxNLocator(nbins=6)); ax.yaxis.set_major_locator(MaxNLocator(nbins=7))
    add_north_arrow(ax); add_scale_bar(ax,lon,lat)
    cbar=fig.colorbar(mesh,ax=ax,fraction=.046,pad=.025); cbar.set_label("Electric field strength, E (V/m)",fontsize=12,labelpad=11)
    handles=[Line2D([0],[0],color="#0A2292",lw=2.8,label="Study area boundary"),
             Line2D([0],[0],marker="o",linestyle="None",markersize=7,markerfacecolor="white",markeredgecolor="#34406A",label="Measurement points"),
             Line2D([0],[0],color="#00F5FF",lw=2.4,label=f"Hotspot threshold\n85th percentile ({p85:.2f} V/m)")]
    fig.legend(handles=handles,loc="lower center",bbox_to_anchor=(.5,.012),ncol=3,frameon=True,
               fancybox=True,framealpha=.97,edgecolor="#B7BCC5",fontsize=10.5,handlelength=2.2,columnspacing=2,borderpad=.75)
    fig.subplots_adjust(left=.105,right=.88,top=.875,bottom=.145)
    out=ROOT/"outputs"/"figures"/f"{cfg['prefix'].lower()}_square"/f"{cfg['prefix']}_IDW_{letter}_{slug}.png"
    out.parent.mkdir(parents=True,exist_ok=True); fig.savefig(out,dpi=300,facecolor="white"); plt.close(fig)
    print(f"{out}: P85={p85:.2f} V/m")


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--site",choices=("kt","mka","all"),default="all")
    parser.add_argument("--no-basemap",action="store_true"); args=parser.parse_args()
    for site in SITES if args.site=="all" else [args.site]:
        df,cfg=load_site(site)
        for band in BANDS: make_map(df,cfg,band,args.no_basemap)


if __name__=="__main__": main()
