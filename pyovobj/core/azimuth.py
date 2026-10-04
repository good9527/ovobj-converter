# -*- coding: utf-8 -*-
"""
pyovobj.core.azimuth
--------------------
Cadastral Boundary Surveying, Geodesic Bearings, and Turning Angles Engine.
Computes high-precision Vincenty forward and back azimuths on reference ellipsoids (CGCS2000/WGS84).
Generates surveyor-grade Cadastral Boundary Demarcation Tables (界址点成果表与界址线走向)
with standard clockwise point ordering starting from the northwest vertex (J1, J2, ...),
ellipsoidal edge distances, turning angles, and Gauss-Kruger projected plane coordinates.
"""

import math
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.geometry.base import BaseGeometry

from .geodesy import GeodeticCalculator, ELLIPSOIDS
from .projection import forward_gauss_kruger, get_central_meridian_3deg

def deg_to_dms(deg: float) -> str:
    """
    Converts decimal degrees to standard surveyor DMS format: DDD°MM'SS.SS"

    :param deg: Angle in decimal degrees (e.g., 89.68532).
    :return: Formatted string (e.g., 089°41'07.15").
    """
    deg_norm = deg % 360.0
    d = int(deg_norm)
    rem = (deg_norm - d) * 60.0
    m = int(rem)
    s = (rem - m) * 60.0
    return f"{d:03d}\u00b0{m:02d}'{s:05.2f}\""

def vincenty_azimuth(
    lon1: float,
    lat1: float,
    lon2: float,
    lat2: float,
    ellipsoid: str = 'CGCS2000'
) -> Tuple[float, float, float]:
    """
    Computes forward geodetic azimuth, back geodetic azimuth, and geodesic distance
    between two points on the reference ellipsoid using Vincenty's inverse formulas.

    :param lon1: Longitude of start point in decimal degrees.
    :param lat1: Latitude of start point in decimal degrees.
    :param lon2: Longitude of end point in decimal degrees.
    :param lat2: Latitude of end point in decimal degrees.
    :param ellipsoid: Reference ellipsoid name ('CGCS2000', 'WGS84', etc.).
    :return: Tuple of (forward_azimuth_deg, back_azimuth_deg, distance_meters).
    """
    if lat1 == lat2 and lon1 == lon2:
        return 0.0, 0.0, 0.0

    calc = GeodeticCalculator(ellipsoid=ellipsoid)
    a = calc.a
    b = calc.b
    f = calc.f

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    u1 = math.atan((1.0 - f) * math.tan(phi1))
    u2 = math.atan((1.0 - f) * math.tan(phi2))
    l_diff = math.radians(lon2 - lon1)
    lambda_val = l_diff

    sin_u1, cos_u1 = math.sin(u1), math.cos(u1)
    sin_u2, cos_u2 = math.sin(u2), math.cos(u2)

    for _ in range(100):
        sin_lambda = math.sin(lambda_val)
        cos_lambda = math.cos(lambda_val)

        sin_sigma = math.sqrt(
            (cos_u2 * sin_lambda) ** 2 +
            (cos_u1 * sin_u2 - sin_u1 * cos_u2 * cos_lambda) ** 2
        )
        if sin_sigma == 0.0:
            return 0.0, 0.0, 0.0

        cos_sigma = sin_u1 * sin_u2 + cos_u1 * cos_u2 * cos_lambda
        sigma = math.atan2(sin_sigma, cos_sigma)

        sin_alpha = (cos_u1 * cos_u2 * sin_lambda) / sin_sigma
        cos2_alpha = 1.0 - sin_alpha ** 2
        cos2_sigma_m = 0.0 if cos2_alpha == 0 else (cos_sigma - 2.0 * sin_u1 * sin_u2 / cos2_alpha)

        c_val = (f / 16.0) * cos2_alpha * (4.0 + f * (4.0 - 3.0 * cos2_alpha))
        lambda_prev = lambda_val
        lambda_val = l_diff + (1.0 - c_val) * f * sin_alpha * (
            sigma + c_val * sin_sigma * (
                cos2_sigma_m + c_val * cos_sigma * (-1.0 + 2.0 * cos2_sigma_m ** 2)
            )
        )
        if abs(lambda_val - lambda_prev) < 1e-12:
            break

    u2_val = cos2_alpha * (a ** 2 - b ** 2) / (b ** 2)
    a_coef = 1.0 + (u2_val / 16384.0) * (4096.0 + u2_val * (-768.0 + u2_val * (320.0 - 175.0 * u2_val)))
    b_coef = (u2_val / 1024.0) * (256.0 + u2_val * (-128.0 + u2_val * (74.0 - 47.0 * u2_val)))
    delta_sigma = b_coef * sin_sigma * (
        cos2_sigma_m + (b_coef / 4.0) * (
            cos_sigma * (-1.0 + 2.0 * cos2_sigma_m ** 2) -
            (b_coef / 6.0) * cos2_sigma_m * (-3.0 + 4.0 * sin_sigma ** 2) * (-3.0 + 4.0 * cos2_sigma_m ** 2)
        )
    )
    dist = b * a_coef * (sigma - delta_sigma)

    alpha1 = math.atan2(cos_u2 * sin_lambda, cos_u1 * sin_u2 - sin_u1 * cos_u2 * cos_lambda)
    alpha2 = math.atan2(cos_u1 * sin_lambda, -sin_u1 * cos_u2 + cos_u1 * sin_u2 * cos_lambda)

    fwd_az = (math.degrees(alpha1) + 360.0) % 360.0
    back_az = (math.degrees(alpha2) + 180.0) % 360.0
    return float(fwd_az), float(back_az), float(dist)

def _is_ring_clockwise(coords: List[Tuple[float, float]]) -> bool:
    """Computes signed planar area to test clockwise orientation (negative signed area)."""
    n = len(coords)
    if n < 3:
        return True
    signed_area = 0.0
    for i in range(n - 1):
        x1, y1 = coords[i]
        x2, y2 = coords[i + 1]
        signed_area += (x1 * y2 - x2 * y1)
    return signed_area < 0.0

def order_vertices_cadastral(coords: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    Standardizes parcel boundary vertices for cadastral demarcation:
    1. Removes closing duplicate vertex.
    2. Enforces strict clockwise orientation.
    3. Identifies the northwest vertex (highest latitude, tie-break lowest longitude) as J1.
    4. Rotates the list to begin at J1.

    :param coords: List of (lon, lat) vertex tuples.
    :return: Ordered list of unique boundary vertices.
    """
    pts = list(coords)
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]

    if len(pts) < 3:
        return pts

    # Ensure closed loop temporarily to evaluate orientation
    loop = pts + [pts[0]]
    if not _is_ring_clockwise(loop):
        # Reverse to clockwise
        pts = pts[::-1]

    # Find north-westernmost vertex: max latitude, min longitude
    # Score: Lat - 0.0001 * Lon (prioritizes high latitude, then low longitude)
    best_idx = 0
    best_score = float('-inf')
    for idx, (lon, lat) in enumerate(pts):
        score = lat - 0.00001 * lon
        if score > best_score:
            best_score = score
            best_idx = idx

    # Rotate so best_idx is 0
    pts = pts[best_idx:] + pts[:best_idx]
    return pts

def analyze_polygon_boundary_points(
    poly: Polygon,
    ellipsoid: str = 'CGCS2000',
    prefix: str = 'J'
) -> List[Dict[str, Union[str, float]]]:
    """
    Analyzes all boundary points of a polygon exterior ring and computes edge metrics:
    - Point ID (J1, J2, ...)
    - Longitude, Latitude (degrees)
    - Next Point ID
    - Segment Geodesic Distance (m)
    - Segment Forward Azimuth (deg & DMS)
    - Interior Vertex Angle (deg)

    :param poly: Input Polygon.
    :param ellipsoid: Reference ellipsoid name (default: 'CGCS2000').
    :param prefix: Boundary point ID prefix (default: 'J').
    :return: List of dictionaries per boundary point.
    """
    if poly is None or poly.is_empty:
        return []

    pts = order_vertices_cadastral(list(poly.exterior.coords))
    n = len(pts)
    if n < 3:
        return []

    records = []

    # First pass: calculate edge bearings and distances
    edge_bearings = []
    edge_distances = []
    for i in range(n):
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        fwd, _, dist = vincenty_azimuth(p1[0], p1[1], p2[0], p2[1], ellipsoid=ellipsoid)
        edge_bearings.append(fwd)
        edge_distances.append(dist)

    # Second pass: calculate turning / interior angles
    for i in range(n):
        pt_id = f"{prefix}{i + 1}"
        next_id = f"{prefix}{((i + 1) % n) + 1}"
        lon, lat = pts[i]

        fwd_az = edge_bearings[i]
        dist_m = edge_distances[i]

        # Incoming bearing from previous edge
        prev_fwd = edge_bearings[(i - 1 + n) % n]

        # Deflection angle (positive = right turn)
        defl = (fwd_az - prev_fwd + 180.0) % 360.0 - 180.0

        # Interior angle for clockwise boundary
        interior_angle = (180.0 - defl) % 360.0

        records.append({
            'point_id': pt_id,
            'lon': float(lon),
            'lat': float(lat),
            'next_point_id': next_id,
            'distance_m': round(dist_m, 4),
            'azimuth_deg': round(fwd_az, 4),
            'azimuth_dms': deg_to_dms(fwd_az),
            'interior_angle_deg': round(interior_angle, 4)
        })

    return records

def extract_cadastral_demarcation_table(
    geom: BaseGeometry,
    ellipsoid: str = 'CGCS2000',
    central_meridian: Optional[float] = None,
    point_prefix: str = 'J'
) -> pd.DataFrame:
    """
    Generates a surveyor-grade Cadastral Boundary Demarcation Table (界址点成果表)
    as a pandas DataFrame.
    Includes both geographic CGCS2000 coordinates and projected Gauss-Kruger 3° coordinates (X Northing, Y Easting).

    :param geom: Polygon or MultiPolygon geometry.
    :param ellipsoid: Reference ellipsoid name (default: 'CGCS2000').
    :param central_meridian: Central meridian for Gauss-Kruger projection. If None, auto-calculated.
    :param point_prefix: Boundary point identifier prefix (default: 'J').
    :return: pandas DataFrame containing complete cadastral demarcation records.
    """
    if geom is None or geom.is_empty:
        return pd.DataFrame()

    if isinstance(geom, MultiPolygon):
        poly = max(geom.geoms, key=lambda p: p.area)
    elif isinstance(geom, Polygon):
        poly = geom
    else:
        raise ValueError(f"Geometry type {geom.geom_type} is not supported for cadastral demarcation table.")

    records = analyze_polygon_boundary_points(poly, ellipsoid=ellipsoid, prefix=point_prefix)
    if not records:
        return pd.DataFrame()

    if central_meridian is None:
        rep = poly.representative_point()
        central_meridian = get_central_meridian_3deg(rep.x)

    # Attach projected coordinates
    for rec in records:
        x_proj, y_proj = forward_gauss_kruger(rec['lon'], rec['lat'], cm_deg=central_meridian)
        rec['proj_x_northing'] = round(x_proj, 3)
        rec['proj_y_easting'] = round(y_proj, 3)
        rec['central_meridian'] = central_meridian

    df = pd.DataFrame(records)
    # Order columns logically
    col_order = [
        'point_id', 'lon', 'lat', 'proj_x_northing', 'proj_y_easting',
        'next_point_id', 'distance_m', 'azimuth_deg', 'azimuth_dms',
        'interior_angle_deg', 'central_meridian'
    ]
    return df[[c for c in col_order if c in df.columns]]
