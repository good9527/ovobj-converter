# Ovobj Converter (Toolkit for Ovital .ovobj Vector Conversion)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue?logo=python" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Precision-100.0000%25-brightgreen" alt="Precision">
  <img src="https://img.shields.io/badge/Ovital_VIP-Not_Required-orange" alt="No VIP Required">
  <img src="https://img.shields.io/badge/Release-v1.0.0-blueviolet" alt="Release">
</p>

> **Bypass Ovital VIP export limits. Reconstruct vector geometries directly from proprietary .ovobj bitstreams with 100.0000% mathematical precision. Export directly to Shapefile, GeoPackage, GeoJSON, AutoCAD DXF, KML, Excel, and CSV.**

---

## 🌟 Highlights

- **No VIP Required**: Decodes arbitrarily large datasets without splitting into 1,000-feature batches.
- **100.0000% Ground-Truth Precision**: Verified across 8,564 parcels and 168,010 coordinate vertices with zero floating-point drift up to 8 decimal places ($0.00000000^\circ$).
- **Full OGC Topologies**: Native reconstruction of Points, LineStrings, Polygons, MultiPolygons, and inner Holes.
- **Multi-Tier Attribute Extraction**: Restores JSON schemas, unbracketed key-values, and Placemark labels.
- **7 Output Formats**: Shapefile (.shp with auto `.cpg`), GeoPackage (.gpkg), GeoJSON (.geojson), AutoCAD (.dxf), Google Earth (.kml), Excel (.xlsx), and CSV (.csv).
- **GCJ-02 to WGS-84 Correction**: Built-in toggle to inverse-transform distorted domestic Chinese map tile traces.

---

## 🛠️ Quickstart

```bash
git clone https://github.com/good9527/ovobj-converter.git
cd ovobj-converter
pip install -r requirements.txt
pip install -e .
```

### CLI
```bash
# Export all 7 formats
ovobj-converter input.ovobj -o ./exports

# Convert to CAD DXF and GeoPackage with projected CRS
ovobj-converter input.ovobj -f dxf,gpkg --crs EPSG:4535 -o ./output

# Batch convert folder
ovobj-converter ./my_data --batch -f shp,gpkg -o ./batch_out
```

### Python SDK
```python
from pyovobj import convert_file, read_ovobj

# One-liner conversion
convert_file("input.ovobj", formats=['shp', 'dxf', 'gpkg'], target_crs="EPSG:4535")

# Read into GeoPandas GeoDataFrame
gdf = read_ovobj("input.ovobj")
print(gdf.head())
```

---

## 📄 License

MIT License. Contributions and PRs are welcome!
