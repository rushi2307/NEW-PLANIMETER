"""
Unit tests for Geometry Engine (Shoelace formula, perimeter, centroid, self-intersection, CAD transform).
"""

import unittest
import math
from core.geometry_engine import GeometryEngine


class TestGeometryEngine(unittest.TestCase):

    def test_shoelace_triangle(self):
        # Right triangle base 30, height 20 => Area = 300.0
        pts = [(0.0, 0.0), (30.0, 0.0), (0.0, 20.0)]
        area = GeometryEngine.shoelace_area(pts)
        self.assertAlmostEqual(area, 300.0, places=6)

    def test_shoelace_trapezoid(self):
        # Trapezoid: Bottom base 40 (0 to 40), top base 25 (5 to 30), height 20
        # Area = (40 + 25) / 2 * 20 = 650.0
        pts = [(0.0, 0.0), (40.0, 0.0), (30.0, 20.0), (5.0, 20.0)]
        area = GeometryEngine.shoelace_area(pts)
        self.assertAlmostEqual(area, 650.0, places=6)

    def test_shoelace_l_shape(self):
        # L-shape: 50x30 with 25x15 notch => (50*30) - (25*15) = 1125.0
        pts = [
            (0.0, 0.0),
            (50.0, 0.0),
            (50.0, 15.0),
            (25.0, 15.0),
            (25.0, 30.0),
            (0.0, 30.0)
        ]
        area = GeometryEngine.shoelace_area(pts)
        self.assertAlmostEqual(area, 1125.0, places=6)

    def test_perimeter(self):
        # Rectangle 10 x 20 => P = 60
        pts = [(0.0, 0.0), (10.0, 0.0), (10.0, 20.0), (0.0, 20.0)]
        p = GeometryEngine.polygon_perimeter(pts)
        self.assertAlmostEqual(p, 60.0, places=6)

    def test_centroid(self):
        # Triangle (0,0), (6,0), (0,6) => Centroid = (2, 2)
        pts = [(0.0, 0.0), (6.0, 0.0), (0.0, 6.0)]
        cx, cy = GeometryEngine.polygon_centroid(pts)
        self.assertAlmostEqual(cx, 2.0, places=5)
        self.assertAlmostEqual(cy, 2.0, places=5)

    def test_self_intersection_detection(self):
        # Figure 8 (bow-tie) self-intersecting polygon
        bowtie = [(0.0, 0.0), (10.0, 10.0), (10.0, 0.0), (0.0, 10.0)]
        val = GeometryEngine.validate_polygon(bowtie)
        self.assertFalse(val["is_valid"])
        self.assertTrue(val["has_self_intersections"])

    def test_valid_polygon(self):
        regular = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        val = GeometryEngine.validate_polygon(regular)
        self.assertTrue(val["is_valid"])
        self.assertFalse(val["has_self_intersections"])

    def test_cad_transformation(self):
        # Image coords: H=1000px, scale=0.1
        # P_img = (100, 200) => P_cad = (100*0.1, (1000-200)*0.1) = (10.0, 80.0)
        pts_px = [(100.0, 200.0)]
        cad_pts = GeometryEngine.transform_pixels_to_cad(pts_px, scale_factor=0.1, image_height=1000.0)
        self.assertAlmostEqual(cad_pts[0][0], 10.0, places=5)
        self.assertAlmostEqual(cad_pts[0][1], 80.0, places=5)


if __name__ == "__main__":
    unittest.main()
