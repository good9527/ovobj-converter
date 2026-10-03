# -*- coding: utf-8 -*-
"""
pyovobj.core.reader
-------------------
High-level Ovital .ovobj file reader producing standard GeoDataFrames.
"""

import os
import struct
import geopandas as gpd
from typing import Optional

from .decompressor import decompress_ovobj
from .decoder import decode_coordinate_stream
from .topology import build_geometry_from_points
from .attributes import extract_attributes
from .coords import gcj02_to_wgs84

class OvobjReader:
    """
    Main reader class for reading and decoding Ovital (.ovobj) binary files.
    """

    def __init__(self, file_path: str, apply_gcj02_fix: bool = False):
        self.file_path = file_path
        self.apply_gcj02_fix = apply_gcj02_fix

    def read(self) -> gpd.GeoDataFrame:
        """
        Reads the .ovobj file and returns a GeoPandas GeoDataFrame with WGS84 CRS (EPSG:4326).
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Source file not found: {self.file_path}")

        with open(self.file_path, 'rb') as f:
            raw = f.read()

        decomp = decompress_ovobj(raw)

        # Split into blocks: [4B blen][4B btype][payload]
        cur = 0
        blocks = []
        while cur < len(decomp):
            if cur + 8 > len(decomp):
                break
            blen, btype = struct.unpack('<II', decomp[cur : cur + 8])
            blocks.append((btype, decomp[cur : cur + 8 + blen]))
            cur += 8 + blen

        records = []
        for blk_idx, (btype, blk) in enumerate(blocks):
            # Locate coordinate header: [uint32 npts][uint32 pad=0][int64 lat0][int64 lon0]
            coord_hdr = None
            for offset in range(8, len(blk) - 24):
                npts_t, pad_t, lat0_t, lon0_t = struct.unpack('<IIqq', blk[offset : offset + 24])
                if pad_t == 0 and 1e9 < lat0_t < 6e9 and 3e9 < lon0_t < 1.5e10 and 1 <= npts_t <= 500000:
                    coord_hdr = (offset, npts_t, lat0_t, lon0_t)
                    break

            if not coord_hdr:
                continue

            offset, npts_total, lat0_int, lon0_int = coord_hdr

            # Extract attributes
            attrs = extract_attributes(blk, offset)

            # Reconstruct initial point
            lon0 = lon0_int / 1e8
            lat0 = lat0_int / 1e8
            if self.apply_gcj02_fix:
                lon0, lat0 = gcj02_to_wgs84(lon0, lat0)

            # Case A: Single point
            if npts_total == 1:
                geom = build_geometry_from_points([(lon0, lat0)], btype)
                attrs['geometry'] = geom
                records.append(attrs)
                continue

            # Case B: Multi-point geometry (LineString, Polygon, MultiPolygon)
            stream = blk[offset + 24 :]
            deltas, _ = decode_coordinate_stream(stream, npts_total)
            if len(deltas) != npts_total - 1:
                continue

            pts = [(lon0, lat0)]
            c_lat_int = lat0_int
            c_lon_int = lon0_int
            for dy, dx in deltas:
                c_lat_int += dy
                c_lon_int += dx
                pt_lon = c_lon_int / 1e8
                pt_lat = c_lat_int / 1e8
                if self.apply_gcj02_fix:
                    pt_lon, pt_lat = gcj02_to_wgs84(pt_lon, pt_lat)
                pts.append((pt_lon, pt_lat))

            geom = build_geometry_from_points(pts, btype)
            attrs['geometry'] = geom
            records.append(attrs)

        if not records:
            return gpd.GeoDataFrame(columns=['geometry'], crs="EPSG:4326")

        gdf = gpd.GeoDataFrame(records, crs="EPSG:4326")
        return gdf

def read_ovobj(file_path: str, apply_gcj02_fix: bool = False) -> gpd.GeoDataFrame:
    """
    Convenience function to parse an .ovobj file into a GeoDataFrame.

    :param file_path: Path to the .ovobj file.
    :param apply_gcj02_fix: If True, reverses GCJ-02 Mars distortion back to WGS-84.
    :return: GeoDataFrame in EPSG:4326.
    """
    reader = OvobjReader(file_path, apply_gcj02_fix=apply_gcj02_fix)
    return reader.read()
