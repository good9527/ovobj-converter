# Ovobj Converter (Toolkit for Ovital .ovobj Vector Conversion)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue?logo=python" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Precision-100.0000%25-brightgreen" alt="Precision">
  <img src="https://img.shields.io/badge/Formats-9%20GIS%20%26%20CAD-orange" alt="9 Formats Supported">
  <img src="https://img.shields.io/badge/Release-v1.3.1-blueviolet" alt="Release">
</p>

> **High-performance native Ovital (.ovobj) binary vector decoding, reverse packing, and multi-format conversion toolkit with 100.0000% mathematical precision. Features STRtree Spatial Indexing Topological Containment Forest, NumPy Vectorized CGCS2000 Ellipsoidal Integration (1.34M vertices/sec), geometric self-healing, and dynamic bitstream quantization.**

---

## 🌟 Highlights & Algorithmic Foundations

- **STRtree Topological Containment Forest**: Employs GEOS STRtree spatial indexing to accelerate recursive containment depth evaluation from $O(N^2)$ to $O(N \log N)$ (5,250 rings/sec). Includes robust Boolean Difference fallback for touching-vertex and shared-edge holes.
- **NumPy Vectorized CGCS2000 Ellipsoidal Integration (GB/T 21010-2017 & TD/T 1055-2019)**: Direct vectorized Simpson quadrature on the CGCS2000 reference ellipsoid ($< 10^{-8}$ relative error, > 1.34 million vertices/sec), completely eliminating Gauss-Kruger planar projection scale distortion.
- **Dynamic Bitstream Delta Quantization ($K=1 \sim 8$)**: Optimal variable-length delta encoding achieving > 1.1 million deltas/sec with 100.0000% zero-drift reconstruction.
- **Topological Self-Healing & Defect Audit**: Detects and repairs bow-tie self-intersections, collinear spike antennas, and duplicate vertices; enforces OGC counter-clockwise exterior and clockwise interior winding rules.
- **Multi-Core Parallel Batch Processing**: Built-in `ProcessPoolExecutor` with `-j / --workers` flag to batch process folders with multi-CPU parallel acceleration.
- **Enhanced CAD DXF Export**: Writes `$INSUNITS=6` metric headers, automatically places parcel name and calculated area text labels, and supports multi-ring solid hatch fills.
- **9 Output Formats**: Shapefile (.shp with auto `.cpg`), GeoPackage (.gpkg), GeoJSON (.geojson), AutoCAD (.dxf), Google Earth (.kml), Excel (.xlsx), CSV (.csv), FlatGeobuf (.fgb), and MapInfo TAB (.tab).

---

## 🚀 Algorithmic Benchmarks

Automated benchmarks evaluated on standard single-core execution (`tests/test_benchmark.py`):

| Algorithm Component | Workload / Scenario | Elapsed Time | Throughput | Fidelity |
| :--- | :--- | :---: | :---: | :---: |
| **Vectorized CGCS2000 Geodesic Area** | 5,000 vertices complex polygon | **3.73 ms** | **1,341,562 vertices/sec** | Rel error $< 1.19 \times 10^{-8}$ |
| **STRtree Containment Forest** | 40 parcels + holes (80 rings) | **15.23 ms** | **5,253 rings/sec** | 100% holes preserved |
| **Dynamic Bitstream Delta Packing ($K=1..8$)** | 5,000 regional jump deltas | **4.51 ms** | **1,107,469 deltas/sec** | 100.0000% lossless |
| **Dynamic Bitstream Delta Decoding** | 5,000 variable-length stream | **6.13 ms** | **815,900 deltas/sec** | Zero floating-point drift |

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

---

## 📄 License

MIT License. Contributions and PRs are welcome!
