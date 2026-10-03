# -*- coding: utf-8 -*-
"""
pyovobj.core
------------
Core binary decoding, decompression, topology construction, and coordinate transformation.
"""

from .coords import gcj02_to_wgs84
from .decompressor import decompress_ovobj
from .decoder import decode_coordinate_stream
from .topology import build_geometry_from_points
from .attributes import extract_attributes
from .reader import OvobjReader, read_ovobj
from .packer import write_ovobj, encode_coordinate_delta

__all__ = [
    "gcj02_to_wgs84",
    "decompress_ovobj",
    "decode_coordinate_stream",
    "encode_coordinate_delta",
    "build_geometry_from_points",
    "extract_attributes",
    "OvobjReader",
    "read_ovobj",
    "write_ovobj",
]
