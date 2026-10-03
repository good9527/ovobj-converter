# -*- coding: utf-8 -*-
"""
tests.test_repair
-----------------
Unit tests for geometric self-healing, bow-tie repair, collinear spike removal,
and topological health auditing.
"""

import unittest
from shapely.geometry import Polygon, MultiPolygon, LineString
from pyovobj.core.repair import (
    heal_geometry,
    audit_geometry_health,
    remove_duplicate_consecutive_points,
    remove_collinear_spikes
)

class TestRepair(unittest.TestCase):

    def test_duplicate_consecutive_points(self):
        pts = [(1.0, 1.0), (1.0, 1.0), (2.0, 2.0), (2.0, 2.0), (3.0, 3.0)]
        cleaned = remove_duplicate_consecutive_points(pts)
        self.assertEqual(len(cleaned), 3)
        self.assertEqual(cleaned, [(1.0, 1.0), (2.0, 2.0), (3.0, 3.0)])

    def test_collinear_spikes(self):
        # A line with a 180-degree needle return spike at (2, 2)
        pts = [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0), (1.0, 1.0), (3.0, 3.0)]
        cleaned = remove_collinear_spikes(pts)
        self.assertLess(len(cleaned), len(pts))

    def test_bowtie_self_intersection_repair(self):
        # Self-intersecting figure-8 bow-tie polygon
        bowtie = Polygon([(0, 0), (2, 2), (2, 0), (0, 2), (0, 0)])
        self.assertFalse(bowtie.is_valid)

        healed = heal_geometry(bowtie)
        self.assertTrue(healed.is_valid)
        self.assertIn(healed.geom_type, ['Polygon', 'MultiPolygon'])
        self.assertAlmostEqual(healed.area, 2.0)

    def test_ogc_orientation_enforcement(self):
        # Clockwise polygon (inverted)
        cw_poly = Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
        self.assertFalse(cw_poly.exterior.is_ccw)

        healed = heal_geometry(cw_poly)
        self.assertTrue(healed.exterior.is_ccw)

    def test_audit_health(self):
        valid_poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
        rep_valid = audit_geometry_health(valid_poly)
        self.assertEqual(rep_valid['status'], 'HEALTHY')
        self.assertTrue(rep_valid['is_valid'])

        invalid_poly = Polygon([(0, 0), (2, 2), (2, 0), (0, 2), (0, 0)])
        rep_invalid = audit_geometry_health(invalid_poly)
        self.assertEqual(rep_invalid['status'], 'DEFECTIVE')
        self.assertFalse(rep_invalid['is_valid'])

if __name__ == '__main__':
    unittest.main()
