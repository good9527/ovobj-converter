# -*- coding: utf-8 -*-
"""
tests.test_grids
----------------
Comprehensive test suite for GB/T 13989-2012 map sheet indexing engine.
"""

import pytest
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

class TestGrids:
    def test_roundtrip_all_scales(self):
        """Tests that forward and reverse calculations match for a known benchmark point."""
        lon, lat = 116.4074, 39.9042  # Benchmark coordinate
        
        for scale in SCALES_CONFIG.keys():
            code = lonlat_to_sheet_code(lon, lat, scale=scale)
            assert isinstance(code, str)
            if scale == '1m':
                assert len(code) == 3
                assert code == 'J50'
            else:
                assert len(code) == 10
                assert code.startswith('J50')
                
            bbox = sheet_code_to_bbox(code)
            assert bbox['lon_min'] <= lon <= bbox['lon_max']
            assert bbox['lat_min'] <= lat <= bbox['lat_max']
            
            poly = sheet_code_to_polygon(code)
            assert poly.is_valid
            assert poly.contains(Point(lon, lat)) or poly.touches(Point(lon, lat))

    def test_intersecting_sheets(self):
        """Tests polygon intersecting multiple map sheet frames."""
        # A polygon spanning across two 1:10k map sheets
        # 1:10k sheet width is 3'45" = 0.0625 deg
        poly = box(116.35, 39.88, 116.45, 39.90)
        sheets = find_intersecting_sheet_codes(poly, scale='10k')
        assert len(sheets) >= 2
        for s in sheets:
            assert 'code' in s
            assert len(s['code']) == 10
            assert s['geometry'].intersects(poly)

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
        assert 'TFH' in out_gdf.columns
        assert len(out_gdf['TFH'].iloc[0]) == 10
        assert len(out_gdf['TFH'].iloc[1]) == 10
        assert out_gdf['TFH'].iloc[0] != out_gdf['TFH'].iloc[1]

    def test_invalid_coordinates(self):
        """Tests exception raising on out-of-range coordinates."""
        with pytest.raises(ValueError):
            lonlat_to_sheet_code(116.0, 95.0, scale='10k')
        with pytest.raises(ValueError):
            sheet_code_to_bbox("INVALID_CODE")
