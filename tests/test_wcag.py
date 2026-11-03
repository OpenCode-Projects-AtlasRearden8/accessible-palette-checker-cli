import unittest

from accessible_palette.color import RGB
from accessible_palette.wcag import (
    AAA_NORMAL,
    AA_NORMAL,
    evaluate_pair,
)


class TestEvaluatePair(unittest.TestCase):
    def test_perfect_pair(self):
        result = evaluate_pair(RGB(0, 0, 0), RGB(255, 255, 255))
        self.assertAlmostEqual(result["ratio"], 21.0)
        for checks in result["checks"].values():
            self.assertTrue(checks["passes"])

    def test_identical_colors_fail(self):
        result = evaluate_pair(RGB(64, 64, 64), RGB(64, 64, 64))
        self.assertAlmostEqual(result["ratio"], 1.0)
        for checks in result["checks"].values():
            self.assertFalse(checks["passes"])

    def test_thresholds_present(self):
        result = evaluate_pair(RGB(0, 0, 0), RGB(255, 255, 255))
        self.assertEqual(result["checks"]["AA-normal"]["threshold"], AA_NORMAL)
        self.assertEqual(result["checks"]["AAA-normal"]["threshold"], AAA_NORMAL)
        self.assertIn("ui-component", result["checks"])

    def test_gray_770(self):
        result = evaluate_pair(RGB(0x77, 0x77, 0x77), RGB(255, 255, 255))
        self.assertFalse(result["checks"]["AA-normal"]["passes"])
        self.assertTrue(result["checks"]["AA-large"]["passes"])
        self.assertTrue(result["checks"]["ui-component"]["passes"])


if __name__ == "__main__":
    unittest.main()
