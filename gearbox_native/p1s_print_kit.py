"""Editable Bambu Studio kit objects. Copy this module into standalone projects."""

from copy import deepcopy
from xml.etree import ElementTree as ET


CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"


def add_printable_copy(**kwargs):
    """Add one independently colourable physical piece. serial is unique across plates."""
    serial = kwargs["serial"]
    name = kwargs["name"]
    mesh = kwargs["mesh"]
    resources = kwargs["resources"]
    build = kwargs["build"]
    settings = kwargs["settings"]
    plate = kwargs["plate"]
    transform = kwargs["transform"]
    filament = kwargs.get("filament", 1)

    if serial < 1 or filament < 1:
        raise ValueError("Printable copy serials and filament slots start at one")
    volume_id = str(2 * serial - 1)
    object_id = str(2 * serial)
    volume = ET.SubElement(resources, f"{{{CORE}}}object", id=volume_id, type="model")
    volume.append(deepcopy(mesh))
    obj = ET.SubElement(resources, f"{{{CORE}}}object", id=object_id, type="model", name=name)
    components = ET.SubElement(obj, f"{{{CORE}}}components")
    ET.SubElement(components, f"{{{CORE}}}component", objectid=volume_id)
    ET.SubElement(build, f"{{{CORE}}}item", objectid=object_id, transform=transform, printable="1")

    # Bambu's editable object references a normal part by its mesh resource ID.
    config = ET.Element("object", id=object_id)
    settings.insert(list(settings).index(settings.find("plate")), config)
    ET.SubElement(config, "metadata", key="name", value=name)
    ET.SubElement(config, "metadata", key="extruder", value=str(filament))
    faces = str(len(mesh.find(f"{{{CORE}}}triangles")))
    ET.SubElement(config, "metadata", face_count=faces)
    part = ET.SubElement(config, "part", id=volume_id, subtype="normal_part")
    ET.SubElement(part, "metadata", key="name", value=name)
    ET.SubElement(part, "metadata", key="matrix", value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1")
    ET.SubElement(part, "mesh_stat", face_count=faces, edges_fixed="0", degenerate_facets="0",
                  facets_removed="0", facets_reversed="0", backwards_edges="0")

    instance = ET.SubElement(plate, "model_instance")
    ET.SubElement(instance, "metadata", key="object_id", value=object_id)
    ET.SubElement(instance, "metadata", key="instance_id", value="0")
    ET.SubElement(instance, "metadata", key="identify_id", value=str(serial))


def validate_editable_copies(**kwargs):
    """Check the object/part/plate contract written above before publishing a kit."""
    model = kwargs["model"]
    settings = kwargs["settings"]
    count = kwargs["count"]
    filament_count = kwargs["filament_count"]

    resources = model.findall(f"{{{CORE}}}resources/{{{CORE}}}object")
    resource_by_id = {obj.get("id"): obj for obj in resources}
    assignments = settings.findall("object")
    config_by_id = {obj.get("id"): obj for obj in assignments}
    build_ids = [item.get("objectid") for item in model.findall(f"{{{CORE}}}build/{{{CORE}}}item")]
    if (len(resource_by_id) != len(resources) or len(build_ids) != count or len(set(build_ids)) != count
            or len(assignments) != count or set(config_by_id) != set(build_ids)):
        raise ValueError("Each physical piece needs one distinct build object and one editable object record")
    plate_ids = []
    identify_ids = set()
    for instance in settings.findall("plate/model_instance"):
        values = {m.get("key"): m.get("value") for m in instance.findall("metadata")}
        if values["instance_id"] != "0" or values["identify_id"] in identify_ids:
            raise ValueError("Each kit piece needs its own instance zero and unique plate identifier")
        identify_ids.add(values["identify_id"])
        plate_ids.append(values["object_id"])
    if sorted(plate_ids) != sorted(build_ids):
        raise ValueError("Plate assignments disagree with printable objects")
    meshes = {}
    volume_ids = set()
    for object_id in build_ids:
        config = config_by_id[object_id]
        obj = resource_by_id[object_id]
        components = obj.findall(f"{{{CORE}}}components/{{{CORE}}}component")
        parts = config.findall("part")
        if len(components) != 1 or len(parts) != 1 or parts[0].get("subtype") != "normal_part":
            raise ValueError(f"Object {object_id} needs one editable normal part")
        volume_id = components[0].get("objectid")
        if volume_id in volume_ids or volume_id != parts[0].get("id"):
            raise ValueError(f"Object {object_id} has a shared or mismatched part ID")
        volume_ids.add(volume_id)
        mesh = resource_by_id[volume_id].find(f"{{{CORE}}}mesh")
        if mesh is None or mesh.find(f"{{{CORE}}}triangles") is None:
            raise ValueError(f"Missing production mesh for {object_id}")
        extruder = config.find("metadata[@key='extruder']")
        if extruder is None or not 1 <= int(extruder.get("value")) <= filament_count:
            raise ValueError(f"Invalid filament assignment for {object_id}")
        meshes[object_id] = mesh
    return meshes
