import unittest

from accessible_palette.color import (
    ColorError,
    RGB,
    contrast_ratio,
    hsl_to_rgb,
    parse_color,
    relative_luminance,
    rgb_distance,
    rgb_to_hsl,
    to_linear,
    to_srgb,
)


class TestParse(unittest.TestCase):
    def test_hex_forms(self):
        self.assertEqual(parse_color("#FFFFFF"), RGB(255, 255, 255))
        self.assertEqual(parse_color("ffffff"), RGB(255, 255, 255))
        self.assertEqual(parse_color("#fff"), RGB(255, 255, 255))
        self.assertEqual(parse_color("000"), RGB(0, 0, 0))
        self.assertEqual(parse_color("#1A2B3C"), RGB(0x1A, 0x2B, 0x3C))

    def test_rgb_functional(self):
        self.assertEqual(parse_color("rgb(255, 0, 16)"), RGB(255, 0, 16))
        self.assertEqual(parse_color("rgb(10 20 30)"), RGB(10, 20, 30))
        self.assertEqual(parse_color("rgba(1,2,3,0.5)"), RGB(1, 2, 3))

    def test_hsl_functional(self):
        self.assertEqual(parse_color("hsl(0, 0%, 0%)"), RGB(0, 0, 0))
        self.assertEqual(parse_color("hsl(120, 100%, 100%)"), RGB(255, 255, 255))
        red = parse_color("hsl(0, 100%, 50%)")
        self.assertEqual((red.r, red.g, red.b), (255, 0, 0))

    def test_invalid(self):
        for bad in ("", "nope", "#12", "#12345", "rgb(256,0,0)", "hsl(0,101%,0%)"):
            with self.assertRaises(ColorError):
                parse_color(bad)


class TestLuminance(unittest.TestCase):
    def test_bounds(self):
        self.assertAlmostEqual(relative_luminance(RGB(0, 0, 0)), 0.0)
        self.assertAlmostEqual(relative_luminance(RGB(255, 255, 255)), 1.0, places=6)

    def test_linear_roundtrip(self):
        for value in (0, 13, 74, 128, 200, 255):
            self.assertEqual(int(to_srgb(to_linear(value))), value)

    def test_green_dominates(self):
        self.assertGreater(
            relative_luminance(RGB(0, 255, 0)),
            relative_luminance(RGB(255, 0, 0)),
        )


class TestContrast(unittest.TestCase):
    def test_black_on_white(self):
        self.assertAlmostEqual(contrast_ratio(RGB(0, 0, 0), RGB(255, 255, 255)), 21.0)

    def test_same_color(self):
        self.assertAlmostEqual(contrast_ratio(RGB(100, 100, 100), RGB(100, 100, 100)), 1.0)

    def test_order_independent(self):
        a = RGB(30, 30, 30)
        b = RGB(220, 220, 220)
        self.assertAlmostEqual(contrast_ratio(a, b), contrast_ratio(b, a))

    def test_known_value(self):
        ratio = contrast_ratio(RGB(0x77, 0x77, 0x77), RGB(255, 255, 255))
        self.assertAlmostEqual(ratio, 4.48, places=1)


class TestHslRoundtrip(unittest.TestCase):
    def test_roundtrip(self):
        for rgb in (RGB(12, 200, 90), RGB(250, 100, 3), RGB(128, 128, 128)):
            h, s, l = rgb_to_hsl(rgb)
            self.assertEqual(hsl_to_rgb(h, s, l), rgb)

    def test_distance(self):
        self.assertAlmostEqual(rgb_distance(RGB(0, 0, 0), RGB(3, 4, 0)), 5.0)

    def test_hue_wrap(self):
        self.assertEqual(
            hsl_to_rgb(370, 100, 50), hsl_to_rgb(10, 100, 50)
        )
        self.assertEqual(
            hsl_to_rgb(-10, 100, 50), hsl_to_rgb(350, 100, 50)
        )


if __name__ == "__main__":
    unittest.main()
