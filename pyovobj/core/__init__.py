# -*- coding: utf-8 -*-
"""
pyovobj.core
------------
Core binary decoding, decompression, topology construction, coordinate transformation,
geodesic ellipsoidal integration, geometric self-healing, projection engine, simplification,
national standard map sheet indexing, sliver polygon elimination, cadastral demarcation,
and Helmert coordinate transformation.
"""

from .coords import gcj02_to_wgs84
from .decompressor import decompress_ovobj
from .decoder import decode_coordinate_stream
from .topology import build_geometry_from_points, build_containment_hierarchy
from .repair import heal_geometry, audit_geometry_health, remove_duplicate_consecutive_points, remove_collinear_spikes
from .geodesy import (
    GeodeticCalculator,
    compute_ellipsoidal_area,
    compute_area_mu,
    compute_geodesic_length,
    attach_geodesic_metrics,
    ELLIPSOIDS
)
from .projection import (
    forward_gauss_kruger,
    inverse_gauss_kruger,
    get_central_meridian_3deg,
    project_coords,
    project_geometry
)
from .simplify import simplify_geometry
from .grids import (
    lonlat_to_sheet_code,
    sheet_code_to_bbox,
    sheet_code_to_polygon,
    find_intersecting_sheet_codes,
    attach_map_sheet_codes,
    SCALES_CONFIG
)
from .sliver import (
    compute_thinness_ratio,
    get_shared_linear_boundary_length,
    eliminate_sliver_polygons
)
from .azimuth import (
    deg_to_dms,
    vincenty_azimuth,
    order_vertices_cadastral,
    analyze_polygon_boundary_points,
    extract_cadastral_demarcation_table
)
from .transform import Helmert2DTransform
from .attributes import extract_attributes
from .reader import OvobjReader, read_ovobj
from .packer import write_ovobj, encode_coordinate_delta

__all__ = [
    "gcj02_to_wgs84",
    "decompress_ovobj",
    "decode_coordinate_stream",
    "encode_coordinate_delta",
    "build_geometry_from_points",
    "build_containment_hierarchy",
    "heal_geometry",
    "audit_geometry_health",
    "remove_duplicate_consecutive_points",
    "remove_collinear_spikes",
    "GeodeticCalculator",
    "compute_ellipsoidal_area",
    "compute_area_mu",
    "compute_geodesic_length",
    "attach_geodesic_metrics",
    "ELLIPSOIDS",
    "forward_gauss_kruger",
    "inverse_gauss_kruger",
    "get_central_meridian_3deg",
    "project_coords",
    "project_geometry",
    "simplify_geometry",
    "lonlat_to_sheet_code",
    "sheet_code_to_bbox",
    "sheet_code_to_polygon",
    "find_intersecting_sheet_codes",
    "attach_map_sheet_codes",
    "SCALES_CONFIG",
    "compute_thinness_ratio",
    "get_shared_linear_boundary_length",
    "eliminate_sliver_polygons",
    "deg_to_dms",
    "vincenty_azimuth",
    "order_vertices_cadastral",
    "analyze_polygon_boundary_points",
    "extract_cadastral_demarcation_table",
    "Helmert2DTransform",
    "extract_attributes",
    "OvobjReader",
    "read_ovobj",
    "write_ovobj",
]
