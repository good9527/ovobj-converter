# -*- coding: utf-8 -*-
"""
pyovobj.exporters.mapinfo
-------------------------
MapInfo TAB exporter for telecommunications, infrastructure, and cadastre workflows.
"""

import os
import geopandas as gpd

def export_mapinfo(gdf: gpd.GeoDataFrame, output_path: str, target_crs: str = None) -> str:
    """
    Exports a GeoDataFrame to MapInfo TAB format.

    :param gdf: Source GeoDataFrame.
    :param output_path: Path to target .tab file.
    :param target_crs: Target CRS string.
    :return: Output file path.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    df_to_save = gdf.copy()
    if target_crs and gdf.crs != target_crs:
        df_to_save = df_to_save.to_crs(target_crs)

    df_to_save.to_file(output_path, driver="MapInfo File")
    return output_path
