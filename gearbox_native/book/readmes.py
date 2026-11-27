"""Build the project overview and the bench instructions from the booklet manifest."""
from pathlib import Path
from PIL import Image, ImageOps
from .geometry import ROOT

AI = ("This is an entirely AI-generated coding project. The source code is largely unreadable "
      "by humans, but usable generated files are included. It is published so others can "
      "use their own AI tools to understand, modify and regenerate the design.")
NOTICE = "> AI-generated CAD images and instructions. Errors possible."


def write(part, data):
    book = data["book"]
    path = part/"assembly"
    thumbs = path/"readme"
    thumbs.mkdir(exist_ok=True)
    with Image.open(path/"render/raw/book_cover.png") as image:
        canvas = Image.new("RGB",image.size,"#fffdf9")
        canvas.paste(image,mask=image.getchannel("A"))
        canvas.thumbnail((800,640))
        canvas.save(thumbs/"assembled.png")
        canvas.thumbnail((220,180))
        canvas.save(thumbs/"index.png")
    for step in data["steps"]:
        key = step["key"]
        with Image.open(path/"cards"/(key+".png")) as image:
            ImageOps.contain(image,(400,300)).save(thumbs/(key+".png"))
    viewer = book["viewer_url"]
    downloads = viewer + "downloads/"
    pdf = "assembly/assembly_instructions.pdf"
    ratio = int(data["parameters"]["ring_count"])
    eccentricity = data["parameters"]["eccentricity"]
    lines = [f"# Manual {ratio}:1 cycloidal gearbox", "", "## Summary", "", book["description"],
             "", NOTICE, "", "![Assembled square-flange gearbox](assembly/readme/assembled.png)",
             "", "## Details", "",
             f"The two cycloids each have {ratio - 1} lobes and run on opposed cams with {eccentricity:g} mm eccentricity. "
             f"The turquoise casing carries {ratio} contacts. Fixing the casing instead gives a {ratio - 1}:1 output at the black carrier, opposite the input.",
             "", f"Print each plate of the [editable P1S kit](working.3mf) once. It contains {data['printed_piece_count']} printed pieces for the square-flange build, including {ratio} loose contact sleeves. "
             "The [print guide](PRINT_KIT.md) lists the plate colours and the alternative flanges and contact ring.",
             "", "[Editable SolidCraft preset](gearbox_controls.solidcraft) · [Shared source master](../../version_11.solidcraft) · [Assembled CAD](true.solidcraft) · [Exploded CAD](exploded.solidcraft) · "
             "[Full print layout](3dpr.scad) · [Individual STLs](native_parts/)",
             "", "Edit the shared master to change all gearboxes. Run `python action_make_all.py` to regenerate the populated ratios. "
             "Run `python working.py --assembly-only` to rebuild these instructions from the verified export.",
             "", "## Parts", "", "[![Labelled exploded assembly](exploded_labeled.png)](exploded_labeled.png)",
             "", "Hardware for one square-flange gearbox with all mounting pockets populated. External frame, drive and load fasteners depend on the installation.",
             "", "| Hardware | Size or use | Quantity | OOMP code |", "| --- | --- | ---: | --- |"]
    uses = {"H1":"50 × 65 × 7 mm, one at each end", "H2":"20 × 27 × 4 mm, two shaft and two disc bearings",
            "H3":f"{ratio} casing contacts","H4":"Six guides and two shaft ties","H5":"Three per cycloid",
            "H6":f"{ratio} casing, 6 guides, 2 ties, 6 disc clamps and 24 mounting nuts"}
    for key,use in uses.items():
        p = data["parts"][key]
        lines.append(f"| [{p['name']}]({p['url']}) | {use} | {p['quantity']} | [{p['md5_6_alpha']}]({p['short_url']}) |")
    lines += ["","[Complete printed and hardware inventory](assembly/parts.csv)", "", "## Assembly", "",
              f"[Open the assembly viewer]({viewer}) · [Download the offline viewer (ZIP)]({downloads}assembly-viewer.zip) · [Download the landscape A4 booklet]({pdf})",
              "", "Open the downloaded HTML file in a browser for offline use. The viewer starts at steps 1–4. "
              "Print the PDF at actual size, using booklet imposition only once if folding it.",
              "", "Prepare a 2.5 mm hex key for the socket caps and a 2 mm key for the countersunk screws. "
              "Lay out the A and B cam pairs separately. The drawings show the native upper end on the bench, with the shaft screws pointing up.", ""]
    for i,step in enumerate(data["steps"],1):
        k = step["key"]
        lines.extend([f"{i}. **{step['title']}.** {step['action']}", "",
                      f"    [![Step {i}. {step['title']}](assembly/readme/{k}.png)](assembly/cards/{k}.png)", ""])
    lines.extend(["The assembly sequence and nut access have been checked in CAD. Physical fit and load capacity remain unverified.", ""])
    (part/"README.md").write_text("\n".join(lines),encoding="utf8", newline="\n")


def write_index():
    from working_oomp_populate import build_oomp_id, get_options, define_assembly_book

    options = get_options()
    first = build_oomp_id(options[0])
    lines = [
        "# OOBB cycloidal gearbox", "",
        "Hold the black inner carrier fixed and drive the centre shaft. The ratio gives the number of input turns for one turn of the turquoise outer casing. Each ratio uses two opposed cycloids, square OOBB flanges and 6810 casing bearings.", "",
        f"[![Assembled gearbox](parts/{first}/assembly/readme/assembled.png)](parts/{first}/README.md)", "",
        "| Reduction | CAD and code | Print kit | Build notes | Assembly viewer | Booklet | Hardware |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for option in options:
        ratio = option["reduction"]
        folder = "parts/" + build_oomp_id(option)
        viewer = define_assembly_book(ratio)["viewer_url"]
        lines.append(f"| **{ratio}:1** | [SolidCraft]({folder}/gearbox_controls.solidcraft) · [Populate code](working_oomp_populate.py) | "
                     f"[4-plate 3MF]({folder}/working.3mf) | [Illustrated guide]({folder}/README.md#assembly) | "
                     f"[Open viewer]({viewer}) | [PDF]({folder}/assembly/assembly_instructions.pdf) | [BOM]({folder}/assembly/parts.csv) |")
    lines += ["", "## Regenerate", "",
              "Add the integer reduction to `RATIOS` in the [populate definition](working_oomp_populate.py). "
              "Run `python action_make_all.py` from the repository root to build each editable preset, export and check its geometry, and regenerate its print kit, guide and table row. "
              "The [shared native master](version_11.solidcraft) contains the design. Above 20:1, eccentricity is 30 mm divided by the reduction so both presets can use the same casing diameter and sleeve size. The build checks the resulting profile, assembly paths and print plates.",
              "", "The [build entry point](action_make_all.py) uses the configured SolidCraft Python environment, Blender and Bambu Studio.",
              "", AI, "", NOTICE, ""]
    (ROOT/"README.md").write_text("\n".join(lines), encoding="utf8", newline="\n")
