# -*- coding: utf-8 -*-
"""
tests.test_sliver
-----------------
Unit tests for Micro-Sliver Polygon Elimination & Common Boundary Dissolving.
"""

import pytest
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, Point
from pyovobj.core.sliver import (
    compute_thinness_ratio,
    get_shared_linear_boundary_length,
    eliminate_sliver_polygons
)

class TestSliver:
    def test_thinness_ratio(self):
        """Tests that thinness ratio correctly distinguishes compact vs elongated shapes."""
        circle = Point(0, 0).buffer(10.0, quad_segs=16)
        t_circle = compute_thinness_ratio(circle)
        assert 1.0 <= t_circle < 1.05

        square = Polygon([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)])
        t_square = compute_thinness_ratio(square)
        assert 1.2 <= t_square <= 1.3

        # Needle sliver: width 0.01, length 10
        needle = Polygon([(0, 0), (10, 0), (10, 0.01), (0, 0.01), (0, 0)])
        t_needle = compute_thinness_ratio(needle)
        assert t_needle > 100.0

    def test_shared_boundary_length(self):
        """Tests measurement of 1D shared linear contact."""
        poly1 = Polygon([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)])
        poly2 = Polygon([(10, 0), (20, 0), (20, 10), (10, 10), (10, 0)])
        
        shared = get_shared_linear_boundary_length(poly1, poly2)
        assert abs(shared - 10.0) < 1e-6

        # Point touch only
        poly3 = Polygon([(10, 10), (20, 10), (20, 20), (10, 20), (10, 10)])
        shared_pt = get_shared_linear_boundary_length(poly1, poly3)
        assert shared_pt == 0.0

    def test_eliminate_sliver_merges_into_longest_neighbor(self):
        """
        Tests that a sliver polygon situated between two unequal neighbors merges
        into the neighbor with the longer shared edge.
        """
        # Neighbor 1: shares edge of length 20
        n1 = Polygon([(0, 0), (20, 0), (20, 10), (0, 10), (0, 0)])
        
        # Sliver: on top of n1, width 20, height 0.05
        # Top half shares edge of length 10 with n2
        sliver = Polygon([(0, 10), (20, 10), (20, 10.05), (0, 10.05), (0, 10)])
        
        # Neighbor 2: on top of sliver, only spanning x from 0 to 10 (shares edge length 10 with sliver)
        n2 = Polygon([(0, 10.05), (10, 10.05), (10, 20), (0, 20), (0, 10.05)])

        gdf = gpd.GeoDataFrame({
            'name': ['N1', 'Sliver', 'N2'],
            'geometry': [n1, sliver, n2]
        })

        clean_gdf, report = eliminate_sliver_polygons(gdf, min_area=2.0)
        assert report['slivers_merged'] == 1
        assert report['final_count'] == 2

        # Sliver should have merged into N1 because shared length with N1 is 20, whereas with N2 it is 10
        n1_new = clean_gdf[clean_gdf['name'] == 'N1'].geometry.iloc[0]
        assert abs(n1_new.area - (n1.area + sliver.area)) < 1e-4

    def test_eliminate_isolated_sliver(self):
        """Tests handling of isolated slivers without neighbors."""
        isolated = Polygon([(0, 0), (10, 0), (10, 0.01), (0, 0.01), (0, 0)])
        gdf = gpd.GeoDataFrame({'name': ['Isolated'], 'geometry': [isolated]})

        # With keep_isolated=False
        clean_gdf, report = eliminate_sliver_polygons(gdf, min_area=1.0, keep_isolated=False)
        assert len(clean_gdf) == 0
        assert report['slivers_dropped'] == 1

        # With keep_isolated=True
        clean_gdf2, report2 = eliminate_sliver_polygons(gdf, min_area=1.0, keep_isolated=True)
        assert len(clean_gdf2) == 1
