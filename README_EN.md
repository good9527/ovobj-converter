# Ovobj Converter (Toolkit for Ovital .ovobj Vector Conversion)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue?logo=python" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Precision-100.0000%25-brightgreen" alt="Precision">
  <img src="https://img.shields.io/badge/Formats-9%20GIS%20%26%20CAD-orange" alt="9 Formats Supported">
  <img src="https://img.shields.io/badge/Release-v1.3.0-blueviolet" alt="Release">
</p>

> **High-performance native Ovital (.ovobj) binary vector decoding, reverse packing, and multi-format conversion toolkit with 100.0000% mathematical precision. Features Topological Containment Forest reconstruction, National Standard CGCS2000 Ellipsoidal Area numerical integration, geometric self-healing, and dynamic bitstream quantization.**

---

## 🌟 Highlights & Algorithmic Foundations

- **Topological Containment Forest Algorithm**: Reconstructs nested MultiPolygons and inner holes to arbitrary depths (Depth 0, 1, 2, 3...) using containment depth trees, eliminating lost holes in multi-ring parcels.
- **National Standard CGCS2000 Ellipsoidal Numerical Integration (GB/T 21010-2017 & TD/T 1055-2019)**: Direct Simpson quadrature on the CGCS2000 reference ellipsoid ($< 10^{-8}$ relative error), eliminating Gauss-Kruger planar map distortion for cadastral audits.
- **Vincenty Inverse Geodesic Distance**: Sub-millimeter ($< 10^{-7}\text{ m}$) geodesic perimeter and line length integration.
- **Topological Self-Healing & Defect Audit**: Detects and repairs bow-tie self-intersections, collinear spike antennas, and duplicate vertices; enforces OGC counter-clockwise exterior and clockwise interior winding rules.
- **Dynamic Bitstream Delta Quantization ($K=1 \sim 8$)**: Full variable-length delta encoding covering large regional jumps.
- **Multi-Core Parallel Batch Processing**: Built-in `ProcessPoolExecutor` with `-j / --workers` flag to batch process folders with multi-CPU parallel acceleration.
- **100.0000% Ground-Truth Precision**: Verified across 8,564 parcels and 168,010 coordinate vertices with zero floating-point drift up to 8 decimal places ($0.00000000^\circ$).
- **Bidirectional Reverse Packing**: Encode any Shapefile / GeoJSON / GeoPackage back into native `.ovobj` binary files for Ovital import.
- **9 Output Formats**: Shapefile (.shp with auto `.cpg`), GeoPackage (.gpkg), GeoJSON (.geojson), AutoCAD (.dxf), Google Earth (.kml), Excel (.xlsx), CSV (.csv), FlatGeobuf (.fgb), and MapInfo TAB (.tab).
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
# Export all 9 formats with surveyor-grade CGCS2000 ellipsoidal metrics
ovobj-converter input.ovobj --metrics -o ./exports

# Perform topological health audit
ovobj-converter input.ovobj --audit

# Batch convert folder with 8 worker processes
ovobj-converter ./my_data --batch -j 8 --metrics -f shp,gpkg,dxf -o ./batch_out

# Reverse-pack Shapefile/GeoJSON into .ovobj
ovobj-converter my_parcels.shp --pack -o output.ovobj
```

### Python SDK
```python
from pyovobj import convert_file, pack_to_ovobj, read_ovobj

# Read with surveyor-grade geodetic metrics
gdf = read_ovobj("input.ovobj", compute_metrics=True)
print(gdf[['area_sqm', 'area_mu', 'perimeter_m']].head())

# Forward conversion
convert_file("input.ovobj", formats=['shp', 'dxf', 'gpkg', 'fgb'], compute_metrics=True)

# Reverse packing into .ovobj
pack_to_ovobj("my_parcels.shp", "my_parcels.ovobj")
```

---

## 📄 License

MIT License. Contributions and PRs are welcome!
