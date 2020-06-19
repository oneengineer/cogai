from PIL import Image, ImageDraw, ImageFont
import numpy as np
# get an image

# make a blank image for the text, initialized to transparent text color
from PIL import FontFile

# --------------------------------------------------------------------
# parse X Bitmap Distribution Format (BDF)
# --------------------------------------------------------------------

bdf_slant = {
    "R": "Roman",
    "I": "Italic",
    "O": "Oblique",
    "RI": "Reverse Italic",
    "RO": "Reverse Oblique",
    "OT": "Other",
}

bdf_spacing = {"P": "Proportional", "M": "Monospaced", "C": "Cell"}


def bdf_char(f):
    # skip to STARTCHAR
    while True:
        s = f.readline()
        if not s:
            return None
        if s[:9] == b"STARTCHAR":
            break
    id = s[9:].strip().decode("ascii")

    # load symbol properties
    props = {}
    while True:
        s = f.readline()
        if not s or s[:6] == b"BITMAP":
            break
        i = s.find(b" ")
        props[s[:i].decode("ascii")] = s[i + 1 : -1].decode("ascii")

    # load bitmap
    bitmap = []
    while True:
        s = f.readline()
        if not s or s[:7] == b"ENDCHAR":
            break
        bitmap.append(s[:-1])
    bitmap = b"".join(bitmap)

    [x, y, l, d] = [int(p) for p in props["BBX"].split()]
    [dx, dy] = [int(p) for p in props["DWIDTH"].split()]

    bbox = (dx, dy), (l, -d - y, x + l, -d), (0, 0, x, y)

    try:
        im = Image.frombytes("1", (x, y), bitmap, "hex", "1")
    except ValueError:
        # deal with zero-width characters
        im = Image.new("1", (x, y))

    return id, int(props["ENCODING"]), bbox, im


##
# Font file plugin for the X11 BDF format.

IMG_EPS = 1e-6

def normalize_0_1(img:np.ndarray):
    assert img.ndim == 2
    m = img.max()
    if m < IMG_EPS:
        return np.ones_like(img, dtype = np.float) * IMG_EPS
    return img / m

class BdfFontFile(FontFile.FontFile):
    def __init__(self, fp):

        FontFile.FontFile.__init__(self)

        s = fp.readline()
        if s[:13] != b"STARTFONT 2.1":
            raise SyntaxError("not a valid BDF file")

        props = {}
        comments = []

        while True:
            s = fp.readline()
            if not s or s[:13] == b"ENDPROPERTIES":
                break
            i = s.find(b" ")
            props[s[:i].decode("ascii")] = s[i + 1 : -1].decode("ascii")
            if s[:i] in [b"COMMENT", b"COPYRIGHT"]:
                if s.find(b"LogicalFontDescription") < 0:
                    comments.append(s[i + 1 : -1].decode("ascii"))

        while True:
            c = bdf_char(fp)
            if not c:
                break
            id, ch, (xy, dst, src), im = c
            if 0 <= ch < len(self.glyph):
                self.glyph[ch] = id, xy, dst, src, im


class FontBase:

    # while character
    def genChar(self, c:str):
        raise Exception("should be implemented as return np.array, PIL.Image")

    def genAllChar(self):
        self.chnp = []
        self.chimg = []
        for i in self.decoding_table:
            a, b = self.genChar(i)
            self.chnp += [a]
            self.chimg += [b]

    def drawOut(self,data:np.ndarray, img0 = None):
        """

        :param data: (H,W, 7 )   ascii, fore rgb, back rgb
        :param img0: (H*hh, W*ww, 3 ) original image before parse, if this is set return diff value
        :return: (H*hh, W*ww, 3 ),  diff value (H, W)
        """
        H,W,_ = data.shape
        h = H * self.h
        w = W * self.w
        d2 = np.zeros( (h, w, 3) )
        diffImg = np.zeros( shape = (H,W) )
        for hi in range(H):
            for wi in range(W):
                ascii_idx,r1,g1,b1,r2,g2,b2 = data[hi,wi].tolist()
                fcolor = np.array([r1,g1,b1]).reshape((1,1,3))
                bcolor = np.array([r2,g2,b2]).reshape((1,1,3))
                stencil = self.chnp[ascii_idx].reshape( (self.h, self.w, 1) )
                stencil = np.repeat(stencil,3,axis=2)
                stencil_neg = 1.0 - stencil
                result = stencil * fcolor
                result += stencil_neg * bcolor
                d2[ hi * self.h: (hi+1) * self.h, wi * self.w : (wi+1) * self.w ] = result

                if img0 is not None:
                    diff = result - img0[ hi * self.h: (hi+1) * self.h, wi * self.w : (wi+1) * self.w ]
                    diff = np.abs(diff)
                    diff = float(np.sum(diff))
                    diffImg[hi,wi] = diff
        if img0 is not None:
            return d2, diffImg
        return d2

    def static_table(self):
        self.decoding_table = [u"\u0000",
u"\u263A",
u"\u263B",
u"\u2665",
u"\u2666",
u"\u2663",
u"\u2660",
u"\u2022",
u"\u25D8",
u"\u25CB",
u"\u25D9",
u"\u2642",
u"\u2640",
u"\u266A",
u"\u266B",
u"\u263C",
u"\u25BA",
u"\u25C4",
u"\u2195",
u"\u203C",
u"\u00B6",
u"\u00A7",
u"\u25AC",
u"\u21A8",
u"\u2191",
u"\u2193",
u"\u2192",
u"\u2190",
u"\u221F",
u"\u2194",
u"\u25B2",
u"\u25BC",
u"\u0020",
u"\u0021",
u"\u0022",
u"\u0023",
u"\u0024",
u"\u0025",
u"\u0026",
u"\u0027",
u"\u0028",
u"\u0029",
u"\u002A",
u"\u002B",
u"\u002C",
u"\u002D",
u"\u002E",
u"\u002F",
u"\u0030",
u"\u0031",
u"\u0032",
u"\u0033",
u"\u0034",
u"\u0035",
u"\u0036",
u"\u0037",
u"\u0038",
u"\u0039",
u"\u003A",
u"\u003B",
u"\u003C",
u"\u003D",
u"\u003E",
u"\u003F",
u"\u0040",
u"\u0041",
u"\u0042",
u"\u0043",
u"\u0044",
u"\u0045",
u"\u0046",
u"\u0047",
u"\u0048",
u"\u0049",
u"\u004A",
u"\u004B",
u"\u004C",
u"\u004D",
u"\u004E",
u"\u004F",
u"\u0050",
u"\u0051",
u"\u0052",
u"\u0053",
u"\u0054",
u"\u0055",
u"\u0056",
u"\u0057",
u"\u0058",
u"\u0059",
u"\u005A",
u"\u005B",
u"\u005C",
u"\u005D",
u"\u005E",
u"\u005F",
u"\u0060",
u"\u0061",
u"\u0062",
u"\u0063",
u"\u0064",
u"\u0065",
u"\u0066",
u"\u0067",
u"\u0068",
u"\u0069",
u"\u006A",
u"\u006B",
u"\u006C",
u"\u006D",
u"\u006E",
u"\u006F",
u"\u0070",
u"\u0071",
u"\u0072",
u"\u0073",
u"\u0074",
u"\u0075",
u"\u0076",
u"\u0077",
u"\u0078",
u"\u0079",
u"\u007A",
u"\u007B",
u"\u007C",
u"\u007D",
u"\u007E",
u"\u2302",
u"\u00C7",
u"\u00FC",
u"\u00E9",
u"\u00E2",
u"\u00E4",
u"\u00E0",
u"\u00E5",
u"\u00E7",
u"\u00EA",
u"\u00EB",
u"\u00E8",
u"\u00EF",
u"\u00EE",
u"\u00EC",
u"\u00C4",
u"\u00C5",
u"\u00C9",
u"\u00E6",
u"\u00C6",
u"\u00F4",
u"\u00F6",
u"\u00F2",
u"\u00FB",
u"\u00F9",
u"\u00FF",
u"\u00D6",
u"\u00DC",
u"\u00A2",
u"\u00A3",
u"\u00A5",
u"\u20A7",
u"\u0192",
u"\u00E1",
u"\u00ED",
u"\u00F3",
u"\u00FA",
u"\u00F1",
u"\u00D1",
u"\u00AA",
u"\u00BA",
u"\u00BF",
u"\u2310",
u"\u00AC",
u"\u00BD",
u"\u00BC",
u"\u00A1",
u"\u00AB",
u"\u00BB",
u"\u2591",
u"\u2592",
u"\u2593",
u"\u2502",
u"\u2524",
u"\u2561",
u"\u2562",
u"\u2556",
u"\u2555",
u"\u2563",
u"\u2551",
u"\u2557",
u"\u255D",
u"\u255C",
u"\u255B",
u"\u2510",
u"\u2514",
u"\u2534",
u"\u252C",
u"\u251C",
u"\u2500",
u"\u253C",
u"\u255E",
u"\u255F",
u"\u255A",
u"\u2554",
u"\u2569",
u"\u2566",
u"\u2560",
u"\u2550",
u"\u256C",
u"\u2567",
u"\u2568",
u"\u2564",
u"\u2565",
u"\u2559",
u"\u2558",
u"\u2552",
u"\u2553",
u"\u256B",
u"\u256A",
u"\u2518",
u"\u250C",
u"\u2588",
u"\u2584",
u"\u258C",
u"\u2590",
u"\u2580",
u"\u03B1",
u"\u00DF",
u"\u0393",
u"\u03C0",
u"\u03A3",
u"\u03C3",
u"\u00B5",
u"\u03C4",
u"\u03A6",
u"\u0398",
u"\u03A9",
u"\u03B4",
u"\u221E",
u"\u03C6",
u"\u03B5",
u"\u2229",
u"\u2261",
u"\u00B1",
u"\u2265",
u"\u2264",
u"\u2320",
u"\u2321",
u"\u00F7",
u"\u2248",
u"\u00B0",
u"\u2219",
u"\u00B7",
u"\u221A",
u"\u207F",
u"\u00B2",
u"\u25A0",
u"\u00A0"]
        self.decoding_table_rmap = { k:v for v,k in enumerate(self.decoding_table) }

    def findC(self, ascii_c:int, color = [255,255,255], bcolor = [0,0,0]): # notice default arg mutable
        raise Exception("should be implemented as return np.array of (h,w,c)")

class TTFFont(FontBase):
    def __init__(self, font_size):
        self.font_size = font_size
        self.scale = 2
        self.h = font_size
        self.w = font_size // 2
        ttf_font = 'terminus-ttf-4.47.0/TerminusTTF-4.47.0.ttf'
        bdf_font = "terminus-font-4.48/ter-u12n.bdf"
        #self.fnt = ImageFont.truetype(ttf_font, font_size * self.scale)
        self.fnt = ImageFont.truetype("courbd.ttf", font_size * self.scale)

        self.static_table()
        self.genAllChar()



    # while character
    def genChar(self, c):
        # 'L' mode grey color
        txt = Image.new('L', (self.font_size*self.scale // 2, self.font_size*self.scale), 0)
        d = ImageDraw.Draw(txt)
        d.text((0,0), c, font=self.fnt, fill=255)
        txt = txt.resize( (self.font_size // 2, self.font_size ),Image.NEAREST )
        #txt.save(f"x_{self.decoding_table_rmap[c]}.bmp")
        return normalize_0_1(np.array(txt, dtype=np.float)), txt

class BitmapFont(FontBase):
    def __init__(self, font_size):
        self.font_size = font_size
        if font_size == 12:
            bdf_font = "terminus-font-4.48/ter-u12n.bdf"
        elif font_size == 18:
            bdf_font = "terminus-font-4.48/ter-u18n.bdf"
        else:
            raise Exception(f"do not support front size {font_size}")

        self.h = font_size
        self.w = font_size // 2 # NOTICE fixed
        self.empty_set = set()

        with open(bdf_font,'rb') as f:
            self.fnt = BdfFontFile(f)

        self.static_table()
        self.genAllChar()

    # while character
    def genChar(self, c):
        ascii_idx = self.decoding_table_rmap[c]
        if self.fnt.glyph[ascii_idx] is None:
            self.empty_set.add(ascii_idx)
            return self.genChar(' ')
        id,_,_,_,im = self.fnt.glyph[ascii_idx]
        return normalize_0_1(1*np.array(im, dtype=np.float)), im

class CombinedBitmapFont(BitmapFont):
    def __init__(self, font_size):
        self._f = TTFFont(font_size)

        self.chBelong = [-1] * 256
        super().__init__(font_size)
        print("done")

    # while character
    def genChar(self, c):
        idx = self.decoding_table_rmap[c]
        ascii_idx = self.decoding_table_rmap[c]
        if self.fnt.glyph[ascii_idx] is None:
            self.empty_set.add(ascii_idx)
            self.chBelong[ ascii_idx ] = 0
            return self._f.genChar(c)
        id,_,_,_,im = self.fnt.glyph[ascii_idx]
        if idx >= 128:
            self.chBelong[ascii_idx] = 0
            return self._f.genChar(c)
        self.chBelong[ascii_idx] = 1
        #im.save(f"x_{self.decoding_table_rmap[c]}.bmp")
        t = normalize_0_1(1*np.array(im, dtype=np.float))
        if self.font_size == 18:
            # it is 18 x 10 size, remove the last column
            t = t[:,:-1]
        return t, im




class PictureFont(FontBase):
    """
    Load "font" from a image
    """
    def __init__(self, font_size = 12):
        if font_size == 12:
            self.path = "cp437_12x12.png"
        if font_size == 18:
            self.path = "cp437_18x18.png"
        self.fullimg = Image.open(self.path)
        fw, fh = self.fullimg.size
        # assume 16 x 16 blocks
        self.w = fw // 16
        self.h = fh // 16
        assert self.h == self.w
        self.font_size = self.h
        self.static_table()
        self.convertImage()
        self.patch()

    def convertImage(self):
        imgArr = np.array(self.fullimg)
        # (h1, h2, w1, w2, c)
        imgArr = imgArr.reshape( (16, self.h, 16, self.w, 3) )
        self.chnp = []
        self.chimg = []
        for i in range(16):
            for j in range(16):
                smallarr = imgArr[ i,:,j,:,:]
                smallImg = Image.fromarray(smallarr)
                smallarr2 = smallarr.sum(axis = -1)
                smallarr2 = normalize_0_1(smallarr2)
                self.chnp += [ smallarr2 ]
                self.chimg += [smallImg]
                #smallImg.save(f"x_{i*16 + j}.bmp")

    def genAllChar(self):
        pass

    # while character
    def genChar(self, c):
        idx = self.decoding_table_rmap[c]
        return self.chnp[idx], self.chimg[idx]

    def patch(self):
        sharp12 = np.array([[0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,],
         [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,],
         [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,],
         [0., 0., 0., 0., 1., 0., 0., 1., 0., 0., 0., 0.,],
         [0., 0., 0., 1., 1., 1., 1., 1., 1., 0., 0., 0.,],
         [0., 0., 0., 0., 1., 0., 0., 1., 0., 0., 0., 0.,],
         [0., 0., 0., 0., 1., 0., 0., 1., 0., 0., 0., 0.,],
         [0., 0., 0., 1., 1., 1., 1., 1., 1., 0., 0., 0.,],
         [0., 0., 0., 0., 1., 0., 0., 1., 0., 0., 0., 0.,],
         [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,],
         [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,],
         [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,]] )
        idx = self.decoding_table_rmap['#']
        if self.path == "cp437_12x12.png":
            self.chnp[idx] = sharp12
            # TODO change self.chimg as well