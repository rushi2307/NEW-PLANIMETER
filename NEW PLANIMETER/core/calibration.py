"""
Scale Calibration Engine for New Planimeter
Handles 2-point known reference calibration, multi-point calibration,
pixel-to-real-world scale factor calculation, and multi-unit conversions.
"""

from typing import List, Tuple, Dict, Any, Optional
import math
import numpy as np


class UnitManager:
    """
    Manages linear and area units with accurate engineering conversion factors.
    Base linear unit: meters (m).
    Base area unit: square meters (m^2).
    """

    # Multipliers to convert unit to METERS
    LINEAR_TO_METERS = {
        "mm": 0.001,
        "cm": 0.01,
        "m": 1.0,
        "km": 1000.0,
        "in": 0.0254,
        "ft": 0.3048,
        "yd": 0.9144,
    }

    # Display names
    LINEAR_NAMES = {
        "mm": "Millimeters (mm)",
        "cm": "Centimeters (cm)",
        "m": "Meters (m)",
        "km": "Kilometers (km)",
        "in": "Inches (in)",
        "ft": "Feet (ft)",
        "yd": "Yards (yd)",
    }

    # Area conversions: factor from (base linear unit)^2 to target area unit
    AREA_UNITS = {
        "m": [("m²", 1.0), ("hectares (ha)", 0.0001), ("acres", 0.000247105), ("km²", 0.000001)],
        "cm": [("cm²", 1.0), ("m²", 0.0001)],
        "mm": [("mm²", 1.0), ("cm²", 0.01), ("m²", 0.000001)],
        "ft": [("ft²", 1.0), ("acres", 1.0 / 43560.0), ("yd²", 1.0 / 9.0)],
        "in": [("in²", 1.0), ("ft²", 1.0 / 144.0)],
        "yd": [("yd²", 1.0), ("ft²", 9.0), ("acres", 1.0 / 4840.0)],
    }

    @classmethod
    def convert_length(cls, value: float, from_unit: str, to_unit: str) -> float:
        if from_unit not in cls.LINEAR_TO_METERS or to_unit not in cls.LINEAR_TO_METERS:
            raise ValueError(f"Unsupported unit: {from_unit} or {to_unit}")
        meters = value * cls.LINEAR_TO_METERS[from_unit]
        return meters / cls.LINEAR_TO_METERS[to_unit]

    @classmethod
    def convert_area_from_linear(cls, area_in_linear_sq: float, linear_unit: str, target_area_unit: str) -> float:
        """
        Convert area (given in linear_unit^2) to a target area unit.
        """
        # First to m^2
        factor_to_m = cls.LINEAR_TO_METERS.get(linear_unit, 1.0)
        area_m2 = area_in_linear_sq * (factor_to_m ** 2)

        if target_area_unit == "m²":
            return area_m2
        elif target_area_unit == "hectares" or target_area_unit == "ha":
            return area_m2 / 10000.0
        elif target_area_unit == "acres" or target_area_unit == "ac":
            return area_m2 * 0.000247105381
        elif target_area_unit == "ft²" or target_area_unit == "sq ft":
            return area_m2 / (0.3048 ** 2)
        elif target_area_unit == "yd²" or target_area_unit == "sq yd":
            return area_m2 / (0.9144 ** 2)
        elif target_area_unit == "in²" or target_area_unit == "sq in":
            return area_m2 / (0.0254 ** 2)
        elif target_area_unit == "cm²":
            return area_m2 * 10000.0
        elif target_area_unit == "mm²":
            return area_m2 * 1000000.0
        elif target_area_unit == "km²":
            return area_m2 / 1000000.0
        return area_in_linear_sq


class ScaleCalibration:
    """
    Stores and computes scale calibration for 2D plans.
    """

    def __init__(self, scale_factor: float = 1.0, unit: str = "m"):
        """
        Args:
            scale_factor: Real-world units per pixel (e.g. 0.05 meters per pixel).
            unit: 'm', 'ft', 'cm', 'mm', 'in', etc.
        """
        self.scale_factor: float = scale_factor
        self.unit: str = unit
        self.reference_points: List[Tuple[float, float]] = []
        self.known_distance: float = 0.0
        self.pixel_distance: float = 0.0
        self.is_calibrated: bool = False
        self.calibration_type: str = "default"  # '2-point', 'multi-point', 'manual'

    def calibrate_2point(self, p1: Tuple[float, float], p2: Tuple[float, float],
                         known_distance: float, unit: str = "m") -> float:
        """
        Perform 2-point scale calibration using a known reference line.
        
        Args:
            p1: First reference point in image pixels (x, y).
            p2: Second reference point in image pixels (x, y).
            known_distance: Real-world length between p1 and p2.
            unit: Unit of measurement ('m', 'ft', etc.).
            
        Returns:
            Scale factor (real-world units / pixel).
        """
        if known_distance <= 0:
            raise ValueError("Known distance must be positive.")

        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        px_dist = math.hypot(dx, dy)

        if px_dist < 1e-4:
            raise ValueError("Reference points are too close together in pixel space.")

        self.scale_factor = float(known_distance / px_dist)
        self.unit = unit
        self.reference_points = [p1, p2]
        self.known_distance = known_distance
        self.pixel_distance = px_dist
        self.is_calibrated = True
        self.calibration_type = "2-point"

        return self.scale_factor

    def calibrate_multipoint(self, point_pairs: List[Tuple[Tuple[float, float], Tuple[float, float]]],
                             known_distances: List[float], unit: str = "m") -> float:
        """
        Perform multi-point calibration via least squares average across multiple reference bars.
        
        Args:
            point_pairs: List of ((x1, y1), (x2, y2)) pixel coordinate pairs.
            known_distances: List of corresponding real-world lengths.
            unit: Real-world unit string.
            
        Returns:
            Optimized scale factor.
        """
        if len(point_pairs) != len(known_distances) or len(point_pairs) == 0:
            raise ValueError("Point pairs and known distances lists must have matching non-zero lengths.")

        pixel_dists = []
        real_dists = []

        for ((p1x, p1y), (p2x, p2y)), d_real in zip(point_pairs, known_distances):
            if d_real <= 0:
                continue
            d_px = math.hypot(p2x - p1x, p2y - p1y)
            if d_px > 1e-4:
                pixel_dists.append(d_px)
                real_dists.append(d_real)

        if not pixel_dists:
            raise ValueError("No valid calibration pairs provided.")

        # Least-squares fit: real_d = scale * pixel_d => scale = sum(pixel_d * real_d) / sum(pixel_d^2)
        px_arr = np.array(pixel_dists)
        real_arr = np.array(real_dists)
        optimal_scale = float(np.sum(px_arr * real_arr) / np.sum(px_arr ** 2))

        self.scale_factor = optimal_scale
        self.unit = unit
        self.is_calibrated = True
        self.calibration_type = "multi-point"
        return self.scale_factor

    def pixels_to_real_length(self, pixel_length: float) -> float:
        return pixel_length * self.scale_factor

    def pixels_to_real_area(self, pixel_area: float) -> float:
        return pixel_area * (self.scale_factor ** 2)

    def real_to_pixels_length(self, real_length: float) -> float:
        if self.scale_factor <= 0:
            return real_length
        return real_length / self.scale_factor

    def get_summary(self) -> Dict[str, Any]:
        return {
            "scale_factor": self.scale_factor,
            "unit": self.unit,
            "is_calibrated": self.is_calibrated,
            "calibration_type": self.calibration_type,
            "reference_points": self.reference_points,
            "known_distance": self.known_distance,
            "pixel_distance": self.pixel_distance,
            "pixels_per_unit": (1.0 / self.scale_factor) if self.scale_factor > 0 else 0.0
        }
