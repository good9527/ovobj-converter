# -*- coding: utf-8 -*-
"""
pyovobj.exporters.manager
-------------------------
Unified multi-format export manager coordinating exports to Shapefile,
GeoPackage, GeoJSON, AutoCAD DXF, Google Earth KML, and Excel/CSV spreadsheets.
"""

import os
import geopandas as gpd

from .shapefile import export_shapefile
from .geopackage import export_geopackage
from .geojson import export_geojson
from .cad_dxf import export_dxf
from .kml import export_kml
from .tabular import export_tabular

SUPPORTED_FORMATS = ['shp', 'gpkg', 'geojson', 'dxf', 'kml', 'xlsx', 'csv']

def export_dataset(
    gdf: gpd.GeoDataFrame,
    output_dir: str,
    base_name: str,
    formats: list[str] = None,
    target_crs: str = "EPSG:4535"
) -> dict[str, str]:
    """
    Exports a GeoDataFrame across multiple user-requested GIS and CAD formats.

    :param gdf: Source GeoDataFrame (in WGS84 EPSG:4326).
    :param output_dir: Destination folder.
    :param base_name: Base stem for generated files.
    :param formats: List of format extensions (e.g. ['shp', 'gpkg', 'dxf', 'kml']). If None, exports all.
    :param target_crs: Projected coordinate system (e.g. 'EPSG:4535' for CGCS2000).
    :return: Dictionary mapping format names to generated file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    if formats is None or 'all' in formats:
        requested = list(SUPPORTED_FORMATS)
    else:
        requested = [f.lower().strip().replace('.', '') for f in formats]

    results = {}

    # 1. ESRI Shapefile
    if 'shp' in requested:
        shp_path = os.path.join(output_dir, f"{base_name}_{target_crs.replace(':', '_')}.shp")
        export_shapefile(gdf, shp_path, target_crs=target_crs)
        results['shp'] = shp_path

    # 2. OGC GeoPackage
    if 'gpkg' in requested:
        gpkg_path = os.path.join(output_dir, f"{base_name}.gpkg")
        export_geopackage(gdf, gpkg_path, layer_name=base_name, target_crs=target_crs)
        results['gpkg'] = gpkg_path

    # 3. GeoJSON
    if 'geojson' in requested:
        geojson_path = os.path.join(output_dir, f"{base_name}.geojson")
        export_geojson(gdf, geojson_path)
        results['geojson'] = geojson_path

    # 4. AutoCAD DXF
    if 'dxf' in requested:
        dxf_path = os.path.join(output_dir, f"{base_name}.dxf")
        export_dxf(gdf, dxf_path, target_crs=target_crs)
        results['dxf'] = dxf_path

    # 5. Google Earth KML
    if 'kml' in requested:
        kml_path = os.path.join(output_dir, f"{base_name}.kml")
        export_kml(gdf, kml_path, doc_name=base_name)
        results['kml'] = kml_path

    # 6. Microsoft Excel
    if 'xlsx' in requested:
        xlsx_path = os.path.join(output_dir, f"{base_name}.xlsx")
        export_tabular(gdf, xlsx_path, calc_metrics=True, metric_crs=target_crs)
        results['xlsx'] = xlsx_path

    # 7. CSV
    if 'csv' in requested:
        csv_path = os.path.join(output_dir, f"{base_name}.csv")
        export_tabular(gdf, csv_path, calc_metrics=True, metric_crs=target_crs)
        results['csv'] = csv_path

    return results
