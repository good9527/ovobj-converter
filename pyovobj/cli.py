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
from pyovobj.exporters.manager import export_dataset, SUPPORTED_FORMATS

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ovobj-converter",
        description=f"Ovobj Converter Toolkit v{__version__} - High-Performance Native Ovital (.ovobj) Vector Converter & Toolkit.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a single file to all supported formats (Shapefile, GPKG, GeoJSON, DXF, KML, Excel, CSV)
  ovobj-converter input.ovobj -o ./output

  # Convert specific formats with target projection
  ovobj-converter input.ovobj -f shp,dxf,gpkg --crs EPSG:4535 -o ./exports

  # Batch convert all .ovobj files in a folder
  ovobj-converter ./data_folder --batch -f shp,gpkg -o ./batch_output

  # Apply GCJ-02 to WGS-84 correction for domestic tile tracings
  # Launch local interactive Web GUI
  ovobj-converter --web

  # Reverse-pack Shapefile/GeoJSON to .ovobj
  ovobj-converter input.shp --pack -o output.ovobj
        """
    )
    parser.add_argument("input", nargs="?", default=None, help="Path to input .ovobj or vector file")
    parser.add_argument("-o", "--output-dir", default=None, help="Output directory path (or output .ovobj path if --pack is used)")
    parser.add_argument("-f", "--formats", default="all", help=f"Comma-separated list of formats ({','.join(SUPPORTED_FORMATS)}) or 'all'")
    parser.add_argument("--crs", default="EPSG:4535", help="Target projected coordinate reference system (default: EPSG:4535 / CGCS2000)")
    parser.add_argument("--fix-gcj02", action="store_true", help="Reverse GCJ-02 (Mars) coordinate distortion back to WGS-84")
    parser.add_argument("--batch", action="store_true", help="Batch mode: process all .ovobj files found in the input directory")
    parser.add_argument("--pack", action="store_true", help="Reverse mode: pack a Shapefile / GeoJSON / GeoPackage into an .ovobj binary file")
    parser.add_argument("--web", "--gui", action="store_true", help="Launch the local interactive Web GUI")
    parser.add_argument("--port", type=int, default=8080, help="Port for the Web GUI server (default: 8080)")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    return parser

def process_file(file_path: str, out_dir: str, formats: list[str], crs: str, fix_gcj02: bool):
    t0 = time.time()
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    print(f"\n========================================================")
    print(f"[*] Processing: {os.path.basename(file_path)}")
    print(f"[*] Source size: {os.path.getsize(file_path) / 1024:.1f} KB")
    
    gdf = read_ovobj(file_path, apply_gcj02_fix=fix_gcj02)
    if gdf.empty:
        print(f"[!] Warning: No valid geometric features found in {file_path}")
        return

    n_feats = len(gdf)
    types_count = gdf.geometry.type.value_counts().to_dict()
    print(f"[+] Reconstructed {n_feats} features: {types_count}")

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

    # 2. Handle Reverse Packing mode
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

    # 3. Handle Normal Conversion mode
    if args.formats.lower() == 'all':
        fmt_list = list(SUPPORTED_FORMATS)
    else:
        fmt_list = [f.strip().lower() for f in args.formats.split(',') if f.strip()]

    if args.batch or os.path.isdir(input_path):
        target_dir = input_path if os.path.isdir(input_path) else os.path.dirname(input_path)
        ovobj_files = glob.glob(os.path.join(target_dir, "*.ovobj"))
        if not ovobj_files:
            print(f"No .ovobj files found in directory '{target_dir}'.", file=sys.stderr)
            sys.exit(1)

        out_root = args.output_dir or os.path.join(target_dir, "ovobj_exports")
        print(f"Batch mode enabled: found {len(ovobj_files)} files. Output directory: {out_root}")
        for fp in ovobj_files:
            process_file(fp, out_root, fmt_list, args.crs, args.fix_gcj02)
    else:
        out_dir = args.output_dir or os.path.join(os.path.dirname(input_path) or ".", f"{os.path.splitext(os.path.basename(input_path))[0]}_export")
        process_file(input_path, out_dir, fmt_list, args.crs, args.fix_gcj02)

if __name__ == '__main__':
    main()
