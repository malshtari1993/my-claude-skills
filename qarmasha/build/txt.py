from PIL import Image, ImageDraw, ImageFont
import sys
F="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def make(name, text, size, color=(255,255,255), sub=None, subsize=60):
    im=Image.new("RGBA",(1080,1920),(0,0,0,0)); d=ImageDraw.Draw(im)
    f=ImageFont.truetype(F,size,layout_engine=ImageFont.Layout.RAQM)
    y=1560
    def line(t,font,y,fill):
        w=d.textlength(t,font=font,direction="rtl",language="ar")
        x=(1080-w)/2
        d.text((x+4,y+4),t,font=font,fill=(0,0,0,160),direction="rtl",language="ar")
        d.text((x,y),t,font=font,fill=fill,direction="rtl",language="ar")
    line(text,f,y,color)
    if sub:
        line(sub,ImageFont.truetype(F,subsize,layout_engine=ImageFont.Layout.RAQM),y+size+40,(255,226,160,255))
    im.save(name)
make("t1.png","قرمشة",150,sub="جرانولا تفتح النفس",subsize=56)
make("t2.png","قرمشة وطعم",120,sub="والله ما تشبع منها",subsize=56)
make("t3.png","قرمشة",160,sub="جرّبها اليوم!",subsize=60)
