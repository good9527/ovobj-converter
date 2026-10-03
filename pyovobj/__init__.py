# -*- coding: utf-8 -*-
"""
pyovobj
-------
Ovital (.ovobj) Native Vector Converter & Geospatial Toolset.
Decodes Ovital binary bitstreams without VIP limits and exports to
Shapefile, GeoPackage, GeoJSON, AutoCAD DXF, KML, and Excel/CSV.
"""

__version__ = "1.0.0"
__author__ = "good9527"

from .core.reader import OvobjReader, read_ovobj
from .core.coords import gcj02_to_wgs84
from .exporters.manager import export_dataset, SUPPORTED_FORMATS

def convert_file(
    input_file: str,
    output_dir: str = None,
    formats: list[str] = None,
    target_crs: str = "EPSG:4535",
    fix_gcj02: bool = False
) -> dict[str, str]:
    """
    High-level Python API to parse an .ovobj file and export it to requested formats.

    :param input_file: Path to the .ovobj file.
    :param output_dir: Directory where exported files will be written.
    :param formats: List of formats to export (e.g. ['shp', 'gpkg', 'dxf', 'kml', 'xlsx']). Default: all.
    :param target_crs: Projected coordinate system (default: 'EPSG:4535' CGCS2000).
    :param fix_gcj02: If True, reverses GCJ-02 distortion back to WGS-84.
    :return: Dictionary mapping exported format keys to file paths.
    """
    import os
    if output_dir is None:
        output_dir = os.path.join(
            os.path.dirname(input_file) or ".",
            f"{os.path.splitext(os.path.basename(input_file))[0]}_export"
        )
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    gdf = read_ovobj(input_file, apply_gcj02_fix=fix_gcj02)
    return export_dataset(gdf, output_dir, base_name, formats=formats, target_crs=target_crs)

__all__ = [
    "__version__",
    "OvobjReader",
    "read_ovobj",
    "convert_file",
    "export_dataset",
    "gcj02_to_wgs84",
    "SUPPORTED_FORMATS",
]
