# -*- coding: utf-8 -*-
"""
tests.test_geodesy
-------------------
Unit tests for National Standard CGCS2000 Ellipsoidal Area Integration
and Vincenty Geodesic Distance calculations, including NumPy vectorization parity.
"""

import math
import unittest
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, LineString
import geopandas as gpd
from pyproj import Geod

from pyovobj.core.geodesy import (
    GeodeticCalculator,
    compute_ellipsoidal_area,
    compute_area_mu,
    compute_geodesic_length,
    attach_geodesic_metrics
)

class TestGeodesy(unittest.TestCase):

    def setUp(self):
        self.calc = GeodeticCalculator(ellipsoid='CGCS2000')
        self.geod = Geod(ellps='WGS84')

    def test_vincenty_distance(self):
        # Two points separated by ~7km
        lon1, lat1 = 77.20, 39.00
        lon2, lat2 = 77.25, 39.05
        d_calc = self.calc.vincenty_distance(lon1, lat1, lon2, lat2)
        _, _, d_geod = self.geod.inv(lon1, lat1, lon2, lat2)
        self.assertAlmostEqual(d_calc, d_geod, delta=0.001)

    def test_ellipsoidal_area_vs_pyproj(self):
        # Large parcel of ~24,000,000 m^2 (~36,000 mu)
        coords = [(77.20, 39.00), (77.25, 39.00), (77.25, 39.05), (77.20, 39.05), (77.20, 39.00)]
        poly = Polygon(coords)
        calc_area = self.calc.polygon_ellipsoidal_area(poly)
        geod_area, _ = self.geod.geometry_area_perimeter(poly)
        geod_area = abs(geod_area)

        rel_error = abs(calc_area - geod_area) / geod_area
        self.assertLess(rel_error, 1e-6)

    def test_vectorized_large_polygon_parity(self):
        # Create a 100-vertex circular parcel (triggers vectorized path m >= 16)
        theta = np.linspace(0, 2 * np.pi, 101)
        lons = 77.25 + 0.05 * np.cos(theta)
        lats = 39.05 + 0.05 * np.sin(theta)
        pts = list(zip(lons, lats))
        poly = Polygon(pts)

        area_calc = self.calc.polygon_ellipsoidal_area(poly)
        geod_area, _ = self.geod.geometry_area_perimeter(poly)
        geod_area = abs(geod_area)

        rel_error = abs(area_calc - geod_area) / geod_area
        self.assertLess(rel_error, 1e-6)
        self.assertGreater(area_calc, 1e6)

    def test_vectorized_length_parity(self):
        # Path with 50 points
        theta = np.linspace(0, np.pi, 50)
        lons = 77.25 + 0.02 * np.cos(theta)
        lats = 39.05 + 0.02 * np.sin(theta)
        pts = list(zip(lons, lats))
        line = LineString(pts)

        calc_len = compute_geodesic_length(line)
        # Compute stepwise with pyproj
        geod_len = 0.0
        for i in range(len(pts) - 1):
            _, _, d = self.geod.inv(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1])
            geod_len += d

        rel_diff = abs(calc_len - geod_len) / geod_len
        self.assertLess(rel_diff, 1e-4)

    def test_polygon_with_hole_area(self):
        outer = [(77.00, 39.00), (77.10, 39.00), (77.10, 39.10), (77.00, 39.10), (77.00, 39.00)]
        hole  = [(77.02, 39.02), (77.08, 39.02), (77.08, 39.08), (77.02, 39.08), (77.02, 39.02)]
        poly_with_hole = Polygon(outer, [hole])
        poly_outer = Polygon(outer)
        poly_hole = Polygon(hole)

        area_total = compute_ellipsoidal_area(poly_with_hole)
        area_outer = compute_ellipsoidal_area(poly_outer)
        area_hole = compute_ellipsoidal_area(poly_hole)

        self.assertAlmostEqual(area_total, area_outer - area_hole, delta=0.01)

    def test_mu_conversion(self):
        # 2000/3 m^2 = 1 mu
        coords = [(77.20, 39.00), (77.25, 39.00), (77.25, 39.05), (77.20, 39.05), (77.20, 39.00)]
        poly = Polygon(coords)
        sqm = compute_ellipsoidal_area(poly)
        mu = compute_area_mu(poly)
        self.assertAlmostEqual(mu, sqm / (2000.0 / 3.0), places=6)

    def test_attach_geodesic_metrics(self):
        p1 = Polygon([(77.0, 39.0), (77.1, 39.0), (77.1, 39.1), (77.0, 39.1), (77.0, 39.0)])
        line1 = LineString([(77.0, 39.0), (77.1, 39.1)])
        gdf = gpd.GeoDataFrame([
            {'name': 'Parcel_A', 'geometry': p1},
            {'name': 'Canal_B', 'geometry': line1}
        ], crs="EPSG:4326")

        enriched = attach_geodesic_metrics(gdf)
        self.assertIn('area_sqm', enriched.columns)
        self.assertIn('area_mu', enriched.columns)
        self.assertIn('perimeter_m', enriched.columns)
        self.assertIn('length_m', enriched.columns)

        self.assertGreater(enriched.loc[0, 'area_sqm'], 0)
        self.assertGreater(enriched.loc[0, 'area_mu'], 0)
        self.assertGreater(enriched.loc[1, 'length_m'], 0)

if __name__ == '__main__':
    unittest.main()
