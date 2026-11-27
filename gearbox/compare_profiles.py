"""Plot two generated catalogue profiles at the same scale.

python -m gearbox.compare_profiles OLD_PARTS_DIRECTORY NEW_PARTS_DIRECTORY
"""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon

from gearbox.lobe import profile_points


def compare(old, new):
    configs = [
        json.loads((p / "gearbox.json").read_text())["parameters"] for p in (old, new)
    ]
    fig, axes = plt.subplots(1, 2, figsize=(11, 6), layout="constrained")
    limit = max(c["housing_radius"] for c in configs) + 3
    for ax, c in zip(axes, configs):
        points = profile_points(
            c["disc_lobes"],
            c["pitch_radius"],
            c["radius_offset"],
            c["lobe_radius"],
            c["lobe_clearance"],
        )
        points = [[x + c["radius_offset"], y] for x, y in points]
        ax.add_patch(
            Circle(
                (0, 0),
                c["housing_radius"],
                fill=False,
                edgecolor="#c64f30",
                linewidth=2,
            )
        )
        ax.add_patch(
            Polygon(points, facecolor="#a5cee4", edgecolor="#23566f", linewidth=1.3)
        )
        for x, y in c["ring_positions"]:
            ax.add_patch(
                Circle(
                    (x, y), c["lobe_radius"], facecolor="#e98a65", edgecolor="#c64f30"
                )
            )
        ax.add_patch(
            Circle(
                (c["radius_offset"], 0),
                c["eccentric_bearing"]["od"] / 2,
                facecolor="white",
                edgecolor="#23566f",
            )
        )
        ax.set(xlim=(-limit, limit), ylim=(-limit, limit), aspect="equal")
        ax.axis("off")
        ax.set_title(f'{c["reduction"]}:1 — {c["disc_lobes"]} disc lobes', fontsize=18)
        ax.text(
            0.5,
            -0.03,
            f'Contact radius {c["lobe_radius"]:g} mm · offset {c["radius_offset"]:g} mm\nRadial lobe depth {2*c["radius_offset"]:g} mm',
            transform=ax.transAxes,
            ha="center",
            fontsize=12,
        )
    fig.suptitle("Same scale · both fit the 89 mm motor plate", fontsize=16)
    fig.savefig(new / "lobe_comparison.png", dpi=180, bbox_inches="tight", pad_inches=0.2)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("old", type=Path)
    parser.add_argument("new", type=Path)
    args = parser.parse_args()
    compare(args.old, args.new)
