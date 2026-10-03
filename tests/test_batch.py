# -*- coding: utf-8 -*-
"""
tests.test_batch
----------------
Unit tests for parallel batch conversion.
"""

import os
import shutil
import unittest
import geopandas as gpd
from shapely.geometry import Polygon
from pyovobj.core.packer import write_ovobj
from pyovobj.batch import batch_convert_parallel

class TestBatch(unittest.TestCase):

    def setUp(self):
        self.in_dir = "temp_test_batch_in"
        self.out_dir = "temp_test_batch_out"
        os.makedirs(self.in_dir, exist_ok=True)
        os.makedirs(self.out_dir, exist_ok=True)

        p1 = Polygon([(77.1, 39.1), (77.2, 39.1), (77.2, 39.2), (77.1, 39.1)])
        p2 = Polygon([(77.3, 39.3), (77.4, 39.3), (77.4, 39.4), (77.3, 39.3)])
        self.f1 = os.path.join(self.in_dir, "test1.ovobj")
        self.f2 = os.path.join(self.in_dir, "test2.ovobj")
        write_ovobj(gpd.GeoDataFrame([{'NAME': 'A', 'geometry': p1}], crs='EPSG:4326'), self.f1)
        write_ovobj(gpd.GeoDataFrame([{'NAME': 'B', 'geometry': p2}], crs='EPSG:4326'), self.f2)

    def tearDown(self):
        if os.path.exists(self.in_dir):
            shutil.rmtree(self.in_dir)
        if os.path.exists(self.out_dir):
            shutil.rmtree(self.out_dir)

    def test_parallel_batch_convert(self):
        summary = batch_convert_parallel(
            input_paths=[self.f1, self.f2],
            output_dir=self.out_dir,
            formats=['geojson'],
            max_workers=2
        )
        self.assertEqual(summary['total_files'], 2)
        self.assertEqual(summary['success_count'], 2)
        self.assertEqual(summary['total_features'], 2)
        self.assertTrue(os.path.exists(os.path.join(self.out_dir, "test1.geojson")))
        self.assertTrue(os.path.exists(os.path.join(self.out_dir, "test2.geojson")))

if __name__ == '__main__':
    unittest.main()
