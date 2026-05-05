"""
Validation tests for the crop-circle-engineer pipeline.
Run with: crop-circle-env/bin/python -m unittest tests.test_pipeline -v
"""
import unittest
import os
import math


class TestPipeline(unittest.TestCase):

    # ------------------------------------------------------------------
    # 1. px_to_meters basic
    # ------------------------------------------------------------------
    def test_px_to_meters_basic(self):
        """px_to_meters(px, dpi=96.0): 100px / 96 * 0.0254 ≈ 0.026458 m"""
        from utils.geometry import px_to_meters
        expected = 100 / 96.0 * 0.0254
        self.assertAlmostEqual(px_to_meters(100), expected, places=5)

    # ------------------------------------------------------------------
    # 2. Baudo mapper smoke
    # ------------------------------------------------------------------
    def test_baudo_mapper_smoke(self):
        """map_baudo_geometry returns a dict with 'rotor_discs' key."""
        from modules.baudo_mapper import map_baudo_geometry

        # circles are (x, y, radius) tuples — matching the real Circle type
        circles = [
            (100.0, 100.0, 5.0),   # smallest → eccentric nucleus
            (100.0, 100.0, 95.0),  # middle → rotor disc
            (100.0, 100.0, 190.0), # largest → counterweight
        ]
        result = map_baudo_geometry(circles)
        self.assertIsInstance(result, dict)
        self.assertIn("rotor_discs", result)
        self.assertGreaterEqual(len(result["rotor_discs"]), 1)

    # ------------------------------------------------------------------
    # 3. Physics simulation smoke
    # ------------------------------------------------------------------
    def test_physics_sim_smoke(self):
        """run_simulation returns expected keys and non-empty time array."""
        from modules.baudo_mapper import map_baudo_geometry
        from modules.physics_sim import run_simulation

        circles = [
            (100.0, 100.0, 5.0),
            (100.0, 100.0, 95.0),
            (100.0, 100.0, 190.0),
        ]
        baudo_params = map_baudo_geometry(circles)
        result = run_simulation(baudo_params, duration_s=1.0, dt=0.1, gravity=False)

        for key in ("t", "rpm", "energy", "peak_rpm"):
            self.assertIn(key, result)
        self.assertGreater(len(result["t"]), 0)

    # ------------------------------------------------------------------
    # 4. Resonance curve smoke
    # ------------------------------------------------------------------
    def test_resonance_curve_smoke(self):
        """compute_resonance_curve returns rpm/amplitude/resonance_rpm with correct length."""
        from modules.baudo_mapper import map_baudo_geometry
        from modules.physics_sim import compute_resonance_curve

        circles = [
            (100.0, 100.0, 5.0),
            (100.0, 100.0, 95.0),
            (100.0, 100.0, 190.0),
        ]
        baudo_params = map_baudo_geometry(circles)
        result = compute_resonance_curve(baudo_params, steps=10)

        for key in ("rpm", "amplitude", "resonance_rpm"):
            self.assertIn(key, result)
        self.assertEqual(len(result["rpm"]), 10)

    # ------------------------------------------------------------------
    # 5. Export CSV
    # ------------------------------------------------------------------
    def test_export_csv(self):
        """export_sim_csv writes a non-empty file to the given path."""
        from modules.baudo_mapper import map_baudo_geometry
        from modules.physics_sim import run_simulation, export_sim_csv

        circles = [
            (100.0, 100.0, 5.0),
            (100.0, 100.0, 95.0),
            (100.0, 100.0, 190.0),
        ]
        baudo_params = map_baudo_geometry(circles)
        sim_result = run_simulation(baudo_params, duration_s=1.0, dt=0.1, gravity=False)

        out_path = "/tmp/test_crop_sim.csv"
        export_sim_csv(sim_result, out_path)

        self.assertTrue(os.path.exists(out_path))
        self.assertGreater(os.path.getsize(out_path), 0)

        os.remove(out_path)


if __name__ == "__main__":
    unittest.main()
