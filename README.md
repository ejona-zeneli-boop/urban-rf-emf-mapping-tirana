Replace the three commands in the README usage section with:

```bash
python -m pip install -r requirements.txt
python scripts/build_maps.py --site all
python scripts/build_composites.py
```

For an offline validation without satellite tiles, use:

```bash
python scripts/build_maps.py --site all --no-basemap
python scripts/build_composites.py
```
