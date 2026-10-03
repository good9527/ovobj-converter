# -*- coding: utf-8 -*-
"""
pyovobj.core.packer
-------------------
Reverse packer encoding standard GeoDataFrames (Points, Lines, Polygons, MultiPolygons)
into native Ovital (.ovobj) binary files.
"""

import os
import zlib
import json
import struct
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon, MultiPolygon

def encode_coordinate_delta(dy_raw: int, dx_raw: int) -> bytes:
    """
    Encodes an integer coordinate delta (dy, dx in 1e-8 degrees) into Ovital variable-length bitstream.
    """
    if dy_raw == 0 and dx_raw == 0:
        return bytes([0x00])

    sign_y = 0x80 if dy_raw < 0 else 0
    sign_x = 0x40 if dx_raw < 0 else 0
    dy = abs(dy_raw)
    dx = abs(dx_raw)
    v1 = dy * 2  # Ovital multiplies dy by 2
    v2 = dx

    # K=1 (1 payload byte)
    if v1 <= 63 and v2 <= 15:
        carry = v1 >> 4
        b0 = ((v1 & 0x0F) << 4) | (v2 & 0x0F)
        w = 4 * 1 + carry
        return bytes([sign_y | sign_x | w, b0])

    # K=2 (2 payload bytes)
    elif v1 <= 1023 and v2 <= 255:
        carry = v1 >> 8
        b0 = v1 & 0xFF
        b1 = v2 & 0xFF
        w = 4 * 2 + carry
        return bytes([sign_y | sign_x | w, b0, b1])

    # K=3 (3 payload bytes)
    elif v1 <= 16383 and v2 <= 4095:
        carry = v1 >> 12
        b0 = (v1 >> 4) & 0xFF
        b1 = ((v1 & 0x0F) << 4) | ((v2 >> 8) & 0x0F)
        b2 = v2 & 0xFF
        w = 4 * 3 + carry
        return bytes([sign_y | sign_x | w, b0, b1, b2])

    # K=4 (4 payload bytes)
    elif v1 <= 262143 and v2 <= 65535:
        carry = v1 >> 16
        b0 = (v1 >> 8) & 0xFF
        b1 = v1 & 0xFF
        b2 = (v2 >> 8) & 0xFF
        b3 = v2 & 0xFF
        w = 4 * 4 + carry
        return bytes([sign_y | sign_x | w, b0, b1, b2, b3])

    # K=5 (5 payload bytes)
    elif v1 <= 4194303 and v2 <= 1048575:
        carry = v1 >> 20
        b0 = (v1 >> 12) & 0xFF
        b1 = (v1 >> 4) & 0xFF
        b2 = ((v1 & 0x0F) << 4) | ((v2 >> 16) & 0x0F)
        b3 = (v2 >> 8) & 0xFF
        b4 = v2 & 0xFF
        w = 4 * 5 + carry
        return bytes([sign_y | sign_x | w, b0, b1, b2, b3, b4])

    # K=6 (6 payload bytes)
    else:
        carry = v1 >> 24
        b0 = (v1 >> 16) & 0xFF
        b1 = (v1 >> 8) & 0xFF
        b2 = v1 & 0xFF
        b3 = (v2 >> 16) & 0xFF
        b4 = (v2 >> 8) & 0xFF
        b5 = v2 & 0xFF
        w = 4 * 6 + carry
        return bytes([sign_y | sign_x | w, b0, b1, b2, b3, b4, b5])


def write_ovobj(gdf: gpd.GeoDataFrame, output_path: str) -> str:
    """
    Serializes a GeoPandas GeoDataFrame into a native Ovital (.ovobj) binary file.

    :param gdf: Source GeoDataFrame.
    :param output_path: Destination .ovobj file path.
    :return: Output file path.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    df_wgs = gdf.copy()
    if df_wgs.crs != "EPSG:4326":
        df_wgs = df_wgs.to_crs("EPSG:4326")

    decomp_body = bytearray()

    for idx, row in df_wgs.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue

        # Extract attributes
        attrs = {}
        for col in row.index:
            if col == 'geometry':
                continue
            val = row[col]
            if val is not None and str(val) != 'nan':
                attrs[str(col)] = val

        attr_json = json.dumps(attrs, ensure_ascii=False).encode('utf-8')

        # Determine block type and coordinate sequence
        if isinstance(geom, Point):
            btype = 1
            pts = [(geom.x, geom.y)]
        elif isinstance(geom, LineString):
            btype = 32
            pts = list(geom.coords)
        elif isinstance(geom, Polygon):
            btype = 31
            pts = list(geom.exterior.coords)
            for interior in geom.interiors:
                pts.extend(list(interior.coords))
        elif isinstance(geom, MultiPolygon):
            btype = 31
            pts = []
            for poly in geom.geoms:
                pts.extend(list(poly.exterior.coords))
                for interior in poly.interiors:
                    pts.extend(list(interior.coords))
        else:
            continue

        npts = len(pts)
        lat0_int = int(round(pts[0][1] * 1e8))
        lon0_int = int(round(pts[0][0] * 1e8))

        # Encode coordinate stream
        stream = bytearray()
        cur_lat = lat0_int
        cur_lon = lon0_int
        for p in pts[1:]:
            target_lat = int(round(p[1] * 1e8))
            target_lon = int(round(p[0] * 1e8))
            dy = target_lat - cur_lat
            dx = target_lon - cur_lon
            cur_lat = target_lat
            cur_lon = target_lon
            stream.extend(encode_coordinate_delta(dy, dx))

        # Format block: [attr XML/JSON envelope] + [coord header] + [coordinate delta stream]
        envelope = b'<?ovital_ct name="ovital_shp">' + attr_json + b'</?ovital_ct>\x00\x00\x00\x00'
        coord_hdr = struct.pack('<IIqq', npts, 0, lat0_int, lon0_int)
        payload = envelope + coord_hdr + bytes(stream)

        block = struct.pack('<II', len(payload), btype) + payload
        decomp_body.extend(block)

    # Standard Ovital container encapsulation: 24B header + Zlib payload + 16B trailer
    header = b'\x00' * 24
    compressed = zlib.compress(bytes(decomp_body))
    trailer = b'\x00' * 16

    with open(output_path, 'wb') as f:
        f.write(header + compressed + trailer)

    return output_path
