# -*- coding: utf-8 -*-
"""
tests.test_azimuth
------------------
Unit tests for Cadastral Boundary Surveying, Geodesic Bearings, and Turning Angles Engine.
"""

import unittest
import pandas as pd
from shapely.geometry import Polygon
from pyovobj.core.azimuth import (
    deg_to_dms,
    vincenty_azimuth,
    order_vertices_cadastral,
    analyze_polygon_boundary_points,
    extract_cadastral_demarcation_table
)

class TestAzimuth(unittest.TestCase):
    def test_deg_to_dms(self):
        """Tests decimal degree formatting to DMS string."""
        s = deg_to_dms(89.68532)
        self.assertTrue(s.startswith("089\u00b041'"))
        self.assertTrue(s.endswith('"'))

    def test_cardinal_azimuths(self):
        """Tests that cardinal direction vectors return precise azimuths."""
        # Due North
        fwd_n, back_n, dist_n = vincenty_azimuth(116.0, 39.0, 116.0, 40.0)
        self.assertTrue(abs(fwd_n - 0.0) < 1e-4 or abs(fwd_n - 360.0) < 1e-4)
        self.assertTrue(abs(back_n - 180.0) < 1e-4)
        self.assertGreater(dist_n, 110000.0)  # ~111 km

        # Due South
        fwd_s, back_s, dist_s = vincenty_azimuth(116.0, 40.0, 116.0, 39.0)
        self.assertTrue(abs(fwd_s - 180.0) < 1e-4)
        self.assertTrue(abs(back_s - 0.0) < 1e-4 or abs(back_s - 360.0) < 1e-4)

    def test_order_vertices_cadastral(self):
        """Tests northwest point selection and clockwise ordering."""
        # Counter-clockwise square
        ccw_coords = [(116.0, 39.0), (116.1, 39.0), (116.1, 39.1), (116.0, 39.1), (116.0, 39.0)]
        ordered = order_vertices_cadastral(ccw_coords)
        self.assertEqual(len(ordered), 4)
        # J1 must be northwest: (116.0, 39.1)
        self.assertEqual(ordered[0], (116.0, 39.1))
        # Clockwise sequence: (116.0, 39.1) -> (116.1, 39.1) -> (116.1, 39.0) -> (116.0, 39.0)
        self.assertEqual(ordered[1], (116.1, 39.1))
        self.assertEqual(ordered[2], (116.1, 39.0))
        self.assertEqual(ordered[3], (116.0, 39.0))

    def test_cadastral_demarcation_table(self):
        """Tests generation of complete surveyor boundary table."""
        poly = Polygon([(116.0, 39.0), (116.1, 39.0), (116.1, 39.1), (116.0, 39.1), (116.0, 39.0)])
        df = extract_cadastral_demarcation_table(poly)
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 4)
        self.assertEqual(list(df['point_id']), ['J1', 'J2', 'J3', 'J4'])
        self.assertEqual(list(df['next_point_id']), ['J2', 'J3', 'J4', 'J1'])
        self.assertIn('proj_x_northing', df.columns)
        self.assertIn('proj_y_easting', df.columns)
        self.assertIn('azimuth_dms', df.columns)
        self.assertIn('interior_angle_deg', df.columns)

        # Verify sum of interior angles for a quadrilateral = 360 degrees
        sum_interior = df['interior_angle_deg'].sum()
        self.assertLess(abs(sum_interior - 360.0), 1.0)  # Sub-degree spherical/ellipsoidal excess

if __name__ == '__main__':
    unittest.main()
