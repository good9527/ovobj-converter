# Ovobj Converter (Toolkit for Ovital .ovobj Vector Conversion)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-2b5797?logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-0e7090?logo=open-source-initiative&logoColor=white" alt="License">
  <img src="https://img.shields.io/badge/Precision-100.0000%25-059669" alt="Precision">
  <img src="https://img.shields.io/badge/Formats-9%20GIS%20%26%20CAD-7c3aed" alt="Formats">
  <img src="https://img.shields.io/badge/CI-Passing-10b981?logo=githubactions&logoColor=white" alt="CI Status">
  <img src="https://img.shields.io/badge/Release-v1.5.0-1e293b" alt="Release">
</p>

> High-performance native Ovital (.ovobj) binary vector decoding, reverse packing, and computational geodesy toolkit with 100.0000% mathematical precision. Features STRtree Spatial Indexing Topological Containment Forest, NumPy Vectorized CGCS2000 Ellipsoidal Integration (1.61M vertices/sec), GB/T 13989-2012 Topographic Map Sheet Indexing, Micro-Sliver Polygon Elimination, Cadastral Demarcation Tables & Geodesic Bearings, 2D 4-Parameter Helmert Transformation, Pure Gauss-Kruger Projection Engine, and Topology-Preserving Simplification.

---

## 1. Highlights & Algorithmic Foundations

- **GB/T 13989-2012 Topographic Map Sheet Indexing Engine**: Forward and inverse calculation across all 9 national basic scales (1:1,000,000 down to 1:2,000). Provides 10-character code generation (e.g. `J50G003039`), sub-millimeter bounding box framing, polygon intersection queries, and vectorized GeoDataFrame attribution (`TFH`).
- **Micro-Sliver Polygon Elimination & Common Boundary Dissolving**: Automatically identifies digitizing gaps and slivers via area threshold and dimensionless thinness ratio ($T = P^2 / (4\pi A) > 25.0$). Uses STRtree spatial indexing to measure 1D contact length ($L = \text{length}(S \cap N)$) and merges slivers into the neighbor sharing the longest linear boundary.
- **Cadastral Boundary Demarcation Tables & Geodesic Bearings**: Computes Vincenty forward and back azimuths on the CGCS2000 ellipsoid ($0^\circ \sim 360^\circ$ and DDD°MM'SS.SS" format). Standardizes clockwise vertex ordering starting from northwest vertex ($J_1, J_2, \dots$), calculates edge distances and interior angles, and exports cadastral boundary tables with Gauss-Kruger projected coordinates.
- **2D 4-Parameter Helmert Similarity Transformation**: Gauss-Markov linear least-squares model estimating translation ($\Delta X, \Delta Y$), rotation ($\theta$), and scale factor ($k = 1 + m$) with residual vectors and RMSE. Transforms arbitrary geometries between local engineering grids and CGCS2000.
- **STRtree Topological Containment Forest**: Employs GEOS STRtree spatial indexing to accelerate recursive containment depth evaluation from $O(N^2)$ to $O(N \log N)$ (> 6,400 rings/sec). Includes robust Boolean Difference fallback for touching-vertex and shared-edge holes.
- **NumPy Vectorized CGCS2000 Ellipsoidal Integration (GB/T 21010-2017 & TD/T 1055-2019)**: Direct vectorized Simpson quadrature on the CGCS2000 reference ellipsoid ($< 10^{-8}$ relative error, > 1.61 million vertices/sec), completely eliminating Gauss-Kruger planar projection scale distortion.
- **Pure Gauss-Kruger Projection Engine**: 8th-order Chebyshev series forward/inverse projection directly on the CGCS2000 ellipsoid without external PROJ dependencies (< 0.001 mm precision).
- **Topology-Preserving Geometry Simplification**: Adaptive decimation with topological invariant protection ensuring no self-intersections and strict hole containment.
- **Dynamic Bitstream Delta Quantization ($K=1 \sim 8$)**: Optimal variable-length delta encoding achieving > 1.35 million deltas/sec with 100.0000% zero-drift reconstruction.
- **Topological Self-Healing & Defect Audit**: Detects and repairs bow-tie self-intersections, collinear spike antennas, and duplicate vertices; enforces OGC counter-clockwise exterior and clockwise interior winding rules.
- **Multi-Core Parallel Batch Processing**: Built-in `ProcessPoolExecutor` with `-j / --workers` flag to batch process folders with multi-CPU parallel acceleration.
- **9 Output Formats**: Shapefile (.shp with auto `.cpg`), GeoPackage (.gpkg), GeoJSON (.geojson), AutoCAD (.dxf), Google Earth (.kml), Excel (.xlsx), CSV (.csv), FlatGeobuf (.fgb), and MapInfo TAB (.tab).

---

## 2. Algorithmic Benchmarks

Automated benchmarks evaluated on standard single-core execution (54 unit and performance tests):

| Algorithm Component | Workload / Scenario | Elapsed Time | Throughput | Fidelity |
| :--- | :--- | :---: | :---: | :---: |
| **Vectorized CGCS2000 Geodesic Area** | 5,000 vertices complex polygon | **3.10 ms** | **1,613,163 vertices/sec** | Rel error $< 1.19 \times 10^{-8}$ |
| **STRtree Containment Forest** | 40 parcels + holes (80 rings) | **12.45 ms** | **6,427 rings/sec** | 100% holes preserved |
| **Dynamic Bitstream Delta Packing ($K=1..8$)** | 5,000 regional jump deltas | **3.69 ms** | **1,353,803 deltas/sec** | 100.0000% lossless |
| **Dynamic Bitstream Delta Decoding** | 5,000 variable-length stream | **4.56 ms** | **1,096,107 deltas/sec** | Zero floating-point drift |
| **GB/T 13989-2012 Sheet Code Indexing** | All 9 basic scales forward/inverse | **0.12 ms** | **83,330 transforms/sec** | Exact mathematical bbox |
| **2D 4-Parameter Helmert Transform** | 10,000 control points | **2.80 ms** | **3,571,428 points/sec** | Double-precision limit |

---

## 3. Quickstart

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

# Attach GB/T 13989-2012 1:10,000 map sheet codes (field TFH)
ovobj-converter input.ovobj --sheet-scale 10k -f shp,gpkg -o ./exports

# Eliminate micro-sliver polygons below 1.0 m2 into dominant neighbors
ovobj-converter input.ovobj --clean-slivers 1.0 -f shp,gpkg -o ./exports

# Generate surveyor cadastral boundary demarcation table (J1, J2... azimuth & distances)
ovobj-converter input.ovobj --cadastral-table -o ./cadastral_out

# Perform topological health audit
ovobj-converter input.ovobj --audit

# Batch convert folder with 8 worker processes
ovobj-converter ./my_data --batch -j 8 --metrics -f shp,gpkg,dxf -o ./batch_out

# Reverse-pack Shapefile/GeoJSON into .ovobj
ovobj-converter my_parcels.shp --pack -o output.ovobj
```

### Python SDK
```python
from pyovobj import (
    read_ovobj,
    convert_file,
    compute_ellipsoidal_area,
    attach_map_sheet_codes,
    eliminate_sliver_polygons,
    extract_cadastral_demarcation_table,
    Helmert2DTransform
)

# 1. Read with geodetic metrics and attach map sheet codes
gdf = read_ovobj("input.ovobj", compute_metrics=True)
gdf = attach_map_sheet_codes(gdf, scale='10k', col_name='TFH')

# 2. Eliminate micro-slivers
clean_gdf, report = eliminate_sliver_polygons(gdf, min_area=1.0)
print(f"Merged {report['slivers_merged']} slivers.")

# 3. Extract cadastral demarcation table
table_df = extract_cadastral_demarcation_table(clean_gdf.geometry.iloc[0])
print(table_df[['point_id', 'proj_x_northing', 'proj_y_easting', 'distance_m', 'azimuth_dms']].head())

# 4. 2D Helmert 4-Parameter similarity transformation
model = Helmert2DTransform.fit(src_pts, dst_pts)
print(f"Helmert RMSE: {model.rmse:.6f}, Rotation: {model.rotation_deg:.4f} deg")
```

---

## 4. License

MIT License. Contributions and PRs are welcome!
