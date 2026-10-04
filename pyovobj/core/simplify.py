# -*- coding: utf-8 -*-
"""
pyovobj.core.simplify
---------------------
Topology-Preserving Adaptive Geometry Simplification algorithm.
Reduces vertex density while rigorously preserving topological invariants:
- Prevents self-intersections and ring inversion
- Preserves interior hole containment within exterior boundaries
- Preserves minimum vertex counts for closed polygons
"""

from typing import Union, List, Tuple
from shapely.geometry import Point, LineString, Polygon, MultiPolygon, MultiLineString
from shapely.geometry.base import BaseGeometry
from shapely.ops import orient

def simplify_ring(coords: List[Tuple[float, float]], tolerance: float) -> List[Tuple[float, float]]:
    """
    Simplifies a single closed ring using Douglas-Peucker, ensuring closure and minimum 4 vertices.
    """
    if len(coords) <= 4:
        return coords

    line = LineString(coords)
    simplified = line.simplify(tolerance, preserve_topology=True)
    simp_coords = list(simplified.coords)

    # Ensure minimum 4 vertices and closure
    if len(simp_coords) < 3:
        return coords

    if simp_coords[0] != simp_coords[-1]:
        simp_coords.append(simp_coords[0])

    if len(simp_coords) < 4:
        return coords

    # Validate that simplified ring does not self-intersect
    p = Polygon(simp_coords)
    if not p.is_valid or p.area <= 0:
        return coords

    return simp_coords

def simplify_polygon(poly: Polygon, tolerance: float) -> Polygon:
    """
    Simplifies a Polygon while ensuring all interior holes remain valid and contained within exterior.
    """
    if poly.is_empty:
        return poly

    ext_simplified = simplify_ring(list(poly.exterior.coords), tolerance)
    p_ext = Polygon(ext_simplified)
    if not p_ext.is_valid or p_ext.area <= 0:
        ext_simplified = list(poly.exterior.coords)
        p_ext = Polygon(ext_simplified)

    simp_holes = []
    for interior in poly.interiors:
        h_simp = simplify_ring(list(interior.coords), tolerance)
        p_h = Polygon(h_simp)
        # Verify hole remains valid and contained inside exterior
        if p_h.is_valid and p_h.area > 0 and (p_ext.contains(p_h) or p_ext.covers(p_h)):
            simp_holes.append(h_simp)
        else:
            simp_holes.append(list(interior.coords))

    try:
        res = Polygon(ext_simplified, simp_holes)
        if res.is_valid and not res.is_empty:
            return orient(res, sign=1.0)
    except Exception:
        pass

    return poly

def simplify_geometry(geom: BaseGeometry, tolerance: float = 1e-5) -> BaseGeometry:
    """
    High-level API to simplify any vector geometry preserving topological invariants.

    :param geom: Input Shapely geometry.
    :param tolerance: Distance tolerance in geometry CRS units (degrees or meters).
    :return: Simplified valid geometry.
    """
    if geom is None or geom.is_empty or tolerance <= 0:
        return geom

    if isinstance(geom, Point):
        return geom
    elif isinstance(geom, LineString):
        simplified = geom.simplify(tolerance, preserve_topology=True)
        return simplified if len(simplified.coords) >= 2 else geom
    elif isinstance(geom, MultiLineString):
        lines = [l.simplify(tolerance, preserve_topology=True) for l in geom.geoms]
        valid_lines = [l for l in lines if len(l.coords) >= 2]
        return MultiLineString(valid_lines) if valid_lines else geom
    elif isinstance(geom, Polygon):
        return simplify_polygon(geom, tolerance)
    elif isinstance(geom, MultiPolygon):
        simplified_polys = [simplify_polygon(p, tolerance) for p in geom.geoms]
        return MultiPolygon(simplified_polys)
    return geom
