# -*- coding: utf-8 -*-
"""
tests.test_packer
-----------------
Unit tests for reverse packing GeoDataFrames to .ovobj binary files
and full dynamic variable-length coordinate delta encoding across K=1..8.
"""

import os
import unittest
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
from pyovobj.core.packer import write_ovobj, encode_coordinate_delta
from pyovobj.core.decoder import decode_coordinate_stream
from pyovobj.core.reader import read_ovobj

class TestPacker(unittest.TestCase):

    def test_encode_coordinate_delta_dynamic_range(self):
        """
        Verify bidirectional lossless compression across small, medium, large,
        and regional jump deltas (K=1 to K=8).
        """
        test_pairs = [
            (0, 0),
            (10, 5),
            (-25, 12),
            (500, -200),
            (-15000, 3000),
            (100000, -50000),
            (-3000000, 800000),
            (50000000, -10000000),
            (-500000000, 200000000),
            (1500000000, -1000000000)
        ]

        for dy, dx in test_pairs:
            encoded = encode_coordinate_delta(dy, dx)
            decoded, consumed = decode_coordinate_stream(encoded, 2)
            self.assertEqual(len(decoded), 1)
            dec_dy, dec_dx = decoded[0]
            self.assertEqual(dec_dy, dy, f"Failed for dy={dy}")
            self.assertEqual(dec_dx, dx, f"Failed for dx={dx}")
            self.assertEqual(consumed, len(encoded))

    def test_roundtrip_pack_and_read(self):
        p1 = Polygon([(77.2, 39.1), (77.3, 39.1), (77.3, 39.2), (77.2, 39.2), (77.2, 39.1)])
        p2 = Point(77.5, 39.5)
        l1 = LineString([(77.6, 39.6), (77.7, 39.7), (77.8, 39.8)])

        gdf = gpd.GeoDataFrame([
            {'NAME': 'Test_Polygon', 'CLASS': 'Plot', 'geometry': p1},
            {'NAME': 'Test_Point', 'CLASS': 'Marker', 'geometry': p2},
            {'NAME': 'Test_Line', 'CLASS': 'Path', 'geometry': l1}
        ], crs='EPSG:4326')

        out_path = 'temp_test_roundtrip.ovobj'
        try:
            write_ovobj(gdf, out_path)
            self.assertTrue(os.path.exists(out_path))
            self.assertGreater(os.path.getsize(out_path), 50)

            read_back = read_ovobj(out_path)
            self.assertEqual(len(read_back), 3)

            # Check Polygon
            row_poly = read_back[read_back['NAME'] == 'Test_Polygon'].iloc[0]
            self.assertEqual(row_poly.geometry.geom_type, 'Polygon')
            self.assertAlmostEqual(row_poly.geometry.area, p1.area, places=6)

            # Check Point
            row_pt = read_back[read_back['NAME'] == 'Test_Point'].iloc[0]
            self.assertEqual(row_pt.geometry.geom_type, 'Point')
            self.assertAlmostEqual(row_pt.geometry.x, p2.x, places=6)
            self.assertAlmostEqual(row_pt.geometry.y, p2.y, places=6)

            # Check Line
            row_line = read_back[read_back['NAME'] == 'Test_Line'].iloc[0]
            self.assertEqual(row_line.geometry.geom_type, 'LineString')
            self.assertEqual(len(row_line.geometry.coords), 3)

        finally:
            if os.path.exists(out_path):
                os.remove(out_path)

if __name__ == '__main__':
    unittest.main()
