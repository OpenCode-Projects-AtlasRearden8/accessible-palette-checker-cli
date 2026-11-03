import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

PALETTE = {
    "title": "Flyer palette",
    "background": "#FFFFFF",
    "simulations": ["protanopia", "deuteranopia"],
    "colors": [
        {"hex": "#1B1B3A", "name": "Ink"},
        {"hex": "#777777"},
        {"hex": "#E4572E", "name": "Accent"},
    ],
}


def run_cli(*args, stdin=None):
    return subprocess.run(
        [sys.executable, "-m", "accessible_palette", *args],
        capture_output=True,
        text=True,
        cwd=REPO,
        env={**os.environ, "PYTHONPATH": str(REPO)},
        input=stdin,
    )


class TestCliContrast(unittest.TestCase):
    def test_passing_pair(self):
        result = run_cli("contrast", "#000000", "#FFFFFF")
        self.assertEqual(result.returncode, 0)
        self.assertIn("PASS", result.stdout)
        self.assertIn("21", result.stdout)

    def test_failing_pair_exit_code(self):
        result = run_cli("contrast", "#777777", "#FFFFFF")
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL", result.stdout)

    def test_json_output(self):
        result = run_cli("contrast", "#000000", "#FFFFFF", "--json")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["text"], "#000000")
        self.assertTrue(payload["checks"]["AAA-normal"]["passes"])

    def test_simulation_flag(self):
        result = run_cli("contrast", "#000000", "#FFFFFF", "--simulate", "protanopia")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("protanopia", result.stdout)

    def test_bad_color_is_error(self):
        result = run_cli("contrast", "not-a-color", "#FFFFFF")
        self.assertEqual(result.returncode, 2)
        self.assertIn("error", result.stderr)

    def test_bad_simulation_is_error(self):
        result = run_cli("contrast", "#000000", "#FFFFFF", "--simulate", "wat")
        self.assertEqual(result.returncode, 2)


class TestCliPalette(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.palette_path = Path(self.tmp.name) / "palette.json"
        self.palette_path.write_text(json.dumps(PALETTE), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_palette_exports(self):
        html_path = Path(self.tmp.name) / "out.html"
        json_out = Path(self.tmp.name) / "out.json"
        result = run_cli(
            "palette",
            str(self.palette_path),
            "--html",
            str(html_path),
            "--json-out",
            str(json_out),
        )
        self.assertIn("Palette: Flyer palette", result.stdout)
        self.assertTrue(html_path.exists())
        data = json.loads(json_out.read_text(encoding="utf-8"))
        self.assertEqual(data["title"], "Flyer palette")
        self.assertEqual(len(data["pairs"]), 3)
        html = html_path.read_text(encoding="utf-8")
        self.assertIn("#1B1B3A", html)
        self.assertIn("protanopia", html)

    def test_stdout_palette(self):
        passing = {**PALETTE, "colors": [{"hex": "#1B1B3A", "name": "Ink"}]}
        result = run_cli(
            "palette", "-", "--json-out", str(Path(self.tmp.name) / "o.json"),
            stdin=json.dumps(passing),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Flyer palette", result.stdout)
        self.assertIn("PASS", result.stdout)

    def test_invalid_palette(self):
        result = run_cli("palette", "-", stdin='{"colors": []}')
        self.assertEqual(result.returncode, 2)

    def test_missing_file(self):
        result = run_cli("palette", "does-not-exist.json")
        self.assertEqual(result.returncode, 2)


class TestCliSuggest(unittest.TestCase):
    def test_suggest_passing(self):
        result = run_cli("suggest", "#777777", "#FFFFFF")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Suggested", result.stdout)
        hex_line = [ln for ln in result.stdout.splitlines() if "Suggested" in ln][0]
        suggested = hex_line.split()[1]
        self.assertTrue(suggested.startswith("#"))

    def test_already_passes(self):
        result = run_cli("suggest", "#000000", "#FFFFFF", "--target", "aaa-normal")
        self.assertEqual(result.returncode, 0)
        self.assertIn("already passes", result.stdout)

    def test_fc7a20(self):
        result = run_cli("suggest", "#7AB648", "#FFFFFF", "--json")
        self.assertEqual(result.returncode, 0)

    def test_version(self):
        result = run_cli("--version")
        self.assertEqual(result.returncode, 0)
        self.assertIn("accessible-palette", result.stdout)


if __name__ == "__main__":
    unittest.main()
