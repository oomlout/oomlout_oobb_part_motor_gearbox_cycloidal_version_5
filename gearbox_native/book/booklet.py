"""Reader-order, signature-padded OOBB book with four pictorial steps per sheet."""
import copy
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageOps
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


def page_plan(**kwargs):
    kwargs = copy.deepcopy(kwargs)
    kwargs.setdefault("steps_per_page", 4)
    kwargs.setdefault("signature_pages", 4)
    kwargs.setdefault("summary_step", True)
    instruction_pages = math.ceil(kwargs["step_count"]/kwargs["steps_per_page"])
    pages = [{"kind": "cover"}, {"kind": "details"}]
    pages.extend({"kind": "instructions", "group": i} for i in range(instruction_pages))
    if kwargs["summary_step"]:
        pages.append({"kind": "summary", "number": kwargs["step_count"]+1})
    padding = (-(len(pages)+2)) % kwargs["signature_pages"]
    pages.extend({"kind": "spacer"} for _ in range(padding))
    pages.extend([{"kind": "parts"}, {"kind": "back"}])
    return pages


def fonts():
    names = {
        "BookRegular": "segoeui.ttf",
        "BookBold": "segoeuib.ttf",
        "BookLight": "segoeuil.ttf",
        "BookMedium": "seguisb.ttf",
        "BookMono": "consola.ttf",
        "BookMonoBold": "consolab.ttf",
    }
    if all((Path("C:/Windows/Fonts")/filename).exists() for filename in names.values()):
        for name, filename in names.items():
            pdfmetrics.registerFont(TTFont(name, str(Path("C:/Windows/Fonts")/filename)))
        return "BookRegular", "BookBold", "BookLight", "BookMedium", "BookMono", "BookMonoBold"
    return "Helvetica", "Helvetica-Bold", "Helvetica", "Helvetica-Bold", "Courier", "Courier-Bold"


def inventory_groups(**kwargs):
    """Merge identical purchased items used in different assembly roles."""
    data = kwargs["data"]
    groups = {"printed": [], "hardware": []}
    merged = {}
    for key, part in data["parts"].items():
        if key in data["printed_keys"]:
            groups["printed"].append(copy.deepcopy(part))
        elif part["id"] in merged:
            merged[part["id"]]["quantity"] += part["quantity"]
        else:
            item = copy.deepcopy(part)
            merged[part["id"]] = item
            groups["hardware"].append(item)
    assert sum(p["quantity"] for group in groups.values() for p in group) == data["physical_item_count"]
    return groups


def publish(**kwargs):
    from .geometry import panel_geometry
    output = Path(kwargs["output"])
    data = kwargs["data"]
    style, book = data["style"], data["book"]
    regular, bold, light, medium, mono, mono_bold = fonts()
    page_w, page_h = [v*mm for v in style["page_mm"]]
    card_w, card_h = [v*mm for v in panel_geometry(style)]
    margin, gutter = style["margin_mm"]*mm, style["gutter_mm"]*mm
    per_page = style["columns"]*style["rows"]
    plan = page_plan(step_count=len(data["steps"]), steps_per_page=per_page, signature_pages=book["signature_pages"], summary_step=book["summary_step"])
    groups = inventory_groups(data=data)
    data["summary_inventory"] = groups
    data["book_pages"] = plan
    data["printed_piece_count"] = sum(data["parts"][key]["quantity"] for key in data["printed_keys"])
    (output/"assembly_manifest.json").write_text(json.dumps(data, indent=2))
    pdf = canvas.Canvas(str(output/"assembly_instructions.pdf"), pagesize=(page_w, page_h), pageCompression=1)
    pdf.setTitle(data["configuration_title"]+" - assembly book")
    pdf.setAuthor("OOBB generated assembly instructions")
    pdf.setSubject("Landscape A4 pages in reading order; padded to a multiple of four")
    ink = HexColor("#000000")
    measured_boxes = []

    def logo(x, y, width, height):
        from reportlab.graphics import renderPDF
        from svglib.svglib import svg2rlg
        from .geometry import ROOT
        # This official CorelDRAW SVG puts its symbol in the first three
        # subpaths and both lines of lettering in the remaining subpaths.
        source = ROOT/book["logo_svg"]
        root = ET.fromstring(source.read_text(encoding="utf-8"))
        paths = list(root.iter("{http://www.w3.org/2000/svg}path"))
        assert len(paths) == 1 and root.attrib["viewBox"] == "0 0 17.5 10"
        segments = re.findall(r"[Mm][^Mm]*", paths[0].attrib["d"])
        assert segments[0].startswith("M12.5 2.49845") and len(segments) == 37
        symbol = "".join(segments[:book["logo_symbol_subpaths"]])
        assets = output/"assets"
        assets.mkdir(exist_ok=True)
        target = assets/"oomlout_logo_black.svg"
        target.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="70mm" height="40mm" viewBox="0 0 17.5 10"><path fill="#000000" fill-rule="evenodd" d="'+symbol+'"/></svg>')
        drawing = svg2rlg(str(target))
        if drawing is None:
            raise ValueError("Missing or unreadable Oomlout logo: "+book["logo_svg"])
        scale = min(width/drawing.width, height/drawing.height)
        w, h = drawing.width*scale, drawing.height*scale
        drawing.scale(scale, scale)
        renderPDF.draw(drawing, pdf, x+(width-w)/2, y+(height-h)/2)

    def border(x, y, w, h, main=True):
        pdf.setStrokeColor(HexColor("#"+style["border"]))
        pdf.setLineWidth(style["border_width_pt"] if main else style["component_border_width_pt"])
        pdf.roundRect(x, y, w, h, (3 if main else 1.5)*mm, fill=0, stroke=1)

    def text(value, x, top, width, height, size=7, font=regular):
        item = Paragraph(value, ParagraphStyle("book", fontName=font, fontSize=size, leading=size*1.14, textColor=ink))
        _, used = item.wrap(width, height)
        if used > height+0.1:
            raise ValueError(f"Book text overflows: {value}")
        item.drawOn(pdf, x, top-used)
        measured_boxes.append([x, top-used, width, used])
        return used

    def picture(name, x, y, width, height):
        image = Image.open(output/"render/raw"/(name+".png"))
        scale = min(width/image.width, height/image.height)
        w, h = image.width*scale, image.height*scale
        left, bottom = x+(width-w)/2, y+(height-h)/2
        pdf.drawImage(ImageReader(image), left, bottom, w, h, mask="auto")
        return left, bottom, w, h

    def part_thumbnail(key, count, x, y, width, height):
        name = "part_" + key
        if count == 1:
            picture(name, x, y, width, height)
            return
        label = f"x{count}"
        size = style["quantity_pt"]
        gap = style["quantity_gap_mm"] * mm
        label_width = pdfmetrics.stringWidth(label, regular, size)
        left, bottom, image_width, _ = picture(name, x, y, width - gap - label_width, height)
        pdf.setFillColor(ink)
        pdf.setFont(regular, size)
        pdf.drawString(left + image_width + gap, bottom + .3*mm, label)

    def part_url(part, x, baseline):
        if "short_url" not in part:
            return
        prefix = "oom.lt/a/"
        pdf.setFillColor(ink)
        pdf.setFont(mono, style["font_url_prefix_pt"])
        pdf.drawString(x, baseline, prefix)
        start_code = x+pdfmetrics.stringWidth(prefix, mono, style["font_url_prefix_pt"])
        pdf.setFont(mono_bold, style["font_code_pt"])
        pdf.drawString(start_code, baseline, part["md5_6_alpha"])
        end = start_code+pdfmetrics.stringWidth(part["md5_6_alpha"], mono_bold, style["font_code_pt"])
        pdf.linkURL(part["short_url"], (x, baseline-1, end, baseline+style["font_code_pt"]), relative=0, thickness=0)

    def panel(index, slot):
        step = data["steps"][index]
        column, row = slot % style["columns"], slot // style["columns"]
        x = margin+column*(card_w+gutter)
        y = page_h-margin-(row+1)*card_h-row*gutter
        top = y+card_h
        pdf.setFillColor(HexColor("#FFFFFF"))
        pdf.setStrokeColor(HexColor("#"+style["border"]))
        pdf.setLineWidth(style["border_width_pt"])
        pdf.roundRect(x, y, card_w, card_h, style["border_radius_mm"]*mm, fill=1, stroke=1)
        pdf.setFillColor(ink)
        pdf.setFont(mono, 27)
        pdf.drawString(x+4*mm, top-11*mm, str(index+1))
        items = list(step["loose_parts"].items())
        assert 0 < len(items) <= 5
        row_height = min(20, 88 / len(items))
        box_w = 34*mm
        box_x, box_top = x+card_w-box_w-3*mm, top-3*mm
        box_h = (len(items)*row_height+4)*mm
        border(box_x, box_top-box_h, box_w, box_h, main=False)
        for item_index, (key, count) in enumerate(items):
            part = data["parts"][key]
            item_top = box_top-(2+item_index*row_height)*mm
            part_thumbnail(key, count, box_x+2*mm, item_top-10*mm, box_w-4*mm, style["thumbnail_height_mm"]*mm)
            name_top = item_top-10.5*mm
            used = text(part["name"], box_x+2*mm, name_top, box_w-4*mm, 6*mm, style["font_body_pt"], medium)
            baseline = name_top-used-0.65*mm-style["font_code_pt"]*.75
            if baseline < item_top-19.8*mm:
                raise ValueError("Part URL outside its row: "+key)
            part_url(part, box_x+2*mm, baseline)
        picture(step["key"], x+2*mm, y+3*mm, box_x-x-4*mm, card_h-15*mm)
        # No arrows, captions, titles, footer or explanatory text on step panels.

    for page in plan:
        kind = page["kind"]
        pdf.setFillColor(ink)
        if kind == "cover":
            border(10*mm, 10*mm, page_w-20*mm, page_h-20*mm)
            logo(18*mm, page_h-39*mm, 22*mm, 22*mm)
            text(book["cover_title"], 48*mm, page_h-18*mm, 190*mm, 17*mm, 30, medium)
            text(book["cover_subtitle"], 49*mm, page_h-34*mm, 200*mm, 9*mm, 11, mono)
            pdf.setLineWidth(style["component_border_width_pt"])
            pdf.line(18*mm, page_h-49*mm, page_w-18*mm, page_h-49*mm)
            picture("book_cover", 35*mm, 40*mm, page_w-70*mm, page_h-92*mm)
            text("ASSEMBLY INSTRUCTIONS", 19*mm, 34*mm, 200*mm, 7*mm, 9, mono_bold)
            text(book["project_name"], 19*mm, 26*mm, page_w-38*mm, 7*mm, 8, mono)
            text("Project on GitHub", 19*mm, 19*mm, page_w-38*mm, 6*mm, 7, mono)
            pdf.linkURL(book["project_url"], (19*mm, 14*mm, page_w-19*mm, 20*mm), thickness=0)
        elif kind == "details":
            text(book["details_title"], 23*mm, page_h-25*mm, 180*mm, 15*mm, 22, medium)
            top = page_h-48*mm
            for detail in book["details"]:
                pdf.setFillColor(ink)
                pdf.circle(25*mm, top-1.6*mm, .65*mm, fill=1, stroke=0)
                used = text(detail, 30*mm, top, page_w-55*mm, 12*mm, 9)
                top -= used+5*mm
        elif kind == "instructions":
            for slot in range(per_page):
                index = page["group"]*per_page+slot
                if index < len(data["steps"]):
                    panel(index, slot)
        elif kind == "summary":
            border(margin, margin, page_w-2*margin, page_h-2*margin)
            pdf.setFont(mono, 27)
            pdf.drawString(margin+4*mm, page_h-margin-11*mm, str(page["number"]))
            picture(book["summary_view"], 29*mm, 16*mm, page_w-58*mm, page_h-40*mm)
        elif kind == "parts":
            for group_index, (group, title) in enumerate([
                ("printed", book["summary_title"]),
                ("hardware", book["hardware_title"]),
            ]):
                box_x = margin+group_index*(card_w+gutter)
                box_y, box_h = margin, page_h-2*margin
                border(box_x, box_y, card_w, box_h, main=False)
                text(title, box_x+6*mm, page_h-margin-5*mm, card_w-12*mm, 10*mm, 15, medium)
                columns = 4 if len(groups[group]) > 15 else 3
                cell_w = (card_w-8*mm)/columns
                row_h = min(35, 174 / math.ceil(len(groups[group])/columns))*mm
                for index, part in enumerate(groups[group]):
                    x = box_x+4*mm+(index%columns)*cell_w
                    top = page_h-margin-22*mm-(index//columns)*row_h
                    if top-row_h < box_y:
                        raise ValueError("Parts inventory exceeds its box")
                    part_thumbnail(part["key"], part["quantity"], x+2*mm, top-17*mm, cell_w-4*mm, 16*mm)
                    name_top = top-18*mm
                    used = text(part["name"], x+2*mm, name_top, cell_w-4*mm, 8*mm, 7, medium)
                    part_url(part, x+2*mm, name_top-used-.65*mm-style["font_code_pt"]*.75)
        elif kind == "back":
            border(10*mm, 10*mm, page_w-20*mm, page_h-20*mm)
            logo(page_w/2-24*mm, page_h/2-24*mm, 48*mm, 48*mm)
        else:
            assert kind == "spacer"  # Intentionally completely blank.
        pdf.showPage()
    pdf.save()
    return measured_boxes


def review_outputs(**kwargs):
    import fitz
    from .geometry import panel_geometry
    output, data = Path(kwargs["output"]), kwargs["data"]
    style, plan = data["style"], data["book_pages"]
    pages_dir, cards_dir = output/"pages", output/"cards"
    pages_dir.mkdir(exist_ok=True)
    cards_dir.mkdir(exist_ok=True)
    pdf = fitz.open(output/"assembly_instructions.pdf")
    assert len(pdf) == len(plan) and len(pdf) % data["book"]["signature_pages"] == 0
    assert [p["kind"] for p in plan[:2]] == ["cover", "details"]
    assert plan[-2]["kind"] == "parts" and plan[-1]["kind"] == "back"
    card_w, card_h = panel_geometry(style)
    per_page = style["columns"]*style["rows"]
    all_instruction_text, thumbnails = "", []
    valid_pages, valid_cards = set(), set()
    for index, (page, spec) in enumerate(zip(pdf, plan)):
        assert abs(page.rect.width-style["page_mm"][0]*mm) < .1
        assert abs(page.rect.height-style["page_mm"][1]*mm) < .1
        content = page.get_text()
        if spec["kind"] == "instructions":
            all_instruction_text += content
            assert "x1\n" not in content
        if spec["kind"] == "spacer":
            assert not content.strip() and not page.get_images() and not page.get_drawings()
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    assert span["color"] == 0
        page_path = pages_dir/f"page_{index+1:02d}.png"
        page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).save(page_path)
        valid_pages.add(page_path.name)
        pil = Image.open(page_path).convert("RGB")
        factor = pil.width/style["page_mm"][0]
        if spec["kind"] == "instructions":
            for slot in range(per_page):
                number = spec["group"]*per_page+slot+1
                if number > len(data["steps"]):
                    break
                left = style["margin_mm"]+(slot%style["columns"])*(card_w+style["gutter_mm"])
                top = style["margin_mm"]+(slot//style["columns"])*(card_h+style["gutter_mm"])
                name = f"step_{number:02d}.png"
                pil.crop(tuple(round(v*factor) for v in [left, top, left+card_w, top+card_h])).save(cards_dir/name)
                valid_cards.add(name)
        if spec["kind"] == "summary":
            name = f"step_{spec['number']:02d}.png"
            pil.save(cards_dir/name)
            valid_cards.add(name)
            assert content.strip() == str(spec["number"])
        thumbnails.append(ImageOps.contain(pil, (600, 425)))
    normalised = "".join(all_instruction_text.split())
    for part in data["parts"].values():
        if "short_label" in part:
            assert part["short_label"] in normalised, part["key"]
    for step in data["steps"]:
        assert step["title"] not in all_instruction_text and step["action"] not in all_instruction_text
    for folder, valid, pattern in [(pages_dir, valid_pages, "page_*.png"), (cards_dir, valid_cards, "step_*.png")]:
        for stale in folder.glob(pattern):
            assert stale.resolve().parent == folder.resolve()
            if stale.name not in valid:
                stale.unlink()
    contact = Image.new("RGB", (1200, math.ceil(len(thumbnails)/2)*425), "#EEEEEE")
    for index, tile in enumerate(thumbnails):
        contact.paste(tile, ((index%2)*600, (index//2)*425))
    contact.save(output/"contact_sheet.png")
    report = {
        "status": "passed",
        "page_count": len(pdf),
        "card_count": len(valid_cards),
        "paper_mm": style["page_mm"],
        "panels_per_instruction_page": per_page,
        "page_roles": [p["kind"] for p in plan],
        "parts_summary_page": len(plan)-1,
        "printed_parts_in_summary": data["printed_piece_count"],
        "hardware_items_in_summary": sum(part["quantity"] for part in data["summary_inventory"]["hardware"]),
        "summary_step": len(data["steps"])+1 if data["book"]["summary_step"] else None,
        "page_order": "Reader order; signature padded. Apply booklet imposition only at print time.",
        "physical_items": data["physical_item_count"],
        "quantity_audit": "Every physical item introduced once; singleton multipliers hidden; printed and hardware summary reconciled to production inventory; identical hardware roles combined",
        "layout_checks": "Text fits; only black typography; compact URL code/prefix hierarchy; no instruction prose or arrows; blank spacer has no marks",
        "physical_validation": "Not physically assembled or load tested",
        "pdf_sha256": hashlib.sha256((output/"assembly_instructions.pdf").read_bytes()).hexdigest(),
    }
    (output/"validation.json").write_text(json.dumps(report, indent=2))
