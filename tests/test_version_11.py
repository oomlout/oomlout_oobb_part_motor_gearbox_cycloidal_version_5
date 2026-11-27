import json
import re
import zipfile

from gearbox_native.project import PROJECT, active_part
from gearbox_native.version_11 import PART_ID, TRAYS
from working_oomp_populate import build_oomp_id, get_options


def test_populated_ratios_have_distinct_exports_and_instructions():
    options = get_options()
    ids = {build_oomp_id(option) for option in options}
    assert {option["reduction"] for option in options} >= {20, 30}
    assert PART_ID == active_part().name and PART_ID in ids
    for directory in ("parts", "parts_source"):
        assert {entry.name for entry in (PROJECT / directory).iterdir()} == ids
    for option in options:
        part = PROJECT / "parts" / build_oomp_id(option)
        ratio = option["reduction"]
        with zipfile.ZipFile(PROJECT / option["native_master"]) as base:
            expected = json.loads(base.read("document.json"))
        for param in expected["params"]:
            if param["name"] in option["native_parameters"]:
                assert param["name"] in expected["favorites"]
                param["expr"] = option["native_parameters"][param["name"]]
        with zipfile.ZipFile(part / "gearbox_controls.solidcraft") as preset:
            assert json.loads(preset.read("document.json")) == expected
        report = json.loads((part / "native_export_verification.json").read_text())
        assert report["parameters"]["ring_count"] == ratio
        motion = json.loads((part / "motion_verification.json").read_text())
        assert list(motion["lobes_per_printed_half"].values()) == [ratio - 1] * 4
        plates = json.loads((part / "P1S_VALIDATION.json").read_text())["production_plates"]
        assert len(plates) == 4 and sum(p["objects"] for p in plates) == ratio + 28
        assert all(p["filament_changes"] == 0 and not p["warnings"] for p in plates)
        proof = json.loads((part / "assembly_verification.json").read_text())
        assert all(s["clear"] for s in proof["steps"]) and not proof["clashes"]
        manifest = json.loads((part / "assembly/assembly_manifest.json").read_text())
        assert manifest["parts"]["printed_contact_sleeve"]["quantity"] == ratio
        assert manifest["parts"]["H6"]["quantity"] == ratio + 38
        assert (part / "working.3mf").is_file()
        table = (PROJECT / "README.md").read_text(encoding="utf8").splitlines()
        row, = (line for line in table if line.startswith(f"| **{ratio}:1**"))
        for href in re.findall(r"\]\(([^)]+)\)", row):
            if href.startswith("https://"):
                assert href == manifest["book"]["viewer_url"]
            else:
                assert (PROJECT / href.split("#")[0]).is_file(), href
    with zipfile.ZipFile(PROJECT / option["native_master"]) as archive:
        document = json.loads(archive.read("document.json"))
    components = {c["name"]: c for c in document["components"]}
    for tray in TRAYS:
        assert (
            components[tray]["parent"]
            == components[tray.removesuffix("_nut_tray")]["parent"]
        )
    assert all(
        (PROJECT / "releases/version_10" / name).exists()
        for name in (
            "working_oomp_populate.py",
            "sources.json",
            "build_inventory.json",
            "outputs_inventory.json",
        )
    )


def test_one_populate_entry_defines_another_ratio(monkeypatch):
    import working_oomp_populate as populate

    monkeypatch.setattr(populate, "RATIOS", (20, 24, 30))
    option = populate.get_options([24])[0]
    assert build_oomp_id(option).endswith("_24_to_1_reduction")
    assert option["native_parameters"]["reduction"] == "24"
    assert populate.define_assembly_book(24)["viewer_url"].endswith("/24-to-1/")
    assert any("24 yellow contact sleeves" in card["action"]
               for card in populate.define_assembly_cards(24))


def test_same_end_ties_and_gravity_loaded_nuts():
    proof = json.loads((active_part() / "assembly_verification.json").read_text())
    assert proof["shaft_thread_engagement_mm"] == [2.5, 2.5]
    assert len(proof["gravity_supports"]) == 24
    assert all(step["clear"] for step in proof["steps"])
    assert not proof["clashes"]


def test_rotors_cams_bearings_and_casing_keep_the_accepted_geometry():
    def document(file):
        with zipfile.ZipFile(PROJECT / file) as archive:
            return json.loads(archive.read("document.json"))

    old = document("simple_double_bearing_version_2.solidcraft")
    new = document("version_11.solidcraft")
    params = {p["name"]: p for p in new["params"]}
    assert all(p == params[p["name"]] for p in old["params"])
    names = {c["id"]: c["name"] for c in old["components"]}
    protected = ("rotor_", "shaft_cam_", "hardware_6810", "hardware_6704", "output_")
    by_id = {f["id"]: f for f in new["features"]}
    for feature in old["features"]:
        bodies = feature.get("bodies", [])
        if names.get(feature["component"], "").startswith(protected) or any(
            body.startswith(protected) for body in bodies
        ):
            assert by_id[feature["id"]] == feature
