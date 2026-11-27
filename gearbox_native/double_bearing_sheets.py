"""Typeset presentation PNGs from the registered orthographic studio renders."""
import json

from PIL import Image, ImageDraw, ImageFont

PAPER = '#FAF8F2'
INK = '#172E32'
MUTED = '#435B5E'
RULE = '#C6D0C9'
ACCENT = '#006C71'


def font(size, bold=False):
    return ImageFont.truetype('segoeuib.ttf' if bold else 'segoeui.ttf', size)


def label(draw, xy, text, size, color=INK, bold=False):
    draw.text(xy, text, fill=color, font=font(size, bold), anchor='lt')


def sheet(size, section, title, description):
    page = Image.new('RGB', size, PAPER)
    d = ImageDraw.Draw(page)
    label(d, (50, 33), 'OOBB     /     SIMPLE DOUBLE BEARING   V2', 23, ACCENT, True)
    d.text((size[0]-50, 33), section, anchor='rt', font=font(23), fill=MUTED)
    d.line((50, 78, size[0]-50, 78), fill=RULE, width=2)
    label(d, (47, 102), title, 64, bold=True)
    label(d, (51, 190), description, 29, MUTED)
    return page, d


def paste(page, cache, key, x, y, size=None):
    im = Image.open(cache / f'{key}.png').convert('RGBA')
    if size:
        im = im.resize(size, Image.Resampling.LANCZOS)
    page.paste(im, (x, y), im)


def legend(d, y):
    x = 52
    for color, text in [('#00B1B7', 'Housing, discs and N'), ('#121212', 'Carriers and C'),
                        ('#FEC601', 'Ring contacts, guides and E'), ('#A1ABAF', 'Metal hardware')]:
        d.ellipse((x, y+5, x+17, y+22), fill=color)
        label(d, (x+28, y), text, 23, MUTED)
        x += 59 + int(d.textlength(text, font=font(23)))


def beauty(cache, part, rounded):
    key = 'rounded' if rounded else 'square'
    title = 'Rounded output plates' if rounded else 'Square output plates'
    description = ('The curved flange follows the bearing housing. A full OOBB mounting row extends along one edge.'
                   if rounded else 'The 7 × 7 OOBB flanges carry the output. The six inner guide sleeves stay with the stationary carriers.')
    page, d = sheet((1620, 1430), 'ASSEMBLED   /   20:1', title, description)
    paste(page, cache, key, 55, 245)
    d.line((50, 1340, 1570, 1340), fill=RULE, width=2)
    legend(d, 1368)
    page.save(part / f'render_assembled_{key}.png')


def exploded(cache, part):
    page, d = sheet((2560, 1740), 'EXPLODED   /   20:1', 'Inside the gearbox',
                    'Three coaxial groups, each viewed from the upper end. Follow each column from the lower end upwards.')
    anchors = json.loads((cache / 'anchors.json').read_text())
    panels = [
        ('housing', 'Output casing', [
            ('hardware_ring_cap_heads', '20 × M3 × 30', 'Socket-cap ring screws'),
            ('output_cap_cylinder', 'Retaining cylinder', 'Houses the full 6810'),
            ('hardware_6810_top', '6810 bearing', '50 × 65 × 7 mm'),
            ('output_cap_plate', 'Flat OOBB flange', 'Closes the outer race'),
            ('printed_contact_sleeve', '20 ring contacts', 'Ø7 × 16 mm sleeves'),
            ('output_nut_plate', 'Lower OOBB flange', 'Matching split face'),
            ('output_nut_cylinder', 'Lower cylinder', 'M3 nuts load below')]),
        ('core', 'Carriers and cycloids', [
            ('hardware_drive_caps', '6 × M3 × 35', 'Stationary guide screws'),
            ('carrier_top_cap', 'Upper carrier cap', 'Full-width 6810 journal'),
            ('hardware_6704_top', '6704 support', '8 mount nuts at split'),
            ('rotor_b', 'Disc B clamshell', 'Screw heads face up'),
            ('printed_drive_sleeve', '6 guide sleeves', 'Ø7 × 16 mm, sunflower'),
            ('rotor_a', 'Disc A clamshell', 'Screw heads face down'),
            ('carrier_bottom', 'Lower carrier core', 'Flat face against cap'),
            ('hardware_6704_base', '6704 support', 'Captured at carrier split'),
            ('hardware_drive_nuts', '6 guide nuts', 'Recessed in lower cap')]),
        ('shaft', 'Input shaft', [
            ('hardware_shaft_M3x35_upper', 'Upper tie screw', 'M3 × 35 socket cap'),
            ('shaft_end_upper', 'E · upper end', 'Flange faces out'),
            ('shaft_mount_upper', 'N · nut carrier', 'Four mount pockets'),
            ('shaft_cam_b_outer', 'C · upper pair', 'Captures bearing B'),
            ('shaft_cam_a_outer', 'C · lower pair', 'Captures bearing A'),
            ('shaft_mount_lower', 'N · nut carrier', 'Four mount pockets'),
            ('shaft_end_lower', 'E · lower end', 'Flange faces out'),
            ('hardware_shaft_M3x35_lower', 'Lower tie screw', 'Enters from below')])]
    for i, (key, title, callouts) in enumerate(panels):
        x = 45 + i*832
        label(d, (x+6, 267), title, 40, bold=True)
        d.line((x+6, 332, x+805, 332), fill=RULE, width=2)
        if i:
            d.line((x-12, 270, x-12, 1625), fill=RULE, width=2)
        w, h = 540, 1234
        ox, oy = x-28, 360
        paste(page, cache, key, ox, oy, (w,h))
        entries = []
        for n, a, b in callouts:
            px, py = anchors[key][n]
            entries.append((ox+px*w/560, oy+py*h/1280, a,b))
        entries.sort(key=lambda item: item[1])
        ys = []
        for entry in entries:
            ys.append(max(entry[1], ys[-1]+94 if ys else oy+25))
        for j in reversed(range(len(ys))):
            ys[j] = min(ys[j], ys[j+1]-94 if j+1 < len(ys) else oy+h-20)
        for (px,py,a,b), y in zip(entries,ys):
            tx = x+515
            d.line([(px, py), (max(px+7, tx-77), py), (tx-22,y), (tx-8,y)], fill='#749194', width=2)
            d.ellipse((px-3,py-3,px+3,py+3), fill=ACCENT)
            label(d,(tx,y-16),a,26,bold=True)
            label(d,(tx,y+19),b,22,MUTED)
    d.line((50,1640,2510,1640),fill=RULE,width=2)
    legend(d,1670)
    page.save(part/'render_exploded.png')


STEPS = [
    ('layer_start', 'Stand the screws in the first layer',
     'Start socket-cap face down. Fit twenty M3 × 30 ring screws, six M3 × 35 guides and two M3 × 35 shaft screws. The E and 6810 inner journal share this layer. One shaft head temporarily occupies E’s empty hex pocket.'),
    ('layer_bearings', 'Lower both bearings',
     'Lower the 6810 over the black journal and the centred 6704 over yellow E. Both approach from above over the standing screws. Seat them on their shoulders.'),
    ('layer_inner', 'Plate, carrier core and N',
     'Preload eight core nuts and four optional N nuts, pockets downward. Lower the OOBB plate, core and N as one concentric layer. Support the plate with at least 50 mm of access underneath.'),
    ('layer_sleeves', 'Lower all sleeves over the screws',
     'Fit six inner guide sleeves and twenty outer contact sleeves. The connected outer ring can replace the twenty sleeves here. The screws now guide the following layers.'),
    ('layer_disc_b', 'First cam and Disc B',
     'Finish both disc clamshells on the bench first. Fit the first C, narrow journal up, then lower B over the standing screws, guides and open cam. B’s heads face down; its index faces the wide guide gap.'),
    ('layer_cams', 'Close B and start the opposite cam',
     'Lower B’s closing C with its journal down. Add A’s first C, journal up, with its eccentric offset 180° opposite B. Keep both shaft screws through these pieces.'),
    ('layer_disc_a', 'Disc A and its closing C',
     'Lower A with its screw heads up and its index toward the same wide gap as B. Once the bearing is seated, fit the last C half, narrow journal down.'),
    ('layer_finish_inner', 'Finishing plate, core and N',
     'Preload eight core nuts and four optional N nuts, pockets upward. Lower the finishing OOBB plate, carrier core and N over their screw circles. Seat the guide sleeve ends in the core.'),
    ('layer_finish_bearings', 'Lower the finishing bearings',
     'Place the second 6810 onto the plate and large inner shoulder. Place the centred 6704 onto N and the central retaining face. Both bearings go in this layer, before the caps.'),
    ('layer_finish_caps', 'Lower the three finishing caps',
     'Lower the outside cylinder, large 6810 carrier cap and small E over the standing screws into their bearings. Wide flanges face up. Match each shaft socket to the opposite end’s hex pocket.'),
    ('layer_reverse', 'Secure, withdraw, then reverse',
     'Start the finishing nuts and secure the correctly directed shaft tie. Pull the temporary screw out underneath, load that empty hex pocket with a nut, then flip the same screw and insert it from above.'),
    ('layer_end', 'Snug and check movement',
     'Snug the two opposed shaft ties, six guide fasteners, then twenty ring fasteners evenly. Hold the stationary carrier and turn E by hand after each group. Both bearings and all sleeves must stay seated.'),
]


def paragraph(d, x, y, text, width, size):
    line = ''
    for word in text.split():
        test = (line + ' ' + word).strip()
        if d.textlength(test, font=font(size)) > width and line:
            label(d,(x,y),line,size,MUTED)
            y += size+9
            line = word
        else:
            line = test
    label(d,(x,y),line,size,MUTED)
    return y+size


def installation(cache, part):
    anchors = json.loads((cache / 'anchors.json').read_text())
    pages = []
    for page_number in range(2):
        page,d = sheet((1930, 2335), f'ASSEMBLY   /   PAGE {page_number+1} OF 2',
                       'Build upward over the screws' if page_number==0 else 'Finish the layers and reverse one screw',
                       'Socket-cap end down. Disc B first, then A. See ASSEMBLY.md for the checked order and screw reversal.')
        for j,(key,title,caption) in enumerate(STEPS[page_number*6:page_number*6+6]):
            i=page_number*6+j
            x,y = 52+(j%2)*937, 263+(j//2)*655
            d.line((x,y,x+889,y),fill=RULE,width=2)
            label(d,(x,y+19),f'{i+1:02}',31,ACCENT,True)
            label(d,(x+59,y+13),title,34,bold=True)
            if key=='layer_start':
                paste(page,cache,key,x+300,y+87,(520,370))
                label(d,(x+12,y+248),'Starting E / underside',21,MUTED,True)
                paste(page,cache,'layer_start_face',x+15,y+281,(220,187))
                label(d,(x+12,y+482),'Round stays; hex reverses',22,ACCENT,True)
            else:
                paste(page,cache,key,x+111,y+67,(650,462))
            if key in ('layer_disc_b', 'layer_disc_a'):
                fastener = 'hardware_disc_b_nut_1' if key == 'layer_disc_b' else 'hardware_disc_a_M3x6_1'
                ax, ay = anchors[key][fastener]
                px, py = x+111+ax*650/690, y+67+ay*462/490
                tx, ty = x+694, py-83
                d.line([(px,py), (px+25,py), (tx-12,ty), (tx,ty)], fill=ACCENT, width=3)
                d.ellipse((px-5,py-5,px+5,py+5), fill='#FEC601', outline=INK)
                label(d,(tx+6,ty-12),'Index screw',24,ACCENT,True)
            if key=='layer_reverse':
                for name,caption_text in [('temporary_shaft_tie','1. Withdraw below'),
                                          ('hardware_shaft_M3x35_lower','2. Refit from above')]:
                    ax,ay=anchors[key][name]
                    px,py=x+111+ax*650/690,y+67+ay*462/490
                    tx=x+645
                    d.line([(px,py),(tx-15,py),(tx-6,py-10)],fill=ACCENT,width=2)
                    label(d,(tx,py-24),caption_text,23,ACCENT,True)
                label(d,(x+12,y+489),'Same screw, two positions',22,MUTED)
            bottom = paragraph(d,x,y+536,caption,890,25)
            if bottom >= y+652:
                raise ValueError('Caption overflows: '+title)
        d.line((52,2230,1870,2230),fill=RULE,width=2)
        legend(d,2265)
        page.save(part/('assembly_lower.png' if page_number==0 else 'assembly_upper.png'))
        pages.append(page)
    combined=Image.new('RGB',(1930,4670),PAPER)
    for i,page in enumerate(pages):
        combined.paste(page,(0,i*2335))
    combined.save(part/'render_installation.png')


def publish(cache, part):
    for rounded in (True, False):
        beauty(cache, part, rounded)
    exploded(cache, part)
    installation(cache, part)
    from .assembly_instructions import write
    write(part)
