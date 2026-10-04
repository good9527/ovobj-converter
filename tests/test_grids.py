# -*- coding: utf-8 -*-
"""
tests.test_grids
----------------
Comprehensive test suite for GB/T 13989-2012 map sheet indexing engine.
"""

import unittest
import geopandas as gpd
from shapely.geometry import Point, Polygon, box
from pyovobj.core.grids import (
    lonlat_to_sheet_code,
    sheet_code_to_bbox,
    sheet_code_to_polygon,
    find_intersecting_sheet_codes,
    attach_map_sheet_codes,
    SCALES_CONFIG
)

class TestGrids(unittest.TestCase):
    def test_roundtrip_all_scales(self):
        """Tests that forward and reverse calculations match for a known benchmark point."""
        lon, lat = 116.4074, 39.9042  # Benchmark coordinate
        
        for scale in SCALES_CONFIG.keys():
            code = lonlat_to_sheet_code(lon, lat, scale=scale)
            self.assertIsInstance(code, str)
            if scale == '1m':
                self.assertEqual(len(code), 3)
                self.assertEqual(code, 'J50')
            else:
                self.assertEqual(len(code), 10)
                self.assertTrue(code.startswith('J50'))
                
            bbox = sheet_code_to_bbox(code)
            self.assertTrue(bbox['lon_min'] <= lon <= bbox['lon_max'])
            self.assertTrue(bbox['lat_min'] <= lat <= bbox['lat_max'])
            
            poly = sheet_code_to_polygon(code)
            self.assertTrue(poly.is_valid)
            self.assertTrue(poly.contains(Point(lon, lat)) or poly.touches(Point(lon, lat)))

    def test_intersecting_sheets(self):
        """Tests polygon intersecting multiple map sheet frames."""
        poly = box(116.35, 39.88, 116.45, 39.90)
        sheets = find_intersecting_sheet_codes(poly, scale='10k')
        self.assertGreaterEqual(len(sheets), 2)
        for s in sheets:
            self.assertIn('code', s)
            self.assertEqual(len(s['code']), 10)
            self.assertTrue(s['geometry'].intersects(poly))

    def test_attach_map_sheet_codes(self):
        """Tests attaching map sheet codes to GeoDataFrame features."""
        gdf = gpd.GeoDataFrame({
            'name': ['Parcel_1', 'Parcel_2'],
            'geometry': [
                Point(116.40, 39.90).buffer(0.001),
                Point(117.10, 40.20).buffer(0.001)
            ]
        }, crs="EPSG:4490")
        
        out_gdf = attach_map_sheet_codes(gdf, scale='10k', col_name='TFH')
        self.assertIn('TFH', out_gdf.columns)
        self.assertEqual(len(out_gdf['TFH'].iloc[0]), 10)
        self.assertEqual(len(out_gdf['TFH'].iloc[1]), 10)
        self.assertNotEqual(out_gdf['TFH'].iloc[0], out_gdf['TFH'].iloc[1])

    def test_invalid_coordinates(self):
        """Tests exception raising on out-of-range coordinates."""
        with self.assertRaises(ValueError):
            lonlat_to_sheet_code(116.0, 95.0, scale='10k')
        with self.assertRaises(ValueError):
            sheet_code_to_bbox("INVALID_CODE")

if __name__ == '__main__':
    unittest.main()
