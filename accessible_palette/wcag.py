"""WCAG 2.x contrast requirements and evaluation."""

from .color import contrast_ratio

AA_NORMAL = 4.5
AA_LARGE = 3.0
AAA_NORMAL = 7.0
AAA_LARGE = 4.5
UI_COMPONENT = 3.0

TEXT_SIZES = ("normal", "large", "bold-large")

SIZE_REQUIREMENTS = {
    "normal": {"AA": AA_NORMAL, "AAA": AAA_NORMAL},
    "large": {"AA": AA_LARGE, "AAA": AAA_LARGE},
    "bold-large": {"AA": AA_LARGE, "AAA": AAA_LARGE},
}


def evaluate_pair(text_rgb, background_rgb):
    ratio = contrast_ratio(text_rgb, background_rgb)
    results = {}
    for size, reqs in SIZE_REQUIREMENTS.items():
        for level, threshold in reqs.items():
            results[f"{level}-{size}"] = {
                "threshold": threshold,
                "passes": ratio >= threshold,
            }
    results["ui-component"] = {
        "threshold": UI_COMPONENT,
        "passes": ratio >= UI_COMPONENT,
    }
    return {"ratio": ratio, "checks": results}


def describe_sizes():
    return {
        "normal": "body text under 18pt (24px) regular / 14pt (18.66px) bold",
        "large": "text 18pt (24px) regular or larger",
        "bold-large": "text 14pt (18.66px) bold or larger",
    }
