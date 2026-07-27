# Urban RF-EMF Mapping in Tirana

This repository contains anonymized datasets, Python scripts, and publication-ready
figures for spatial mapping of multi-band radiofrequency electromagnetic field
(RF-EMF) exposure at two urban squares in Tirana, Albania:

- Karl Topia Square (KT; locally known as Zogu i Zi), with 86 measurement locations.
- Mustafa Kemal Atatürk Square (MKA), with 85 measurement locations.

The maps show interpolated electric-field strength, measurement locations, the study
area boundary, a 100 m scale bar, a north arrow, and hotspot contours defined by the
85th percentile.

## Repository structure

```text
urban-rf-emf-mapping-tirana/
├── data/
│   ├── mka_square_anonymized.xlsx
│   └── zogu_zi_anonymized.xlsx
├── outputs/
│   └── figures/
│       ├── mka_square/
│       └── zogu_zi/
├── scripts/
│   ├── map_mka_square.py
│   └── map_zogu_zi.py
├── CITATION.cff
├── LICENSE
├── README.md
└── requirements.txt
```

## Measurement information

Outdoor measurements were collected using a NARDA SRM-3006 selective radiation
meter mounted on a tripod at a height of 1.5 m. Electric-field values are expressed
in volts per metre (V/m).

The public datasets contain anonymized point identifiers and geographic coordinates
with no personal identifiers. The MKA dataset contains band-specific values derived
from the measured ACT spectra using root-sum-square aggregation within each frequency
range.

## Frequency bands

| Band | Frequency range |
|---|---:|
| LTE800 | 791–862 MHz |
| GSM900 | 880–960 MHz |
| LTE1800 | 1710–1880 MHz |
| UMTS2100 | 1920–2170 MHz |
| LTE2600 | 2500–2690 MHz |
| 5G NR | 3400–3800 MHz |

## Installation

Python 3.10 or later is recommended.

```bash
pip install -r requirements.txt
```

The satellite basemap is retrieved online from Esri World Imagery through
`contextily`, so an internet connection is required when regenerating the complete
figures.

## Usage

Run either script from the repository root:

```bash
python scripts/map_zogu_zi.py
python scripts/map_mka_square.py
```

Generated figures are written to:

```text
outputs/figures/zogu_zi/
outputs/figures/mka_square/
```

## Spatial processing

The scripts:

1. read the anonymized measurement data;
2. construct the study-area boundary from the convex hull of the measurement points;
3. interpolate band-specific electric-field values using linear interpolation;
4. mask interpolated values outside the study boundary;
5. calculate the 85th-percentile hotspot threshold independently for each band; and
6. export color figures at 300 dpi.

Interpolation visualizes spatial patterns between sampled locations and does not
represent additional measurements.

## Reproducibility

The included processed datasets and scripts reproduce the analytical workflow without
requiring local absolute paths or the original instrument-export workbooks. Small
visual differences in the satellite basemap may occur if the external tile provider
updates its imagery.

## License

Code is released under the MIT License. The included data and figures are provided for
research and reproducibility purposes; third-party basemap imagery remains subject to
the source provider's terms and attribution requirements.

