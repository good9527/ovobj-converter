# -*- coding: utf-8 -*-
"""
pyovobj.exporters.shapefile
---------------------------
ESRI Shapefile (.shp) exporter with DBF 10-byte column name sanitization,
hash-based collision avoidance, and automatic .cpg (GBK) creation for ArcMap/AutoCAD compatibility.
"""

import os
import geopandas as gpd

def export_shapefile(gdf: gpd.GeoDataFrame, output_path: str, target_crs: str = None) -> str:
    """
    Exports a GeoDataFrame to ESRI Shapefile format.

    :param gdf: Source GeoDataFrame.
    :param output_path: Path to target .shp file.
    :param target_crs: Target CRS string (e.g. 'EPSG:4535' for CGCS2000).
    :return: Output file path.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # 1. Project if target_crs specified
    df_to_save = gdf.copy()
    if target_crs and gdf.crs != target_crs:
        df_to_save = df_to_save.to_crs(target_crs)

    # 2. Sanitize column names for DBF 10-byte limit
    col_mapping = {}
    used_names = set()
    for col in df_to_save.columns:
        if col == 'geometry':
            continue
        base = col[:10]
        cand = base
        count = 1
        while cand.lower() in used_names:
            suffix = f"_{count}"
            cand = base[: max(1, 10 - len(suffix))] + suffix
            count += 1
        used_names.add(cand.lower())
        col_mapping[col] = cand

    df_shp = df_to_save.rename(columns=col_mapping)

    # 3. Save with GBK encoding
    df_shp.to_file(output_path, driver='ESRI Shapefile', encoding='gbk')

    # 4. Generate .cpg file to ensure ArcGIS and CAD display Chinese without gibberish
    cpg_path = os.path.splitext(output_path)[0] + ".cpg"
    with open(cpg_path, 'w', encoding='ascii') as f:
        f.write("GBK\n")

    return output_path
