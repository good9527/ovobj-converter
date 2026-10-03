# -*- coding: utf-8 -*-
"""
pyovobj.exporters.cad_dxf
-------------------------
AutoCAD DXF exporter converting GIS vector geometries into native CAD entities
(closed LWPOLYLINE, LINE, POINT, TEXT labels, and optional HATCH fills) with
standard AutoCAD metric headers, intelligent layer grouping, and text styling.
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
    label_field: str = None,
    add_labels: bool = True,
    text_height: float = 3.0,
    add_hatch: bool = False,
    default_layer: str = "OMAP_FEATURES"
) -> str:
    """
    Exports a GeoDataFrame to AutoCAD DXF format with metric units and annotations.

    :param gdf: Source GeoDataFrame.
    :param output_path: Path to target .dxf file.
    :param target_crs: Target projected CRS (e.g. 'EPSG:4535' for metric CAD drawing).
    :param layer_field: Optional attribute column to group entities into distinct CAD layers.
    :param label_field: Optional attribute column to use for text annotations.
    :param add_labels: If True, renders polygon centroid / representative point text labels.
    :param text_height: Font height in drawing units (meters).
    :param add_hatch: If True, adds solid hatch fills to polygon interiors.
    :param default_layer: Fallback CAD layer name.
    :return: Output file path.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    df_to_save = gdf.copy()
    if target_crs and gdf.crs != target_crs:
        df_to_save = df_to_save.to_crs(target_crs)

    doc = ezdxf.new('R2010')
    
    # Configure AutoCAD drawing headers for Metric (Meters)
    try:
        doc.header['$INSUNITS'] = 6       # 6 = Meters
        doc.header['$MEASUREMENT'] = 1    # 1 = Metric
    except Exception:
        pass

    msp = doc.modelspace()

    # Palette of distinctive AutoCAD indexing colors
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

        # Determine layer name
        layer_val = default_layer
        if layer_field and layer_field in row and row[layer_field]:
            layer_val = str(row[layer_field])
        elif 'DLMC' in row and row['DLMC']:
            layer_val = str(row['DLMC'])
        elif 'NAME' in row and row['NAME']:
            layer_val = str(row['NAME'])

        cad_layer = get_or_create_layer(layer_val)

        # Determine label text
        label_text = ""
        if label_field and label_field in row and row[label_field]:
            label_text = str(row[label_field])
        elif 'NAME' in row and row['NAME']:
            label_text = str(row['NAME'])
        elif 'DLMC' in row and row['DLMC']:
            label_text = str(row['DLMC'])

        # Case 1: Point
        if isinstance(geom, Point):
            msp.add_point((geom.x, geom.y), dxfattribs={'layer': cad_layer})
            if add_labels and label_text:
                msp.add_text(label_text, dxfattribs={
                    'insert': (geom.x + text_height * 0.5, geom.y + text_height * 0.5),
                    'height': text_height,
                    'layer': cad_layer
                })

        # Case 2: LineString
        elif isinstance(geom, LineString):
            coords = [(p[0], p[1]) for p in geom.coords]
            msp.add_lwpolyline(coords, close=False, dxfattribs={'layer': cad_layer})

        # Case 3: Polygon
        elif isinstance(geom, Polygon):
            ext_coords = [(p[0], p[1]) for p in geom.exterior.coords]
            msp.add_lwpolyline(ext_coords, close=True, dxfattribs={'layer': cad_layer})
            for interior in geom.interiors:
                hole_coords = [(p[0], p[1]) for p in interior.coords]
                hole_layer = get_or_create_layer(cad_layer + "_HOLE")
                msp.add_lwpolyline(hole_coords, close=True, dxfattribs={'layer': hole_layer})

            # Optional solid hatch
            if add_hatch:
                try:
                    hatch = msp.add_hatch(color=assigned_layers.get(cad_layer, 7), dxfattribs={'layer': cad_layer})
                    hatch.paths.add_polyline_path(ext_coords, is_closed=True)
                except Exception:
                    pass

            # Text label at representative point
            if add_labels and label_text:
                try:
                    rp = geom.representative_point()
                    lbl_layer = get_or_create_layer(cad_layer + "_LABEL")
                    msp.add_text(label_text, dxfattribs={
                        'insert': (rp.x, rp.y),
                        'height': text_height,
                        'layer': lbl_layer
                    })
                except Exception:
                    pass

        # Case 4: MultiPolygon
        elif isinstance(geom, MultiPolygon):
            for poly in geom.geoms:
                ext_coords = [(p[0], p[1]) for p in poly.exterior.coords]
                msp.add_lwpolyline(ext_coords, close=True, dxfattribs={'layer': cad_layer})
                for interior in poly.interiors:
                    hole_coords = [(p[0], p[1]) for p in interior.coords]
                    hole_layer = get_or_create_layer(cad_layer + "_HOLE")
                    msp.add_lwpolyline(hole_coords, close=True, dxfattribs={'layer': hole_layer})

            if add_labels and label_text:
                try:
                    rp = geom.representative_point()
                    lbl_layer = get_or_create_layer(cad_layer + "_LABEL")
                    msp.add_text(label_text, dxfattribs={
                        'insert': (rp.x, rp.y),
                        'height': text_height,
                        'layer': lbl_layer
                    })
                except Exception:
                    pass

    doc.saveas(output_path)
    return output_path
