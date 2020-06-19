from fonts import *



class ASCIIConverter:
    def __init__(self, font_size = 12):
        self.f:BitmapFont = CombinedBitmapFont(font_size)
        self.bigf = TTFFont(56)
        self.hh = self.f.h # char h
        self.ww = self.f.w # char w
        self._prepare_stencil()

    def loadImg(self, path):
        self.img = np.array(Image.open(path),dtype=np.float)

    def transpose(self, img:np.ndarray):
        self.H = img.shape[0]
        self.W = img.shape[1]
        # h x w x 3
        img = img.reshape( ( self.H // self.hh, self.hh, self.W // self.ww, self.ww , 3  ) )
        img:np.ndarray = img.transpose( [0,2,1,3,4] )
        # now it is height, width of char images, channel is leading
        self.img = img
        return img

    def transposeBatched(self, imgs:np.ndarray):
        self.N = imgs.shape[0]
        self.H = imgs.shape[1]
        self.W = imgs.shape[2]
        # h x w x 3
        img = imgs.reshape( (self.N, self.H // self.hh, self.hh, self.W // self.ww, self.ww , 3  ) )
        img:np.ndarray = img.transpose( [0,1,3,2,4,5] )
        # now it is height, width of char images, channel is leading
        self.img = img
        return img

    def _flat_img(self, img: np.ndarray):
        """
        flat the last 2 dimension
        :param img: (batch, H, W, c? ww, hh)
        :return: (batch, H, W, c?, -1)
        """
        t = img.shape[:-2]
        return img.reshape( (*t, -1))

    def _normalize_l1_img(self, img:np.ndarray):
        """
        normalize to make max value 1 and min 0,   then shift -0.5, mean value is not necessary to be 0
        if channel exist, normalize each chanel INDIVIDUALLY !!
        that is to say all pixel in r,g,b togather sum to 1.0
        :param img: (batch, H, W, hh, ww, c?)
        :return: (batch, H, W, hh, ww, c?)
        """

        move_c = False
        c = 1
        if img.ndim == 6:
            # reshape, make color in front hh ww
            img = img.transpose([0,1,2,5,3,4])
            c = 3
            move_c = True
        result = img

        img = self._flat_img(img)
        max = img.max( axis = img.ndim - 1 ) # last dim sum
        min = img.min( axis=img.ndim - 1)  # last dim sum

        # now s(sums) has shape (batch, H, W)
        # if result.ndim == 6:
        #     max = max.reshape( (*max.shape, 1, 1 ,1) )
        #     min = min.reshape((*min.shape, 1, 1, 1))
        # else :
        max = max.reshape((*max.shape, 1, 1))
        min = min.reshape((*min.shape, 1, 1))

        result = (result - min)/( max - min + IMG_EPS)

        result = result - 0.5/c

        if move_c:
            # move back C channel
            result = result.transpose( [0,1,2,4,5,3] )
        return result

    def _prepare_stencil(self):
        self.stencil = np.array( self.f.chnp, dtype=np.float )
        n_ascii = self.stencil.shape[0]
        self.n_ascii = n_ascii

        self.stencil_neg = 1.0 - self.stencil
        self.stencil_weight = self.stencil.reshape( ( n_ascii, -1) )
        self.stencil_weight = self.stencil_weight.sum(axis = 1) + IMG_EPS
        self.stencil_neg_weight = self.stencil_neg.reshape( ( n_ascii, -1) )
        self.stencil_neg_weight = self.stencil_neg_weight.sum(axis = 1) + IMG_EPS
        # (asciid, h, w)-> (flat_image, ascii_id)
        self.stencil_normalized = self.stencil - 0.5
        self.stencil_neg_normalized = self.stencil_neg - 0.5
        self.stencil_mat = self.stencil_normalized.reshape( (n_ascii, -1)).T
        self.stencil_neg_mat = self.stencil_neg_normalized.reshape((n_ascii, -1)).T

    def _fore_back_ground_color_img(self, img:np.ndarray, ascii_ids:np.array):
        """
        :param img: (batch, H, W, hh, ww, c)
        :param ascii_ids: (batch, H, W)  and integer array
        :return: (batch, H, W, 3) , (batch, H, W, 3)  each represents foreground and background
        """
        # extract colors of 1's in
        stencil_f = self.stencil[ascii_ids]
        stencil_b = self.stencil_neg[ascii_ids]
        def getcolor(stencil2, stencil2_sum):
            # has shape (batch, H, W, hh, ww)
            # move c channel to front so that it can broadcast
            img2 = img.transpose( [5,0,1,2,3,4] )
            img2 = img2 * stencil2
            # !! use median as the result color in img2
            c,b,h1,w1,h2,w2 = img2.shape

            img2 = img2.reshape( (c,b,h1,w1, -1) )
            img3 = img2.sum(axis = -1)
            img3 = img3 / stencil2_sum

            #img3 = np.median(img2,axis = -1)
            # transpose back, color at last
            img3 = img3.transpose([1, 2, 3, 0])
            return img3.astype(np.int)

        a = getcolor(stencil_f, self.stencil_weight[ascii_ids] )
        b = getcolor(stencil_b, self.stencil_neg_weight[ascii_ids] )
        return a,b


    def parseImg(self, img:np.ndarray):
        """
        for one or a batch of images,
        get foreground color, background color and its ascii code for each hh,ww block.

        img can be (batch, block_h, block_w, hh, ww, color)
        img can be (block_h, block_w, hh, ww, color)

        :param img:
        :return: an ndarray of 4 element which is ascii, (r,g,b), (r,g,b)  it has shape (batch?, block_h, block_w, 7)
        """
        batched = False
        if img.ndim == 6:
            batched = True
        elif img.ndim == 5:
            batched = False
        else :
            raise Exception("img shape is not right")

        # make unbahced batched
        if not batched:
            img = img.reshape( (1, *img.shape))

        #TODO debug
        #img = img[:, 40:, 29:]

        oldimg = img

        b,h1,w1,h2,w2,c = img.shape
        # normalize
        img:np.ndarray = self._normalize_l1_img(img)
        greyimg = img.sum(axis = img.ndim - 1)
        # flat h,w
        greyimg = greyimg.reshape( (b,h1,w1,-1) )

        # use grey img to decide ascii
        # need matrix multiply ( [batch,h,w],  flat_image) X (flat_image, ascii_id)
        positive_img = np.matmul(greyimg, self.stencil_mat)
        negative_img = np.matmul(greyimg, self.stencil_neg_mat)

        # base on max value to decide positive/negative image
        positive_ids = positive_img.argmax(axis=-1)
        negative_ids = negative_img.argmax(axis=-1)

        positive_val = positive_img.max(axis=-1)
        negative_val = negative_img.max(axis=-1)


        def debug_position(y,x, suspect):
            chunk = greyimg[0][y][x].reshape( (self.hh,self.ww) )
            chunk = np.around(chunk,2)
            chunk[chunk < 0] = 0
            chunk[chunk > 0] = 1
            print( chunk,"\n")

            ascii_idx = suspect
            if type(suspect) is str:
                ascii_idx = self.f.decoding_table_rmap[suspect]
            chunk2 = self.f.chnp[ascii_idx]
            chunk2 = np.around(chunk2, 2)
            print(chunk2, "\n")

            p1 = positive_img[0][y][x]
            topn = p1.argsort()[::-1]
            for idx in topn.tolist()[:30]:
                print(idx, ":", self.f.decoding_table[idx], p1.reshape(-1)[idx])

        #debug_position(0,0,'#')


        use_positive = positive_val > negative_val

        ascii_idx = negative_ids[:]
        ascii_idx[ use_positive ] = positive_ids[ use_positive ]

        # now get color of foreground and background
        foreground, background = self._fore_back_ground_color_img(oldimg, ascii_idx)

        # print(self.f.decoding_table[ascii_idx[0,3,2]])
        # print(foreground[0,3,2])
        # print(background[0, 3, 2])
        ascii_idx = np.expand_dims(ascii_idx,axis=-1)
        result = np.concatenate( [ascii_idx,foreground, background], axis=-1 )
        return result


class ASCIIConverterBig(ASCIIConverter):
    def __init__(self, font_size = 12):
        self.f = PictureFont(font_size)
        self.bigf = self.f
        self.hh = self.f.h  # char h
        self.ww = self.f.w  # char w
        self._prepare_stencil()


class UnionASCIIConverter:
    def __init__(self, font_size = 12):
        self.cbig = ASCIIConverterBig(font_size)
        self.csmall = ASCIIConverter(font_size)
        self.big_tiles = (60 , 106)
        self.small_tiles = (60, 212)
        self.borderTL = (10, 0)
        self.borderBR = (60, 152)

        self.borderTL_pix = (10 * self.csmall.f.h, 0)
        self.borderBR_pix = (60 * self.csmall.f.h, 152 * self.csmall.f.w)

    def convert(self, converter:ASCIIConverter, imgPath:str):
        converter.loadImg(imgPath)
        converter.transpose(converter.img)
        result = converter.parseImg(converter.img)
        self.H = converter.H
        self.W = converter.W
        return result


    def convertBatched(self, converter:ASCIIConverter, imgs:np.ndarray):
        imgs = converter.transposeBatched(imgs)
        result = converter.parseImg(imgs)
        self.H = converter.H
        self.W = converter.W
        return result

    def draw(self, converter, ndarray):
        o = converter.f.drawOut(ndarray[0])
        Image.fromarray(o.astype('uint8')).convert('RGB').save("z.bmp", "bmp")

    def duplicate_big_img(self,data:np.ndarray):
        assert self.csmall.f.w * 2 == self.cbig.f.w
        # data's shape : (batch, h1,w1, 7)
        # duplicate w1
        result = np.repeat(data, 2, axis=2)
        return result

    def smartDraw(self, img1, img2, img0):
        """

        :param img1: small converted
        :param img2: big converted
        :param img0:
        :return:
        """
        img1, diff1 = self.csmall.f.drawOut(img1,img0)
        img2, diff2 = self.cbig.f.drawOut(img2,img0)
        assert img1.shape == img2.shape

        # diff1 : (H,W,hh,ww)
        def reshapeDiff(diff:np.ndarray, hh, ww):
            diff = diff.reshape((*diff.shape, 1, 1))
            diff = diff.repeat(hh, axis=2)
            diff = diff.repeat(ww, axis=3)
            diff = diff.transpose([0,2,1,3])
            diff = diff.reshape( img1.shape[:2] ) # H * hh, W * ww
            return diff

        diff1 = reshapeDiff(diff1, self.csmall.hh, self.csmall.ww)
        diff2 = reshapeDiff(diff2, self.cbig.hh, self.cbig.ww)
        d = diff1 > diff2
        img1[d, :] = img2[d, :]
        Image.fromarray(img1.astype('uint8')).convert('RGB').save("z.bmp", "bmp")



    def convertAllBatched(self, imgs:np.ndarray):
        """

        :param imgs: images of shape (N, H * hh, W * ww, 3)
        :return:
        """
        r1 = self.convertBatched(self.csmall, imgs)
        r2 = self.convertBatched(self.cbig, imgs)
        r2 = self.duplicate_big_img(r2)
        #r2' color is not necessary anymore
        # b  h w 7
        r2 = r2[:,:,:,:1]
        result = np.concatenate([r2,r1],axis=-1)
        return result


    def convertAll(self, imgPath:str, return_img = False):
        """

        :param imgPath:
        :param return_img: shape (batch, h, w, 8)  8 =  ascii big, ascii small, fore rgb, back rgb
        :return:
        """
        r1 = self.convert(self.csmall, imgPath)
        r2 = self.convert(self.cbig, imgPath)
        if return_img:
            # img1 = self.csmall.f.drawOut(r1[0])
            # img2 = self.cbig.f.drawOut(r2[0])
            # img1[ self.borderTL_pix[0]:self.borderBR_pix[0], self.borderTL_pix[1]:self.borderBR_pix[1] ] = \
            #     img2[ self.borderTL_pix[0]:self.borderBR_pix[0], self.borderTL_pix[1]:self.borderBR_pix[1] ]
            # Image.fromarray(img1.astype('uint8')).convert('RGB').save("z.bmp", "bmp")
            tttt = np.array(Image.open(imgPath), dtype=np.float)
            self.smartDraw(r1[0], r2[0], tttt)
        #concat r1, r2
        r2 = self.duplicate_big_img(r2)
        #r2' color is not necessary anymore
        # b  h w 7
        r2 = r2[:,:,:,:1]

        result = np.concatenate([r2,r1],axis=-1)
        return result

def work():

    # a = ASCIIConverter()
    # a.loadImg("b.bmp")
    # t1 = a.transpose(a.img)
    # #a.classify(t1)
    # result = a.parseImg(t1)
    # i = a.f.drawOut(result[0])
    # Image.fromarray(i.astype('uint8')).convert('RGB').save("z.bmp","bmp")
    converter = UnionASCIIConverter(12)
    #converter.convert(converter.cbig, "b.bmp")
    converter.convertAll("d.bmp", True)