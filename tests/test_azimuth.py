# -*- coding: utf-8 -*-
"""
tests.test_azimuth
------------------
Unit tests for Cadastral Boundary Surveying, Geodesic Bearings, and Turning Angles Engine.
"""

import pytest
import pandas as pd
from shapely.geometry import Polygon
from pyovobj.core.azimuth import (
    deg_to_dms,
    vincenty_azimuth,
    order_vertices_cadastral,
    analyze_polygon_boundary_points,
    extract_cadastral_demarcation_table
)

class TestAzimuth:
    def test_deg_to_dms(self):
        """Tests decimal degree formatting to DMS string."""
        s = deg_to_dms(89.68532)
        assert s.startswith("089\u00b041'")
        assert s.endswith('"')

    def test_cardinal_azimuths(self):
        """Tests that cardinal direction vectors return precise azimuths."""
        # Due North
        fwd_n, back_n, dist_n = vincenty_azimuth(116.0, 39.0, 116.0, 40.0)
        assert abs(fwd_n - 0.0) < 1e-4 or abs(fwd_n - 360.0) < 1e-4
        assert abs(back_n - 180.0) < 1e-4
        assert dist_n > 110000.0  # ~111 km

        # Due South
        fwd_s, back_s, dist_s = vincenty_azimuth(116.0, 40.0, 116.0, 39.0)
        assert abs(fwd_s - 180.0) < 1e-4
        assert abs(back_s - 0.0) < 1e-4 or abs(back_s - 360.0) < 1e-4

    def test_order_vertices_cadastral(self):
        """Tests northwest point selection and clockwise ordering."""
        # Counter-clockwise square
        ccw_coords = [(116.0, 39.0), (116.1, 39.0), (116.1, 39.1), (116.0, 39.1), (116.0, 39.0)]
        ordered = order_vertices_cadastral(ccw_coords)
        assert len(ordered) == 4
        # J1 must be northwest: (116.0, 39.1)
        assert ordered[0] == (116.0, 39.1)
        # Clockwise sequence: (116.0, 39.1) -> (116.1, 39.1) -> (116.1, 39.0) -> (116.0, 39.0)
        assert ordered[1] == (116.1, 39.1)
        assert ordered[2] == (116.1, 39.0)
        assert ordered[3] == (116.0, 39.0)

    def test_cadastral_demarcation_table(self):
        """Tests generation of complete surveyor boundary table."""
        poly = Polygon([(116.0, 39.0), (116.1, 39.0), (116.1, 39.1), (116.0, 39.1), (116.0, 39.0)])
        df = extract_cadastral_demarcation_table(poly)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 4
        assert list(df['point_id']) == ['J1', 'J2', 'J3', 'J4']
        assert list(df['next_point_id']) == ['J2', 'J3', 'J4', 'J1']
        assert 'proj_x_northing' in df.columns
        assert 'proj_y_easting' in df.columns
        assert 'azimuth_dms' in df.columns
        assert 'interior_angle_deg' in df.columns

        # Verify sum of interior angles for a quadrilateral = 360 degrees
        sum_interior = df['interior_angle_deg'].sum()
        assert abs(sum_interior - 360.0) < 1.0  # Sub-degree spherical/ellipsoidal excess
