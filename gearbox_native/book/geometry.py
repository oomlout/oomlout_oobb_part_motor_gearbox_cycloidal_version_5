"""Match the production STEP solids to SolidCraft's named-body index."""
import hashlib
import json
from pathlib import Path

from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.StlAPI import StlAPI_Writer

from gearbox_native.nema17_end_caps_checks import named_shapes

ROOT = Path(__file__).resolve().parents[2]


def panel_geometry(style):
    def size(axis, count):
        return (style["page_mm"][axis] - 2 * style["margin_mm"] -
                (count - 1) * style["gutter_mm"]) / count
    return size(0, style["columns"]), size(1, style["rows"])


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def geometry_index(part, views):
    proof = json.loads((part / "assembly_verification.json").read_text())
    step = part / "true.step"
    if digest(step) != proof["assembled_step_sha256"]:
        raise ValueError("The assembly access report belongs to another STEP file.")
    index = part / "assembly" / "geometry_index.json"
    if views:
        bodies = json.loads((views / "assembled_health.json").read_text())["bodies"]
        data = {"step_sha256": digest(step), "bodies": [
            {"name": body["name"], "bbox": body["bbox"]} for body in bodies]}
        index.write_text(json.dumps(data, indent=2))
    data = json.loads(index.read_text())
    if data["step_sha256"] != digest(step):
        raise ValueError("Regenerate the V11 native export to refresh the body index.")
    return data


def meshes(part, index, destination, wanted):
    shapes = named_shapes(part / "true.step", index)
    if set(shapes) - {"output_circle_plate", "output_lower_row_plate"} != set(wanted):
        raise ValueError("Assembly instructions do not cover all installed CAD bodies.")
    writer = StlAPI_Writer()
    writer.ASCIIMode = False
    for name in wanted:
        shape = shapes[name]
        BRepMesh_IncrementalMesh(shape, 0.065, False, 0.18, False).Perform()
        if not writer.Write(shape, str(destination / (name + ".stl"))):
            raise RuntimeError(name)

