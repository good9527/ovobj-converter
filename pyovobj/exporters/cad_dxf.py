# -*- coding: utf-8 -*-
"""
pyovobj.exporters.cad_dxf
-------------------------
AutoCAD DXF exporter converting GIS vector geometries into native CAD entities
(closed LWPOLYLINE, LINE, POINT, TEXT) with intelligent layer grouping and styling.
"""

import os
import re
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon, MultiPolygon
import ezdxf

def export_dxf(
    gdf: gpd.GeoDataFrame,
    output_path: str,
    target_crs: str = None,
    layer_field: str = None,
    default_layer: str = "OMAP_FEATURES"
) -> str:
    """
    Exports a GeoDataFrame to AutoCAD DXF format.

    :param gdf: Source GeoDataFrame.
    :param output_path: Path to target .dxf file.
    :param target_crs: Target projected CRS (e.g. 'EPSG:4535' for metric CAD drawing).
    :param layer_field: Optional attribute column to group entities into distinct CAD layers.
    :param default_layer: Fallback CAD layer name.
    :return: Output file path.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    df_to_save = gdf.copy()
    if target_crs and gdf.crs != target_crs:
        df_to_save = df_to_save.to_crs(target_crs)

    doc = ezdxf.new('R2010')
    msp = doc.modelspace()

    # Pre-populate basic colors for layers
    palette_colors = [1, 2, 3, 4, 5, 6, 7, 8, 9, 30, 40, 50, 130, 150, 200]
    assigned_layers = {}

    def get_or_create_layer(layer_name: str) -> str:
        # Strip illegal AutoCAD characters: < > / \ " : ; ? * | = ` and control chars
        clean_name = re.sub(r'[<>\\/":;?*|=`\x00-\x1f]', '_', str(layer_name).strip())
        clean_name = clean_name[:31].strip()
        if not clean_name or not ezdxf.lldxf.validator.is_valid_layer_name(clean_name):
            clean_name = default_layer
            
        if clean_name not in assigned_layers:
            color_idx = palette_colors[len(assigned_layers) % len(palette_colors)]
            try:
                doc.layers.add(clean_name, color=color_idx)
            except Exception:
                pass
            assigned_layers[clean_name] = color_idx
        return clean_name

    for idx, row in df_to_save.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue

        layer_val = default_layer
        if layer_field and layer_field in row and row[layer_field]:
            layer_val = str(row[layer_field])
        elif 'DLMC' in row and row['DLMC']:
            layer_val = str(row['DLMC'])
        elif 'NAME' in row and row['NAME']:
            layer_val = str(row['NAME'])

        cad_layer = get_or_create_layer(layer_val)

        # Handle Points
        if isinstance(geom, Point):
            msp.add_point((geom.x, geom.y), dxfattribs={'layer': cad_layer})
            label = str(row.get('NAME') or row.get('DLMC') or '')
            if label:
                msp.add_text(label, dxfattribs={'insert': (geom.x, geom.y), 'height': 2.5, 'layer': cad_layer})

        # Handle LineStrings
        elif isinstance(geom, LineString):
            coords = [(p[0], p[1]) for p in geom.coords]
            msp.add_lwpolyline(coords, close=False, dxfattribs={'layer': cad_layer})

        # Handle Polygons
        elif isinstance(geom, Polygon):
            ext_coords = [(p[0], p[1]) for p in geom.exterior.coords]
            msp.add_lwpolyline(ext_coords, close=True, dxfattribs={'layer': cad_layer})
            for interior in geom.interiors:
                hole_coords = [(p[0], p[1]) for p in interior.coords]
                hole_layer = get_or_create_layer(cad_layer + "_HOLE")
                msp.add_lwpolyline(hole_coords, close=True, dxfattribs={'layer': hole_layer})

        # Handle MultiPolygons
        elif isinstance(geom, MultiPolygon):
            for poly in geom.geoms:
                ext_coords = [(p[0], p[1]) for p in poly.exterior.coords]
                msp.add_lwpolyline(ext_coords, close=True, dxfattribs={'layer': cad_layer})
                for interior in poly.interiors:
                    hole_coords = [(p[0], p[1]) for p in interior.coords]
                    hole_layer = get_or_create_layer(cad_layer + "_HOLE")
                    msp.add_lwpolyline(hole_coords, close=True, dxfattribs={'layer': hole_layer})

    doc.saveas(output_path)
    return output_path
