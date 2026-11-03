"""Find the nearest color to an original that passes a WCAG threshold."""

from .color import (
    ColorError,
    contrast_ratio,
    hsl_to_rgb,
    parse_color,
    rgb_distance,
    rgb_to_hsl,
)
from .wcag import AA_LARGE, AA_NORMAL, AAA_LARGE, AAA_NORMAL, UI_COMPONENT

TARGETS = {
    "aa-normal": AA_NORMAL,
    "aa-large": AA_LARGE,
    "aaa-normal": AAA_NORMAL,
    "aaa-large": AAA_LARGE,
    "ui-component": UI_COMPONENT,
}


def target_threshold(target_name):
    try:
        return TARGETS[target_name]
    except KeyError:
        raise ValueError(
            f"unknown target {target_name!r}; choose from: " + ", ".join(TARGETS)
        ) from None


def _closest_passing_lightness(h, s, l0, background, threshold):
    spans = [
        (max(0.0, l0 - 25.0), min(100.0, l0 + 25.0)),
        (0.0, 100.0),
    ]
    best = None
    for lo, hi in spans:
        step = 0.2 if hi - lo <= 50.0 else 0.5
        count = int((hi - lo) / step) + 1
        for i in range(count):
            lightness = min(100.0, lo + i * step)
            candidate = hsl_to_rgb(h, s, lightness)
            if contrast_ratio(candidate, background) >= threshold:
                candidate_refined = _refine(
                    h, s, l0, lightness, background, threshold
                )
                if best is None or abs(candidate_refined - l0) < abs(best - l0):
                    best = candidate_refined
        if best is not None:
            break
    return best


def _refine(h, s, l0, lightness, background, threshold):
    fine = 0.004
    start = max(0.0, lightness - 0.25)
    end = min(100.0, lightness + 0.25)
    current = start
    best = None
    while current <= end:
        candidate = hsl_to_rgb(h, s, current)
        if contrast_ratio(candidate, background) >= threshold and (
            best is None or abs(current - l0) < abs(best - l0)
        ):
            best = current
        current += fine
    return best if best is not None else lightness


def suggest(text, background, target="aa-normal", max_distance=140.0):
    threshold = target_threshold(target)
    text_rgb = parse_color(text)
    background_rgb = parse_color(background)
    if contrast_ratio(text_rgb, background_rgb) >= threshold:
        return None
    h, s, l = rgb_to_hsl(text_rgb)
    variants = [(h, s)]
    for delta in (-30, -18, -9, 9, 18, 30):
        variants.append(((h + delta) % 360.0, s))
    for delta in (-18, -9, -4, 4, 9, 18):
        variants.append((h, min(100.0, max(0.0, s - delta))))
    best_rgb = None
    best_distance = None
    for hue, sat in variants:
        lightness = _closest_passing_lightness(hue, sat, l, background_rgb, threshold)
        if lightness is None:
            continue
        candidate = hsl_to_rgb(hue, sat, lightness)
        if candidate == text_rgb:
            continue
        distance = rgb_distance(text_rgb, candidate)
        if distance <= max_distance and (
            best_distance is None or distance < best_distance
        ):
            best_rgb = candidate
            best_distance = distance
    if best_rgb is None:
        raise ColorError(
            f"no color within {max_distance:.0f} RGB units of {text} passes "
            f"{target} ({threshold:g}:1) against {background}"
        )
    return {
        "original": text_rgb.css_hex(),
        "suggested": best_rgb.css_hex(),
        "distance": best_distance,
        "ratio": contrast_ratio(best_rgb, background_rgb),
        "target": target,
        "threshold": threshold,
    }
