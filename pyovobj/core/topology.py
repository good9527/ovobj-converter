# -*- coding: utf-8 -*-
"""
pyovobj.core.topology
---------------------
Topological Containment Forest Algorithm and geometry reconstruction for Points,
LineStrings, Polygons, and complex MultiPolygons with recursive nested hole hierarchies.
Accelerated with R-Tree (STRtree) spatial indexing and robust geometric boolean difference healing.
"""

from typing import Union, List, Tuple, Set
from shapely.geometry import Point, LineString, Polygon, MultiPolygon, GeometryCollection
from shapely.validation import make_valid
from shapely.ops import orient, unary_union
from shapely import STRtree

from .repair import remove_duplicate_consecutive_points, heal_geometry

def build_containment_hierarchy(rings: List[List[Tuple[float, float]]]) -> Union[Polygon, MultiPolygon]:
    """
    Topological Containment Forest Algorithm:
    Rigorously decomposes arbitrary collections of closed rings into parent exterior boundaries
    and child interior voids (holes) at any nesting depth without losing topological holes.
    Accelerated with STRtree spatial indexing dropping complexity from O(N^2) to O(N log N).

    - Depth 0, 2, 4 (Even): Exterior positive surfaces (Polygon boundaries / nested islands)
    - Depth 1, 3, 5 (Odd):  Interior negative voids (Holes) belonging to immediate parent exterior
    """
    polys: List[Polygon] = []
    for r in rings:
        r_clean = remove_duplicate_consecutive_points(r)
        if len(r_clean) < 3:
            continue
        if r_clean[0] != r_clean[-1]:
            r_clean.append(r_clean[0])
        if len(r_clean) < 4:
            continue

        p = Polygon(r_clean)
        if not p.is_valid:
            try:
                fixed = make_valid(p)
                if isinstance(fixed, Polygon) and not fixed.is_empty and fixed.area > 0:
                    polys.append(fixed)
                elif isinstance(fixed, (MultiPolygon, GeometryCollection)):
                    for g in fixed.geoms:
                        if isinstance(g, Polygon) and not g.is_empty and g.area > 0:
                            polys.append(g)
            except Exception:
                p_buf = p.buffer(0)
                if isinstance(p_buf, Polygon) and not p_buf.is_empty and p_buf.area > 0:
                    polys.append(p_buf)
        elif not p.is_empty and p.area > 0:
            polys.append(p)

    if not polys:
        return Polygon(rings[0]) if rings else Polygon()

    if len(polys) == 1:
        return orient(polys[0], sign=1.0)

    n = len(polys)
    # Compute containment matrix: j is an ancestor of i if Area(j) > Area(i) and j covers i
    ancestors: dict[int, Set[int]] = {i: set() for i in range(n)}
    if n >= 4:
        # O(N log N) spatial indexing via GEOS STRtree
        tree = STRtree(polys)
        for i in range(n):
            candidates = tree.query(polys[i], predicate='covered_by')
            for j in candidates:
                j_idx = int(j)
                if i != j_idx and polys[j_idx].area > polys[i].area:
                    ancestors[i].add(j_idx)
    else:
        for i in range(n):
            for j in range(n):
                if i != j and polys[j].area > polys[i].area:
                    if polys[j].covers(polys[i]) or polys[j].contains(polys[i]):
                        ancestors[i].add(j)

    depths = {i: len(ancestors[i]) for i in range(n)}

    # Even depth = Exterior boundary; Odd depth = Hole
    exterior_indices = [i for i in range(n) if depths[i] % 2 == 0]

    # Map each hole to its immediate parent exterior
    hole_map: dict[int, List[List[Tuple[float, float]]]] = {ext_i: [] for ext_i in exterior_indices}
    for i in range(n):
        if depths[i] % 2 == 1:
            ext_ancs = [a for a in ancestors[i] if a in exterior_indices]
            if ext_ancs:
                parent = max(ext_ancs, key=lambda a: depths[a])
                hole_map[parent].append(list(polys[i].exterior.coords))

    # Reconstruct OGC SFS compliant polygons
    reconstructed: List[Polygon] = []
    for ext_i in exterior_indices:
        ext_poly = orient(polys[ext_i], sign=1.0)
        holes = hole_map[ext_i]
        if not holes:
            reconstructed.append(ext_poly)
            continue

        try:
            # Fast path: OGC standard Polygon(ext, holes)
            p = Polygon(ext_poly.exterior.coords, holes)
            if p.is_valid and not p.is_empty:
                reconstructed.append(orient(p, sign=1.0))
            else:
                # Robust path: geometric boolean difference (handles touching holes, shared edges, overlapping holes)
                hole_polys = [Polygon(h) for h in holes if len(h) >= 4]
                hole_union = unary_union(hole_polys)
                diff = ext_poly.difference(hole_union)
                if isinstance(diff, Polygon) and not diff.is_empty and diff.area > 0:
                    reconstructed.append(orient(diff, sign=1.0))
                elif isinstance(diff, (MultiPolygon, GeometryCollection)):
                    for sub_p in diff.geoms:
                        if isinstance(sub_p, Polygon) and not sub_p.is_empty and sub_p.area > 0:
                            reconstructed.append(orient(sub_p, sign=1.0))
                else:
                    reconstructed.append(ext_poly)
        except Exception:
            reconstructed.append(ext_poly)

    if not reconstructed:
        return polys[0]
    if len(reconstructed) == 1:
        return reconstructed[0]
    return MultiPolygon(reconstructed)


def build_geometry_from_points(
    pts: List[Tuple[float, float]],
    btype: int = 0,
    auto_heal: bool = True
) -> Union[Point, LineString, Polygon, MultiPolygon]:
    """
    Constructs an OGC-compliant geometry from a sequence of reconstructed (lon, lat) points
    with automatic closed ring segmentation, containment forest nesting, and self-healing.

    :param pts: Sequence of (longitude, latitude) coordinates.
    :param btype: Block type identifier from the Ovital container (1=Point, 31=Polygon, 32=LineString).
    :param auto_heal: If True, executes geometric self-healing algorithms.
    :return: Shapely geometry object (Point, LineString, Polygon, or MultiPolygon).
    """
    if not pts:
        raise ValueError("Cannot construct geometry from empty point list.")

    # Case 1: Point
    if len(pts) == 1:
        return Point(pts[0])

    # Detect closed rings in the point stream
    rings: List[List[Tuple[float, float]]] = []
    cur_ring: List[Tuple[float, float]] = []

    for p in pts:
        cur_ring.append(p)
        if len(cur_ring) >= 4 and cur_ring[0] == cur_ring[-1]:
            rings.append(cur_ring)
            cur_ring = []

    # Handle remaining points in buffer
    if cur_ring:
        if btype == 31 and len(cur_ring) >= 3:
            # Polygon block with unclosed ring: snap close
            if cur_ring[0] != cur_ring[-1]:
                cur_ring.append(cur_ring[0])
            rings.append(cur_ring)

    # Case 2: Open line (Track / LineString)
    if not rings:
        if btype == 31:
            pts_poly = list(pts)
            if pts_poly[0] != pts_poly[-1]:
                pts_poly.append(pts_poly[0])
            p = Polygon(pts_poly)
            geom = p if p.is_valid else p.buffer(0)
            return heal_geometry(geom) if auto_heal else geom

        pts_clean = remove_duplicate_consecutive_points(pts)
        if len(pts_clean) < 2:
            pts_clean = pts
        line = LineString(pts_clean)
        return heal_geometry(line) if auto_heal else line

    # Case 3: Polygons & MultiPolygons with Containment Forest
    geom = build_containment_hierarchy(rings)
    if auto_heal:
        geom = heal_geometry(geom)
    return geom
