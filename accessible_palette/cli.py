import argparse
import json
import sys

from . import __version__
from .color import ColorError, parse_color
from .report import build_report, report_to_html, report_to_json
from .simulate import SIMULATION_NAMES
from .suggest import suggest
from .wcag import evaluate_pair

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_ERROR = 2


def make_parser():
    parser = argparse.ArgumentParser(
        prog="accessible-palette",
        description=(
            "Check color palettes for WCAG AA/AAA contrast, simulate "
            "color-blindness, and suggest accessible color alternatives. "
            "Pure Python, no browser required. A free tool by Asdale Dynamics, LLC."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_contrast = subparsers.add_parser(
        "contrast", help="check one text/background pair"
    )
    p_contrast.add_argument("text", help="text color (hex, rgb(), or hsl())")
    p_contrast.add_argument("background", help="background color")
    p_contrast.add_argument(
        "--simulate",
        default="",
        help="comma-separated color-blindness simulations: "
        + ", ".join(SIMULATION_NAMES),
    )
    p_contrast.add_argument("--json", action="store_true", help="output JSON")

    p_palette = subparsers.add_parser(
        "palette", help="check a palette file and export HTML/JSON reports"
    )
    p_palette.add_argument("file", help="palette JSON file ('-' for stdin)")
    p_palette.add_argument(
        "--simulate",
        default=None,
        help="comma-separated simulations (overrides palette file setting)",
    )
    p_palette.add_argument("--html", help="write a standalone HTML swatch report")
    p_palette.add_argument("--json-out", help="write a JSON report file")

    p_suggest = subparsers.add_parser(
        "suggest", help="suggest a nearby color that passes the target ratio"
    )
    p_suggest.add_argument("text", help="text color to adjust")
    p_suggest.add_argument("background", help="background color (kept as-is)")
    p_suggest.add_argument(
        "--target",
        default="aa-normal",
        help="aa-normal | aa-large | aaa-normal | aaa-large | ui-component",
    )
    p_suggest.add_argument(
        "--max-distance",
        type=float,
        default=140.0,
        help="largest allowed RGB distance from the original color",
    )
    p_suggest.add_argument("--json", action="store_true", help="output JSON")
    return parser


def parse_simulation_list(text):
    if not text or not text.strip():
        return []
    sims = []
    for token in text.split(","):
        name = token.strip().lower()
        if not name:
            continue
        if name not in SIMULATION_NAMES:
            raise ValueError(
                f"unknown simulation {name!r}; choose from: "
                + ", ".join(SIMULATION_NAMES)
            )
        if name not in sims:
            sims.append(name)
    return sims


def load_palette(data):
    if not isinstance(data, dict):
        raise ColorError("palette JSON must be an object with a 'colors' key")
    colors = data.get("colors")
    if not isinstance(colors, list) or not colors:
        raise ColorError(
            "palette JSON needs a non-empty 'colors' list; each entry is a "
            "color string or {\"hex\": \"...\", \"name\": \"...\"}"
        )
    try:
        background_rgb = parse_color(data.get("background", "#FFFFFF"))
    except ColorError as exc:
        raise ColorError(f"palette 'background' invalid: {exc}") from None
    entries = []
    seen = set()
    for item in colors:
        if isinstance(item, str):
            hex_text, name = item, None
        elif isinstance(item, dict):
            hex_text = item.get("hex") or item.get("color")
            if not hex_text:
                raise ColorError(f"palette color entry missing 'hex': {item!r}")
            name = item.get("name")
        else:
            raise ColorError(f"palette color entry must be a string or object: {item!r}")
        rgb = parse_color(hex_text)
        if rgb in seen:
            continue
        seen.add(rgb)
        entries.append({"rgb": rgb, "hex": rgb.css_hex(), "name": name})
    return entries, background_rgb, data.get("title")


def failure_summary(pairs, sim_names):
    failed = 0
    total = 0
    for pair in pairs:
        data_sets = [("base", pair)] + [
            (sim, sim_pair) for sim, sim_pair in pair.get("simulations", {}).items()
        ]
        for _, data in data_sets:
            total += len(data["checks"])
            failed += sum(1 for c in data["checks"].values() if not c["passes"])
    return failed, total


def cmd_contrast(args):
    try:
        text_rgb = parse_color(args.text)
        background_rgb = parse_color(args.background)
        sims = parse_simulation_list(args.simulate)
    except (ColorError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    evaluation = evaluate_pair(text_rgb, background_rgb)
    payload = {
        "tool": "accessible-palette-checker",
        "text": text_rgb.css_hex(),
        "background": background_rgb.css_hex(),
        "ratio": round(evaluation["ratio"], 2),
        "checks": {
            k: {"threshold": v["threshold"], "passes": v["passes"]}
            for k, v in evaluation["checks"].items()
        },
    }
    if sims:
        from .simulate import simulate

        payload["simulations"] = {}
        for sim in sims:
            sim_text = simulate(text_rgb, sim)
            sim_bg = simulate(background_rgb, sim)
            sim_eval = evaluate_pair(sim_text, sim_bg)
            payload["simulations"][sim] = {
                "text": sim_text.css_hex(),
                "background": sim_bg.css_hex(),
                "ratio": round(sim_eval["ratio"], 2),
                "checks": {
                    k: {"threshold": v["threshold"], "passes": v["passes"]}
                    for k, v in sim_eval["checks"].items()
                },
            }
    if args.json:
        print(json.dumps(payload, indent=2))
        return EXIT_OK if _all_pass(payload) else EXIT_FAIL
    ratio = payload["ratio"]
    print(f"{payload['text']} on {payload['background']}: {ratio}:1")
    for key, data in payload["checks"].items():
        mark = "PASS" if data["passes"] else "FAIL"
        print(f"  {key:<14} {data['threshold']:>5}:1  {mark}")
    for sim, sim_data in payload.get("simulations", {}).items():
        print(f"  as seen with {sim} ({sim_data['text']}):")
        print(f"    simulated pair: {sim_data['text']} on {sim_data['background']} "
              f"{sim_data['ratio']}:1")
        for key, data in sim_data["checks"].items():
            mark = "PASS" if data["passes"] else "FAIL"
            print(f"    {key:<12} {data['threshold']:>5}:1  {mark}")
    return EXIT_OK if _all_pass(payload) else EXIT_FAIL


def _all_pass(payload):
    return all(
        c["passes"]
        for c in payload["checks"].values()
    ) and all(
        c["passes"]
        for sim in payload.get("simulations", {}).values()
        for c in sim["checks"].values()
    )


def cmd_palette(args):
    try:
        if args.file == "-":
            raw = sys.stdin.read()
        else:
            with open(args.file, encoding="utf-8") as handle:
                raw = handle.read()
        data = json.loads(raw)
        entries, background_rgb, title = load_palette(data)
        sims_arg = args.simulate if args.simulate is not None else data.get(
            "simulations", ""
        )
        if isinstance(sims_arg, list):
            sims = parse_simulation_list(",".join(sims_arg))
        else:
            sims = parse_simulation_list(sims_arg or "")
    except (ColorError, ValueError, json.JSONDecodeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    for entry in entries:
        entry["simulated"] = entry["rgb"]
    report = build_report(title=title, colors=entries,
                          background=background_rgb, simulations=sims)
    if args.json_out:
        try:
            with open(args.json_out, "w", encoding="utf-8") as handle:
                handle.write(report_to_json(report) + "\n")
        except OSError as exc:
            print(f"error: could not write JSON report: {exc}", file=sys.stderr)
            return EXIT_ERROR
    if args.html:
        try:
            with open(args.html, "w", encoding="utf-8") as handle:
                handle.write(report_to_html(report) + "\n")
        except OSError as exc:
            print(f"error: could not write HTML report: {exc}", file=sys.stderr)
            return EXIT_ERROR
    failed, total = failure_summary(report["pairs"], sims)
    print(f"Palette: {report['title']}")
    print(f"Background: {report['background']}")
    print(f"Checked {len(report['pairs'])} color(s) against the background.")
    for pair in report["pairs"]:
        label = pair["name"] or pair["text"]
        base_failed = [
            k for k, v in pair["checks"].items() if not v["passes"]
        ]
        if base_failed:
            marks = ", ".join(base_failed)
            print(f"  {label:<14} {pair['ratio']:>6}:1  FAIL ({marks})")
        else:
            print(f"  {label:<14} {pair['ratio']:>6}:1  PASS (all checks)")
    if sims:
        sim_failed_total = 0
        for pair in report["pairs"]:
            for sim, sim_pair in pair.get("simulations", {}).items():
                if any(not v["passes"] for v in sim_pair["checks"].values()):
                    sim_failed_total += 1
        if sim_failed_total:
            print(
                f"  Simulation check: {sim_failed_total} of "
                f"{len(report['pairs']) * len(sims)} simulated pairs still fail some "
                "conditions (see HTML report for details)."
            )
    print(f"{failed}/{total} checks failed"
          + ("  (see --html / --json-out for full details)" if failed else ""))
    return EXIT_OK if failed == 0 else EXIT_FAIL


def cmd_suggest(args):
    try:
        result = suggest(
            args.text,
            args.background,
            target=args.target,
            max_distance=args.max_distance,
        )
    except (ColorError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    if result is None:
        if args.json:
            print(
                report_to_json(
                    {
                        "tool": "accessible-palette-checker",
                        "already_passes": True,
                        "text": args.text,
                        "background": args.background,
                        "target": args.target,
                    }
                )
            )
        else:
            print(f"{args.text} already passes {args.target} against {args.background}")
        return EXIT_OK
    if args.json:
        print(report_to_json({"tool": "accessible-palette-checker", **result}))
        return EXIT_OK
    print(
        f"Original:  {result['original']}  (below target {result['target']})"
    )
    print(
        f"Suggested: {result['suggested']}  {result['ratio']:.2f}:1  "
        f"(target {result['target']} >= {result['threshold']}:1, "
        f"RGB distance {result['distance']:.1f})"
    )
    return EXIT_OK


def main(argv=None):
    parser = make_parser()
    args = parser.parse_args(argv)
    if args.command == "contrast":
        return cmd_contrast(args)
    if args.command == "palette":
        return cmd_palette(args)
    if args.command == "suggest":
        return cmd_suggest(args)
    parser.error(f"unknown command: {args.command}")


if __name__ == "__main__":
    sys.exit(main())
