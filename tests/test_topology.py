# -*- coding: utf-8 -*-
"""
tests.test_topology
-------------------
Unit tests for geometry construction and topology classification.
"""

import unittest
from shapely.geometry import Point, LineString, Polygon, MultiPolygon
from pyovobj.core.topology import build_geometry_from_points

class TestTopology(unittest.TestCase):

    def test_point(self):
        pts = [(77.25, 39.05)]
        geom = build_geometry_from_points(pts)
        self.assertIsInstance(geom, Point)
        self.assertAlmostEqual(geom.x, 77.25)
        self.assertAlmostEqual(geom.y, 39.05)

    def test_linestring(self):
        pts = [(77.25, 39.05), (77.26, 39.06), (77.27, 39.07)]
        geom = build_geometry_from_points(pts)
        self.assertIsInstance(geom, LineString)
        self.assertEqual(len(geom.coords), 3)

    def test_closed_polygon(self):
        pts = [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]
        geom = build_geometry_from_points(pts)
        self.assertIsInstance(geom, Polygon)
        self.assertTrue(geom.is_valid)
        self.assertAlmostEqual(geom.area, 1.0)

    def test_polygon_with_hole(self):
        # Outer ring 0..10, Inner ring 2..8
        outer = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
        inner = [(2, 2), (8, 2), (8, 8), (2, 8), (2, 2)]
        pts = outer + inner
        geom = build_geometry_from_points(pts)
        self.assertIsInstance(geom, Polygon)
        self.assertEqual(len(geom.interiors), 1)
        self.assertAlmostEqual(geom.area, 100.0 - 36.0)

if __name__ == '__main__':
    unittest.main()
