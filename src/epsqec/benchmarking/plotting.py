"""Shared matplotlib style for report figures (static PNG/SVG).

Colours: categorical slots of the reference palette, assigned in fixed order; identity is
never colour-alone (marker + line style + legend).  Every figure carries a footer naming the
experiment id and config hash it was drawn from.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SLOTS = {
    "blue": "#2a78d6",
    "orange": "#eb6834",
    "aqua": "#1baf7a",
    "yellow": "#eda100",
    "magenta": "#e87ba4",
    "green": "#008300",
    "violet": "#6250d6",
    "red": "#e34948",
    "gray": "#7d7c78",
}
TEXT = "#0b0b0b"
TEXT2 = "#52514e"
GRID = "#d9d8d4"
SURFACE = "#fcfcfb"


def setup():
    plt.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": TEXT2,
        "axes.labelcolor": TEXT,
        "axes.titlecolor": TEXT,
        "xtick.color": TEXT2,
        "ytick.color": TEXT2,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "axes.grid": True,
        "axes.grid.which": "both",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "lines.linewidth": 2.0,
        "lines.markersize": 6.5,
        "font.size": 10,
        "legend.frameon": False,
        "savefig.dpi": 150,
    })


def footer(fig, text: str):
    fig.text(0.01, 0.005, text, fontsize=7, color=TEXT2, ha="left", va="bottom")
