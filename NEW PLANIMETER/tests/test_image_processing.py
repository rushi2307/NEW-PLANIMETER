"""
Unit tests for Image Processing and Contour Detection.
"""

import unittest
import os
import cv2
import numpy as np
from core.image_processor import ImageProcessor
from core.contour_detector import ContourDetector


class TestImageProcessing(unittest.TestCase):

    def setUp(self):
        # Create a synthetic test image with a white rectangle on black background
        self.img = np.zeros((400, 600, 3), dtype=np.uint8)
        # Rectangle from (100, 100) to (500, 300) => 400 x 200 => area 80000 px^2
        cv2.rectangle(self.img, (100, 100), (500, 300), (255, 255, 255), -1)

    def test_grayscale_and_threshold(self):
        gray = ImageProcessor.to_grayscale(self.img)
        self.assertEqual(len(gray.shape), 2)
        binary = ImageProcessor.apply_threshold(gray, method="otsu", invert=False)
        self.assertEqual(binary.shape, (400, 600))
        # Non-zero pixels should be roughly 400 * 200 = 80000
        count = np.count_nonzero(binary)
        self.assertAlmostEqual(count, 80000, delta=1000)

    def test_contour_detection(self):
        gray = ImageProcessor.to_grayscale(self.img)
        binary = ImageProcessor.apply_threshold(gray, method="binary", thresh_val=127, invert=False)
        candidates = ContourDetector.find_all_candidates(binary, min_area_px=1000.0, epsilon_percent=1.0)
        self.assertGreaterEqual(len(candidates), 1)

        primary = candidates[0]
        # Check area
        self.assertAlmostEqual(primary.raw_area, 80000.0, delta=500.0)
        # Polygon should have 4 vertices (approx rectangle)
        self.assertEqual(len(primary.polygon_points), 4)

    def test_semi_auto_point_selection(self):
        gray = ImageProcessor.to_grayscale(self.img)
        binary = ImageProcessor.apply_threshold(gray, method="binary", thresh_val=127, invert=False)
        candidates = ContourDetector.find_all_candidates(binary, min_area_px=1000.0)

        # Click inside (300, 200)
        selected = ContourDetector.find_candidate_at_point(candidates, 300.0, 200.0)
        self.assertIsNotNone(selected)
        self.assertAlmostEqual(selected.raw_area, 80000.0, delta=500.0)

    def test_perspective_homography(self):
        # 4 corners of rectangle
        src = [(100.0, 100.0), (500.0, 100.0), (500.0, 300.0), (100.0, 300.0)]
        warped, mat = ImageProcessor.perspective_homography(self.img, src)
        self.assertIsNotNone(warped)
        self.assertEqual(mat.shape, (3, 3))


if __name__ == "__main__":
    unittest.main()
