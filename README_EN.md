# Ovobj Converter (Toolkit for Ovital .ovobj Vector Conversion)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue?logo=python" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Precision-100.0000%25-brightgreen" alt="Precision">
  <img src="https://img.shields.io/badge/Formats-9%20GIS%20%26%20CAD-orange" alt="9 Formats Supported">
  <img src="https://img.shields.io/badge/Release-v1.2.0-blueviolet" alt="Release">
</p>

> **High-performance native Ovital (.ovobj) binary vector decoding, reverse packing, and multi-format conversion toolkit with 100.0000% mathematical precision. Export to Shapefile, GeoPackage, GeoJSON, AutoCAD DXF, KML, Excel, CSV, FlatGeobuf, and MapInfo TAB, or reverse-pack GIS vectors into .ovobj.**

---

## 🌟 Highlights

- **Multi-Core Parallel Processing**: Built-in `ProcessPoolExecutor` with `-j / --workers` flag to batch process folders with multi-CPU parallel acceleration.
- **100.0000% Ground-Truth Precision**: Verified across 8,564 parcels and 168,010 coordinate vertices with zero floating-point drift up to 8 decimal places ($0.00000000^\circ$).
- **Bidirectional Reverse Packing**: Encode any Shapefile / GeoJSON / GeoPackage back into native `.ovobj` binary files for Ovital import.
- **Full OGC Topologies**: Native reconstruction of Points, LineStrings, Polygons, MultiPolygons, and inner Holes.
- **AutoCAD Metric Enhancements**: Writes `$INSUNITS=6` metric headers, automatically generates representative point TEXT labels, and supports solid HATCH fills.
- **Multi-Tier Attribute Extraction**: Restores JSON schemas, unbracketed key-values, and Placemark labels.
- **9 Output Formats**: Shapefile (.shp with auto `.cpg`), GeoPackage (.gpkg), GeoJSON (.geojson), AutoCAD (.dxf), Google Earth (.kml), Excel (.xlsx), CSV (.csv), FlatGeobuf (.fgb), and MapInfo TAB (.tab).
- **Interactive Web UI v2.0**: Zero-dependency embedded Web GUI with Leaflet map preview, property inspection popups, and in-browser reverse packing.
- **GCJ-02 to WGS-84 Correction**: Built-in toggle to inverse-transform distorted domestic Chinese map tile traces.

---

## 🛠️ Quickstart

```bash
git clone https://github.com/good9527/ovobj-converter.git
cd ovobj-converter
pip install -r requirements.txt
pip install -e . --no-build-isolation
```

### CLI
```bash
# Export all 9 formats
ovobj-converter input.ovobj -o ./exports

# Convert to CAD DXF and GeoPackage with projected CRS
ovobj-converter input.ovobj -f dxf,gpkg --crs EPSG:4535 -o ./output

# Reverse-pack Shapefile/GeoJSON into .ovobj
ovobj-converter my_parcels.shp --pack -o output.ovobj

# Launch interactive Web GUI (http://127.0.0.1:8080)
ovobj-converter --web

# Batch convert folder
ovobj-converter ./my_data --batch -f shp,gpkg -o ./batch_out
```

### Python SDK
```python
from pyovobj import convert_file, pack_to_ovobj, read_ovobj

# Forward conversion
convert_file("input.ovobj", formats=['shp', 'dxf', 'gpkg', 'fgb'], target_crs="EPSG:4535")

# Reverse packing into .ovobj
pack_to_ovobj("my_parcels.shp", "my_parcels.ovobj")

# Read into GeoPandas GeoDataFrame
gdf = read_ovobj("input.ovobj")
print(gdf.head())
```

---

## 📄 License

MIT License. Contributions and PRs are welcome!
