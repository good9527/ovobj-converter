# -*- coding: utf-8 -*-
"""
pyovobj.exporters.geojson
-------------------------
Standard RFC 7946 GeoJSON exporter for web mapping, Mapbox, Leaflet, and Cesium.
"""

import os
import geopandas as gpd

def export_geojson(gdf: gpd.GeoDataFrame, output_path: str) -> str:
    """
    Exports a GeoDataFrame to standard WGS84 GeoJSON format.

    :param gdf: Source GeoDataFrame.
    :param output_path: Path to target .geojson file.
    :return: Output file path.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # GeoJSON specification RFC 7946 requires WGS84 (EPSG:4326)
    df_to_save = gdf.copy()
    if df_to_save.crs != "EPSG:4326":
        df_to_save = df_to_save.to_crs("EPSG:4326")

    df_to_save.to_file(output_path, driver="GeoJSON")
    return output_path
