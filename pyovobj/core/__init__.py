# -*- coding: utf-8 -*-
"""
pyovobj.core
------------
Core binary decoding, decompression, topology construction, coordinate transformation,
geodesic ellipsoidal integration, geometric self-healing, projection engine, and simplification.
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
    "extract_attributes",
    "OvobjReader",
    "read_ovobj",
    "write_ovobj",
]
