"""Build an editable Bambu project from a gearbox's native, print-oriented STLs."""

import argparse
import hashlib
import io
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from collections import Counter
from copy import deepcopy
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import trimesh
from PIL import Image, ImageDraw

from gearbox_native.p1s_print_kit import (
    CORE,
    add_printable_copy,
    validate_editable_copies,
)

ROOT = Path(__file__).resolve().parent
RECIPES = ROOT / "source_file/print_kit"
STARTER_SHA = "2dbe41cec9ed16e34dbe2c74a136f2b2d7bc7ec4a4ba0353d2cfd04c581c8d9e"
SETTINGS = "Metadata/project_settings.config"
C = "{" + CORE + "}"
ET.register_namespace("", CORE)


def xml(element):
    return ET.tostring(element, encoding="utf-8", xml_declaration=True)


def placements(group):
    if "series" in group:
        stem = group["series"]
        names = [
            stem if i == 1 else f"{stem} ({i})" for i in range(1, group["count"] + 1)
        ]
    else:
        names = group["parts"]
    cols = group.get("columns", len(names))
    for i, name in enumerate(names):
        x = group["start"][0] + (i % cols) * group["step"][0]
        y = (
            group["start"][1]
            + (i // cols if "columns" in group else i) * group["step"][1]
        )
        yield name, x, y


def load_mesh(path):
    mesh = trimesh.load_mesh(path)
    if not mesh.is_volume or not mesh.is_watertight or mesh.body_count != 1:
        raise ValueError(f"Expected one closed printable solid: {path}")
    if abs(mesh.bounds[0, 2]) > 0.01:
        raise ValueError(f"Source is not in native print orientation: {path}")
    cx, cy, _ = mesh.bounds.mean(axis=0)
    mesh.apply_translation([-cx, -cy, -mesh.bounds[0, 2]])
    element = ET.Element(C + "mesh")
    vertices = ET.SubElement(element, C + "vertices")
    for x, y, z in mesh.vertices:
        ET.SubElement(vertices, C + "vertex", x=f"{x:.7f}", y=f"{y:.7f}", z=f"{z:.7f}")
    faces = ET.SubElement(element, C + "triangles")
    for a, b, c in mesh.faces:
        ET.SubElement(faces, C + "triangle", v1=str(a), v2=str(b), v3=str(c))
    return mesh, element


def png(image, size):
    buf = io.BytesIO()
    image.resize((size, size), Image.Resampling.LANCZOS).save(buf, format="PNG")
    return buf.getvalue()


def read_recipe(part, recipe_path):
    recipe = json.loads(recipe_path.read_text(encoding="utf8"))
    parameters = json.loads((part / "native_export_verification.json").read_text())["parameters"]
    recipe["title"] = recipe["title"].format(reduction=int(parameters["reduction"]))
    for plate in recipe["plates"]:
        for group in plate["groups"]:
            if isinstance(group.get("count"), str):
                group["count"] = int(parameters[group["count"]])
    return recipe


def publish(part, recipe_path):
    part, recipe_path = Path(part), Path(recipe_path)
    recipe = read_recipe(part, recipe_path)
    starter = RECIPES / "default.3mf"
    if hashlib.sha256(starter.read_bytes()).hexdigest() != STARTER_SHA:
        raise ValueError("Unexpected OOBB P1S template")
    kit = part / recipe["file"]
    meshes = part / "native_parts"
    with zipfile.ZipFile(starter) as template:
        settings_bytes = template.read(SETTINGS)
        profile = json.loads(settings_bytes)
        colours = profile["filament_colour"]
        plate_template = ET.fromstring(
            template.read("Metadata/model_settings.config")
        ).find("plate")
        payload = {
            k: template.read(k)
            for k in (
                "[Content_Types].xml",
                "_rels/.rels",
                "Metadata/slice_info.config",
            )
        }
    payload[SETTINGS] = settings_bytes
    model = ET.Element(C + "model", unit="millimeter", attrib={"xml:lang": "en-US"})
    for k, v in [
        ("Application", "BambuStudio-02.09.02.62"),
        ("BambuStudio:3mfVersion", "1"),
        ("Title", recipe["title"]),
    ]:
        ET.SubElement(model, C + "metadata", name=k).text = v
    resources = ET.SubElement(model, C + "resources")
    build = ET.SubElement(model, C + "build")
    config = ET.Element("config")
    grid_width = math.ceil(math.sqrt(len(recipe["plates"])))
    seen = set()
    rows = []
    expected = {}
    for num, spec in enumerate(recipe["plates"], 1):
        plate = deepcopy(plate_template)
        config.append(plate)
        for tag in list(plate):
            key = tag.get("key")
            if key in ("thumbnail_no_light_file", "top_file", "pick_file"):
                plate.remove(tag)
            elif key in ("plater_id", "plater_name", "thumbnail_file"):
                tag.set(
                    "value",
                    {
                        "plater_id": str(num),
                        "plater_name": spec["name"],
                        "thumbnail_file": f"Metadata/plate_{num}.png",
                    }[key],
                )
        slot = spec["filament"]
        colour = colours[slot - 1]
        if profile["filament_type"][slot - 1] != "PLA":
            raise ValueError(f"Unexpected material on plate {num}")
        ox, oy = 307.2 * ((num - 1) % grid_width), -307.2 * ((num - 1) // grid_width)
        regions = [(0, 0, 18, 28)]  # P1S cutter exclusion
        preview = Image.new("RGB", (512, 512), "#efefeb")
        draw = ImageDraw.Draw(preview)
        for group in spec["groups"]:
            for name, x, y in placements(group):
                if name in seen:
                    raise ValueError(f"Duplicate production piece: {name}")
                seen.add(name)
                serial = len(seen)
                mesh, geometry = load_mesh(meshes / (name + ".stl"))
                lo, hi = mesh.bounds
                box = (x + lo[0], y + lo[1], x + hi[0], y + hi[1])
                if min(box[:2]) < 3 or max(box[2:]) > 253:
                    raise ValueError(f"Off bed: {name}")
                for a, b, c, d in regions:
                    if not (
                        box[0] >= c + 3
                        or box[1] >= d + 3
                        or box[2] <= a - 3
                        or box[3] <= b - 3
                    ):
                        raise ValueError(f"Insufficient plate clearance: {name}")
                regions.append(box)
                label = name
                if "series" in group:
                    copy_num = re.search(r"\((\d+)\)$", name)
                    label = f"{group['series']} ({copy_num[1] if copy_num else 1} of {group['count']})"
                transform = f"1 0 0 0 1 0 0 0 1 {x+ox:.7f} {y+oy:.7f} 0"
                add_printable_copy(
                    serial=serial,
                    name=label,
                    mesh=geometry,
                    resources=resources,
                    build=build,
                    settings=config,
                    plate=plate,
                    transform=transform,
                    filament=slot,
                )
                expected[str(2 * serial)] = (mesh.extents, slot, str(num), transform)
                for tri in mesh.triangles[mesh.face_normals[:, 2] > 0.001]:
                    draw.polygon(
                        [(2 * (x + v[0]), 512 - 2 * (y + v[1])) for v in tri],
                        fill=colour,
                    )
        rows.append(f"| {num} | {spec['name']} | {slot} | {len(regions)-1} |")
        payload[f"Metadata/plate_{num}.png"] = png(preview, 512)
        payload[f"Metadata/plate_{num}_small.png"] = png(preview, 128)
    all_stems = {p.stem for p in meshes.glob("*.stl")}
    excluded = set(recipe["exclude"])
    if seen & excluded or seen | excluded != all_stems:
        raise ValueError(
            f"Review the print BOM: {(seen | excluded) ^ all_stems}, duplicated: {seen & excluded}"
        )
    ET.SubElement(config, "assemble")
    payload["Metadata/model_settings.config"] = xml(config)
    payload["3D/3dmodel.model"] = xml(model)
    payload["Metadata/filament_sequence.json"] = json.dumps(
        {f"plate_{n}": {"sequence": []} for n in range(1, len(rows) + 1)}
    )
    del model, resources, build, config
    with tempfile.NamedTemporaryFile(dir=part, suffix=".tmp", delete=False) as f:
        temp = Path(f.name)
    try:
        with zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as z:
            for k, v in payload.items():
                z.writestr(k, v)
        with zipfile.ZipFile(temp) as z:
            assert z.testzip() is None and z.read(SETTINGS) == settings_bytes
            model = ET.fromstring(z.read("3D/3dmodel.model"))
            config = ET.fromstring(z.read("Metadata/model_settings.config"))
            after = validate_editable_copies(
                model=model,
                settings=config,
                count=len(seen),
                filament_count=len(colours),
            )
            for item in model.find(C + "build"):
                oid = item.get("objectid")
                dims, slot, plate_id, transform = expected[oid]
                pts = np.array(
                    [
                        [float(v.get(ax)) for ax in "xyz"]
                        for v in after[oid].find(C + "vertices")
                    ]
                )
                assert np.allclose(np.ptp(pts, axis=0), dims, atol=1e-6)
                assert item.get("transform") == transform
                assert config.find(
                    f"object[@id='{oid}']/metadata[@key='extruder']"
                ).get("value") == str(slot)
                owners = [
                    p
                    for p in config.findall("plate")
                    if p.find(
                        f"model_instance/metadata[@key='object_id'][@value='{oid}']"
                    )
                    is not None
                ]
                assert (
                    len(owners) == 1
                    and owners[0].find("metadata[@key='plater_id']").get("value")
                    == plate_id
                )
        temp.replace(kit)
    finally:
        temp.unlink(missing_ok=True)
    instructions = (RECIPES / "PRINT_KIT.md").read_text(encoding="utf8")
    instructions = instructions.replace("{part_id}",part.name).replace("{kit}", kit.name).replace(
        "{table}", "\n".join(rows)
    )
    instructions = instructions.replace("{recipe}", recipe_path.name).replace(
        "{count}", str(len(seen))
    )
    instructions = instructions.replace("{excluded}", ", ".join(sorted(excluded)))
    (part / "PRINT_KIT.md").write_text(instructions, encoding="utf8", newline="\n")
    return kit


def slice_project(project, output):
    binary = shutil.which("bambu-studio") or str(
        Path(os.environ["ProgramFiles"]) / "Bambu Studio/bambu-studio.exe"
    )
    output.mkdir(parents=True, exist_ok=False)
    subprocess.run(
        [binary, "--slice", "0", "--outputdir", str(output), str(project.resolve())],
        check=True,
    )
    validate_slice(project, output)


def validate_slice(project, output):
    """Compare the slicer's per-plate object list to the saved editable project."""
    report = json.loads((output / "result.json").read_text(encoding="utf8"))
    with zipfile.ZipFile(project) as z:
        config = ET.fromstring(z.read("Metadata/model_settings.config"))
    plates = config.findall("plate")
    names = {
        obj.get("id"): obj.find("metadata[@key='name']").get("value")
        for obj in config.findall("object")
    }
    expected = {
        int(plate.find("metadata[@key='plater_id']").get("value")): Counter(
            names[obj.get("value")]
            for obj in plate.findall("model_instance/metadata[@key='object_id']")
        )
        for plate in plates
    }
    assert not report["return_code"] and sorted(
        p["id"] for p in report["sliced_plates"]
    ) == list(range(1, len(plates) + 1))
    for p in report["sliced_plates"]:
        gcode = output / f"plate_{p['id']}.gcode"
        if Counter(obj["name"] for obj in p["objects"]) != expected[p["id"]]:
            raise ValueError(f"Wrong objects sliced on plate {p['id']}")
        if p["warning_message"] or not gcode.is_file() or not gcode.stat().st_size:
            raise ValueError(f"Check slice for plate {p['id']}: {p['warning_message']}")
    with zipfile.ZipFile(project) as project_file:
        hashes = {key: hashlib.sha256(project_file.read(key)).hexdigest() for key in
                  ["3D/3dmodel.model", "Metadata/model_settings.config", SETTINGS]}
    dest = project.parent / "P1S_VALIDATION.json"
    previous = json.loads(dest.read_text()) if dest.exists() else {}
    with (output / "plate_1.gcode").open("rb") as first_plate:
        version = re.search(rb"Bambu\s*Studio\s+([0-9.]+)", first_plate.read(8192), re.I)
    slicer = "Bambu Studio" + (" " + version[1].decode() if version else "")
    result = {"project": project.name, "slicer": slicer, "sha256": hashes, "production_plates": [
        {"plate": p["id"], "objects": len(p["objects"]), "filament_slots": [f["id"] for f in p["filaments"]],
         "estimated_grams": round(sum(f["total_used_g"] for f in p["filaments"]), 2),
         "filament_changes": p["filament_change_times"], "warnings": p["warning_message"]}
        for p in report["sliced_plates"]]}
    if hashes == previous.get("sha256") and "disposable_edit" in previous:
        result["disposable_edit"] = previous["disposable_edit"]
    dest.write_text(json.dumps(result, indent=2) + "\n", newline="\n")
    print(f"Validated {len(plates)} sliced plates in {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--part",
        type=Path,
        help="Published part folder (defaults to the active gearbox)",
    )
    parser.add_argument(
        "--recipe", type=Path, help="Plate/BOM JSON (defaults to the active version)"
    )
    parser.add_argument(
        "--slice-to",
        type=Path,
        help="Also validate the kit using a new scratch directory",
    )
    args = parser.parse_args()
    active = json.loads((ROOT / "solidcraft/active_design.json").read_text())
    kit = publish(
        args.part or ROOT / "parts" / active["part_id"],
        args.recipe or RECIPES / (active["version"] + ".json"),
    )
    print(kit, flush=True)
    if args.slice_to:
        slice_project(kit, args.slice_to)
