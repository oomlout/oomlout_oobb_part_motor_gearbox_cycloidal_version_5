"""Compose a concise geometry-review sheet from native mesh renders."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def compose(folder, destination):
    folder,destination=map(Path,(folder,destination))
    page=Image.new('RGB',(1600,1600),'#FAF9F5');draw=ImageDraw.Draw(page)
    def text(x,y,value,size=28,bold=False,color='#20272A'):
        font=ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf' if bold else 'C:/Windows/Fonts/segoeui.ttf',size)
        draw.text((x,y),value,font=font,fill=color)
    def fit(name,box):
        im=Image.open(folder/name).convert('RGBA');im=im.crop(im.getbbox())
        im.thumbnail((box[2],box[3]),Image.Resampling.LANCZOS)
        page.paste(im,(box[0]+(box[2]-im.width)//2,box[1]+(box[3]-im.height)//2),im)
    text(45,30,'NEMA17 • revised supports and coupler inserts',43,True)
    text(47,95,'40 mm motor body • depth is part of the catalogue definition',27,color='#008C91')
    text(80,160,'FIXED: continuous 3 mm-wall tube',27,True)
    text(820,160,'OUTPUT: separate ring + 3 identical joiners',27,True)
    fit('supports.png',(35,210,1530,800))
    draw.line((50,1040,1550,1040),fill='#D6DBD8',width=2)
    text(50,1060,'Matching 6704 innards: four M3 axes on a Ø16 mm bolt circle',30,True)
    fit('coupler_inserts.png',(80,1120,1440,350))
    text(50,1500,'Conversion print only: 18 added or changed pieces; reuse the rest of the base gearbox.',26)
    text(50,1550,'AI-generated CAD illustration • Geometry review; assembly instructions have not been updated.',20,color='#637274')
    destination.parent.mkdir(parents=True,exist_ok=True);page.save(destination)


if __name__=='__main__':
    import sys
    compose(sys.argv[1],sys.argv[2])
