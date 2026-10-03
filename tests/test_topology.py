# -*- coding: utf-8 -*-
"""
tests.test_topology
-------------------
Unit tests for Topological Containment Forest Algorithm and geometry reconstruction.
Verifies zero hole loss across complex nested MultiPolygons and islands.
"""

import unittest
from shapely.geometry import Point, LineString, Polygon, MultiPolygon
from pyovobj.core.topology import build_geometry_from_points, build_containment_hierarchy

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

    def test_multipolygon_hole_preservation(self):
        """
        Critical test: MultiPolygon where Polygon 1 has a hole and Polygon 2 does not.
        Previously, len(outlines) > 1 discarded holes entirely.
        With Containment Forest, holes must be strictly preserved!
        """
        outer1 = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
        hole1  = [(2, 2), (8, 2), (8, 8), (2, 8), (2, 2)]
        outer2 = [(20, 0), (30, 0), (30, 10), (20, 10), (20, 0)]
        pts = outer1 + hole1 + outer2

        geom = build_geometry_from_points(pts)
        self.assertIsInstance(geom, MultiPolygon)
        self.assertEqual(len(geom.geoms), 2)

        # One part has 1 hole (area 64), the other has 0 holes (area 100)
        areas = sorted([p.area for p in geom.geoms])
        self.assertAlmostEqual(areas[0], 64.0)
        self.assertAlmostEqual(areas[1], 100.0)

        holes_count = sum(len(p.interiors) for p in geom.geoms)
        self.assertEqual(holes_count, 1)

    def test_multipolygon_multiple_independent_holes(self):
        """
        MultiPolygon where both polygons have independent holes.
        """
        outer1 = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
        hole1  = [(2, 2), (8, 2), (8, 8), (2, 8), (2, 2)]

        outer2 = [(20, 0), (40, 0), (40, 20), (20, 20), (20, 0)]
        hole2a = [(22, 2), (28, 2), (28, 8), (22, 8), (22, 2)]
        hole2b = [(32, 2), (38, 2), (38, 8), (32, 8), (32, 2)]

        pts = outer1 + hole1 + outer2 + hole2a + hole2b
        geom = build_geometry_from_points(pts)
        self.assertIsInstance(geom, MultiPolygon)
        self.assertEqual(len(geom.geoms), 2)

        total_holes = sum(len(p.interiors) for p in geom.geoms)
        self.assertEqual(total_holes, 3)

        expected_area = (100.0 - 36.0) + (400.0 - 36.0 - 36.0)
        self.assertAlmostEqual(geom.area, expected_area)

    def test_nested_donut_with_island(self):
        """
        Donut with island inside hole (Depth 0, 1, 2, 3).
        - Ring 0 (Depth 0): Outer 0..20 (area 400)
        - Ring 1 (Depth 1): Hole 4..16 (area 144)
        - Ring 2 (Depth 2): Island 6..14 (area 64)
        - Ring 3 (Depth 3): Hole inside Island 8..12 (area 16)
        """
        outer = [(0, 0), (20, 0), (20, 20), (0, 20), (0, 0)]
        hole  = [(4, 4), (16, 4), (16, 16), (4, 16), (4, 4)]
        island = [(6, 6), (14, 6), (14, 14), (6, 14), (6, 6)]
        island_hole = [(8, 8), (12, 8), (12, 12), (8, 12), (8, 8)]

        pts = outer + hole + island + island_hole
        geom = build_geometry_from_points(pts)
        self.assertIsInstance(geom, MultiPolygon)
        self.assertEqual(len(geom.geoms), 2)

        # Expected total area: (400 - 144) + (64 - 16) = 256 + 48 = 304.0
        self.assertAlmostEqual(geom.area, 304.0)

    def test_unclosed_polygon_stream_healing(self):
        """
        Unclosed coordinate stream for block type 31 (polygon).
        """
        pts = [(0, 0), (5, 0), (5, 5), (0, 5)]  # missing closing (0, 0)
        geom = build_geometry_from_points(pts, btype=31)
        self.assertIsInstance(geom, Polygon)
        self.assertTrue(geom.is_valid)
        self.assertAlmostEqual(geom.area, 25.0)

if __name__ == '__main__':
    unittest.main()
