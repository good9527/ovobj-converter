# -*- coding: utf-8 -*-
"""
pyovobj.core.sliver
-------------------
Micro-Sliver Polygon Elimination & Common Boundary Dissolving Engine.
Identifies small and elongated sliver parcels resulting from topological digitization,
overlay operations, or boundary snapping discrepancies.
Dissolves each sliver into its adjacent neighbor sharing the longest common linear boundary,
preserving attribute schemas and geometric validity.
"""

import math
from typing import Dict, List, Optional, Set, Tuple, Union
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon, LineString, MultiLineString, GeometryCollection
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union
from shapely.strtree import STRtree

from .repair import heal_geometry

def compute_thinness_ratio(geom: BaseGeometry) -> float:
    """
    Computes the isoperimetric thinness ratio: T = P^2 / (4 * pi * A).
    For a circle, T = 1.0 (most compact).
    For regular polygons (square, rectangle), T is small (1.27 to ~3.0).
    For extremely narrow slivers and needle-like artifacts, T >> 25.0.

    :param geom: Polygon or MultiPolygon.
    :return: Dimensionless thinness index T.
    """
    if geom is None or geom.is_empty:
        return 0.0
    area = geom.area
    if area <= 1e-12:
        return float('inf')
    perimeter = geom.length
    return (perimeter * perimeter) / (4.0 * math.pi * area)

def get_shared_linear_boundary_length(geom1: BaseGeometry, geom2: BaseGeometry) -> float:
    """
    Computes the 1D linear contact length between two polygons.
    Filters out 0D point touches (isolated vertices).

    :param geom1: First geometry.
    :param geom2: Second geometry.
    :return: Total shared boundary length in coordinate units.
    """
    if geom1 is None or geom2 is None or geom1.is_empty or geom2.is_empty:
        return 0.0
    if not geom1.intersects(geom2):
        return 0.0

    try:
        inter = geom1.intersection(geom2)
        if inter.is_empty:
            return 0.0

        if isinstance(inter, (LineString, MultiLineString)):
            return float(inter.length)
        elif isinstance(inter, GeometryCollection):
            total = 0.0
            for g in inter.geoms:
                if isinstance(g, (LineString, MultiLineString)):
                    total += g.length
            return float(total)
        return 0.0
    except Exception:
        return 0.0

def eliminate_sliver_polygons(
    gdf: gpd.GeoDataFrame,
    min_area: float = 1.0,
    max_thinness: float = 25.0,
    max_sliver_area: float = 100.0,
    keep_isolated: bool = False,
    max_iterations: int = 5,
    is_geographic: Optional[bool] = None
) -> Tuple[gpd.GeoDataFrame, Dict[str, Union[int, float]]]:
    """
    Eliminates micro-sliver polygons by iteratively merging them into adjacent neighbors
    sharing the longest common boundary.

    :param gdf: Input GeoDataFrame containing Polygon/MultiPolygon features.
    :param min_area: Absolute area threshold below which a feature is unconditionally treated as a sliver.
    :param max_thinness: Thinness ratio threshold (P^2 / 4*pi*A) above which a feature is treated as a sliver.
    :param max_sliver_area: Maximum area ceiling for thinness-based sliver classification.
    :param keep_isolated: If True, retains slivers that have no adjacent neighbors sharing a linear boundary.
    :param max_iterations: Maximum iterative merging passes.
    :param is_geographic: Explicitly specifies whether coordinates are geographic (lon/lat degrees).
                          Defaults to detecting from gdf.crs.
    :return: Tuple of (cleaned GeoDataFrame, report dictionary).
    """
    if gdf.empty:
        return gdf, {'initial_count': 0, 'slivers_merged': 0, 'slivers_dropped': 0, 'final_count': 0}

    # Working copy
    work_df = gdf.copy().reset_index(drop=True)
    initial_count = len(work_df)
    total_merged = 0
    total_dropped = 0

    if is_geographic is None:
        if gdf.crs is not None:
            try:
                is_geographic = bool(gdf.crs.is_geographic)
            except Exception:
                is_geographic = False
        else:
            is_geographic = False

    from .geodesy import compute_ellipsoidal_area

    for iteration in range(max_iterations):
        # Identify slivers
        is_sliver_flags = []
        for geom in work_df.geometry:
            if geom is None or geom.is_empty:
                is_sliver_flags.append(True)
                continue
            if not isinstance(geom, (Polygon, MultiPolygon)):
                is_sliver_flags.append(False)
                continue

            area_sqm = compute_ellipsoidal_area(geom) if is_geographic else geom.area
            if area_sqm < min_area:
                is_sliver_flags.append(True)
            elif area_sqm <= max_sliver_area:
                t = compute_thinness_ratio(geom)
                is_sliver_flags.append(t > max_thinness)
            else:
                is_sliver_flags.append(False)

        sliver_indices = [i for i, flag in enumerate(is_sliver_flags) if flag]
        if not sliver_indices:
            break

        # Sort slivers by area ascending (merge smallest first)
        sliver_indices.sort(key=lambda idx: work_df.geometry.iloc[idx].area if work_df.geometry.iloc[idx] else 0.0)

        # Build spatial index on all active features
        all_geoms = list(work_df.geometry)
        tree = STRtree(all_geoms)

        eliminated_in_this_pass: Set[int] = set()
        merged_count = 0
        dropped_count = 0

        for s_idx in sliver_indices:
            if s_idx in eliminated_in_this_pass:
                continue

            s_geom = work_df.geometry.iloc[s_idx]
            if s_geom is None or s_geom.is_empty:
                eliminated_in_this_pass.add(s_idx)
                dropped_count += 1
                continue

            # Query intersecting candidates
            candidate_indices = tree.query(s_geom, predicate='intersects')

            best_neighbor_idx = None
            max_shared_len = 0.0

            for c_idx in candidate_indices:
                if c_idx == s_idx or c_idx in eliminated_in_this_pass:
                    continue

                c_geom = work_df.geometry.iloc[c_idx]
                shared_len = get_shared_linear_boundary_length(s_geom, c_geom)
                if shared_len > max_shared_len:
                    max_shared_len = shared_len
                    best_neighbor_idx = c_idx

            if best_neighbor_idx is not None and max_shared_len > 0.0:
                # Merge sliver into best neighbor
                n_geom = work_df.geometry.iloc[best_neighbor_idx]
                merged_geom = unary_union([n_geom, s_geom])
                merged_geom = heal_geometry(merged_geom)
                work_df.loc[best_neighbor_idx, 'geometry'] = merged_geom
                eliminated_in_this_pass.add(s_idx)
                merged_count += 1
            else:
                # No neighbor sharing a linear edge
                if not keep_isolated:
                    eliminated_in_this_pass.add(s_idx)
                    dropped_count += 1

        total_merged += merged_count
        total_dropped += dropped_count

        # Filter out eliminated rows
        surviving_mask = [i not in eliminated_in_this_pass for i in range(len(work_df))]
        work_df = work_df[surviving_mask].reset_index(drop=True)

        if merged_count == 0 and dropped_count == 0:
            break

    final_count = len(work_df)
    report = {
        'initial_count': initial_count,
        'slivers_merged': total_merged,
        'slivers_dropped': total_dropped,
        'final_count': final_count,
        'iterations': iteration + 1
    }

    return work_df, report
