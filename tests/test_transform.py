# -*- coding: utf-8 -*-
"""
tests.test_transform
--------------------
Unit tests for 2D 4-Parameter Helmert Similarity Transformation Engine.
"""

import unittest
import numpy as np
from shapely.geometry import Point, LineString, Polygon
import geopandas as gpd
from pyovobj.core.transform import Helmert2DTransform

class TestTransform(unittest.TestCase):
    def test_fit_and_invertibility(self):
        """Tests least-squares parameter recovery and exact inverse roundtrip."""
        dx_true = 500.0
        dy_true = 1200.0
        scale_true = 1.00025
        rot_deg_true = 45.0
        rot_rad_true = np.radians(rot_deg_true)

        a_true = scale_true * np.cos(rot_rad_true)
        b_true = scale_true * np.sin(rot_rad_true)

        src_pts = np.array([
            [10.0, 20.0],
            [100.0, 50.0],
            [150.0, 200.0],
            [30.0, 180.0]
        ])

        dst_pts = np.zeros_like(src_pts)
        for i in range(len(src_pts)):
            x, y = src_pts[i]
            dst_pts[i, 0] = dx_true + a_true * x - b_true * y
            dst_pts[i, 1] = dy_true + b_true * x + a_true * y

        # Fit model
        model = Helmert2DTransform.fit(src_pts, dst_pts)
        
        self.assertAlmostEqual(model.dx, dx_true, places=3)
        self.assertAlmostEqual(model.dy, dy_true, places=3)
        self.assertAlmostEqual(model.scale_k, scale_true, places=5)
        self.assertAlmostEqual(model.rotation_deg, rot_deg_true, places=4)
        self.assertLess(model.rmse, 1e-7)

        # Test forward transform
        transformed = model.transform_coords(src_pts)
        np.testing.assert_allclose(transformed, dst_pts, atol=1e-5)

        # Test inverse transform
        inverted = model.inverse_coords(dst_pts)
        np.testing.assert_allclose(inverted, src_pts, atol=1e-5)

    def test_geometry_transform(self):
        """Tests transforming Shapely geometries forward and backward."""
        model = Helmert2DTransform(dx=100.0, dy=200.0, scale_k=2.0, rotation_deg=90.0)
        
        pt = Point(10.0, 0.0)
        transformed_pt = model.transform_geometry(pt)
        self.assertAlmostEqual(transformed_pt.x, 100.0, places=5)
        self.assertAlmostEqual(transformed_pt.y, 220.0, places=5)

        # Invert
        inverted_pt = model.inverse_geometry(transformed_pt)
        self.assertAlmostEqual(inverted_pt.x, pt.x, places=5)
        self.assertAlmostEqual(inverted_pt.y, pt.y, places=5)

    def test_geodataframe_transform(self):
        """Tests transforming an entire GeoDataFrame."""
        poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)])
        gdf = gpd.GeoDataFrame({'id': [1]}, geometry=[poly])

        model = Helmert2DTransform(dx=50.0, dy=50.0, scale_k=1.5, rotation_deg=0.0)
        out_gdf = model.transform_geodataframe(gdf)

        # Area should scale by scale_k^2 = 1.5^2 = 2.25
        self.assertAlmostEqual(out_gdf.geometry.iloc[0].area, poly.area * 2.25, places=5)

if __name__ == '__main__':
    unittest.main()
