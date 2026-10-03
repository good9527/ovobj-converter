# -*- coding: utf-8 -*-
"""
pyovobj.exporters.geopackage
----------------------------
OGC GeoPackage (.gpkg) exporter preserving 100% of untruncated column names,
data types, and UTF-8 string encoding without DBF size restrictions.
"""

import os
import geopandas as gpd

def export_geopackage(gdf: gpd.GeoDataFrame, output_path: str, layer_name: str = None, target_crs: str = None) -> str:
    """
    Exports a GeoDataFrame to OGC GeoPackage format.

    :param gdf: Source GeoDataFrame.
    :param output_path: Path to target .gpkg file.
    :param layer_name: Layer name inside GeoPackage (defaults to file stem).
    :param target_crs: Target CRS string.
    :return: Output file path.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    df_to_save = gdf.copy()
    if target_crs and gdf.crs != target_crs:
        df_to_save = df_to_save.to_crs(target_crs)

    if not layer_name:
        layer_name = os.path.splitext(os.path.basename(output_path))[0]

    df_to_save.to_file(output_path, layer=layer_name, driver="GPKG")
    return output_path
