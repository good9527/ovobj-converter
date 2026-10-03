# -*- coding: utf-8 -*-
"""
pyovobj.exporters.kml
---------------------
Google Earth & Ovital re-import KML exporter with styled translucent polygons,
crisp boundary linework, and full ExtendedData attribute tables.
"""

import os
import html
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon, MultiPolygon

def export_kml(gdf: gpd.GeoDataFrame, output_path: str, doc_name: str = None) -> str:
    """
    Exports a GeoDataFrame to standard OGC KML 2.2 format.

    :param gdf: Source GeoDataFrame.
    :param output_path: Path to target .kml file.
    :param doc_name: Name of the KML document.
    :return: Output file path.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    df_to_save = gdf.copy()
    if df_to_save.crs != "EPSG:4326":
        df_to_save = df_to_save.to_crs("EPSG:4326")

    if not doc_name:
        doc_name = os.path.splitext(os.path.basename(output_path))[0]

    kml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        '  <Document>',
        f'    <name>{html.escape(doc_name)}</name>',
        '    <Style id="poly_style">',
        '      <LineStyle>',
        '        <color>ff0000ff</color>',
        '        <width>2</width>',
        '      </LineStyle>',
        '      <PolyStyle>',
        '        <color>7f00ff00</color>',
        '        <fill>1</fill>',
        '        <outline>1</outline>',
        '      </PolyStyle>',
        '    </Style>',
        '    <Style id="line_style">',
        '      <LineStyle>',
        '        <color>ffff0000</color>',
        '        <width>3</width>',
        '      </LineStyle>',
        '    </Style>'
    ]

    def render_extended_data(row, exclude=('geometry',)):
        lines = ['      <ExtendedData>']
        for col in row.index:
            if col in exclude:
                continue
            val = row[col]
            if val is not None and not (isinstance(val, float) and str(val) == 'nan'):
                sval = html.escape(str(val))
                scol = html.escape(str(col))
                lines.append(f'        <Data name="{scol}"><value>{sval}</value></Data>')
        lines.append('      </ExtendedData>')
        return '\n'.join(lines)

    def render_poly_xml(poly):
        lines = ['      <Polygon>', '        <outerBoundaryIs>', '          <LinearRing>', '            <coordinates>']
        ext_coords = ' '.join(f"{p[0]:.8f},{p[1]:.8f},0" for p in poly.exterior.coords)
        lines.append(f"              {ext_coords}")
        lines.extend(['            </coordinates>', '          </LinearRing>', '        </outerBoundaryIs>'])
        for interior in poly.interiors:
            lines.extend(['        <innerBoundaryIs>', '          <LinearRing>', '            <coordinates>'])
            in_coords = ' '.join(f"{p[0]:.8f},{p[1]:.8f},0" for p in interior.coords)
            lines.append(f"              {in_coords}")
            lines.extend(['            </coordinates>', '          </LinearRing>', '        </innerBoundaryIs>'])
        lines.append('      </Polygon>')
        return '\n'.join(lines)

    for idx, row in df_to_save.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue

        name_str = str(row.get('NAME') or row.get('DLMC') or f"Feature_{idx + 1}")
        kml_lines.append('    <Placemark>')
        kml_lines.append(f'      <name>{html.escape(name_str)}</name>')
        kml_lines.append(render_extended_data(row))

        if isinstance(geom, Point):
            kml_lines.append(f'      <Point><coordinates>{geom.x:.8f},{geom.y:.8f},0</coordinates></Point>')
        elif isinstance(geom, LineString):
            kml_lines.append('      <styleUrl>#line_style</styleUrl>')
            coords_str = ' '.join(f"{p[0]:.8f},{p[1]:.8f},0" for p in geom.coords)
            kml_lines.append(f'      <LineString><coordinates>{coords_str}</coordinates></LineString>')
        elif isinstance(geom, Polygon):
            kml_lines.append('      <styleUrl>#poly_style</styleUrl>')
            kml_lines.append(render_poly_xml(geom))
        elif isinstance(geom, MultiPolygon):
            kml_lines.append('      <styleUrl>#poly_style</styleUrl>')
            kml_lines.append('      <MultiGeometry>')
            for sub_poly in geom.geoms:
                kml_lines.append(render_poly_xml(sub_poly))
            kml_lines.append('      </MultiGeometry>')

        kml_lines.append('    </Placemark>')

    kml_lines.extend(['  </Document>', '</kml>'])

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(kml_lines))

    return output_path
