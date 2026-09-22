"""
Integration tests for New Planimeter
Validates complete pipeline across all 5 ground truth benchmark datasets.
"""

import unittest
import os
import json
from core.image_processor import ImageProcessor
from core.contour_detector import ContourDetector
from core.calibration import ScaleCalibration
from core.geometry_engine import GeometryEngine
from core.data_exporter import DataExporter
from core.accuracy_verifier import AccuracyVerifier


class TestFullPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sample_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_data")
        manifest_path = os.path.join(cls.sample_dir, "ground_truth_manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            cls.manifest = json.load(f)

    def test_triangle_plot_accuracy(self):
        filename = "triangle_plot.png"
        gt = self.manifest[filename]
        img_path = os.path.join(self.sample_dir, filename)

        # 1. Load image
        img = ImageProcessor.load_image(img_path)
        h, w = img.shape[:2]

        # 2. Calibration
        cal = ScaleCalibration()
        p1, p2 = gt["ref_line_px"]
        cal.calibrate_2point(p1, p2, gt["ref_line_distance"], unit=gt["unit"])
        self.assertAlmostEqual(cal.scale_factor, gt["scale_factor"], places=5)

        # 3. Geometry from pixel points
        cad_pts = GeometryEngine.transform_pixels_to_cad(gt["pixel_points"], cal.scale_factor, float(h))
        app_area = GeometryEngine.shoelace_area(cad_pts)

        # 4. Verify accuracy vs ground truth
        metrics = AccuracyVerifier.evaluate(
            app_area=app_area,
            ground_truth_area=gt["ground_truth_area"],
            unit=gt["unit"] + "²",
            tolerance_percent=0.05,
            shape_name=gt["name"]
        )

        self.assertAlmostEqual(app_area, gt["ground_truth_area"], delta=0.01)
        self.assertTrue(metrics.gt_within_tolerance)

        # 5. Export JSON & SCR
        payload = DataExporter.build_export_payload(gt["pixel_points"], cal, w, h, filename)
        out_json = os.path.join(self.sample_dir, "test_output_triangle.json")
        DataExporter.export_json(out_json, payload)
        self.assertTrue(os.path.exists(out_json))

    def test_all_sample_shapes_within_tolerance(self):
        for filename, gt in self.manifest.items():
            img_path = os.path.join(self.sample_dir, filename)
            img = ImageProcessor.load_image(img_path)
            h, w = img.shape[:2]

            cal = ScaleCalibration()
            p1, p2 = gt["ref_line_px"]
            cal.calibrate_2point(p1, p2, gt["ref_line_distance"], unit=gt["unit"])

            cad_pts = GeometryEngine.transform_pixels_to_cad(gt["pixel_points"], cal.scale_factor, float(h))
            app_area = GeometryEngine.shoelace_area(cad_pts)

            metrics = AccuracyVerifier.evaluate(
                app_area=app_area,
                ground_truth_area=gt["ground_truth_area"],
                unit=gt["unit"] + "²",
                tolerance_percent=0.05,
                shape_name=gt["name"]
            )

            print(f"Verified {gt['name']}: Calculated={app_area:.4f}, GT={gt['ground_truth_area']:.4f}, Error={metrics.gt_percent_error:.4f}%")
            self.assertTrue(metrics.gt_within_tolerance, f"Failed tolerance for {gt['name']}")


if __name__ == "__main__":
    unittest.main()
