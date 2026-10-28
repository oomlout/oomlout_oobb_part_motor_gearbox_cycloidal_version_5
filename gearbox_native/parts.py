"""SolidCraft-owned V6 construction helpers; SCAD helpers remain in gearbox/."""
import copy
import math
from oobb_solidcraft import api as oobb
from pathlib import Path
import yaml


def default_parameters():
    return yaml.safe_load(Path(__file__).with_name("common_defaults.yaml").read_text(encoding="utf-8"))


def resolve(kwargs):
    from gearbox_native.captured import resolve as current
    return current(kwargs)


def polar(radius, angle):
    a = math.radians(angle)
    return [radius * math.cos(a), radius * math.sin(a)]


def ring(radius, count, phase=0):
    return [polar(radius, phase + i * 360 / count) for i in range(count)]


def bearing_spec(name):
    objects = oobb.oe(shape="oobb_bearing", bearing_size=name, type="p", pos=[0, 0, 0])
    while isinstance(objects, list):
        objects = objects[0]
    return {"id": objects["id"] * 2, "od": objects["od"] * 2, "depth": objects["depth"]}


def blank():
    return {"components": [], "components_objects": [], "components_string": []}


def add(t, shape, typ="p", pos=None, **kw):
    p3 = copy.deepcopy(kw)
    p3["shape"] = shape
    p3["type"] = typ
    p3["pos"] = list(pos or [0, 0, 0])
    if shape == 'oobb_hole':
        p3['native_hole_array'] = True
    start = len(t["components"])
    oobb.append_full(t, **p3)
    if shape == 'oobb_screw_countersunk':
        from gearbox_native.geometry import continuous_countersinks
        t['components'][start:] = continuous_countersinks(t['components'][start:])
    if shape == 'oobb_nut':
        # Build a single continuous cutter with an already requested coaxial
        # bore. Its union is unchanged, but no bridge is cut across an existing
        # circular hole in a separate Boolean operation.
        groups = t['components'][start:]
        if len(groups) == 1 and groups[0].get('type') == 'rotation' and not any(groups[0].get('rot', [0,0,0])[:2]):
            group = groups[0]
            matches = []
            for index, leaf in enumerate(t['components'][:start]):
                if (isinstance(leaf, dict) and leaf.get('type') in ('n','negative')
                        and leaf.get('intent', {}).get('shape') == 'oobb_hole'
                        and all(abs(a-b)<1e-10 for a,b in zip(leaf['pos'][:2],group['pos'][:2]))):
                    clone = copy.deepcopy(leaf)
                    clone['type'] = 'positive'
                    clone['pos'] = [0,0,leaf['pos'][2]-group['pos'][2]]
                    group['objects'].append(clone)
                    matches.append(index)
            for index in reversed(matches):
                del t['components'][index]
            start -= len(matches)
    def mark(item):
        if isinstance(item, list):
            for child in item:
                mark(child)
        else:
            item["intent"] = copy.deepcopy(p3)
            for child in item.get("objects", []):
                mark(child)
    for item in t["components"][start:]:
        mark(item)


def cylinder(t, radius, depth, z=0, typ="p", xy=(0, 0)):
    add(t, "oobb_cylinder", typ, [*xy, z], radius=radius, depth=depth, zz="bottom")


def hole(t, radius, depth, xy=(0, 0), z=-0.01):
    add(t, "oobb_hole", "n", [*xy, z], radius=radius, depth=depth + 0.02)


def through(t, positions, depth, size="m3", countersink=False, nut=False):
    for xy in positions:
        if countersink:
            add(
                t,
                "oobb_screw_countersunk",
                "n",
                [*xy, depth],
                radius_name=size,
                depth=depth + 0.02,
                zz="top",
                nut_include=False,
                overhang=False,
            )
        else:
            add(t, "oobb_hole", "n", [*xy, -0.01], radius_name=size, depth=depth + 0.02)
        if nut:
            add(
                t,
                "oobb_nut",
                "n",
                [*xy, depth + 0.1],
                radius_name=size,
                depth=oobb.gv("nut_depth_" + size, "true") + 0.2,
                zz="top",
                overhang=True,
            )


def layout(parts, **kwargs):
    c = kwargs
    placements = []
    x = 0
    y = 0
    row = 0
    gap = c.get("print_gap", 8.0)
    for name, p in sorted(parts.items(), key=lambda item: -item[1]["width"]):
        for i in range(p["quantity"]):
            w = p["width"]
            if x + w > c.get("print_width", 240.0) and x:
                x = 0
                y += row + gap
                row = 0
            placements.append(
                {
                    "part": name,
                    "copy": i + 1,
                    "pos": [x + w / 2, y + w / 2, 0],
                    "width": w,
                }
            )
            x += w + gap
            row = max(row, w)
    return placements


def group(t, child, pos=(0, 0, 0), rot=(0, 0, 0), typ="p"):
    """Nested OOBB CSG preserves local cuts before union with other features."""
    t["components"].append(
        {
            "type": "rotation",
            "typetype": typ,
            "pos": list(pos),
            "rot": list(rot),
            "objects": child["components"],
        }
    )


def cut_group(t, cuts, pos, rot):
    cuts = copy.deepcopy(cuts)

    def invert(items):
        for item in items:
            if isinstance(item, list):
                invert(item)
            elif item.get("type") in ("n", "negative"):
                item["type"] = "positive"
            elif item.get("type") == "rotation":
                item["typetype"] = "p"

    invert(cuts["components"])
    group(t, cuts, pos, rot, typ="n")


def seat(t, name, spec, top, clearance, endplay=0.1):
    depth = spec["depth"] + 2 * endplay
    # Dimensions come from the OOBB bearing lookup. A plain OOBB cylindrical
    # seat avoids its legacy through-relief cutter, which removes the entire
    # core for bearings with an ID below 20 mm.
    hole(t, spec["od"] / 2 + clearance, depth, z=top - depth)


def mounting_lugs(t, c, depth, z=0):
    for xy in c["housing_positions"]:
        cylinder(t, c.get("housing_lug_radius", 5), depth, z, xy=xy)


def radial_bore(t, radius, start, length, z, angle):
    cutter = blank()
    cylinder(cutter, radius, length)
    group(t, cutter, [*polar(start, angle), z], [0, 90, angle], typ="n")


def output_casing(**kwargs):
    c = resolve(kwargs)
    t = blank()
    h = c["housing_depth"]
    base = c["rear_retainer_depth"]
    # Open underside: lower this casing onto the bearing already on the mount.
    shell = blank()
    cylinder(shell, c["housing_radius"], h + base)
    mounting_lugs(shell, c, h + base)
    hole(shell, c["casing_bore_radius"], h + base)
    group(t, shell)
    for xy in c["ring_positions"]:
        cylinder(t, c["lobe_radius"], h, base, xy=xy)
        # Preserve the round working face, back it with parallel straight sides.
        angle = math.degrees(math.atan2(xy[1], xy[0]))
        length = c["housing_radius"] - c["pitch_radius"] - 0.2
        back = blank()
        add(
            back,
            "oobb_cube",
            pos=[c["pitch_radius"] + length / 2, 0, base],
            size=[length, 2 * c["lobe_radius"], h],
            zz="bottom",
        )
        group(t, back, rot=[0, 0, angle])
    shoulder = c["rear_bearing_top"] + c["bearing_endplay"] - c["casing_bottom_z"]
    cup = blank()
    cylinder(cup, c["bearing_cup_radius"], shoulder)
    hole(cup, c["output_bearing"]["od"] / 2 + c["bearing_seat_clearance"], shoulder)
    group(t, cup)
    bridge = blank()
    cylinder(bridge, c["housing_radius"], c["minimum_wall"], shoulder)
    hole(bridge, c["output_bearing"]["od"] / 2 - 1.3, c["minimum_wall"], z=shoulder)
    group(t, bridge)
    through(t, c["housing_positions"], base + h)
    nut_top = (
        c["case_nut_bottom"] - c["casing_bottom_z"] + oobb.gv("nut_depth_m3", "true")
    )
    for xy in c["housing_positions"]:
        add(
            t,
            "oobb_nut",
            "n",
            [*xy, nut_top + 0.1],
            radius_name="m3",
            depth=nut_top + 0.2,
            zz="top",
            overhang=True,
        )
    # One index dimple makes casing rotation and assembly orientation visible.
    hole(t, 1, 1, xy=(c["pitch_radius"] + 3, 0), z=base + h - 1)
    return t


def coupling_nut_pockets(t, c, top):
    """Shared production/coupon cutters: full-size outward loading channels."""

    def orient_hex(item):
        if isinstance(item, list):
            return [orient_hex(child) for child in item]
        if item.get("shape") == "polyg":
            return {
                "type": "rotation",
                "typetype": "p",
                "pos": [0, 0, 0],
                "rot": [0, 0, c["coupling_nut_hex_rotation"]],
                "objects": [item],
            }
        if "objects" in item:
            item["objects"] = orient_hex(item["objects"])
        return item

    for xy, angle in zip(c["coupling_positions"], c["coupling_nut_rotations"]):
        cutter = blank()
        add(
            cutter,
            "oobb_nut",
            "n",
            [*xy, top + 0.1],
            radius_name="m3",
            depth=oobb.gv("nut_depth_m3", "true") + 0.2,
            zz="top",
            overhang=True,
            clearance="right",
            extra_clearance=c["coupling_nut_side_clearance"],
            rot=[0, 0, angle],
        )
        # Retain OOBB's right clearance and overhang geometry. Only the hex
        # receives this extra rotation; the rectangular channel stays radial.
        t["components"].extend(orient_hex(cutter["components"]))
