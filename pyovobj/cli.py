# -*- coding: utf-8 -*-
"""
pyovobj.cli
-----------
Command-line interface for the Ovobj Converter Toolkit.
"""

import os
import sys
import glob
import time
import argparse

from pyovobj import __version__
from pyovobj.core.reader import read_ovobj
from pyovobj.core.repair import audit_geometry_health
from pyovobj.exporters.manager import export_dataset, SUPPORTED_FORMATS

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ovobj-converter",
        description=f"Ovobj Converter Toolkit v{__version__} - High-Performance Native Ovital (.ovobj) Vector Converter & Toolkit.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a single file to all supported formats (Shapefile, GPKG, GeoJSON, DXF, KML, FlatGeobuf, TAB, Excel, CSV)
  ovobj-converter input.ovobj -o ./output

  # Convert with CGCS2000 geodetic area & perimeter calculations
  ovobj-converter input.ovobj --metrics -f shp,xlsx -o ./output

  # Perform topological health audit on .ovobj features
  ovobj-converter input.ovobj --audit

  # Convert specific formats with target projection
  ovobj-converter input.ovobj -f shp,dxf,gpkg --crs EPSG:4535 -o ./exports

  # Batch convert all .ovobj files in a folder with parallel workers and geodetic metrics
  ovobj-converter ./data_folder --batch --metrics -f shp,gpkg -o ./batch_output

  # Reverse-pack Shapefile/GeoJSON to .ovobj
  ovobj-converter input.shp --pack -o output.ovobj
        """
    )
    parser.add_argument("input", nargs="?", default=None, help="Path to input .ovobj or vector file")
    parser.add_argument("-o", "--output-dir", default=None, help="Output directory path (or output .ovobj path if --pack is used)")
    parser.add_argument("-f", "--formats", default="all", help=f"Comma-separated list of formats ({','.join(SUPPORTED_FORMATS)}) or 'all'")
    parser.add_argument("--crs", default="EPSG:4535", help="Target projected coordinate reference system (default: EPSG:4535 / CGCS2000)")
    parser.add_argument("--metrics", action="store_true", help="Calculate and attach surveyor-grade CGCS2000 ellipsoidal area (m² and mu) and geodesic perimeter/length")
    parser.add_argument("--audit", action="store_true", help="Perform topological health audit on features and output diagnostic report")
    parser.add_argument("--no-heal", action="store_true", help="Disable geometric auto-healing and topological defect repair")
    parser.add_argument("--fix-gcj02", action="store_true", help="Reverse GCJ-02 (Mars) coordinate distortion back to WGS-84")
    parser.add_argument("--batch", action="store_true", help="Batch mode: process all .ovobj files found in the input directory")
    parser.add_argument("-j", "--workers", type=int, default=None, help="Number of parallel worker processes for batch mode (defaults to CPU cores)")
    parser.add_argument("--pack", action="store_true", help="Reverse mode: pack a Shapefile / GeoJSON / GeoPackage into an .ovobj binary file")
    parser.add_argument("--web", "--gui", action="store_true", help="Launch the local interactive Web GUI")
    parser.add_argument("--port", type=int, default=8080, help="Port for the Web GUI server (default: 8080)")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    return parser

def audit_file(file_path: str, fix_gcj02: bool):
    print(f"\n========================================================")
    print(f"[*] Topological Health Audit: {os.path.basename(file_path)}")
    gdf = read_ovobj(file_path, apply_gcj02_fix=fix_gcj02, auto_heal=False)
    if gdf.empty:
        print(f"[!] File contains no geometric features.")
        return

    n_feats = len(gdf)
    defective_count = 0
    total_holes = 0
    print(f"[*] Auditing {n_feats} features for self-intersections, bow-ties, and spikes...")

    for idx, geom in enumerate(gdf.geometry):
        report = audit_geometry_health(geom)
        if not report['is_valid']:
            defective_count += 1
            if defective_count <= 5:
                print(f"  [DEFECT] Feature #{idx}: {report['geom_type']} invalid: {report['reason']}")
        total_holes += report['num_holes']

    print(f"\n[AUDIT REPORT SUMMARY]")
    print(f"  - Total Features: {n_feats}")
    print(f"  - Valid OGC Geometries: {n_feats - defective_count} ({(n_feats - defective_count) / n_feats * 100:.1f}%)")
    print(f"  - Defective Geometries: {defective_count} ({defective_count / n_feats * 100:.1f}%)")
    print(f"  - Total Interior Rings (Holes): {total_holes}")
    if defective_count > 0:
        print(f"  [+] Note: Default converter automatically self-heals all {defective_count} defects via make_valid and OGC orientation.")
    print(f"========================================================\n")

def process_file(
    file_path: str,
    out_dir: str,
    formats: list[str],
    crs: str,
    fix_gcj02: bool,
    compute_metrics: bool,
    auto_heal: bool
):
    t0 = time.time()
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    print(f"\n========================================================")
    print(f"[*] Processing: {os.path.basename(file_path)}")
    print(f"[*] Source size: {os.path.getsize(file_path) / 1024:.1f} KB")
    
    gdf = read_ovobj(
        file_path,
        apply_gcj02_fix=fix_gcj02,
        auto_heal=auto_heal,
        compute_metrics=compute_metrics
    )
    if gdf.empty:
        print(f"[!] Warning: No valid geometric features found in {file_path}")
        return

    n_feats = len(gdf)
    types_count = gdf.geometry.type.value_counts().to_dict()
    print(f"[+] Reconstructed {n_feats} features: {types_count}")

    if compute_metrics:
        print(f"[+] Computed CGCS2000 Geodetic Metrics (area_sqm, area_mu, perimeter_m, length_m)")

    cols = [c for c in gdf.columns if c != 'geometry']
    print(f"[+] Preserved {len(cols)} attribute fields: {cols[:6]}{'...' if len(cols) > 6 else ''}")

    print(f"[*] Exporting requested formats: {formats}...")
    res = export_dataset(gdf, out_dir, base_name, formats=formats, target_crs=crs)
    
    elapsed = time.time() - t0
    print(f"[SUCCESS] Export completed in {elapsed:.2f}s!")
    for fmt, p in res.items():
        print(f"  -> [{fmt.upper()}]: {p}")

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    parser = build_parser()
    args = parser.parse_args()

    # 1. Handle Web GUI mode
    if args.web:
        from pyovobj.web import start_web_server
        start_web_server(port=args.port)
        return

    # Check input argument
    input_path = args.input
    if not input_path:
        parser.print_help()
        sys.exit(1)

    if not os.path.exists(input_path):
        print(f"Error: Input path '{input_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # 2. Handle Topological Audit mode
    if args.audit:
        audit_file(input_path, fix_gcj02=args.fix_gcj02)
        return

    # 3. Handle Reverse Packing mode
    if args.pack:
        import geopandas as gpd
        from pyovobj.core.packer import write_ovobj
        out_ovobj = args.output_dir
        if not out_ovobj:
            out_ovobj = f"{os.path.splitext(input_path)[0]}.ovobj"
        print(f"[*] Reading vector file: {input_path}...")
        gdf = gpd.read_file(input_path)
        print(f"[*] Packing {len(gdf)} features into native .ovobj binary stream...")
        write_ovobj(gdf, out_ovobj)
        print(f"[SUCCESS] Generated: {out_ovobj} ({os.path.getsize(out_ovobj)} bytes)!")
        return

    # 4. Handle Normal Conversion mode
    if args.formats.lower() == 'all':
        fmt_list = list(SUPPORTED_FORMATS)
    else:
        fmt_list = [f.strip().lower() for f in args.formats.split(',') if f.strip()]

    auto_heal = not args.no_heal

    if args.batch or os.path.isdir(input_path):
        target_dir = input_path if os.path.isdir(input_path) else os.path.dirname(input_path)
        ovobj_files = glob.glob(os.path.join(target_dir, "*.ovobj"))
        if not ovobj_files:
            print(f"No .ovobj files found in directory '{target_dir}'.", file=sys.stderr)
            sys.exit(1)

        out_root = args.output_dir or os.path.join(target_dir, "ovobj_exports")
        from pyovobj.batch import batch_convert_parallel
        batch_convert_parallel(
            input_paths=ovobj_files,
            output_dir=out_root,
            formats=fmt_list,
            crs=args.crs,
            fix_gcj02=args.fix_gcj02,
            compute_metrics=args.metrics,
            auto_heal=auto_heal,
            max_workers=args.workers
        )
    else:
        out_dir = args.output_dir or os.path.join(os.path.dirname(input_path) or ".", f"{os.path.splitext(os.path.basename(input_path))[0]}_export")
        process_file(
            file_path=input_path,
            out_dir=out_dir,
            formats=fmt_list,
            crs=args.crs,
            fix_gcj02=args.fix_gcj02,
            compute_metrics=args.metrics,
            auto_heal=auto_heal
        )

if __name__ == '__main__':
    main()
