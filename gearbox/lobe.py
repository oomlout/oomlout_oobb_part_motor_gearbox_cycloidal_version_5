"""The only new geometric primitive: an N-1 lobe roller-envelope profile.

The pin centre in rotor coordinates is q(t) = R exp(it) - e exp(i N t).
Offset inward along its unit normal by the roller radius plus clearance.
This avoids the old hypocycloid's forced pitch-radius/eccentricity coupling.
"""

from math import cos, sin, hypot, tau


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

    def point(t):
        x = pitch_radius * cos(t) - eccentricity * cos(n * t)
        y = pitch_radius * sin(t) - eccentricity * sin(n * t)
        dx = -pitch_radius * sin(t) + n * eccentricity * sin(n * t)
        dy = pitch_radius * cos(t) - n * eccentricity * cos(n * t)
        length = hypot(dx, dy)
        offset = pin_radius + clearance
        return [x - offset * dy / length, y + offset * dx / length]

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
