# -*- coding: utf-8 -*-
"""
pyovobj.core.grids
------------------
GB/T 13989-2012 National Basic Scale Topographic Map Sheet Indexing Engine.
Supports forward and inverse indexing for all 9 standard national scales:
- 1:1,000,000 (1m)
- 1:500,000   (500k, Code 'B')
- 1:250,000   (250k, Code 'C')
- 1:100,000   (100k, Code 'D')
- 1:50,000    (50k,  Code 'E')
- 1:25,000    (25k,  Code 'F')
- 1:10,000    (10k,  Code 'G')
- 1:5,000     (5k,   Code 'H')
- 1:2,000     (2k,   Code 'I')

Provides sub-millimeter bounding box reconstructions, polygon framing,
vectorized GeoDataFrame map sheet attribution, and polygon intersection indexing.
"""

import math
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import geopandas as gpd
from shapely.geometry import box, Point, Polygon, MultiPolygon
from shapely.geometry.base import BaseGeometry

# Standard GB/T 13989-2012 scale configuration
# Latitude and longitude grid subdivisions per 1:1,000,000 map sheet
SCALES_CONFIG: Dict[str, Dict[str, Union[str, float, int, None]]] = {
    '1m':   {'letter': None, 'dlat': 4.0,        'dlon': 6.0,        'rows': 1,   'cols': 1},
    '500k': {'letter': 'B',  'dlat': 2.0,        'dlon': 3.0,        'rows': 2,   'cols': 2},
    '250k': {'letter': 'C',  'dlat': 1.0,        'dlon': 1.5,        'rows': 4,   'cols': 4},
    '100k': {'letter': 'D',  'dlat': 20.0 / 60,  'dlon': 30.0 / 60,  'rows': 12,  'cols': 12},
    '50k':  {'letter': 'E',  'dlat': 10.0 / 60,  'dlon': 15.0 / 60,  'rows': 24,  'cols': 24},
    '25k':  {'letter': 'F',  'dlat': 5.0 / 60,   'dlon': 7.5 / 60,   'rows': 48,  'cols': 48},
    '10k':  {'letter': 'G',  'dlat': 2.5 / 60,   'dlon': 3.75 / 60,  'rows': 96,  'cols': 96},
    '5k':   {'letter': 'H',  'dlat': 1.25 / 60,  'dlon': 1.875 / 60, 'rows': 192, 'cols': 192},
    '2k':   {'letter': 'I',  'dlat': 37.5 / 3600,'dlon': 56.25 / 3600, 'rows': 384, 'cols': 384},
}

LETTER_TO_SCALE: Dict[str, str] = {
    v['letter']: k for k, v in SCALES_CONFIG.items() if v['letter'] is not None
}

ALIAS_TO_SCALE: Dict[str, str] = {
    '1:1000000': '1m', '1000000': '1m', '1m': '1m',
    '1:500000': '500k', '500000': '500k', '500k': '500k',
    '1:250000': '250k', '250000': '250k', '250k': '250k',
    '1:100000': '100k', '100000': '100k', '100k': '100k',
    '1:50000': '50k', '50000': '50k', '50k': '50k',
    '1:25000': '25k', '25000': '25k', '25k': '25k',
    '1:10000': '10k', '10000': '10k', '10k': '10k',
    '1:5000': '5k', '5000': '5k', '5k': '5k',
    '1:2000': '2k', '2000': '2k', '2k': '2k',
}

def normalize_scale(scale: str) -> str:
    """Normalizes scale input string to internal standard key."""
    s = str(scale).strip().lower().replace(" ", "")
    if s in ALIAS_TO_SCALE:
        return ALIAS_TO_SCALE[s]
    if s in SCALES_CONFIG:
        return s
    raise ValueError(f"Unsupported map sheet scale: '{scale}'. Supported: {list(SCALES_CONFIG.keys())}")

def lonlat_to_sheet_code(lon: float, lat: float, scale: str = '10k') -> str:
    """
    Computes standard GB/T 13989-2012 topographic map sheet code for a coordinate point.

    :param lon: Longitude in decimal degrees (e.g., 116.4074).
    :param lat: Latitude in decimal degrees (e.g., 39.9042).
    :param scale: Map scale (e.g., '10k', '1:10000', '50k', '1m').
    :return: 10-character standard sheet code (e.g., 'J50G003039') or 3-char for 1:1M ('J50').
    """
    scale_key = normalize_scale(scale)
    cfg = SCALES_CONFIG[scale_key]

    a = int(math.floor(lat / 4.0)) + 1
    if not (1 <= a <= 22):
        raise ValueError(f"Latitude {lat} out of GB/T 13989-2012 coverage (0 to 88 deg N)")

    a_char = chr(ord('A') + a - 1)
    b = int(math.floor(lon / 6.0)) + 31
    if not (1 <= b <= 60):
        raise ValueError(f"Longitude {lon} out of standard zone coverage (180W to 180E)")

    code_1m = f"{a_char}{b:02d}"
    if scale_key == '1m':
        return code_1m

    b_max_1m = a * 4.0
    l_min_1m = (b - 31) * 6.0

    # GB/T 13989-2012: Row numbered from North to South (1-indexed)
    # Column numbered from West to East (1-indexed)
    row = int(math.floor((b_max_1m - lat - 1e-12) / cfg['dlat'])) + 1
    row = max(1, min(int(cfg['rows']), row))

    col = int(math.floor((lon - l_min_1m) / cfg['dlon'])) + 1
    col = max(1, min(int(cfg['cols']), col))

    return f"{code_1m}{cfg['letter']}{row:03d}{col:03d}"

def sheet_code_to_bbox(code: str) -> Dict[str, Union[str, float]]:
    """
    Decodes a standard GB/T 13989-2012 sheet code into its geographic bounding box.

    :param code: Map sheet code string (e.g., 'J50G003039' or 'J50').
    :return: Dictionary containing scale, code, lon_min, lat_min, lon_max, lat_max.
    """
    clean_code = code.strip().upper()
    if len(clean_code) == 3:
        a_char = clean_code[0]
        a = ord(a_char) - ord('A') + 1
        b = int(clean_code[1:3])
        lat_min = (a - 1) * 4.0
        lat_max = a * 4.0
        lon_min = (b - 31) * 6.0
        lon_max = (b - 30) * 6.0
        return {
            'scale': '1m',
            'code': clean_code,
            'lon_min': lon_min,
            'lat_min': lat_min,
            'lon_max': lon_max,
            'lat_max': lat_max
        }
    elif len(clean_code) == 10:
        a_char = clean_code[0]
        a = ord(a_char) - ord('A') + 1
        b = int(clean_code[1:3])
        scale_letter = clean_code[3]
        if scale_letter not in LETTER_TO_SCALE:
            raise ValueError(f"Unknown scale identifier '{scale_letter}' in sheet code '{clean_code}'")

        scale_key = LETTER_TO_SCALE[scale_letter]
        cfg = SCALES_CONFIG[scale_key]

        row = int(clean_code[4:7])
        col = int(clean_code[7:10])

        b_max_1m = a * 4.0
        l_min_1m = (b - 31) * 6.0

        lat_max = b_max_1m - (row - 1) * float(cfg['dlat'])
        lat_min = lat_max - float(cfg['dlat'])
        lon_min = l_min_1m + (col - 1) * float(cfg['dlon'])
        lon_max = lon_min + float(cfg['dlon'])

        return {
            'scale': scale_key,
            'code': clean_code,
            'lon_min': lon_min,
            'lat_min': lat_min,
            'lon_max': lon_max,
            'lat_max': lat_max
        }
    else:
        raise ValueError(f"Invalid sheet code format: '{code}'. Expected 3 or 10 characters.")

def sheet_code_to_polygon(code: str) -> Polygon:
    """
    Constructs a Shapely Polygon representing the exact rectangular geographic frame of a map sheet.
    """
    b = sheet_code_to_bbox(code)
    return box(b['lon_min'], b['lat_min'], b['lon_max'], b['lat_max'])

def find_intersecting_sheet_codes(geom: BaseGeometry, scale: str = '10k') -> List[Dict[str, Union[str, float, Polygon]]]:
    """
    Finds all standard map sheets at the given scale that spatially intersect the input geometry.

    :param geom: Shapely geometry (Polygon, MultiPolygon, LineString, Point) in WGS84/CGCS2000 lon/lat.
    :param scale: Map scale (default: '10k').
    :return: List of dicts with 'code', 'scale', 'bbox', and 'geometry'.
    """
    if geom is None or geom.is_empty:
        return []

    scale_key = normalize_scale(scale)
    cfg = SCALES_CONFIG[scale_key]

    minx, miny, maxx, maxy = geom.bounds

    # Find bounding 1:1M zones
    a_min = max(1, int(math.floor(miny / 4.0)) + 1)
    a_max = min(22, int(math.floor(maxy / 4.0)) + 1)
    b_min = max(1, int(math.floor(minx / 6.0)) + 31)
    b_max = min(60, int(math.floor(maxx / 6.0)) + 31)

    results = []

    for a in range(a_min, a_max + 1):
        a_char = chr(ord('A') + a - 1)
        b_max_1m = a * 4.0
        for b in range(b_min, b_max + 1):
            code_1m = f"{a_char}{b:02d}"
            l_min_1m = (b - 31) * 6.0

            if scale_key == '1m':
                poly_box = box(l_min_1m, b_max_1m - 4.0, l_min_1m + 6.0, b_max_1m)
                if geom.intersects(poly_box):
                    results.append({
                        'code': code_1m,
                        'scale': '1m',
                        'geometry': poly_box
                    })
                continue

            # Calculate row and column spans within this 1:1M sheet
            lat_top = min(b_max_1m, maxy)
            lat_bottom = max(b_max_1m - 4.0, miny)
            lon_left = max(l_min_1m, minx)
            lon_right = min(l_min_1m + 6.0, maxx)

            if lat_top <= lat_bottom or lon_right <= lon_left:
                continue

            r_start = max(1, int(math.floor((b_max_1m - lat_top - 1e-12) / cfg['dlat'])) + 1)
            r_end = min(int(cfg['rows']), int(math.floor((b_max_1m - lat_bottom) / cfg['dlat'])) + 1)

            c_start = max(1, int(math.floor((lon_left - l_min_1m) / cfg['dlon'])) + 1)
            c_end = min(int(cfg['cols']), int(math.floor((lon_right - l_min_1m - 1e-12) / cfg['dlon'])) + 1)

            for r in range(r_start, r_end + 1):
                for c in range(c_start, c_end + 1):
                    sheet_code = f"{code_1m}{cfg['letter']}{r:03d}{c:03d}"
                    sheet_poly = sheet_code_to_polygon(sheet_code)
                    if geom.intersects(sheet_poly):
                        results.append({
                            'code': sheet_code,
                            'scale': scale_key,
                            'geometry': sheet_poly
                        })

    return results

def attach_map_sheet_codes(
    gdf: gpd.GeoDataFrame,
    scale: str = '10k',
    col_name: str = 'map_sheet'
) -> gpd.GeoDataFrame:
    """
    Computes and attaches standard GB/T 13989-2012 map sheet codes to each feature in a GeoDataFrame.
    Uses representative point (guaranteed to fall inside the geometry) for point determination.

    :param gdf: Input GeoDataFrame (in geographic coordinates lon/lat).
    :param scale: Map scale (default: '10k').
    :param col_name: Column name to store the generated sheet code (default: 'map_sheet').
    :return: GeoDataFrame with attached sheet code column.
    """
    if gdf.empty:
        return gdf

    df_out = gdf.copy()
    codes = []

    for geom in df_out.geometry:
        if geom is None or geom.is_empty:
            codes.append("")
            continue
        try:
            pt = geom.representative_point()
            code = lonlat_to_sheet_code(pt.x, pt.y, scale=scale)
            codes.append(code)
        except Exception:
            codes.append("")

    df_out[col_name] = codes
    return df_out
