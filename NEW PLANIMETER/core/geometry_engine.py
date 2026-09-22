"""
Geometry Engine for New Planimeter
High-precision polygon area, perimeter, centroid, self-intersection validation,
and coordinate transformation between image space and CAD Cartesian space.
"""

from typing import List, Tuple, Dict, Any, Optional
import math
import numpy as np


class GeometryEngine:
    """
    Mathematical and geometric calculation engine for irregular polygons.
    """

    @staticmethod
    def shoelace_area(points: List[Tuple[float, float]]) -> float:
        """
        Calculate polygon area using the Shoelace formula (Gauss's Area Formula).
        A = 0.5 * |sum_{i=0}^{n-1} (x_i * y_{i+1} - x_{i+1} * y_i)|
        
        Args:
            points: List of (x, y) coordinates forming a closed polygon.
            
        Returns:
            Absolute area in squared coordinate units.
        """
        n = len(points)
        if n < 3:
            return 0.0

        pts = np.array(points, dtype=np.float64)
        x = pts[:, 0]
        y = pts[:, 1]

        # Shift arrays by 1 to compute cross product terms
        area = 0.5 * np.abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
        return float(area)

    @staticmethod
    def polygon_perimeter(points: List[Tuple[float, float]]) -> float:
        """
        Calculate perimeter of closed polygon by summing Euclidean segment lengths.
        
        Args:
            points: List of (x, y) coordinates.
            
        Returns:
            Perimeter in coordinate units.
        """
        n = len(points)
        if n < 2:
            return 0.0

        pts = np.array(points, dtype=np.float64)
        next_pts = np.roll(pts, -1, axis=0)
        distances = np.linalg.norm(next_pts - pts, axis=1)
        return float(np.sum(distances))

    @staticmethod
    def polygon_centroid(points: List[Tuple[float, float]]) -> Tuple[float, float]:
        """
        Calculate polygon centroid (center of mass).
        
        Args:
            points: List of (x, y) coordinates.
            
        Returns:
            (Cx, Cy) tuple.
        """
        n = len(points)
        if n < 3:
            if n == 0:
                return (0.0, 0.0)
            pts = np.array(points, dtype=np.float64)
            return (float(np.mean(pts[:, 0])), float(np.mean(pts[:, 1])))

        pts = np.array(points, dtype=np.float64)
        x = pts[:, 0]
        y = pts[:, 1]

        # Signed Shoelace area
        cross = x * np.roll(y, -1) - np.roll(x, -1) * y
        signed_area = 0.5 * np.sum(cross)

        if abs(signed_area) < 1e-12:
            return (float(np.mean(x)), float(np.mean(y)))

        cx = (1.0 / (6.0 * signed_area)) * np.sum((x + np.roll(x, -1)) * cross)
        cy = (1.0 / (6.0 * signed_area)) * np.sum((y + np.roll(y, -1)) * cross)
        return (float(cx), float(cy))

    @staticmethod
    def _segments_intersect(p1: Tuple[float, float], p2: Tuple[float, float],
                            p3: Tuple[float, float], p4: Tuple[float, float]) -> bool:
        """
        Check if line segment p1-p2 strictly intersects with p3-p4.
        """
        def ccw(a, b, c):
            return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])

        # Exclude shared endpoints
        if (p1 == p3 or p1 == p4 or p2 == p3 or p2 == p4):
            return False

        # CCW intersection test
        return (ccw(p1, p3, p4) != ccw(p2, p3, p4)) and (ccw(p1, p2, p3) != ccw(p1, p2, p4))

    @classmethod
    def validate_polygon(cls, points: List[Tuple[float, float]]) -> Dict[str, Any]:
        """
        Validate polygon for minimum vertex count, non-zero area, and self-intersections.
        
        Returns:
            Dictionary with 'is_valid' (bool), 'errors' (list of str), 'warnings' (list of str).
        """
        errors = []
        warnings = []
        n = len(points)

        if n < 3:
            errors.append(f"Insufficient vertices: Polygon has only {n} point(s). Minimum 3 required.")
            return {"is_valid": False, "errors": errors, "warnings": warnings}

        area = cls.shoelace_area(points)
        if area < 1e-7:
            errors.append("Collinear or zero-area polygon detected.")

        # Check self-intersection between edges
        intersections = []
        for i in range(n):
            p1, p2 = points[i], points[(i + 1) % n]
            for j in range(i + 1, n):
                # Don't check adjacent edges or same edge
                if abs(i - j) <= 1 or (i == 0 and j == n - 1):
                    continue
                p3, p4 = points[j], points[(j + 1) % n]
                if cls._segments_intersect(p1, p2, p3, p4):
                    intersections.append((i, j))

        if intersections:
            errors.append(f"Self-intersecting polygon detected at {len(intersections)} edge pair(s).")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "vertex_count": n,
            "raw_area": area,
            "has_self_intersections": len(intersections) > 0,
            "intersection_pairs": intersections
        }

    @staticmethod
    def transform_pixels_to_cad(points_px: List[Tuple[float, float]],
                                scale_factor: float,
                                image_height: float,
                                origin_mode: str = "bottom_left") -> List[Tuple[float, float]]:
        """
        Convert image pixel coordinates to CAD Cartesian coordinates.
        Image coords: (0, 0) is top-left, Y increases downwards.
        CAD coords: (0, 0) is bottom-left, Y increases upwards.
        
        Args:
            points_px: List of (x_px, y_px) in image pixels.
            scale_factor: Real units per pixel (e.g. meters/pixel).
            image_height: Image height in pixels.
            origin_mode: 'bottom_left' or 'centroid'.
            
        Returns:
            List of (X_cad, Y_cad) in real-world units.
        """
        cad_points = []
        for x_px, y_px in points_px:
            x_cad = x_px * scale_factor
            y_cad = (image_height - y_px) * scale_factor
            cad_points.append((float(x_cad), float(y_cad)))

        if origin_mode == "centroid" and len(cad_points) >= 3:
            pts = np.array(cad_points)
            cx, cy = np.mean(pts[:, 0]), np.mean(pts[:, 1])
            cad_points = [(p[0] - cx, p[1] - cy) for p in cad_points]

        return cad_points

    @staticmethod
    def transform_cad_to_pixels(points_cad: List[Tuple[float, float]],
                                scale_factor: float,
                                image_height: float) -> List[Tuple[float, float]]:
        """
        Convert CAD Cartesian coordinates back to image pixel coordinates.
        """
        if scale_factor <= 0:
            return points_cad
        px_points = []
        for x_cad, y_cad in points_cad:
            x_px = x_cad / scale_factor
            y_px = image_height - (y_cad / scale_factor)
            px_points.append((float(x_px), float(y_px)))
        return px_points
