import json
import tempfile
import os
import unittest
from pathlib import Path

from accessible_palette.color import RGB
from accessible_palette.report import (
    build_report,
    report_to_html,
    report_to_json,
)


def sample_report():
    return build_report(
        title="Sample",
        colors=[{"rgb": RGB(0, 0, 0), "name": "Ink"}, {"rgb": RGB(0x77, 0x77, 0x77)}],
        background=RGB(255, 255, 255),
        simulations=("achromatopsia",),
    )


class TestBuildReport(unittest.TestCase):
    def test_structure(self):
        report = sample_report()
        self.assertEqual(report["title"], "Sample")
        self.assertEqual(report["background"], "#FFFFFF")
        self.assertEqual(report["simulations"], ["achromatopsia"])
        self.assertEqual(len(report["pairs"]), 2)

    def test_pair_fields(self):
        pair = sample_report()["pairs"][0]
        self.assertEqual(pair["name"], "Ink")
        self.assertEqual(pair["text"], "#000000")
        self.assertAlmostEqual(pair["ratio"], 21.0)
        self.assertIn("AA-normal", pair["checks"])
        self.assertTrue(pair["checks"]["AA-normal"]["passes"])

    def test_simulations_included(self):
        pair = sample_report()["pairs"][1]
        self.assertIn("achromatopsia", pair["simulations"])
        sim_pair = pair["simulations"]["achromatopsia"]
        self.assertEqual(len(sim_pair["checks"]), len(pair["checks"]))

    def test_json_roundtrip(self):
        report = sample_report()
        parsed = json.loads(report_to_json(report))
        self.assertEqual(parsed["title"], report["title"])

    def test_html_contains_content(self):
        html = report_to_html(sample_report())
        self.assertIn("#777777", html)
        self.assertIn("FAIL", html)
        self.assertIn("PASS", html)
        self.assertIn("achromatopsia", html)
        self.assertIn("Asdale Dynamics, LLC", html)


class TestFiles(unittest.TestCase):
    def test_writable(self):
        report = sample_report()
        with tempfile.TemporaryDirectory() as tmp:
            json_path = Path(tmp) / "report.json"
            html_path = Path(tmp) / "report.html"
            json_path.write_text(report_to_json(report), encoding="utf-8")
            html_path.write_text(report_to_html(report), encoding="utf-8")
            self.assertTrue(json_path.stat().st_size > 0)
            self.assertTrue(html_path.stat().st_size > 0)


if __name__ == "__main__":
    unittest.main()
