import colorsys
import math
import re


class ColorError(ValueError):
    pass


_HEX_RE = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_RGB_RE = re.compile(
    r"^rgba?\(\s*(\d{1,3})\s*[, ]\s*(\d{1,3})\s*[, ]\s*(\d{1,3})"
    r"\s*(?:[,/]\s*([\d.]+%?)\s*)?\)$"
)
_HSL_RE = re.compile(
    r"^hsla?\(\s*([\d.]+)(?:deg)?\s*[, ]\s*([\d.]+)%\s*[, ]\s*([\d.]+)%"
    r"\s*(?:[,/]\s*([\d.]+%?)\s*)?\)$"
)


class RGB:
    __slots__ = ("r", "g", "b")

    def __init__(self, r, g, b):
        vals = (round(float(r)), round(float(g)), round(float(b)))
        for v in vals:
            if not (0 <= v <= 255):
                raise ColorError(f"channel out of range: {v!r}")
        self.r, self.g, self.b = vals

    def __eq__(self, other):
        return isinstance(other, RGB) and (self.r, self.g, self.b) == (
            other.r,
            other.g,
            other.b,
        )

    def __hash__(self):
        return hash((self.r, self.g, self.b))

    def __repr__(self):
        return f"RGB({self.r}, {self.g}, {self.b})"

    def css_hex(self):
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}"


def parse_color(text):
    if not isinstance(text, str):
        raise ColorError(f"color must be a string, got {type(text).__name__}")
    s = text.strip().lower()
    m = _HEX_RE.match(s)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return RGB(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    m = _RGB_RE.match(s)
    if m:
        r, g, b = (int(m.group(i)) for i in (1, 2, 3))
        if max(r, g, b) > 255:
            raise ColorError(f"rgb channel out of range in: {text}")
        return RGB(r, g, b)
    m = _HSL_RE.match(s)
    if m:
        h, s_pct, l_pct = (float(m.group(i)) for i in (1, 2, 3))
        if not (0 <= s_pct <= 100 and 0 <= l_pct <= 100):
            raise ColorError(f"hsl percentage out of range in: {text}")
        r_f, g_f, b_f = colorsys.hls_to_rgb(h / 360.0, l_pct / 100.0, s_pct / 100.0)
        return RGB(r_f * 255.0, g_f * 255.0, b_f * 255.0)
    raise ColorError(f"unsupported color format: {text!r}")


def hex_to_rgb(hex_text):
    m = re.fullmatch(r"#?([0-9a-fA-F]{6})", hex_text.strip())
    if not m:
        raise ColorError(f"expected 6-digit hex color (with optional #): {hex_text!r}")
    h = m.group(1)
    return RGB(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def rgb_to_hex(rgb):
    return rgb.css_hex()


def to_linear(channel):
    c = channel / 255.0
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def to_srgb(linear):
    clamped = min(1.0, max(0.0, linear))
    if clamped <= 0.0031308:
        return round(clamped * 12.92 * 255.0)
    return round((clamped ** (1.0 / 2.4)) * 1.055 * 255.0 - 0.055 * 255.0)


def relative_luminance(rgb):
    r = to_linear(rgb.r)
    g = to_linear(rgb.g)
    b = to_linear(rgb.b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(rgb1, rgb2):
    l1 = relative_luminance(rgb1)
    l2 = relative_luminance(rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def rgb_to_hsl(rgb):
    h, l, s = colorsys.rgb_to_hls(rgb.r / 255.0, rgb.g / 255.0, rgb.b / 255.0)
    return h * 360.0, s * 100.0, l * 100.0


def hsl_to_rgb(h, s, l):
    r_f, g_f, b_f = colorsys.hls_to_rgb((h % 360.0) / 360.0, l / 100.0, s / 100.0)
    return RGB(r_f * 255.0, g_f * 255.0, b_f * 255.0)


def rgb_distance(a, b):
    return math.sqrt((a.r - b.r) ** 2 + (a.g - b.g) ** 2 + (a.b - b.b) ** 2)
