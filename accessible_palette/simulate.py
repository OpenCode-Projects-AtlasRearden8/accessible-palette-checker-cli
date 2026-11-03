"""Color-blindness simulation using linear-RGB filter matrices.

Matrices from Machado, Oliveira & Fernandes (2009), severity 1.0,
applied in linear-light RGB then re-encoded to sRGB.
"""

from .color import to_linear, to_srgb, RGB

SIMULATIONS = {
    "protanopia": (
        (0.152286, 1.052583, -0.204868),
        (0.114503, 0.786281, 0.099216),
        (-0.003882, -0.048116, 1.051998),
    ),
    "deuteranopia": (
        (0.367322, 0.860646, -0.227968),
        (0.280085, 0.672501, 0.047413),
        (-0.011820, 0.042940, 0.968881),
    ),
    "tritanopia": (
        (1.255528, -0.076749, -0.178779),
        (-0.078411, 0.930809, 0.147602),
        (0.004733, 0.691367, 0.303900),
    ),
    "achromatopsia": (
        (0.2126, 0.7152, 0.0722),
        (0.2126, 0.7152, 0.0722),
        (0.2126, 0.7152, 0.0722),
    ),
}

SIMULATION_NAMES = tuple(SIMULATIONS)


def simulate(rgb, sim_name):
    try:
        matrix = SIMULATIONS[sim_name]
    except KeyError:
        raise ValueError(
            f"unknown simulation {sim_name!r}; choose from: "
            + ", ".join(SIMULATION_NAMES)
        ) from None
    lr = to_linear(rgb.r)
    lg = to_linear(rgb.g)
    lb = to_linear(rgb.b)
    out = []
    for row in matrix:
        out.append(to_srgb(row[0] * lr + row[1] * lg + row[2] * lb))
    return RGB(*out)
