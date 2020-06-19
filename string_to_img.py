from PIL import Image, ImageDraw, ImageFont

# get an image

# make a blank image for the text, initialized to transparent text color
txt = Image.new('RGB', (200,200), (0,0,0))

# get a font
fnt = ImageFont.truetype('terminus-ttf-4.47.0/TerminusTTF-4.47.0.ttf', 12 * 2)
# get a drawing context
d = ImageDraw.Draw(txt)

# draw text, half opacity
d.text((0,0), "144", font=fnt, fill=(255,255,255))
# draw text, full opacity
d.text((10,60), "World", font=fnt, fill=(255,128,255))

txt = txt.resize( (100,100) )
txt.save("text.bmp")
txt.show()