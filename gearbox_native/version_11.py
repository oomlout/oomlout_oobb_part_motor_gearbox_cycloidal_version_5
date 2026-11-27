"""Create the V11 native document from the archived, checked manual V10 master."""

import copy
import hashlib
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLE = "version_11"
PART_ID = "oobb_part_motor_gearbox_cycloidal_version_11_20_to_1_reduction"
TRAYS = {"carrier_top_nut_tray": (894, 52), "shaft_mount_upper_nut_tray": (894, 105)}
SOURCE_HASH = "e4c646be6079b041450ba12ffcc06680de2377b67a075100331bacb06a9addbd"


def place_loose_contact_sleeves(document):
    # Keep the sleeves at their operating pitch in print mode. The spare area
    # behind the carrier caps also fits the denser ring without joining sleeves.
    component = next(c["id"] for c in document["components"] if c["name"] == "printed_contact_sleeve")
    sketches = [f["sketch"] for f in document["features"] if f["component"] == component and f["type"] == "sketch"]
    assert len(sketches) == 2  # outside circles and matching screw bores
    for sketch in sketches:
        pattern, = sketch["patterns"]
        centre_id = pattern["kind"]["center"]
        circle, = (c for c in sketch["curves"] if c["id"] in pattern["entities"])
        seed_id = f"p{circle['c']}"
        points = {p["id"]: p for p in sketch["points"]}
        for axis, centre, trig in (("x", 450, "cos"), ("y", 185, "sin")):
            shift = f"{centre} mm * layout_scale * print_layout"
            points[centre_id]["exprs"][axis] = shift
            points[seed_id]["exprs"][axis] = f"{shift} + pitch * {trig}(output_angle)"


def author(source, target):
    assert hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_HASH
    with zipfile.ZipFile(source) as z:
        doc = json.loads(z.read("document.json"))
        container = z.read("container.json")
    old = {f["id"]: f for f in doc["features"]}
    params = {p["name"]: p for p in doc["params"]}

    def uid():
        value = doc["next_id"]
        doc["next_id"] += 1
        return value

    def clone(features, substitutions=None, component=None):
        # Native sketches reference feature IDs and named model dimensions.
        mapping = {f["id"]: uid() for f in features}
        names = dict(substitutions or {})
        for name in sorted(set(re.findall(r'"(d\d+)"', json.dumps(features)))):
            new = "d" + str(10000 + uid())
            names[name] = new
            if name in params:
                p = dict(params[name], name=new)
                params[new] = p
                doc["params"].append(p)
        pattern = (
            re.compile(
                "|".join(
                    (
                        re.escape(k) + (r"(?!\d)" if re.fullmatch(r"d\d+", k) else "")
                        for k in sorted(names, key=len, reverse=True)
                    )
                )
            )
            if names
            else None
        )

        def sub(s):
            return pattern.sub(lambda m: names[m.group()], s) if pattern else s

        rows = json.loads(sub(json.dumps(features)))
        # Tool bodies need distinct native names. Their OOBB cutter dimensions
        # must continue to use the original shared parameters.
        for original, copied in zip(features, rows):
            if "extent" in original:
                copied["extent"] = copy.deepcopy(original["extent"])
            if isinstance(original.get("sketch"), dict):
                for a, b in zip(
                    original["sketch"]["points"], copied["sketch"]["points"]
                ):
                    if "exprs" in a:
                        b["exprs"] = copy.deepcopy(a["exprs"])
        for f in rows:
            f["id"] = mapping[f["id"]]
            f["name"] = "V11_" + str(f["id"]) + "_" + f["name"]
            if component is not None:
                f["component"] = component
            if isinstance(f.get("sketch"), int):
                f["sketch"] = mapping[f["sketch"]]
        return rows

    def replace(start, end, rows):
        fs = doc["features"]
        i = fs.index(old[start])
        j = fs.index(old[end])
        fs[i : j + 1] = rows

    # Two copies of the original socket/bridge at the starting end and two
    # copies of the actual OOBB overhang nut cutter at the finishing end.
    for start, end, src, stop, sign in [
        (910, 932, 904, 909, "-"),
        (783, 788, 789, 811, ""),
    ]:
        rows = clone(
            [old[i] for i in range(src, stop + 1) if i in old],
            {"cut_166": "v11_second_nut"},
        )
        for f in rows:
            if isinstance(f.get("sketch"), dict):
                for pt in f["sketch"]["points"]:
                    for axis, s in pt.get("exprs", {}).items():
                        pt["exprs"][axis] = s.replace(
                            sign + "shaft_tie_pitch / sqrt(2)",
                            ("" if sign else "-") + "shaft_tie_pitch / sqrt(2)",
                        )
            if f.get("translate") and "shaft_tie_pitch" in f["translate"][0]:
                f["translate"][:2] = ["-shaft_tie_pitch / sqrt(2)"] * 2
        replace(start, end, rows)
    turn = clone(
        [old[1304]],
        {"hardware_shaft_M3x35_upper": "hardware_shaft_M3x35_lower"},
        old[1252]["component"],
    )
    doc["features"][
        doc["features"].index(old[1252]) : doc["features"].index(old[1252])
    ] = turn
    old[1254]["translate"][2] = old[1307]["translate"][2]
    old[1316]["translate"][2] = old[1263]["translate"][2]
    # Divide the two first-end parts across the existing hex wells. Each
    # tray keeps the native bearing lands, hex orientation and guide bores.
    for name, h in [
        ("carrier_top", "carrier_core"),
        ("shaft_mount_upper", "shaft_mount_depth"),
    ]:
        comp = next(c for c in doc["components"] if c["name"] == name)
        occ = next(o for o in doc["occurrences"] if o["component"] == comp["id"])
        tray = name + "_nut_tray"
        cid = uid()
        doc["components"].append(dict(comp, id=cid, name=tray))
        doc["occurrences"].append(dict(occ, id=uid(), name=tray + ":1", component=cid))
        local = [f for f in old.values() if f["component"] == comp["id"]]
        placement = [
            f
            for f in old.values()
            if f["type"] == "move" and f.get("bodies") == [name] and f not in local
        ]
        assert placement and placement[-1]["translate"]
        copies = clone(local, {name: tray, "cut_": "v11_tray_cut_"}, cid)

        def trim(body, owner, z, depth):
            sk, ex = clone([old[783], old[784]], {"shaft_end_lower": body}, owner)
            sk["plane"]["distance"] = z
            point = sk["sketch"]["points"][1]
            point["exprs"] = {"x": "0 mm", "y": "0 mm"}
            point["pos"] = [0, 0]
            size = sk["sketch"]["constraints"][0]
            size["value"] = 120
            params[size["param"]]["expr"] = "120 mm"
            sk["sketch"]["curves"][0]["r"] = 60
            ex["extent"]["distance"] = depth
            return [sk, ex]

        cut = h + " - v11_tray_depth"
        i = doc["features"].index(local[-1]) + 1
        doc["features"][i:i] = trim(name, comp["id"], cut, "v11_tray_depth + 0.1 mm")
        moves = clone(placement, {name: tray}, cid)
        x, y = TRAYS[tray]
        moves[-1]["translate"] = [
            f"{x} mm * layout_scale * print_layout",
            f"{y} mm * layout_scale * print_layout",
            moves[-1]["translate"][2]
            + f" + 0.5 * explode * (1-print_layout) - ({cut}) * print_layout",
        ]
        doc["features"] += (
            copies + trim(tray, cid, "-0.1 mm", cut + " + 0.1 mm") + moves
        )
    doc["params"].append(
        dict(
            name="v11_tray_depth",
            expr="1.4 mm",
            unit="mm",
            model=False,
            comment="Gravity-loading split across the starting-end captive nuts.",
        )
    )
    live = {f["id"] for f in doc["features"]}
    doc["timeline_groups"] = [
        dict(g, features=[i for i in g["features"] if i in live])
        for g in doc["timeline_groups"]
        if any(i in live for i in g["features"])
    ]
    place_loose_contact_sleeves(doc)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("document.json", json.dumps(doc))
        z.writestr("container.json", container)


if __name__ == "__main__":
    author(
        ROOT / "simple_double_bearing_version_2.solidcraft",
        ROOT / "version_11.solidcraft",
    )
