# STATUS.md — Accessible Palette Checker

Last updated: 2026-11-03 by Asdale Dynamics, LLC (Dylan Asdale)

## What was built

`accessible-palette` — a pure-Python (stdlib-only, Python 3.9+) CLI that
checks color palettes for WCAG 2.x AA/AAA contrast, simulates common
color-blindness filters, suggests nearby colors that pass, and exports a
standalone HTML swatch report plus a JSON report. Offline-only: no network,
accounts, keys, or personal data. Written for craft sellers and marketers
doing flyers, covers, and listing graphics; a free tool from Asdale
Dynamics, LLC.

Capabilities:

- `contrast TEXT BACKGROUND [--simulate ...] [--json]` — full WCAG check of
  one text/background pair: AA/AAA for normal (4.5/7), large (3/4.5),
  bold-large (3/4.5), plus UI-component (3:1) guidance.
- `palette FILE [--simulate ...] [--html OUT.html] [--json-out OUT.json]` —
  every palette color checked as text on the shared background; `FILE` may be
  `-` for stdin. HTML report includes live text previews and simulated views.
- `suggest TEXT BACKGROUND [--target ...] [--max-distance N] [--json]` —
  smallest-RGB-distance color that reaches the target ratio (aa-normal,
  aa-large, aaa-normal, aaa-large, ui-component).
- Color-blindness simulations (linear-light RGB, Machado et al. 2009
  severity 1.0): protanopia, deuteranopia, tritanopia, achromatopsia.
  Simulated text is re-checked against the simulated background.
- Color parsing: `#RGB`, `#RRGGBB`, `rgb()`, `rgba()`, `hsl()`, `hsla()`.
- Exit codes for automation: 0 all pass, 1 some check fails, 2 invalid input.

## How to run it

```bash
# no install:
python3 -m accessible_palette contrast "#000000" "#FFFFFF"
python3 -m accessible_palette palette examples/summer-flyer-palette.json \
  --html report.html --json-out report.json
python3 -m accessible_palette suggest "#7AB648" "#FDF8F2"

# with an installed command:
pip install .
accessible-palette contrast "#29323C" "#FDF8F2" --simulate protanopia
```

Full usage and a sample palette file are documented in `README.md`.

## Verification performed

- `python3 -m unittest discover -s tests` → **50 tests, all pass** on
  Python 3.13.5 (also exercised via subprocess-driven CLI end-to-end tests).
- `pip install .` into a clean venv succeeded; the installed
  `accessible-palette` command ran `--version`, `contrast`, and
  `palette` correctly.
- Export verification: `--html` produced a valid standalone HTML file (3
  preview cards + simulation views per pair); `--json-out` output parsed
  with `python3 -m json.tool` with no errors.
- Spot checks against expected WCAG values: #000 on #FFF = 21:1 (all pass),
  #777 on #FFF = 4.48:1 (fails AA-normal, passes AA-large/UI 3:1 — matches
  the published 4.477:1 figure); simulation of #FFF stays #FFF; red/green
  simulation examples behave as expected.
- `suggest` results re-verified to actually meet the requested ratio
  (programmatic test asserts ratio >= threshold).

## Known gaps

- Thresholds are the WCAG 2.x sRGB numbers shared by WCAG 2.1/2.2 — the
  perceptual APCA model is not implemented.
- Simulations are approximations of deficiency types, not medical
  reproductions of any person's vision; treat them as design aid.
- Alpha in `rgba()`/`hsla()` is accepted for parsing but not composited;
  check colors against your final opaque background.
- HTML preview typography is representative (not a print proof); always do
  a final eyeball check on the actual medium.
- Internationalized color names (CSS named colors) are not supported.
