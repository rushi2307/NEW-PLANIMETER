"""
Contour Detection & Vectorization Engine for New Planimeter
Extracts closed boundaries, approximates contours to polygonal vertices (Douglas-Peucker),
and provides point-in-polygon selection for Semi-Automatic measurement mode.
"""

from typing import List, Tuple, Dict, Any, Optional
import cv2
import numpy as np
from core.geometry_engine import GeometryEngine


class ContourCandidate:
    """
    Represents a detected candidate boundary with metadata and polygon approximation.
    """

    def __init__(self, raw_contour: np.ndarray, index: int,
                 epsilon_percent: float = 1.0, total_image_area: float = 1.0):
        self.index = index
        self.raw_contour = raw_contour
        self.raw_area = float(cv2.contourArea(raw_contour))
        self.raw_perimeter = float(cv2.arcLength(raw_contour, True))
        self.area_ratio = (self.raw_area / total_image_area) if total_image_area > 0 else 0.0

        # Bounding box & centroid
        x, y, w, h = cv2.boundingRect(raw_contour)
        self.bounding_rect = (x, y, w, h)

        M = cv2.moments(raw_contour)
        if M["m00"] != 0:
            self.centroid = (float(M["m10"] / M["m00"]), float(M["m01"] / M["m00"]))
        else:
            self.centroid = (float(x + w / 2), float(y + h / 2))

        # Convexity & solidity
        hull = cv2.convexHull(raw_contour)
        hull_area = cv2.contourArea(hull)
        self.solidity = float(self.raw_area / hull_area) if hull_area > 0 else 0.0

        # Douglas-Peucker Polygon Approximation
        self.polygon_points: List[Tuple[float, float]] = []
        self.update_approximation(epsilon_percent)

    def update_approximation(self, epsilon_percent: float = 1.0):
        """
        Approximate contour to polygon using Douglas-Peucker algorithm.
        epsilon = epsilon_percent % of contour perimeter.
        """
        if self.raw_perimeter <= 0:
            self.polygon_points = []
            return

        epsilon = (epsilon_percent / 100.0) * self.raw_perimeter
        epsilon = max(0.5, epsilon)
        approx = cv2.approxPolyDP(self.raw_contour, epsilon, True)

        pts = []
        for pt in approx:
            x, y = pt[0]
            pts.append((float(x), float(y)))

        self.polygon_points = pts


class ContourDetector:
    """
    Detection and vectorization engine for plot boundaries.
    """

    @classmethod
    def find_all_candidates(cls, binary_img: np.ndarray,
                            min_area_px: float = 100.0,
                            max_area_ratio: float = 0.80,
                            epsilon_percent: float = 1.0) -> List[ContourCandidate]:
        """
        Extract all closed contour candidates from a binary image.
        """
        h, w = binary_img.shape[:2]
        total_img_area = float(h * w)

        # RETR_TREE captures all internal and external closed shapes
        contours, hierarchy = cv2.findContours(binary_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        candidates = []
        for i, cnt in enumerate(contours):
            area = cv2.contourArea(cnt)
            # Filter tiny noise specks and image border frames
            if area < min_area_px:
                continue
            if total_img_area > 0 and (area / total_img_area) > max_area_ratio:
                continue

            # Check bounding box to filter out border rectangles
            bx, by, bw, bh = cv2.boundingRect(cnt)
            if (bw / float(w)) > 0.85 and (bh / float(h)) > 0.85:
                continue

            candidate = ContourCandidate(
                raw_contour=cnt,
                index=len(candidates),
                epsilon_percent=epsilon_percent,
                total_image_area=total_img_area
            )

            # Keep if polygon has at least 3 points
            if len(candidate.polygon_points) >= 3:
                candidates.append(candidate)

        # Sort candidates descending by area (largest plot candidate first)
        candidates.sort(key=lambda c: c.raw_area, reverse=True)
        for i, c in enumerate(candidates):
            c.index = i

        return candidates

    @classmethod
    def find_candidate_at_point(cls, candidates: List[ContourCandidate],
                                click_x: float, click_y: float) -> Optional[ContourCandidate]:
        """
        Semi-Automatic selection: finds the smallest enclosing candidate contour
        or closest contour to the user's click coordinate.
        """
        enclosing_candidates = []

        for candidate in candidates:
            # cv2.pointPolygonTest returns > 0 inside, == 0 on edge, < 0 outside
            dist = cv2.pointPolygonTest(candidate.raw_contour, (float(click_x), float(click_y)), False)
            if dist >= 0:
                enclosing_candidates.append(candidate)

        if enclosing_candidates:
            # Return the tightest (smallest enclosing) candidate for precise region selection
            enclosing_candidates.sort(key=lambda c: c.raw_area)
            return enclosing_candidates[0]

        # If click wasn't inside any contour, find the candidate with minimum distance to click
        closest_candidate = None
        min_dist = float("inf")
        for candidate in candidates:
            dist = abs(cv2.pointPolygonTest(candidate.raw_contour, (float(click_x), float(click_y)), True))
            if dist < min_dist:
                min_dist = dist
                closest_candidate = candidate

        return closest_candidate
