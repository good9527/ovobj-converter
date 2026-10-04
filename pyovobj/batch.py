# -*- coding: utf-8 -*-
"""
pyovobj.batch
-------------
High-performance multi-process parallel batch conversion engine
for processing hundreds of .ovobj files across multi-core CPUs.
Supports batch geodetic metrics, GB/T 13989-2012 map sheet indexing,
sliver polygon elimination, and topology simplification.
"""

import os
import time
import glob
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Optional, List, Dict

from pyovobj.core.reader import read_ovobj
from pyovobj.core.grids import attach_map_sheet_codes
from pyovobj.core.sliver import eliminate_sliver_polygons
from pyovobj.core.simplify import simplify_geometry
from pyovobj.exporters.manager import export_dataset, SUPPORTED_FORMATS

def _worker_convert_file(task_args: tuple) -> dict:
    """
    Worker function executed in worker subprocess.
    """
    (
        file_path, out_dir, formats, crs, fix_gcj02, compute_metrics, auto_heal,
        sheet_scale, clean_slivers_tol, simplify_tol
    ) = task_args

    t0 = time.time()
    base_name = os.path.splitext(os.path.basename(file_path))[0]

    try:
        gdf = read_ovobj(
            file_path,
            apply_gcj02_fix=fix_gcj02,
            auto_heal=auto_heal,
            compute_metrics=compute_metrics
        )
        if gdf.empty:
            return {
                'file': file_path,
                'status': 'empty',
                'features': 0,
                'elapsed': time.time() - t0,
                'results': {}
            }

        if clean_slivers_tol is not None:
            gdf, _ = eliminate_sliver_polygons(gdf, min_area=clean_slivers_tol)

        if simplify_tol is not None and simplify_tol > 0:
            gdf['geometry'] = [simplify_geometry(g, tolerance=simplify_tol) for g in gdf.geometry]

        if sheet_scale:
            gdf = attach_map_sheet_codes(gdf, scale=sheet_scale, col_name='TFH')

        res = export_dataset(gdf, out_dir, base_name, formats=formats, target_crs=crs)
        return {
            'file': file_path,
            'status': 'success',
            'features': len(gdf),
            'elapsed': time.time() - t0,
            'results': res
        }
    except Exception as e:
        return {
            'file': file_path,
            'status': 'error',
            'error': str(e),
            'features': 0,
            'elapsed': time.time() - t0,
            'results': {}
        }

def batch_convert_parallel(
    input_paths: List[str],
    output_dir: str,
    formats: List[str] = None,
    crs: str = "EPSG:4535",
    fix_gcj02: bool = False,
    compute_metrics: bool = False,
    auto_heal: bool = True,
    sheet_scale: Optional[str] = None,
    clean_slivers_tol: Optional[float] = None,
    simplify_tol: Optional[float] = None,
    max_workers: Optional[int] = None
) -> dict:
    """
    Executes high-throughput multi-process parallel conversion over a list of .ovobj files.

    :param input_paths: List of input .ovobj file paths.
    :param output_dir: Destination directory.
    :param formats: Output formats to export.
    :param crs: Target projected coordinate system.
    :param fix_gcj02: Reverse GCJ-02 distortion if True.
    :param compute_metrics: If True, calculates and appends surveyor geodetic metrics.
    :param auto_heal: If True, executes geometric self-healing algorithms.
    :param sheet_scale: Attach GB/T 13989-2012 map sheet codes at scale (e.g. '10k', '5k').
    :param clean_slivers_tol: Minimum parcel area threshold for sliver dissolving (m²).
    :param simplify_tol: Simplification tolerance in degrees.
    :param max_workers: Number of parallel worker processes (defaults to CPU core count).
    :return: Summary dictionary with conversion statistics.
    """
    os.makedirs(output_dir, exist_ok=True)
    t_start = time.time()

    if max_workers is None:
        max_workers = min(len(input_paths), os.cpu_count() or 4)

    tasks = [
        (
            fp, output_dir, formats, crs, fix_gcj02, compute_metrics, auto_heal,
            sheet_scale, clean_slivers_tol, simplify_tol
        )
        for fp in input_paths
    ]
    total_files = len(tasks)
    print(f"\n[*] Starting Parallel Batch Conversion on {total_files} files using {max_workers} worker processes...")

    completed = 0
    total_features = 0
    success_count = 0
    error_count = 0

    results_summary = []

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_worker_convert_file, task): task[0] for task in tasks}
        for future in as_completed(futures):
            res = future.result()
            completed += 1
            fname = os.path.basename(res['file'])
            if res['status'] == 'success':
                success_count += 1
                total_features += res['features']
                print(f"  [{completed}/{total_files}] [SUCCESS] {fname} ({res['features']} features in {res['elapsed']:.2f}s)")
            elif res['status'] == 'empty':
                print(f"  [{completed}/{total_files}] [EMPTY] {fname} (0 features)")
            else:
                error_count += 1
                print(f"  [{completed}/{total_files}] [FAILED] {fname}: {res.get('error')}")
            results_summary.append(res)

    total_elapsed = time.time() - t_start
    throughput = total_features / max(total_elapsed, 0.001)

    print(f"\n========================================================")
    print(f"[SUMMARY] Parallel Conversion Complete:")
    print(f"  - Total Files Processed: {total_files}")
    print(f"  - Successfully Converted: {success_count}")
    print(f"  - Total Features Reconstructed: {total_features:,}")
    print(f"  - Total Elapsed Time: {total_elapsed:.2f} seconds")
    print(f"  - Processing Throughput: {throughput:,.1f} features/second")
    print(f"========================================================\n")

    return {
        'total_files': total_files,
        'success_count': success_count,
        'error_count': error_count,
        'total_features': total_features,
        'elapsed_seconds': total_elapsed,
        'throughput_features_per_sec': throughput,
        'details': results_summary
    }
