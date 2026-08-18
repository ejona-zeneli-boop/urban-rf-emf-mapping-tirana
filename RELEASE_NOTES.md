# Release notes — v1.1.0

## Changes from v1.0.0

- Replaced the previous maps with IDW-interpolated maps.
- Added a six-panel composite for each study area.
- Standardized band names and panel labels.
- Defined hotspots using the band-specific 85th percentile.
- Added a portable script that uses repository-relative paths.
- Removed dependencies on private absolute Windows paths and raw instrument files.

## Validation

The corrected KT data supplied for this revision were filtered to the 86 KT
locations and reduced to the variables required for reproduction. Dates,
times, antenna identifiers and unrelated study-area records were not retained
in the public workbook. Both public workbooks reproduce the P85 values printed
in the revised figures after rounding to two decimal places.
