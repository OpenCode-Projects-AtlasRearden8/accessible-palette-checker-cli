import json
from datetime import datetime, timezone

from .color import contrast_ratio
from .simulate import simulate
from .wcag import evaluate_pair

ORDER = [
    "AA-normal",
    "AA-large",
    "AAA-normal",
    "AAA-large",
    "AA-bold-large",
    "AAA-bold-large",
    "ui-component",
]

LABELS = {
    "AA-normal": "AA normal text (4.5:1)",
    "AA-large": "AA large text (3:1)",
    "AAA-normal": "AAA normal text (7:1)",
    "AAA-large": "AAA large text (4.5:1)",
    "AA-bold-large": "AA bold large text (3:1)",
    "AAA-bold-large": "AAA bold large text (4.5:1)",
    "ui-component": "UI component / graphics (3:1)",
}


def _ordered_checks(checks):
    ordered = {}
    for key in ORDER:
        if key in checks:
            ordered[key] = checks[key]
    for key, value in checks.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def build_report(colors, background, simulations=(), title=None):
    background_rgb = background
    pairs = []
    for entry in colors:
        text_rgb = entry["rgb"]
        evaluation = evaluate_pair(text_rgb, background_rgb)
        pair = {
            "name": entry.get("name"),
            "text": text_rgb.css_hex(),
            "background": background_rgb.css_hex(),
            "ratio": round(evaluation["ratio"], 2),
            "checks": {
                k: {"threshold": v["threshold"], "passes": v["passes"]}
                for k, v in _ordered_checks(evaluation["checks"]).items()
            },
        }
        if entry.get("note"):
            pair["note"] = entry["note"]
        simulations_out = {}
        for sim in simulations:
            sim_bg = simulate(background_rgb, sim)
            sim_text = (
                entry["simulated"]
                if "simulated" in entry
                else simulate(text_rgb, sim)
            )
            sim_eval = evaluate_pair(sim_text, sim_bg)
            simulations_out[sim] = {
                "text": text_rgb.css_hex(),
                "background": sim_bg.css_hex(),
                "ratio": round(sim_eval["ratio"], 2),
                "checks": {
                    k: {"threshold": v["threshold"], "passes": v["passes"]}
                    for k, v in _ordered_checks(sim_eval["checks"]).items()
                },
            }
        if simulations_out:
            pair["simulations"] = simulations_out
        pairs.append(pair)
    report = {
        "tool": "accessible-palette-checker",
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "title": title or "Palette contrast report",
        "background": background_rgb.css_hex(),
        "simulations": list(simulations),
        "pairs": pairs,
    }
    return report


def _simulated_background(background_rgb, sim):
    return simulate(background_rgb, sim)


def report_to_json(report, indent=2):
    return json.dumps(report, indent=indent)


_HTML_CSS = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body { font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
       margin: 0; background: #f6f7fb; color: #16181d; }
header { padding: 24px 32px 8px; }
h1 { margin: 0 0 4px; font-size: 22px; }
.meta { color: #5a6072; font-size: 13px; margin: 0; }
main { padding: 8px 32px 40px; }
.pair { background: #fff; border: 1px solid #e3e6ef; border-radius: 10px;
        margin: 16px 0; overflow: hidden; }
.pair-head { display: flex; align-items: baseline; gap: 14px;
             padding: 14px 18px; border-bottom: 1px solid #e3e6ef; }
.pair-head h2 { font-size: 15px; margin: 0; font-family: ui-monospace, monospace; }
.ratio { font-size: 15px; font-weight: 600; }
.badge { font-size: 11px; font-weight: 600; padding: 3px 9px;
         border-radius: 999px; letter-spacing: 0.3px; }
.pass { background: #e2f5e9; color: #14683a; border: 1px solid #9ad4b1; }
.fail { background: #fdeaea; color: #8f1f2b; border: 1px solid #f0b0b6; }
.preview { padding: 26px 18px; display: flex; gap: 22px;
           border-bottom: 1px solid #e9ecf3; flex-wrap: wrap; }
.preview .card { flex: 1 1 240px; padding: 18px; border-radius: 8px;
                 font-size: 15px; }
.preview .card h3 { margin: 0 0 8px; font-size: 20px; font-weight: 700; }
.preview .card p { margin: 0; line-height: 1.5; }
.preview .card .small { font-size: 12.5px; margin-top: 8px; }
.preview .card .big { font-size: 21px; margin-top: 12px; }
.checks { display: flex; flex-wrap: wrap; gap: 8px; padding: 14px 18px; }
.chip { font-size: 12px; padding: 5px 10px; border-radius: 7px;
        border: 1px solid #d9dce6; background: #fafbfe; }
.chip b { font-weight: 700; }
.chip.ok b { color: #14683a; }
.chip.no b { color: #8f1f2b; }
footer { padding: 0 32px 32px; color: #5a6072; font-size: 12px; }
"""


def _badge(value):
    if value:
        return '<span class="badge pass">PASS</span>'
    return '<span class="badge fail">FAIL</span>'


def _card(text_hex, background_hex, extra_class="", extra_html=""):
    return (
        f'<div class="card {extra_class}" style="background:{background_hex};'
        f'color:{text_hex};"><h3>Large heading</h3>'
        f"<p>Body text sample at 15px, plus <b>bold 15px</b>.</p>"
        f'<p class="big">Big 21px text sample</p>'
        f'<p class="small">Tiny 12.5px caption{extra_html}</p></div>'
    )


def _checks_html(checks, ratio):
    chips = []
    for key, data in checks.items():
        state = "ok" if data["passes"] else "no"
        chips.append(
            f'<span class="chip {state}"><b>{key}</b> '
            f'{data["threshold"]}:1 &rarr; {_badge(data["passes"])}</span>'
        )
    return (
        f'<div class="checks"><span class="chip num"><b>ratio</b> {ratio}</span>'
        + "".join(chips)
        + "</div>"
    )


def report_to_html(report):
    title = report.get("title", "Palette contrast report")
    parts = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{_esc(title)}</title>",
        f"<style>{_HTML_CSS}</style></head><body>",
        "<header><h1>Palette contrast report</h1>"
        f'<p class="meta">{_esc(title)} &middot; generated {report["generated"]}'
        " &middot; WCAG 2.x thresholds</p></header><main>",
    ]
    for pair in report["pairs"]:
        parts.append('<div class="pair"><div class="pair-head">')
        parts.append(
            f"<h2>{pair['text']} on {pair['background']}</h2>"
            f'<span class="ratio">{pair["ratio"]}:1</span>'
        )
        parts.append("</div>")
        parts.append('<div class="preview">')
        parts.append(_card(pair["text"], pair["background"]))
        for sim_name, sim_pair in pair.get("simulations", {}).items():
            parts.append(_card(sim_pair["text"], sim_pair["background"], sim_name))
        parts.append("</div>")
        parts.append(_checks_html(pair["checks"], pair["ratio"]))
        for sim_name, sim_pair in pair.get("simulations", {}).items():
            parts.append(f"<h4 style='margin:10px 18px 0'>as seen with {sim_name}</h4>")
            parts.append(_checks_html(sim_pair["checks"], sim_pair["ratio"]))
        parts.append("</div>")
    parts.append(
        "</main><footer>Generated by accessible-palette-checker "
        "(Asdale Dynamics, LLC). Thresholds from WCAG 2.x; simulations use "
        "Machado et al. (2009) matrices. Always pair tooling with manual "
        "review.</footer></body></html>"
    )
    return "\n".join(parts)


def _esc(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
