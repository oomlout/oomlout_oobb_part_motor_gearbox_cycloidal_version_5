"""Shared equation component adapter and legacy numeric-profile diagnostics.

The pin centre in rotor coordinates is q(t) = R exp(it) - e exp(i N t).
Offset inward along its unit normal by the roller radius plus clearance.
The active simple gearbox uses shared_component; the numeric sampler remains
for independent comparisons and older recipe architectures.
"""

from math import cos, sin, hypot, tau
from gearbox_native.cycloid_equation import CycloidEquation


def shared_component(config, depth):
    """Shared native equation primitive; pass only its supported fields."""
    return dict(type='positive',shape='cycloidal_disc',pos=[0,0,0],depth=depth,
        ring_pin_count=config['ring_pin_count'],pitch_radius=config['pitch_radius'],
        eccentricity=config['radius_offset'],roller_radius=config['lobe_radius'],
        clearance=config.get('lobe_clearance',.20),
        profile_tolerance=config.get('profile_tolerance',.005),
        samples_per_lobe=config.get('samples_per_lobe',48))


def profile_points(
    lobe_count,
    pitch_radius,
    eccentricity,
    pin_radius,
    clearance=0.0,
    samples_per_lobe=240,
    profile_tolerance=0.0005,
):
    n = lobe_count + 1
    count = lobe_count * samples_per_lobe

    equation = CycloidEquation(n,pitch_radius,eccentricity,pin_radius,clearance)
    equation.validate_offset()
    point = equation.point

    def distance_to_chord(p, a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        norm = dx * dx + dy * dy
        u = (
            max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / norm))
            if norm
            else 0
        )
        return hypot(p[0] - a[0] - u * dx, p[1] - a[1] - u * dy)

    points = []

    def segment(t0, p0, t1, p1, depth=0):
        tm = (t0 + t1) / 2
        pm = point(tm)
        # High eccentricity gives fast-changing normals at the root. Refine
        # those spans instead of multiplying the entire polygon's point count.
        error = max(
            distance_to_chord(point(t0 + (t1 - t0) * u), p0, p1)
            for u in (0.25, 0.5, 0.75)
        )
        if error > profile_tolerance:
            if depth >= 12:
                raise ValueError(
                    "Lobe refinement exceeded limit; reduce eccentricity or relax profile_tolerance"
                )
            segment(t0, p0, tm, pm, depth + 1)
            segment(tm, pm, t1, p1, depth + 1)
        else:
            points.append(p0)

    for i in range(count):
        a, b = tau * i / count, tau * (i + 1) / count
        segment(a, point(a), b, point(b))
    return points


def component(config, depth):
    return {
        "type": "positive",
        "shape": "polygon",
        "depth": depth,
        "pos": [0, 0, 0],
        "points": profile_points(
            config["disc_lobes"],
            config["pitch_radius"],
            config["radius_offset"],
            config["lobe_radius"],
            config.get("lobe_clearance", 0.20),
            config.get("samples_per_lobe", 240),
            config.get("profile_tolerance", 0.0005),
        ),
    }
