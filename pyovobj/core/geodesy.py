# -*- coding: utf-8 -*-
"""
pyovobj.core.geodesy
--------------------
National Standard CGCS2000 Ellipsoidal Polygon Area Integration Algorithm (GB/T 21010-2017
and Third National Land Survey TD/T 1055-2019 Appendix D) and Vincenty Geodesic Distance Integration.

Calculates true geodetic ellipsoidal surface areas and geodesic perimeters directly on the
reference ellipsoid, completely eliminating planar map projection scale distortions.
Optimized with NumPy vectorized numerical quadrature for high throughput over massive parcel datasets.
"""

import math
from typing import Tuple, List, Union, Optional
import numpy as np
from shapely.geometry import Point, LineString, Polygon, MultiPolygon, MultiLineString
from shapely.geometry.base import BaseGeometry
import geopandas as gpd

# Geodetic Reference Ellipsoids
ELLIPSOIDS = {
    'CGCS2000': {
        'a': 6378137.0,                 # Semi-major axis (meters)
        'f': 1.0 / 298.257222101,       # Flattening
        'name': 'China Geodetic Coordinate System 2000'
    },
    'WGS84': {
        'a': 6378137.0,
        'f': 1.0 / 298.257223563,
        'name': 'World Geodetic System 1984'
    },
    'XIAN80': {
        'a': 6378140.0,
        'f': 1.0 / 298.257,
        'name': 'Xi\'an Geodetic Coordinate System 1980'
    },
    'BEIJING54': {
        'a': 6378245.0,
        'f': 1.0 / 298.3,
        'name': 'Beijing Coordinate System 1954 (Krasovsky 1940)'
    }
}

class GeodeticCalculator:
    """
    High-precision geodesic calculator implementing ellipsoidal surface integration
    and Vincenty inverse distance equations with vector acceleration.
    """

    def __init__(self, ellipsoid: str = 'CGCS2000'):
        ell_info = ELLIPSOIDS.get(ellipsoid.upper(), ELLIPSOIDS['CGCS2000'])
        self.a = float(ell_info['a'])
        self.f = float(ell_info['f'])
        self.b = self.a * (1.0 - self.f)
        self.e2 = 2.0 * self.f - self.f * self.f
        self.e = math.sqrt(self.e2)
        self.b2 = self.b * self.b

    def _authalic_q(self, lat_rad: float) -> float:
        """
        Exact closed-form authalic latitude integral function Q(B):
        Q(B) = sin(B) / [2 * (1 - e^2 * sin^2(B))] + (1 / [4 * e]) * ln[(1 + e * sin(B)) / (1 - e * sin(B))]
        """
        sin_b = math.sin(lat_rad)
        term1 = sin_b / (2.0 * (1.0 - self.e2 * sin_b * sin_b))
        arg = (1.0 + self.e * sin_b) / max(1e-15, 1.0 - self.e * sin_b)
        term2 = (1.0 / (4.0 * self.e)) * math.log(max(1e-15, arg))
        return term1 + term2

    def _np_authalic_q(self, lat_rad_arr: np.ndarray) -> np.ndarray:
        """
        Vectorized closed-form authalic latitude integral for NumPy arrays.
        """
        sin_b = np.sin(lat_rad_arr)
        term1 = sin_b / (2.0 * (1.0 - self.e2 * sin_b * sin_b))
        arg = np.maximum(1e-15, (1.0 + self.e * sin_b) / np.maximum(1e-15, 1.0 - self.e * sin_b))
        term2 = (1.0 / (4.0 * self.e)) * np.log(arg)
        return term1 + term2

    def ring_ellipsoidal_area(self, coords: List[Tuple[float, float]]) -> float:
        """
        Computes the ellipsoidal surface area enclosed by an arbitrary closed ring
        using Simpson numerical quadrature along each edge.
        Auto-switches to vectorized matrix acceleration for long rings.

        :param coords: List of (lon, lat) tuples in decimal degrees.
        :return: Ellipsoidal surface area in square meters (m^2).
        """
        if len(coords) < 3:
            return 0.0

        pts = coords[:-1] if coords[0] == coords[-1] else coords
        m = len(pts)
        if m < 3:
            return 0.0

        # Vectorized path for complex rings (m >= 16 vertices)
        if m >= 16:
            arr = np.asarray(pts, dtype=np.float64)
            lons = np.radians(arr[:, 0])
            lats = np.radians(arr[:, 1])

            lons_next = np.roll(lons, -1)
            lats_next = np.roll(lats, -1)

            dL = (lons_next - lons + np.pi) % (2.0 * np.pi) - np.pi
            B_mid = 0.5 * (lats + lats_next)

            q1 = self._np_authalic_q(lats)
            q_mid = self._np_authalic_q(B_mid)
            q2 = self._np_authalic_q(lats_next)

            q_avg = (q1 + 4.0 * q_mid + q2) / 6.0
            total = np.sum(dL * q_avg)
            return float(abs(total * self.b2))

        # Scalar path for small parcels (avoids NumPy overhead)
        total_area = 0.0
        for i in range(m):
            lon1, lat1 = pts[i]
            lon2, lat2 = pts[(i + 1) % m]

            L1 = math.radians(lon1)
            L2 = math.radians(lon2)
            B1 = math.radians(lat1)
            B2 = math.radians(lat2)

            dL = (L2 - L1 + math.pi) % (2.0 * math.pi) - math.pi
            B_mid = 0.5 * (B1 + B2)
            q_avg = (self._authalic_q(B1) + 4.0 * self._authalic_q(B_mid) + self._authalic_q(B2)) / 6.0
            total_area += dL * q_avg

        return abs(total_area * self.b2)

    def polygon_ellipsoidal_area(self, poly: Polygon) -> float:
        """
        Computes the true geodetic ellipsoidal area of a Polygon,
        subtracting all interior voids (holes).
        """
        if poly.is_empty:
            return 0.0

        ext_area = self.ring_ellipsoidal_area(list(poly.exterior.coords))
        hole_area = sum(self.ring_ellipsoidal_area(list(interior.coords)) for interior in poly.interiors)
        return max(0.0, ext_area - hole_area)

    def geometry_ellipsoidal_area(self, geom: BaseGeometry) -> float:
        """
        Computes geodetic ellipsoidal area for any geometry (Polygon, MultiPolygon).
        """
        if geom is None or geom.is_empty:
            return 0.0

        if isinstance(geom, Polygon):
            return self.polygon_ellipsoidal_area(geom)
        elif isinstance(geom, MultiPolygon):
            return sum(self.polygon_ellipsoidal_area(p) for p in geom.geoms)
        return 0.0

    def vincenty_distance(self, lon1: float, lat1: float, lon2: float, lat2: float) -> float:
        """
        Calculates the geodesic distance between two points on the ellipsoid
        using Vincenty's inverse formula (accurate to sub-millimeter precision).
        """
        if lat1 == lat2 and lon1 == lon2:
            return 0.0

        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        U1 = math.atan((1.0 - self.f) * math.tan(phi1))
        U2 = math.atan((1.0 - self.f) * math.tan(phi2))
        L = math.radians(lon2 - lon1)
        Lambda = L

        sinU1, cosU1 = math.sin(U1), math.cos(U1)
        sinU2, cosU2 = math.sin(U2), math.cos(U2)

        for _ in range(100):
            sinLambda, cosLambda = math.sin(Lambda), math.cos(Lambda)
            sin_sigma = math.sqrt((cosU2 * sinLambda) ** 2 + (cosU1 * sinU2 - sinU1 * cosU2 * cosLambda) ** 2)
            if sin_sigma == 0:
                return 0.0
            cos_sigma = sinU1 * sinU2 + cosU1 * cosU2 * cosLambda
            sigma = math.atan2(sin_sigma, cos_sigma)
            sin_alpha = (cosU1 * cosU2 * sinLambda) / sin_sigma
            cos2_alpha = 1.0 - sin_alpha ** 2
            cos2_sigma_m = 0.0 if cos2_alpha == 0 else (cos_sigma - 2.0 * sinU1 * sinU2 / cos2_alpha)
            C = (self.f / 16.0) * cos2_alpha * (4.0 + self.f * (4.0 - 3.0 * cos2_alpha))
            Lambda_prev = Lambda
            Lambda = L + (1.0 - C) * self.f * sin_alpha * (
                sigma + C * sin_sigma * (cos2_sigma_m + C * cos_sigma * (-1.0 + 2.0 * cos2_sigma_m ** 2))
            )
            if abs(Lambda - Lambda_prev) < 1e-12:
                break

        u2 = cos2_alpha * (self.a ** 2 - self.b ** 2) / (self.b ** 2)
        A = 1.0 + (u2 / 16384.0) * (4096.0 + u2 * (-768.0 + u2 * (320.0 - 175.0 * u2)))
        B = (u2 / 1024.0) * (256.0 + u2 * (-128.0 + u2 * (74.0 - 47.0 * u2)))
        delta_sigma = B * sin_sigma * (
            cos2_sigma_m + (B / 4.0) * (
                cos_sigma * (-1.0 + 2.0 * cos2_sigma_m ** 2) -
                (B / 6.0) * cos2_sigma_m * (-3.0 + 4.0 * sin_sigma ** 2) * (-3.0 + 4.0 * cos2_sigma_m ** 2)
            )
        )
        return self.b * A * (sigma - delta_sigma)

    def coords_length(self, coords: List[Tuple[float, float]]) -> float:
        """
        Computes geodesic length along a sequence of (lon, lat) coordinates.
        Uses vectorized differential ellipsoidal arc integration for long paths (m >= 16).
        """
        if len(coords) < 2:
            return 0.0

        if len(coords) >= 16:
            arr = np.asarray(coords, dtype=np.float64)
            lons = np.radians(arr[:, 0])
            lats = np.radians(arr[:, 1])

            dL = np.diff(lons)
            dB = np.diff(lats)
            B_mid = 0.5 * (lats[:-1] + lats[1:])

            sin_b = np.sin(B_mid)
            denom = np.sqrt(1.0 - self.e2 * sin_b * sin_b)
            M = self.a * (1.0 - self.e2) / (denom ** 3)
            N = self.a / denom

            dx = N * np.cos(B_mid) * dL
            dy = M * dB
            ds = np.hypot(dx, dy)
            return float(np.sum(ds))

        total_len = 0.0
        for i in range(len(coords) - 1):
            p1 = coords[i]
            p2 = coords[i + 1]
            total_len += self.vincenty_distance(p1[0], p1[1], p2[0], p2[1])
        return total_len

    def geometry_length_or_perimeter(self, geom: BaseGeometry) -> float:
        """
        Computes geodesic perimeter (for polygons) or geodesic length (for lines).
        """
        if geom is None or geom.is_empty:
            return 0.0

        if isinstance(geom, LineString):
            return self.coords_length(list(geom.coords))
        elif isinstance(geom, MultiLineString):
            return sum(self.coords_length(list(line.coords)) for line in geom.geoms)
        elif isinstance(geom, Polygon):
            ext_len = self.coords_length(list(geom.exterior.coords))
            hole_len = sum(self.coords_length(list(h.coords)) for h in geom.interiors)
            return ext_len + hole_len
        elif isinstance(geom, MultiPolygon):
            return sum(self.geometry_length_or_perimeter(p) for p in geom.geoms)
        return 0.0

def compute_ellipsoidal_area(geom: BaseGeometry, ellipsoid: str = 'CGCS2000') -> float:
    """
    Computes true geodetic ellipsoidal area in square meters (m^2).
    """
    calc = GeodeticCalculator(ellipsoid=ellipsoid)
    return calc.geometry_ellipsoidal_area(geom)

def compute_area_mu(geom: BaseGeometry, ellipsoid: str = 'CGCS2000') -> float:
    """
    Computes geodetic area in standard Chinese Mu (1 亩 = 2000/3 m^2 ≈ 666.666667 m^2).
    """
    sqm = compute_ellipsoidal_area(geom, ellipsoid=ellipsoid)
    return sqm / (2000.0 / 3.0)

def compute_geodesic_length(geom: BaseGeometry, ellipsoid: str = 'CGCS2000') -> float:
    """
    Computes geodesic perimeter or line length in meters.
    """
    calc = GeodeticCalculator(ellipsoid=ellipsoid)
    return calc.geometry_length_or_perimeter(geom)

def attach_geodesic_metrics(gdf: gpd.GeoDataFrame, ellipsoid: str = 'CGCS2000') -> gpd.GeoDataFrame:
    """
    Computes and attaches surveyor-grade geodetic metrics to a GeoDataFrame:
    - area_sqm: True CGCS2000 ellipsoidal surface area in m^2 (for Polygons)
    - area_mu: True area in Chinese Mu (for Polygons)
    - perimeter_m: Geodesic perimeter in meters (for Polygons)
    - length_m: Geodesic length in meters (for LineStrings)
    """
    if gdf.empty:
        return gdf

    df_out = gdf.copy()
    calc = GeodeticCalculator(ellipsoid=ellipsoid)

    areas_sqm = []
    areas_mu = []
    perimeters = []
    lengths = []

    for geom in df_out.geometry:
        if geom is None or geom.is_empty:
            areas_sqm.append(0.0)
            areas_mu.append(0.0)
            perimeters.append(0.0)
            lengths.append(0.0)
            continue

        if isinstance(geom, (Polygon, MultiPolygon)):
            sqm = calc.geometry_ellipsoidal_area(geom)
            mu = sqm / (2000.0 / 3.0)
            peri = calc.geometry_length_or_perimeter(geom)
            areas_sqm.append(round(sqm, 2))
            areas_mu.append(round(mu, 4))
            perimeters.append(round(peri, 2))
            lengths.append(0.0)
        elif isinstance(geom, (LineString, MultiLineString)):
            l_m = calc.geometry_length_or_perimeter(geom)
            areas_sqm.append(0.0)
            areas_mu.append(0.0)
            perimeters.append(0.0)
            lengths.append(round(l_m, 2))
        else:
            areas_sqm.append(0.0)
            areas_mu.append(0.0)
            perimeters.append(0.0)
            lengths.append(0.0)

    # Attach columns only if relevant geometry types exist
    has_polys = any(t in ['Polygon', 'MultiPolygon'] for t in df_out.geometry.type)
    has_lines = any(t in ['LineString', 'MultiLineString'] for t in df_out.geometry.type)

    if has_polys:
        df_out['area_sqm'] = areas_sqm
        df_out['area_mu'] = areas_mu
        df_out['perimeter_m'] = perimeters

    if has_lines:
        df_out['length_m'] = lengths

    return df_out
