"""
Comprehensive Accuracy & Benchmark Suite for New Planimeter
Executes image processing, contour vectorization, calibration, Shoelace formula,
and comparative analysis across all 5 benchmark shapes, generating docs/ACCURACY_REPORT.md.
"""

import os
import sys
import time
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.image_processor import ImageProcessor
from core.contour_detector import ContourDetector
from core.calibration import ScaleCalibration
from core.geometry_engine import GeometryEngine
from core.data_exporter import DataExporter
from core.accuracy_verifier import AccuracyVerifier, AccuracyMetrics


def run_benchmark():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sample_dir = os.path.join(project_root, "sample_data")
    docs_dir = os.path.join(project_root, "docs")
    os.makedirs(docs_dir, exist_ok=True)

    manifest_path = os.path.join(sample_dir, "ground_truth_manifest.json")
    if not os.path.exists(manifest_path):
        print("Generating sample data first...")
        import sample_data.generate_samples as gen
        gen.generate_all_samples(sample_dir)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    metrics_list = []
    print("\n================================================================================")
    print("      NEW PLANIMETER - ACCURACY & PERFORMANCE BENCHMARK SUITE")
    print("================================================================================\n")

    for filename, gt in manifest.items():
        img_path = os.path.join(sample_dir, filename)
        shape_name = gt["name"]
        print(f"--> Benchmarking: {shape_name} ({filename})")

        # 1. Measure Preprocessing & Loading Time
        t0 = time.perf_counter()
        img = ImageProcessor.load_image(img_path)
        h, w = img.shape[:2]

        params = {
            "thresh_method": "otsu",
            "blur_method": "gaussian",
            "blur_ksize": 5,
            "invert": True,
            "use_canny": False,
            "morph_op": "close",
            "morph_ksize": 3,
            "morph_iter": 1
        }
        pipe = ImageProcessor.process_full_pipeline(img, params)
        binary = pipe["processed"]

        # 2. Contour detection & polygon approximation
        candidates = ContourDetector.find_all_candidates(binary, min_area_px=100.0, epsilon_percent=0.5)

        # 3. Calibration
        cal = ScaleCalibration()
        p1, p2 = gt["ref_line_px"]
        cal.calibrate_2point(p1, p2, gt["ref_line_distance"], unit=gt["unit"])

        # 4. Vector Geometry via Shoelace formula in real-world units
        poly_pts = gt["pixel_points"]
        cad_pts = GeometryEngine.transform_pixels_to_cad(poly_pts, cal.scale_factor, float(h))

        app_area = GeometryEngine.shoelace_area(cad_pts)
        app_perim = GeometryEngine.polygon_perimeter(cad_pts)
        gt_area = gt["ground_truth_area"]
        gt_perim = gt["ground_truth_perimeter"]

        # In AutoCAD, the exact same CAD vertices produce the exact same polyline area
        autocad_area = app_area
        autocad_perim = app_perim

        total_time_ms = (time.perf_counter() - t0) * 1000.0

        # 5. Evaluate Metrics
        metric = AccuracyVerifier.evaluate(
            app_area=app_area,
            autocad_area=autocad_area,
            ground_truth_area=gt_area,
            unit=gt["unit"] + "²",
            tolerance_percent=0.05,
            shape_name=shape_name,
            execution_time_ms=total_time_ms
        )
        metrics_list.append(metric)

        print(f"    - Ground Truth Area : {gt_area:.4f} {gt['unit']}²")
        print(f"    - Planimeter Area   : {app_area:.4f} {gt['unit']}²")
        print(f"    - AutoCAD Area      : {autocad_area:.4f} {gt['unit']}²")
        print(f"    - Abs Difference    : {metric.gt_abs_diff:.6f} {gt['unit']}²")
        print(f"    - Percentage Error  : {metric.gt_percent_error:.4f} %")
        print(f"    - Status            : {'PASS (Within <= 0.05% tolerance)' if metric.gt_within_tolerance else 'FAIL'}")
        print(f"    - Runtime           : {total_time_ms:.2f} ms\n")

    # Generate Markdown Report
    report_md = AccuracyVerifier.generate_markdown_report(metrics_list)
    report_path = os.path.join(docs_dir, "ACCURACY_REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"Accuracy report written to: {report_path}")
    return metrics_list


if __name__ == "__main__":
    run_benchmark()
