"""Compose the checked-CAD assembly renders into printable instruction sheets.

python -m gearbox_native.nema17_assembly_visuals
First run nema17_assembly_studio.py in Blender against the current checked scene.
"""
import hashlib
import json
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PART = ROOT / 'parts/oobb_part_motor_gearbox_cycloidal_simple_double_bearing_version_2_20_to_1_reduction_nema17_flange'
RAW = ROOT / 'build/nema17_assembly_guide'
OUT = PART / 'assembly_guide'
BG = '#FAF9F5'
INK = '#20272A'
TEAL = '#008C91'
YELLOW = '#FEC601'


def font(size, bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf' if bold else 'C:/Windows/Fonts/segoeui.ttf', size)


def lines(draw, text, xy, size=25, width=58, fill=INK, bold=False):
    x, y = xy
    for paragraph in text.split('\n'):
        for line in textwrap.wrap(paragraph, width=width) or ['']:
            draw.text((x, y), line, font=font(size, bold), fill=fill)
            y += int(size * 1.4)
    return y


def picture(canvas, name, box):
    im = Image.open(RAW / (name + '.png')).convert('RGBA')
    im.thumbnail((box[2], box[3]), Image.Resampling.LANCZOS)
    x = box[0] + (box[2]-im.width)//2
    y = box[1] + (box[3]-im.height)//2
    canvas.paste(im, (x, y), im)
    return x, y, im.width/ Image.open(RAW / (name+'.png')).width


STEPS = [
    ('01_core', '1  Build the gearbox core',
     'Start socket-cap end DOWN; motor end finishes UP. Fit both bearings together at each end. Disc B goes first, then A; their cam offsets oppose.',
     'Start only 3 × M3 × 35 guide screws. Core view omits long fasteners for clarity.'),
    ('02_coupler', '2  Finish shaft ties; fit the coupler',
     'Reverse the temporary shaft tie and tighten both ties BEFORE fitting the flange. Capture four M3 nuts inside the motor-end N piece.',
     '4 × M3 × 14 socket caps + 0.5 mm washers. Wide flange against yellow E; barrel toward motor.'),
    ('03_motor', '3  Make the motor subassembly',
     'Fasten the motor to the black inner adapter on the bench. This panel shows the motor face from the other side.',
     '4 × M3 × 8 socket caps. Tighten now: the gearbox blocks their access bores later.'),
    ('04_mount', '4  Seat the motor; tighten the grubs',
     'Slide motor shaft into coupler and seat the adapter. Side-load its three guide nuts, then insert the remaining guide screws from the opposite end.',
     '3 × M3 × 40 socket caps. Rotate input to reach the grub screws through the adapter windows.'),
    ('05_cage', '5  Fit the fixed motor cage',
     'First finish tightening the coupler grubs. Load the three cage nuts into their side slots, then slide the cage over the motor from its rear.',
     '3 × M3 × 16 socket caps. Keep the motor cable within the fixed assembly.'),
    ('06_covers', '6  Close both fixed end covers',
     'Turn over as needed. Fit front spacer; capture chosen M6/M3 mounting nuts between each cover pair before closing. Route cable through rear passage.',
     'Front: 4 × M3 × 25 countersunk. Rear: 3 × M3 × 16 countersunk.'),
    ('07_extension', '7  Add the rotating rear extension',
     'Side-load four nuts into the teal posts. Slide the extension around the motor from behind until its posts seat on the motor-side output plate.',
     '4 × M3 × 10 countersunk. Feed through front access holes; heads seat in the MOTOR-SIDE plate.'),
    ('08_finished', '8  Brace the plates; check rotation',
     'Slide two yellow Ø7 × 16 braces radially between the plates. Put nuts below the motor-side plate, then screw from the front through each brace.',
     '2 × M3 × 25 countersunk. Black covers stay fixed; teal housing and rear frame rotate together.'),
]


def sheet(first, filename, title):
    canvas = Image.new('RGB', (2000, 2140), BG)
    d = ImageDraw.Draw(canvas)
    d.text((65, 40), title, font=font(48, True), fill=INK)
    d.text((68, 112), 'NEMA17 / 20:1 / circular output plates / current checked CAD', font=font(27), fill=TEAL)
    for j, (name, heading, body, hardware) in enumerate(STEPS[first:first+4]):
        x, y = 50+(j % 2)*980, 190+(j//2)*925
        d.rounded_rectangle((x, y, x+950, y+895), radius=18, fill='white', outline='#DADDD9', width=2)
        d.text((x+24, y+18), heading, font=font(32, True), fill=INK)
        picture(canvas, name, (x+20, y+67, 910, 565))
        d = ImageDraw.Draw(canvas)
        lines(d, body, (x+26, y+641), size=25, width=64)
        lines(d, hardware, (x+26, y+772), size=24, width=65, fill=TEAL, bold=True)
    d.text((65, 2075), 'AI-generated CAD illustration • Exploded spacing is illustrative; use the written layer order.', font=font(23), fill='#687274')
    canvas.save(OUT / filename)


def overview():
    canvas = Image.new('RGB', (2100, 1980), BG)
    d = ImageDraw.Draw(canvas)
    d.text((60, 35), 'How the NEMA17 version goes together', font=font(49, True), fill=INK)
    d.text((64, 109), 'Fixed motor support inside a rotating output casing', font=font(30), fill=TEAL)
    x, y, scale = picture(canvas, 'overview', (630, 175, 1400, 1700))
    d = ImageDraw.Draw(canvas)
    anchors = json.loads((RAW/'overview.json').read_text())
    labels = [
        ('A', 'Front cover + spacer', 'Fixed. Split cover captures mounting nuts.', 'front_cover_nuts'),
        ('B', 'Gearbox core', 'Twin cycloids, 6810 casing bearings and stacked 6704 shaft.', 'circular_top'),
        ('C', '5 mm flange coupler', 'Four screws into the modified shaft end. Grubs grip motor shaft.', 'hardware_flange_coupler_5mm'),
        ('D', 'Motor inner adapter', 'Bolt to motor first; then attach to the three long guide screws.', 'motor_inner_adapter'),
        ('E', 'NEMA17 motor', '40 mm body in this configuration.', 'hardware_NEMA17_motor'),
        ('F', 'Fixed motor cage', 'Slides over motor; joins to adapter with three socket caps.', 'motor_cage'),
        ('G', 'Rear cover', 'Fixed. Split cover captures mounting nuts and clears cable.', 'rear_cover_nuts'),
        ('H', 'Rear output extension', 'Rotates with the teal plates. Shown to the side for clarity.', 'rear_output_extension'),
    ]
    for i, (letter, title, desc, name) in enumerate(labels):
        yy = 200+i*192
        d.ellipse((64, yy+2, 110, yy+48), fill=TEAL)
        d.text((78, yy+4), letter, font=font(28, True), fill='white')
        d.text((127, yy), title, font=font(30, True), fill=INK)
        lines(d, desc, (127, yy+48), size=25, width=34)
        px, py = anchors[name]
        px, py = x+px*scale, y+py*scale
        d.ellipse((px-23, py-23, px+23, py+23), fill=TEAL, outline='white', width=3)
        d.text((px-10, py-20), letter, font=font(28, True), fill='white')
    d.line((65, 1790, 600, 1790), fill='#DADDD9', width=2)
    lines(d, 'Black: fixed supports\nTeal: output housing / structural parts\nYellow: contact sleeves / shaft ends', (65, 1810), size=23, width=45)
    d.text((65, 1930), 'AI-generated CAD illustration • Module overview; follow the numbered sheets for assembly order.', font=font(23), fill='#687274')
    canvas.save(OUT/'exploded_overview.png')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    master = ROOT / 'simple_double_bearing_version_2_nema17_flange.solidcraft'
    digest = hashlib.sha256(master.read_bytes()).hexdigest()
    verification = json.loads((PART/'native_export_verification.json').read_text())
    assert digest == verification['source_sha256'], 'Native master has changed; export and restage the CAD first.'
    sheet(0, '01_motor_assembly.png', '01–04  Gearbox layers and motor connection')
    sheet(4, '02_covers_and_output.png', '05–08  Fixed covers and rotating output')
    overview()
    (OUT/'source.json').write_text(json.dumps({
        'master': master.name,
        'master_sha256': digest,
        'mesh_source': 'build/nema17_carrier_overhang/studio/motor_variant.blend',
        'geometry_changed': False,
        'note': 'Illustrative separation of checked CAD meshes; not a new motion simulation.'
    }, indent=2)+'\n')


if __name__ == '__main__':
    main()
