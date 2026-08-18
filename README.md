# Urban RF-EMF Mapping in Tirana

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21625221.svg)](https://doi.org/10.5281/zenodo.21625221)

This repository provides anonymized measurement data, Python code, and revised
publication figures for inverse-distance-weighted (IDW) mapping of multi-band
radiofrequency electromagnetic-field (RF-EMF) exposure at two urban squares in
Tirana, Albania:

- Karl Topia Square (KT; locally known as Zogu i Zi), 86 locations;
- Mustafa Kemal Atatürk Square (MKA), 85 locations.

This is the revised `v1.1.0` release. It replaces the earlier interpolation
figures with band-specific IDW maps and six-panel composite figures prepared in
response to peer-review comments.

## Repository structure

```text
data/
  kt_square_anonymized.xlsx
  mka_square_anonymized.xlsx
outputs/figures/
  kt_square/
  mka_square/
scripts/
  generate_idw_maps.py
CITATION.cff
LICENSE
README.md
RELEASE_NOTES.md
requirements.txt
```

## Frequency bands

| Panel | Band | Frequency range |
|---|---|---:|
| (a) | LTE 800 | 791–862 MHz |
| (b) | 900 MHz mobile band | 880–960 MHz |
| (c) | LTE 1800 | 1710–1880 MHz |
| (d) | 2100 MHz mobile band | 1920–2170 MHz |
| (e) | LTE 2600 | 2500–2690 MHz |
| (f) | 5G NR 3600 | 3400–3800 MHz |

## Method

For each band, the script applies IDW interpolation with power 2 on a regular
grid. Results are clipped to the convex hull of the measurement locations. The
cyan contour marks the band-specific 85th percentile of the measured values.
The maps are visualizations between sampled locations and are not additional
measurements.

Outdoor measurements were collected using a NARDA SRM-3006 selective radiation
meter mounted on a tripod at 1.5 m. Electric-field strength is reported in V/m.

## Installation and use

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
```

Activate the environment, then run:

```bash
python -m pip install -r requirements.txt
python scripts/generate_idw_maps.py --site mka
python scripts/generate_idw_maps.py --site kt
```

Use `--no-basemap` for an offline run. The Esri World Imagery basemap is fetched
by `contextily`; imagery and attribution remain subject to the provider's terms.

## Reproducibility status

The included public datasets reproduce the reported 85th-percentile thresholds
in the revised figures after rounding to two decimal places. For KT these are
2.44, 1.58, 1.70, 1.05, 1.28 and 1.52 V/m; for MKA they are 1.67, 1.36, 1.44,
1.08, 1.75 and 1.46 V/m.

## Citation

Please cite the archived release. The DOI
[`10.5281/zenodo.21625221`](https://doi.org/10.5281/zenodo.21625221) resolves to
the latest version. Version-specific citation metadata is in `CITATION.cff`.

## License

Code is licensed under the MIT License. Third-party satellite imagery is not
covered by that license.
