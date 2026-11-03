import unittest

from accessible_palette.color import RGB
from accessible_palette.simulate import SIMULATION_NAMES, simulate


class TestSimulate(unittest.TestCase):
    def test_names(self):
        self.assertEqual(
            set(SIMULATION_NAMES),
            {"protanopia", "deuteranopia", "tritanopia", "achromatopsia"},
        )

    def test_output_in_range(self):
        for name in SIMULATION_NAMES:
            for rgb in (RGB(200, 40, 10), RGB(10, 200, 40), RGB(40, 10, 200)):
                out = simulate(rgb, name)
                for channel in (out.r, out.g, out.b):
                    self.assertTrue(0 <= channel <= 255)

    def test_unknown_raises(self):
        with self.assertRaises(ValueError):
            simulate(RGB(1, 2, 3), "nope-not-real")

    def test_achromatopsia_is_gray(self):
        out = simulate(RGB(200, 40, 10), "achromatopsia")
        self.assertEqual(out.r, out.g)
        self.assertEqual(out.g, out.b)

    def test_white_stays_white(self):
        for name in SIMULATION_NAMES:
            self.assertEqual(
                simulate(RGB(255, 255, 255), name), RGB(255, 255, 255)
            )

    def test_deuteranopia_dulls_green(self):
        green = RGB(60, 180, 50)
        out = simulate(green, "deuteranopia")
        self.assertGreater(out.r, green.r)


if __name__ == "__main__":
    unittest.main()
