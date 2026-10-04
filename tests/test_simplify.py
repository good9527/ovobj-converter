# -*- coding: utf-8 -*-
"""
tests.test_simplify
-------------------
Unit tests for topology-preserving geometry simplification.
Verifies that simplification reduces vertex count while preserving valid OGC topology and holes.
"""

import math
import unittest
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, LineString

from pyovobj.core.simplify import simplify_geometry

class TestSimplify(unittest.TestCase):

    def test_simplify_linestring(self):
        # Dense sine wave line with 100 points
        x = np.linspace(0, 10, 100)
        y = np.sin(x) * 0.001
        line = LineString(list(zip(x, y)))

        self.assertEqual(len(line.coords), 100)
        simplified = simplify_geometry(line, tolerance=0.0005)
        self.assertLess(len(simplified.coords), 50)
        self.assertGreaterEqual(len(simplified.coords), 2)

    def test_simplify_polygon_with_hole(self):
        # Outer ring circular with 100 points, Hole circular with 50 points
        theta_ext = np.linspace(0, 2 * np.pi, 101)
        ext = list(zip(10 * np.cos(theta_ext), 10 * np.sin(theta_ext)))
        ext[-1] = ext[0]

        theta_hole = np.linspace(0, 2 * np.pi, 51)
        hole = list(zip(4 * np.cos(theta_hole), 4 * np.sin(theta_hole)))
        hole[-1] = hole[0]

        poly = Polygon(ext, [hole])
        self.assertEqual(len(poly.exterior.coords), 101)
        self.assertEqual(len(poly.interiors[0].coords), 51)

        # Simplify with tolerance 0.1
        simp = simplify_geometry(poly, tolerance=0.1)
        self.assertIsInstance(simp, Polygon)
        self.assertTrue(simp.is_valid)
        self.assertLess(len(simp.exterior.coords), 40)
        self.assertLess(len(simp.interiors[0].coords), 30)
        self.assertEqual(len(simp.interiors), 1)

    def test_simplify_preserves_validity(self):
        # Triangle (minimum 4 points)
        poly = Polygon([(0, 0), (10, 0), (5, 10), (0, 0)])
        simp = simplify_geometry(poly, tolerance=100.0)  # Aggressive tolerance
        self.assertTrue(simp.is_valid)
        self.assertEqual(len(simp.exterior.coords), 4)

if __name__ == '__main__':
    unittest.main()
