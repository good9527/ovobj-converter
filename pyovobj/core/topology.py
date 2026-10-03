# -*- coding: utf-8 -*-
"""
pyovobj.core.topology
---------------------
Topology construction for Points, LineStrings, Polygons, and MultiPolygons
with automatic ring closure, hole detection, and geometric validation.
"""

from typing import Union
from shapely.geometry import Point, LineString, Polygon, MultiPolygon
from shapely.validation import make_valid

def build_geometry_from_points(pts: list[tuple[float, float]], btype: int = 0) -> Union[Point, LineString, Polygon, MultiPolygon]:
    """
    Constructs an OGC-compliant geometry from a sequence of reconstructed (lon, lat) points.

    :param pts: Sequence of (longitude, latitude) coordinates.
    :param btype: Block type identifier from the Ovital container.
    :return: Shapely geometry object.
    """
    if not pts:
        raise ValueError("Cannot construct geometry from empty point list.")

    # Case 1: Single point (Marker / Placemark)
    if len(pts) == 1:
        return Point(pts[0])

    # Detect closed rings in the point stream
    rings = []
    cur_ring = []
    for p in pts:
        cur_ring.append(p)
        if len(cur_ring) >= 4 and cur_ring[0] == cur_ring[-1]:
            rings.append(cur_ring)
            cur_ring = []

    # Case 2: Open line (Track / LineString) - no closed rings and not explicitly typed as polygon
    if not rings:
        if btype == 31:
            if pts[0] != pts[-1]:
                pts.append(pts[0])
            p = Polygon(pts)
            return p if p.is_valid else p.buffer(0)
        return LineString(pts)

    # Single ring polygon
    if len(rings) == 1:
        p = Polygon(rings[0])
        return p if p.is_valid else p.buffer(0)

    # Multi-ring: Differentiate exterior outlines from interior holes
    polys_made = []
    for r in rings:
        if len(r) >= 4:
            p = Polygon(r)
            if not p.is_valid:
                p = p.buffer(0)
            if p.is_valid and not p.is_empty:
                polys_made.append(p)

    if not polys_made:
        return Polygon(rings[0])

    if len(polys_made) == 1:
        return polys_made[0]

    outlines = []
    holes = []
    for p_i in polys_made:
        is_hole = False
        for p_j in polys_made:
            if p_i != p_j and p_j.contains(p_i):
                is_hole = True
                break
        if is_hole:
            holes.append(p_i.exterior.coords)
        else:
            outlines.append(p_i)

    if len(outlines) == 1:
        p = Polygon(outlines[0].exterior.coords, holes)
        return p if p.is_valid else p.buffer(0)
    elif len(outlines) > 1:
        return MultiPolygon(outlines)
    else:
        return polys_made[0]
