"""Small reusable ReportLab layout for technical assembly manuals.

Coordinates use points from the top-left. Images retain their aspect ratio.
No navigation chrome, decorative cards, badges, or marketing copy.
"""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

INK='#222625'
GREY='#59615F'
ACCENT='#006D70'
PAPER='#FFFFFF'
RULE='#CFD3D0'


class Manual:
    def __init__(self, destination, title, font_dir=None, size=(900,675)):
        self.width, self.height = size
        font_dir = Path(font_dir or 'C:/Windows/Fonts')
        if (font_dir/'segoeui.ttf').exists():
            for name, filename in [('Body','segoeui.ttf'),('Strong','segoeuib.ttf')]:
                pdfmetrics.registerFont(TTFont(name,str(font_dir/filename)))
            self.regular, self.bold = 'Body','Strong'
            pdfmetrics.registerFontFamily('Body',normal='Body',bold='Strong',italic='Body',boldItalic='Strong')
        else:
            self.regular, self.bold = 'Helvetica','Helvetica-Bold'
        self.canvas=canvas.Canvas(str(destination),pagesize=size)
        self.canvas.setTitle(title)
        self.canvas.setAuthor('AI-generated project documentation')
        self.page_number=0

    def text(self,x,y,value,size=11,bold=False,color=INK):
        c=self.canvas;c.setFont(self.bold if bold else self.regular,size)
        c.setFillColor(HexColor(color));c.drawString(x,self.height-y-size*.8,str(value))

    def paragraph(self,x,y,value,width,size=11,color=INK,leading=None):
        style=ParagraphStyle('body',fontName=self.regular,fontSize=size,leading=leading or size*1.45,textColor=HexColor(color))
        p=Paragraph(value,style);_,height=p.wrap(width,1000)
        p.drawOn(self.canvas,x,self.height-y-height)
        return y+height

    def line(self,x,y,x2,y2,color=RULE,width=.6):
        self.canvas.setStrokeColor(HexColor(color));self.canvas.setLineWidth(width)
        self.canvas.line(x,self.height-y,x2,self.height-y2)

    def rect(self,x,y,w,h,color):
        self.canvas.setFillColor(HexColor(color));self.canvas.rect(x,self.height-y-h,w,h,fill=1,stroke=0)

    def image(self,path,x,y,w,h):
        # Flatten Blender alpha explicitly: ReportLab otherwise paints it black.
        from PIL import Image
        bitmap=Image.open(path)
        if bitmap.mode == 'RGBA':
            paper=Image.new('RGBA',bitmap.size,'#FAF8F2')
            bitmap=Image.alpha_composite(paper,bitmap).convert('RGB')
        im=ImageReader(bitmap);iw,ih=im.getSize();scale=min(w/iw,h/ih)
        dw,dh=iw*scale,ih*scale;left=x+(w-dw)/2;top=y+(h-dh)/2
        self.canvas.drawImage(im,left,self.height-top-dh,dw,dh)
        return lambda a,b:(left+a*dw,top+b*dh)

    def page(self,title,subtitle=None):
        self.page_number+=1
        self.rect(0,0,self.width,self.height,PAPER)
        self.text(42,34,title,28,True)
        if subtitle:self.paragraph(43,77,subtitle,self.width-86,10.5,GREY)

    def finish(self):
        self.text(42,self.height-28,'AI-generated images and instructions. Errors possible.',8,color=GREY)
        self.text(self.width-54,self.height-29,self.page_number,9,color=GREY)
        self.canvas.showPage()

    def save(self):self.canvas.save()

    def caption(self,x,y,label,body,width):
        return self.paragraph(x,y,f'<b>{label}</b> {body}',width,9.5,GREY)

    def step(self,x,y,number,title,body,width):
        self.text(x,y,f'{number}. {title}',13,True)
        return self.paragraph(x,y+24,body,width,10.5)+18

    def leader(self,point,x,y,label,size=9):
        px,py=point
        self.line(px,py,x,y+size*.5,ACCENT,.65)
        self.text(x+4,y,label,size,True,ACCENT)

    def dimension(self,x1,x2,y,label):
        self.line(x1,y,x2,y,ACCENT,.8)
        for x in (x1,x2):self.line(x,y-4,x,y+4,ACCENT,.8)
        width=pdfmetrics.stringWidth(label,self.regular,9)
        self.text((x1+x2-width)/2,y-17,label,9,color=ACCENT)
