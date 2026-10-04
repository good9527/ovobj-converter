# -*- coding: utf-8 -*-
"""
tests.test_projection
----------------------
Unit tests for pure-mathematical CGCS2000 Gauss-Kruger 3-degree forward and inverse projections.
Cross-verifies precision against PROJ / PyProj EPSG:4514 standard.
"""

import unittest
from shapely.geometry import Point, LineString, Polygon
from pyproj import Transformer

from pyovobj.core.projection import (
    forward_gauss_kruger,
    inverse_gauss_kruger,
    project_coords,
    project_geometry
)

class TestProjection(unittest.TestCase):

    def setUp(self):
        # CGCS2000 3-degree Zone 26 (Central Meridian 78E -> EPSG:4514)
        self.trans_forward = Transformer.from_crs('EPSG:4326', 'EPSG:4514', always_xy=True)
        self.trans_inverse = Transformer.from_crs('EPSG:4514', 'EPSG:4326', always_xy=True)

    def test_forward_projection_precision(self):
        # Benchmark coordinates: lon 77.25, lat 39.05
        lon, lat = 77.25, 39.05
        pyproj_x, pyproj_y = self.trans_forward.transform(lon, lat)

        my_x, my_y = forward_gauss_kruger(lon, lat, cm_deg=78.0, with_zone_prefix=True)

        diff_north = abs(my_x - pyproj_y)
        diff_east = abs(my_y - pyproj_x)

        # Accuracy must be within 0.001 meters (1 millimeter)
        self.assertLess(diff_north, 0.001)
        self.assertLess(diff_east, 0.001)

    def test_inverse_projection_precision(self):
        lon_orig, lat_orig = 77.25, 39.05
        x_north, y_east = forward_gauss_kruger(lon_orig, lat_orig, cm_deg=78.0, with_zone_prefix=False)

        lon_back, lat_back = inverse_gauss_kruger(x_north, y_east, cm_deg=78.0)

        self.assertAlmostEqual(lon_back, lon_orig, places=7)
        self.assertAlmostEqual(lat_back, lat_orig, places=7)

    def test_project_geometry(self):
        poly_deg = Polygon([(77.20, 39.00), (77.25, 39.00), (77.25, 39.05), (77.20, 39.05), (77.20, 39.00)])
        poly_metric = project_geometry(poly_deg, cm_deg=78.0, with_zone_prefix=False)

        self.assertIsInstance(poly_metric, Polygon)
        self.assertTrue(poly_metric.is_valid)
        # Area in metric meters should be approx 24,000,000 m^2
        self.assertGreater(poly_metric.area, 2e7)
        self.assertLess(poly_metric.area, 3e7)

if __name__ == '__main__':
    unittest.main()
