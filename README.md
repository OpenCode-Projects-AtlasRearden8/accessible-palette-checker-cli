# Accessible Palette Checker

A tiny, pure-Python command-line tool that checks color palettes for **WCAG
AA/AAA contrast** and simulates how they look to people with **color vision
deficiencies** — no browser, no npm, no API keys, no accounts. Built by
**Asdale Dynamics, LLC** as a free utility for craft sellers, marketers, and
anyone designing flyers, covers, or product graphics.

```
Text needs enough contrast with its background to be readable.
"Text" also means the ink on your buttons, contact info, and prices.
AA is the legal-minimum bar for most public-facing content; AAA is the
bamboo-grade bar for people with low vision.
```

## Why you might want this

- You sell on Etsy/eBay and design your own flyers, listings, and covers.
- You picked colors that *look* great on screen but smear into mush when
  printed small or viewed by the ~8% of people (mostly men) with red/green
  color blindness.
- You want a fast, private, offline check — this tool never touches a network.

## Features

- **WCAG 2.x contrast checks** for one pair (`contrast`) or a whole palette
  (`palette`): AA normal text (4.5:1), AA large text (3:1), AAA normal
  (7:1), AAA large (4.5:1), bold large text, and UI components/graphics (3:1).
- **Color-blindness simulations** via linear-RGB filter matrices (Machado,
  Oliveira & Fernandes 2009): `protanopia`, `deuteranopia`, `tritanopia`,
  `achromatopsia`. Simulated pairs are re-checked against simulated backgrounds.
- **Smart suggestions** (`suggest`): if a color fails, get the nearest color
  (smallest RGB change — hue, saturation, or lightness) that passes your
  chosen target.
- **Exports**: a standalone HTML swatch report (open it in any browser, send
  it to a client) and a machine-readable JSON report.
- **Zero dependencies**: Python 3.9+ standard library only.

## Quick start

```bash
# from this folder, no install needed (Python 3.9+):
python3 -m accessible_palette contrast "#29323C" "#FDF8F2"

# or install the `accessible-palette` command:
pip install .
accessible-palette --help
```

### Check one text/background pair

```bash
python3 -m accessible_palette contrast "#000000" "#FFFFFF"
# exit code 0 = every check passes; 1 = some check fails; 2 = bad input

python3 -m accessible_palette contrast "#29323C" "#FDF8F2" --simulate protanopia
python3 -m accessible_palette contrast "rgb(240, 169, 59)" "#FFFFFF" --json
```

Colors accept `#RGB`, `#RRGGBB`, `rgb(…)`, and `hsl(h, s%, l%)` forms.

### Check a whole palette and export reports

```bash
python3 -m accessible_palette palette examples/summer-flyer-palette.json \
  --html report.html --json-out report.json
open report.html   # then view in any browser
```

Palette files are simple JSON:

```json
{
  "title": "Summer Craft Fair Flyer",
  "background": "#FDF8F2",
  "simulations": ["protanopia", "deuteranopia", "tritanopia"],
  "colors": [
    { "hex": "#29323C", "name": "Charcoal heading" },
    { "hex": "#7AB648", "name": "Lime accent" }
  ]
}
```

Every color is checked as *text on your background* — which is how accents,
buttons, and prices are actually used. Pass `-` as the file name to read the
palette JSON from stdin instead.

### Suggest a color that passes

```bash
python3 -m accessible_palette suggest "#7AB648" "#FDF8F2"
# Suggested: #607A49  4.54:1  (target aa-normal >= 4.5:1, RGB distance 65.4)

python3 -m accessible_palette suggest "#7AB648" "#FDF8F2" \
  --target aaa-normal --json
```

Targets: `aa-normal` (4.5:1), `aa-large` (3:1), `aaa-normal` (7:1),
`aaa-large` (4.5:1), `ui-component` (3:1). Use `--max-distance` to limit how
far the suggestion may drift from your original color. The background color is
kept as-is; the text color is nudged. (To darken a background instead, swap
the arguments conceptually or re-run with colors swapped.)

### Simulate color blindness

Simulations are applied in linear-light RGB (the perceptually sane way), then
re-checked against the simulated background, so you see whether your palette
*still passes* for colorblind readers:

```bash
python3 -m accessible_palette contrast "#1B1B3A" "#FDF8F2" --simulate protanopia,achromatopsia
```

## Which checks run and what they mean

| Check | Threshold | Applies to |
| --- | --- | --- |
| AA normal text | 4.5:1 | body text under 18pt/24px |
| AA large text | 3:1 | text 18pt (24px) regular, or larger |
| AAA normal text | 7:1 | same range, stricter bar |
| AAA large text | 4.5:1 | same range, stricter bar |
| AA/AAA bold large | 3:1 / 4.5:1 | text 14pt (18.66px) bold and up |
| UI component | 3:1 | buttons, icons, form borders, focus rings |

Exit codes: `0` all checks pass, `1` some check fails, `2` invalid input.
That makes `accessible-palette palette p.json --json-out out.json` easy to
wire into CI or a pre-publish script.

## Running the tests

```bash
python3 -m unittest discover -s tests -v
```

## Project layout

```
accessible_palette/
  color.py       parsing (hex/rgb/hsl), sRGB math, contrast ratio
  wcag.py        WCAG 2.x thresholds and pair evaluation
  simulate.py    color-blindness filter matrices
  suggest.py     nearest-accessible-color search
  report.py      JSON + standalone HTML swatch report
  cli.py         argparse CLI and exit codes
examples/        sample palette files to try immediately
tests/           unittest suite (50 tests)
```

## Known limitations

- Contrast thresholds follow WCAG 2.x sRGB math (2.1/2.2 agree on these
  numbers); APCA (the newer perceptual model) is intentionally out of scope.
- Simulations use Machado et al. (2009) severity-1.0 matrices; they are good
  approximations, not medical reproductions, of how any individual sees.
- `hsl()`/`rgb()` alpha values are accepted for parsing but transparency is
  not composited — design against your final solid background color.

## About / license

Free, MIT-licensed software from **Asdale Dynamics, LLC**
(friendly AI guides and practical tools from Dylan Asdale —
dylanasdale.github.io, author of *The Massive AI Manual*). Copyright
(c) 2026 Asdale Dynamics, LLC. No accounts, no network calls, no secrets:
it runs fully offline and collects nothing.

Suggestions here are design aid, not an accessibility certification; pair the
output with real user testing when something important ships.
