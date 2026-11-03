import unittest

from accessible_palette.color import ColorError, contrast_ratio, parse_color
from accessible_palette.suggest import suggest, target_threshold
from accessible_palette.wcag import AA_NORMAL


class TestSuggest(unittest.TestCase):
    def test_already_passing_returns_none(self):
        self.assertIsNone(suggest("#000000", "#FFFFFF"))

    def test_suggestion_passes_target(self):
        result = suggest("#7AB648", "#FFFFFF", target="aa-normal")
        self.assertIsNotNone(result)
        suggested = parse_color(result["suggested"])
        self.assertGreaterEqual(contrast_ratio(suggested, parse_color("#FFFFFF")), AA_NORMAL)

    def test_known_gray_gets_suggested(self):
        result = suggest("#777777", "#FFFFFF")
        self.assertEqual(result["original"], "#777777")
        self.assertEqual(result["threshold"], 4.5)
        self.assertGreaterEqual(result["ratio"], 4.5)

    def test_dark_background_darkens_text(self):
        result = suggest("#5B8DEF", "#1B2A41", target="aa-normal")
        self.assertIsNotNone(result)
        self.assertGreaterEqual(result["ratio"], 4.5)

    def test_target_lookup(self):
        self.assertEqual(target_threshold("aa-normal"), 4.5)
        self.assertEqual(target_threshold("ui-component"), 3.0)
        with self.assertRaises(ValueError):
            target_threshold("bogus")

    def test_impossible_request_raises(self):
        with self.assertRaises(ColorError):
            suggest("#FF0000", "#FFFFFF", target="aaa-normal", max_distance=1.0)
