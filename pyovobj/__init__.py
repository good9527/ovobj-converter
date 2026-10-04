# -*- coding: utf-8 -*-
"""
pyovobj
-------
Ovital (.ovobj) Native Vector Converter & Geospatial Toolkit.
Decodes Ovital binary bitstreams with 100% precision and exports to
Shapefile, GeoPackage, GeoJSON, AutoCAD DXF, KML, FlatGeobuf, MapInfo TAB, and Excel/CSV.
Includes National Standard CGCS2000 Ellipsoidal Area Integration,
Topological Containment Forest reconstruction, and geometric self-healing.
"""

__version__ = "1.3.1"
__author__ = "good9527"

from .core.reader import OvobjReader, read_ovobj
from .core.packer import write_ovobj
from .core.coords import gcj02_to_wgs84
from .core.topology import build_geometry_from_points, build_containment_hierarchy
from .core.repair import heal_geometry, audit_geometry_health
from .core.geodesy import (
    GeodeticCalculator,
    compute_ellipsoidal_area,
    compute_area_mu,
    compute_geodesic_length,
    attach_geodesic_metrics,
    ELLIPSOIDS
)
from .exporters.manager import export_dataset, SUPPORTED_FORMATS

def pack_to_ovobj(input_vector: str, output_ovobj: str = None) -> str:
    """
    Reverse-pack any GIS vector file (Shapefile, GeoPackage, GeoJSON, etc.) into an .ovobj file.

    :param input_vector: Path to input vector file.
    :param output_ovobj: Path to output .ovobj file.
    :return: Output .ovobj file path.
    """
    import os
    import geopandas as gpd
    if output_ovobj is None:
        base = os.path.splitext(input_vector)[0]
        output_ovobj = f"{base}.ovobj"
    gdf = gpd.read_file(input_vector)
    return write_ovobj(gdf, output_ovobj)

def convert_file(
    input_file: str,
    output_dir: str = None,
    formats: list[str] = None,
    target_crs: str = "EPSG:4535",
    fix_gcj02: bool = False,
    compute_metrics: bool = False,
    auto_heal: bool = True
) -> dict[str, str]:
    """
    High-level Python API to parse an .ovobj file and export it to requested formats.

    :param input_file: Path to the .ovobj file.
    :param output_dir: Directory where exported files will be written.
    :param formats: List of formats to export. Default: all.
    :param target_crs: Projected coordinate system (default: 'EPSG:4535' CGCS2000).
    :param fix_gcj02: If True, reverses GCJ-02 distortion back to WGS-84.
    :param compute_metrics: If True, attaches surveyor-grade geodetic area and perimeter metrics.
    :param auto_heal: If True, executes geometric self-healing and topology validation.
    :return: Dictionary mapping exported format keys to file paths.
    """
    import os
    if output_dir is None:
        output_dir = os.path.join(
            os.path.dirname(input_file) or ".",
            f"{os.path.splitext(os.path.basename(input_file))[0]}_export"
        )
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    gdf = read_ovobj(
        input_file,
        apply_gcj02_fix=fix_gcj02,
        auto_heal=auto_heal,
        compute_metrics=compute_metrics
    )
    return export_dataset(gdf, output_dir, base_name, formats=formats, target_crs=target_crs)

__all__ = [
    "__version__",
    "OvobjReader",
    "read_ovobj",
    "write_ovobj",
    "pack_to_ovobj",
    "convert_file",
    "export_dataset",
    "gcj02_to_wgs84",
    "build_geometry_from_points",
    "build_containment_hierarchy",
    "heal_geometry",
    "audit_geometry_health",
    "GeodeticCalculator",
    "compute_ellipsoidal_area",
    "compute_area_mu",
    "compute_geodesic_length",
    "attach_geodesic_metrics",
    "ELLIPSOIDS",
    "SUPPORTED_FORMATS",
]
