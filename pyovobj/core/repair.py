# -*- coding: utf-8 -*-
"""
pyovobj.core.repair
-------------------
Computational geometry health auditing and auto-healing algorithms for vector geometries.
Repairs self-intersections, bow-tie degeneracies, collinear spikes, duplicate vertices,
and enforces OGC SFS winding orientation (CCW exteriors, CW interiors).
"""

import math
from typing import Union, Tuple, List
from shapely.geometry import (
    Point, LineString, Polygon, MultiPolygon, MultiLineString, GeometryCollection
)
from shapely.geometry.base import BaseGeometry
from shapely.validation import make_valid
from shapely.ops import orient, unary_union

def remove_duplicate_consecutive_points(coords: List[Tuple[float, float]], tol: float = 1e-9) -> List[Tuple[float, float]]:
    """
    Removes consecutive duplicate or near-duplicate coordinate vertices.
    """
    if not coords or len(coords) < 2:
        return coords

    cleaned = [coords[0]]
    for pt in coords[1:]:
        last = cleaned[-1]
        if abs(pt[0] - last[0]) > tol or abs(pt[1] - last[1]) > tol:
            cleaned.append(pt)

    # For closed rings, ensure minimum 4 points and closure
    if len(coords) >= 4 and coords[0] == coords[-1]:
        if len(cleaned) >= 3 and cleaned[0] != cleaned[-1]:
            cleaned.append(cleaned[0])

    return cleaned

def remove_collinear_spikes(coords: List[Tuple[float, float]], tol: float = 1e-9) -> List[Tuple[float, float]]:
    """
    Removes collinear 180-degree needle returns (GPS jitter antenna spikes) where
    a line segment immediately reverses back along itself.
    """
    if len(coords) < 3:
        return coords

    pts = list(coords)
    is_closed = (pts[0] == pts[-1])
    if is_closed:
        pts = pts[:-1]

    changed = True
    iteration = 0
    max_iter = 10
    while changed and iteration < max_iter:
        changed = False
        iteration += 1
        n = len(pts)
        if n < 3:
            break
        filtered = []
        for i in range(n):
            p_prev = pts[(i - 1) % n] if is_closed else (pts[i - 1] if i > 0 else None)
            p_curr = pts[i]
            p_next = pts[(i + 1) % n] if is_closed else (pts[i + 1] if i < n - 1 else None)

            if p_prev is None or p_next is None:
                filtered.append(p_curr)
                continue

            # Vector 1: curr -> prev; Vector 2: curr -> next
            v1x, v1y = p_prev[0] - p_curr[0], p_prev[1] - p_curr[1]
            v2x, v2y = p_next[0] - p_curr[0], p_next[1] - p_curr[1]
            d1 = math.hypot(v1x, v1y)
            d2 = math.hypot(v2x, v2y)

            if d1 > tol and d2 > tol:
                dot = (v1x * v2x + v1y * v2y) / (d1 * d2)
                # If dot product is close to 1.0, the two segments fold onto each other (180 deg reversal spike)
                if dot > 0.999999:
                    changed = True
                    continue

            filtered.append(p_curr)
        pts = filtered

    if is_closed and len(pts) >= 3:
        pts.append(pts[0])

    return pts if len(pts) >= (4 if is_closed else 2) else coords

def repair_polygon_collection(geom: BaseGeometry) -> Union[Polygon, MultiPolygon]:
    """
    Extracts pure Polygon/MultiPolygon components from arbitrary GeometryCollections
    produced by geometric breakdowns or make_valid, discarding dangling zero-area linear spikes.
    """
    if isinstance(geom, (Polygon, MultiPolygon)) and geom.is_valid and not geom.is_empty:
        return geom

    if isinstance(geom, GeometryCollection):
        polys = [g for g in geom.geoms if isinstance(g, (Polygon, MultiPolygon)) and not g.is_empty and g.area > 0]
        if not polys:
            return geom
        unioned = unary_union(polys)
        if isinstance(unioned, (Polygon, MultiPolygon)):
            return unioned

    # Fallback to buffer(0) healing
    try:
        buffered = geom.buffer(0)
        if isinstance(buffered, (Polygon, MultiPolygon)) and not buffered.is_empty:
            return buffered
    except Exception:
        pass

    return geom

def heal_geometry(geom: BaseGeometry, drop_sliver_area: float = 1e-10) -> BaseGeometry:
    """
    Comprehensive self-healing algorithm for any vector geometry:
    1. Validates topological integrity.
    2. Repairs self-intersections (bow-ties / figure-8s) via make_valid.
    3. Filters out dangling zero-area linear antennas and collapse points from GeometryCollections.
    4. Enforces OGC SFS winding orientation (exterior counter-clockwise, interior clockwise).
    5. Cleans micro-sliver polygons smaller than the sliver area threshold.
    """
    if geom is None or geom.is_empty:
        return geom

    if isinstance(geom, Point):
        return geom

    if isinstance(geom, LineString):
        coords = list(geom.coords)
        coords = remove_duplicate_consecutive_points(coords)
        coords = remove_collinear_spikes(coords)
        if len(coords) < 2:
            return geom
        return LineString(coords)

    if isinstance(geom, (Polygon, MultiPolygon)):
        # First check validity
        if not geom.is_valid:
            try:
                fixed = make_valid(geom)
                fixed = repair_polygon_collection(fixed)
                if isinstance(fixed, (Polygon, MultiPolygon)):
                    geom = fixed
            except Exception:
                geom = geom.buffer(0)

        # Filter slivers and orient
        if isinstance(geom, Polygon):
            if geom.area <= drop_sliver_area:
                return geom
            return orient(geom, sign=1.0)
        elif isinstance(geom, MultiPolygon):
            valid_parts = []
            for p in geom.geoms:
                if p.is_valid and p.area > drop_sliver_area:
                    valid_parts.append(orient(p, sign=1.0))
            if not valid_parts:
                return geom
            return valid_parts[0] if len(valid_parts) == 1 else MultiPolygon(valid_parts)

    return geom

def audit_geometry_health(geom: BaseGeometry) -> dict:
    """
    Performs a thorough topological audit of a geometry, diagnosing defects.
    """
    if geom is None or geom.is_empty:
        return {"status": "EMPTY", "is_valid": False, "reason": "Geometry is empty or None"}

    is_valid = geom.is_valid
    reason = "Valid OGC geometry" if is_valid else "Topology defect detected"
    num_holes = 0
    num_parts = 1

    if isinstance(geom, Polygon):
        num_holes = len(geom.interiors)
    elif isinstance(geom, MultiPolygon):
        num_parts = len(geom.geoms)
        num_holes = sum(len(p.interiors) for p in geom.geoms)

    return {
        "status": "HEALTHY" if is_valid else "DEFECTIVE",
        "geom_type": geom.geom_type,
        "is_valid": is_valid,
        "is_simple": geom.is_simple,
        "num_parts": num_parts,
        "num_holes": num_holes,
        "area": getattr(geom, 'area', 0.0),
        "length": getattr(geom, 'length', 0.0),
        "reason": reason
    }
