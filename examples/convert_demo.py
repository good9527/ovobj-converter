# -*- coding: utf-8 -*-
"""
examples/convert_demo.py
------------------------
Quick demonstration showing how to use pyovobj in Python code.
"""

from pyovobj import read_ovobj, convert_file

def main():
    ovobj_path = "path/to/your/input.ovobj"
    output_dir = "./output_exports"

    # Option 1: One-line conversion to multiple formats
    print("[1] Converting .ovobj to Shapefile, GeoPackage, DXF, GeoJSON, KML, and Excel...")
    results = convert_file(
        input_file=ovobj_path,
        output_dir=output_dir,
        formats=['shp', 'gpkg', 'dxf', 'geojson', 'kml', 'xlsx'],
        target_crs="EPSG:4535",  # CGCS2000 3-degree GK zone
        fix_gcj02=False          # Set True if manually drawn on GCJ-02 domestic tiles
    )
    for fmt, path in results.items():
        print(f"  -> Generated [{fmt.upper()}]: {path}")

    # Option 2: Read directly into GeoPandas GeoDataFrame for custom spatial analytics
    print("\n[2] Reading .ovobj directly into GeoDataFrame...")
    gdf = read_ovobj(ovobj_path)
    print(f"Total features: {len(gdf)}")
    print(f"Columns: {list(gdf.columns)}")
    print(f"Geometry summary:\n{gdf.geometry.type.value_counts()}")

if __name__ == '__main__':
    main()
