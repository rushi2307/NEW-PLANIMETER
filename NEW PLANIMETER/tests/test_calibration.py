"""
Unit tests for Scale Calibration Engine.
"""

import unittest
from core.calibration import ScaleCalibration, UnitManager


class TestCalibration(unittest.TestCase):

    def test_2point_calibration(self):
        cal = ScaleCalibration()
        # Reference line from (100, 100) to (500, 100) => dx = 400px
        # Known real distance = 20.0 meters => scale = 20 / 400 = 0.05 m/px
        scale = cal.calibrate_2point((100.0, 100.0), (500.0, 100.0), 20.0, unit="m")
        self.assertAlmostEqual(scale, 0.05, places=6)
        self.assertTrue(cal.is_calibrated)
        self.assertEqual(cal.unit, "m")

        # Check conversion: 200px length = 10m
        self.assertAlmostEqual(cal.pixels_to_real_length(200.0), 10.0, places=6)
        # Check area conversion: 40000 px^2 = 40000 * 0.0025 = 100 m^2
        self.assertAlmostEqual(cal.pixels_to_real_area(40000.0), 100.0, places=6)

    def test_multipoint_calibration(self):
        cal = ScaleCalibration()
        # 3 reference lines
        pairs = [
            ((0.0, 0.0), (200.0, 0.0)),   # 200 px -> 10 m (0.05)
            ((0.0, 0.0), (0.0, 400.0)),   # 400 px -> 20 m (0.05)
            ((100.0, 100.0), (300.0, 100.0))  # 200 px -> 10 m (0.05)
        ]
        dists = [10.0, 20.0, 10.0]
        scale = cal.calibrate_multipoint(pairs, dists, unit="m")
        self.assertAlmostEqual(scale, 0.05, places=5)

    def test_unit_conversions(self):
        # 1 meter = 3.28084 feet
        feet = UnitManager.convert_length(1.0, "m", "ft")
        self.assertAlmostEqual(feet, 3.280839895, places=4)

        # 10000 m^2 = 1 hectare
        ha = UnitManager.convert_area_from_linear(10000.0, "m", "hectares")
        self.assertAlmostEqual(ha, 1.0, places=4)

        # 4046.8564224 m^2 = 1 acre
        ac = UnitManager.convert_area_from_linear(4046.8564224, "m", "acres")
        self.assertAlmostEqual(ac, 1.0, places=3)


if __name__ == "__main__":
    unittest.main()
