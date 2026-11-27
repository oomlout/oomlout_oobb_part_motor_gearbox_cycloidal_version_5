"""Publish the illustrated gearbox instructions from the verified native assembly."""
import argparse
import csv
from collections import Counter
import fnmatch
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

from gearbox_native.book import booklet, viewer
from gearbox_native.book.geometry import ROOT, digest, geometry_index, meshes
from working_oomp_populate import define_assembly_book, define_assembly_cards
from working_3mf import RECIPES, placements, read_recipe

BOOK = ROOT / "gearbox_native/book"
STYLE = dict(page_mm=[297,210], columns=2, rows=2, margin_mm=6, gutter_mm=4,
             border_radius_mm=3, border_width_pt=3., component_border_width_pt=1.1,
             thumbnail_height_mm=8.5, quantity_gap_mm=1., border="000000",
             font_body_pt=7, font_code_pt=6.4, font_url_prefix_pt=4.8, quantity_pt=5.8)


def inventory(part, proof):
    """A cap and its threaded shank are separate CAD bodies on the same screw."""
    catalogue = json.loads((ROOT / "presentation/project.json").read_text(encoding="utf8"))
    recipe = read_recipe(part, RECIPES / "version_11.json")
    printable = {name for plate in recipe["plates"] for group in plate["groups"]
                 for name, *_ in placements(group)}
    printed_labels = {key: next((p["name"] for p in catalogue["printed_parts"]
                                 if re.search(p["scene_pattern"], key)), key) for key in printable}
    printed_labels.update(carrier_top_nut_tray="Carrier nut tray",
                          shaft_mount_upper_nut_tray="Shaft nut tray")
    parts, objects, colours, examples = {}, {}, {}, {}
    for name in [n for step in proof["steps"] for n in step["moving"]]:
        if name in objects:
            raise ValueError(f"Duplicate CAD body {name}")
        stem = name.split(" (")[0]
        if name in printable:
            key = stem
            label = printed_labels[key]
            if key.startswith("printed_"):
                label = ("Contact" if "contact" in key else "Guide")+" sleeve 7 × 16 mm"
            record = {"name": label, "id": key, "provenance": "Native CAD body"}
            colour = ("yellow" if key.startswith(("printed_", "shaft_end")) else
                      "black" if key.startswith(("carrier", "shaft_cam")) else "teal")
            physical = name
        else:
            canonical = name.replace("hardware_ring_cap_heads","hardware_ring_M3_shanks").replace("hardware_drive_caps","hardware_drive_shanks")
            item, = [h for h in catalogue["hardware"] if re.search(h["scene_pattern"], canonical)]
            key = item["ref"]
            identity = item["oomp_id"]
            code = item["md5_6_alpha"]
            record = dict(name=item["name"], id=identity, md5=hashlib.md5(identity.encode()).hexdigest(),
                          md5_6_alpha=code, short_label="oom.lt/a/"+code, short_url="https://oom.lt/a/"+code,
                          url=item["url"], provenance=item["verification"])
            physical = canonical
            colour = "steel" if key in ("H1","H2","H6") else "screw"
        parts[key] = dict(record, key=key)
        objects[name] = (key, physical)
        colours[name] = colour
        examples.setdefault(key, physical)
    if printable != {name for name,(key,_) in objects.items() if key not in {h["ref"] for h in catalogue["hardware"]}}:
        raise ValueError("Print kit differs from assembled geometry")
    counts = Counter(dict((physical,key) for key,physical in objects.values()).values())
    for key, rec in parts.items():
        rec["quantity"] = counts[key]
    ring = counts["printed_contact_sleeve"]
    guides = counts["printed_drive_sleeve"]
    expected = {"H1": 2, "H2": 4, "H3": ring, "H4": guides + 2, "H5": 6,
                "H6": ring + guides + 2 + 6 + len(proof["gravity_supports"])}
    for key, count in expected.items():
        assert counts[key] == count, (key, counts[key], count)
    return parts, objects, colours, examples


def scenes(part, proof):
    parts, objects, colours, examples = inventory(part, proof)
    ratio = parts["printed_contact_sleeve"]["quantity"]
    built, steps, views = {}, [], []
    for number, definition in enumerate(define_assembly_cards(ratio), 1):
        offsets = {}
        for pattern, height in definition["add"].items():
            names = fnmatch.filter(objects, pattern)
            if not names or set(names) & (built.keys() | offsets.keys()):
                raise ValueError(f"Empty or repeated selection at step {number}: {pattern}")
            offsets.update({name: height*1.35 for name in names})
        placed = dict.fromkeys(built,0)
        # Keep the preassembled disc clear of the tall screws until its fasteners are fitted.
        for disc in "ab":
            if any(n.startswith("hardware_disc_"+disc+"_") for n in offsets):
                for n in ("rotor_"+disc, "rotor_"+disc+"_cap", "hardware_6704_disc_"+disc):
                    placed[n] = 54*1.35
        pairs = {objects[n] for n in offsets}
        loose = dict(Counter(k for k,_ in sorted(pairs)))
        assert len(loose) <= 4
        key = f"step_{number:02d}"
        steps.append(dict(key=key, title=definition["title"], action=definition["action"],
                          add=list(offsets), loose_parts=loose))
        placed.update(offsets)
        views.append(dict(key=key, offsets=placed, size=[900,680]))
        built.update(dict.fromkeys(offsets,0))
    if set(built) != set(objects):
        raise ValueError(f"Unassigned CAD bodies: {set(objects)-set(built)}")
    totals = sum((Counter(step["loose_parts"]) for step in steps),Counter())
    assert totals == Counter({key: p["quantity"] for key,p in parts.items()})
    views.append(dict(key="book_cover",offsets=built,size=[1280,900]))
    for key, physical in examples.items():
        views.append(dict(key="part_"+key,offsets={n:0 for n,p in objects.items() if p==(key,physical)},
                          size=[300,220]))
    data = dict(book=define_assembly_book(ratio),style=STYLE,configuration_title=f"Manual {ratio}:1 cycloidal gearbox",
                parts=parts,steps=steps,printed_keys=[k for k in parts if not k.startswith("H")],
                physical_item_count=sum(totals.values()),production_step_sha256=proof["assembled_step_sha256"])
    return data, dict(views=views,materials=colours)


def render(part, output, index, plan):
    raw = output / "render/raw"
    raw.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(json.dumps([index["step_sha256"],plan,digest(BOOK/"render.py")],
                                     sort_keys=True).encode()).hexdigest()
    stamp = raw.parent / "source.sha256"
    if stamp.exists() and stamp.read_text()==key and all((raw/(v["key"]+".png")).exists() for v in plan["views"]):
        return
    with tempfile.TemporaryDirectory() as folder:
        job = Path(folder)
        meshes(part,index,job,plan["materials"])
        (job/"scenes.json").write_text(json.dumps(dict(plan,output=str(raw))))
        subprocess.run(["blender","-b","--python-exit-code","1","-P",str(BOOK/"render.py"),"--",str(job)],check=True)
    for view in plan["views"]:
        file = raw / (view["key"]+".png")
        with Image.open(file) as image:
            box = image.getchannel("A").getbbox()
            if not box:
                raise ValueError(f"Empty render {file}")
            cropped = image.crop(box)
        cropped.save(file)
    stamp.write_text(key)


def publish(part, views=None):
    part = Path(part).resolve()
    export = json.loads((part / "native_export_verification.json").read_text())
    if not views and digest(ROOT / "version_11.solidcraft") != export.get("template_sha256",export["source_sha256"]):
        raise ValueError("The master has changed. Run python action_export_native.py --populate.")
    if digest(part / "gearbox_controls.solidcraft") != export["source_sha256"]:
        raise ValueError("The published master differs from its native export.")
    output = part / "assembly"
    output.mkdir(exist_ok=True)
    index = geometry_index(part, views)
    proof = json.loads((part/"assembly_verification.json").read_text())
    data,plan = scenes(part,proof)
    data["source_master_sha256"] = export["source_sha256"]
    data["parameters"] = {k:export["parameters"][k] for k in ("ring_count","eccentricity","guide_count")}
    if data["parts"]["printed_contact_sleeve"]["quantity"] != int(data["parameters"]["ring_count"]):
        raise ValueError("The assembly inventory differs from the evaluated ring pattern")
    data["source_logo_sha256"] = digest(BOOK / "oomlout.svg")
    render(part,output,index,plan)
    booklet.publish(output=output,data=data)
    booklet.review_outputs(output=output,data=data)
    viewer.publish(output=output,data=data)
    fields = ["key","name","quantity","id","md5","md5_6_alpha","short_url","provenance"]
    with (output/"parts.csv").open("w",newline="",encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file,fields,extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data["parts"].values())
    from gearbox_native.book.readmes import write
    write(part,data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", type=Path, help="Catalogue part to document")
    parser.add_argument("--views",type=Path,help="Verified native export, when refreshing the body index")
    args = parser.parse_args()
    active = json.loads((ROOT/"solidcraft/active_design.json").read_text())
    publish(args.part or ROOT/"parts"/active["part_id"],args.views)
    from gearbox_native.book.readmes import write_index
    write_index()

