# -*- coding: utf-8 -*-
"""
pyovobj.exporters.tabular
-------------------------
Tabular data exporter for Microsoft Excel (.xlsx) and CSV (.csv), incorporating
all attribute fields, Well-Known Text (WKT) geometries, centroids, and area calculations.
"""

import os
import geopandas as gpd
import pandas as pd

def export_tabular(
    gdf: gpd.GeoDataFrame,
    output_path: str,
    calc_metrics: bool = True,
    metric_crs: str = "EPSG:4535"
) -> str:
    """
    Exports a GeoDataFrame to an Excel (.xlsx) or CSV (.csv) spreadsheet.

    :param gdf: Source GeoDataFrame.
    :param output_path: Target path (ending in .xlsx or .csv).
    :param calc_metrics: If True, computes Centroids, Area (sqm and 亩), and Length.
    :param metric_crs: Projected coordinate system used for precise metric calculations.
    :return: Output file path.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    df = gdf.copy()

    # Calculate centroids and metrics using projected coordinate system
    if calc_metrics:
        try:
            metric_geom = df.to_crs(metric_crs).geometry
            df['area_sqm'] = metric_geom.area
            df['area_mu'] = metric_geom.area * 0.0015
            df['length_m'] = metric_geom.length
            
            # Reproject projected centroid to WGS84 for true geodetic coordinates
            wgs_centroids = metric_geom.centroid.to_crs("EPSG:4326")
            df['centroid_lon'] = wgs_centroids.x
            df['centroid_lat'] = wgs_centroids.y
        except Exception:
            wgs_geom = df.geometry if df.crs == "EPSG:4326" else df.to_crs("EPSG:4326").geometry
            df['centroid_lon'] = [p.centroid.x for p in wgs_geom]
            df['centroid_lat'] = [p.centroid.y for p in wgs_geom]
    else:
        wgs_geom = df.geometry if df.crs == "EPSG:4326" else df.to_crs("EPSG:4326").geometry
        df['centroid_lon'] = [p.centroid.x for p in wgs_geom]
        df['centroid_lat'] = [p.centroid.y for p in wgs_geom]

    df['geometry_wkt'] = df.geometry.to_wkt()

    # Drop shapely geometry object for pure tabular serialization
    tab_df = pd.DataFrame(df.drop(columns=['geometry']))

    ext = os.path.splitext(output_path)[1].lower()
    if ext == '.csv':
        tab_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    else:
        tab_df.to_excel(output_path, index=False, engine='openpyxl')

    return output_path
