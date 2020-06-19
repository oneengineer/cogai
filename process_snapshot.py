import win32gui
import win32ui
from ctypes import windll
# import Image
from PIL import Image
import numpy as np
all_ims = []
import time

class WindowCapture:

    def __init__(self, font_size = 12):
        self.font_size = font_size
        self.select_handle()
        self.init()

    def select_handle(self):
        self.hwnd = win32gui.FindWindow(None, 'cogmind - Beta 9.4')

    def init(self):
        left, top, right, bot = win32gui.GetWindowRect(self.hwnd)
        #print("left, top, right, bot",left, top, right, bot)
        if self.font_size == 12:
            w = 1280 - 2
            h = 755
        if self.font_size == 18:
            w = 106 * 18 - ( - 3 - 3)
            h = 60 * 18 - (- 32 - 3)
        self.windowH = h
        self.windowW = w

        hwndDC = win32gui.GetWindowDC(self.hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
        saveDC.SelectObject(saveBitMap)
        self.saveDC = saveDC
        self.saveBitMap = saveBitMap

    def capture_and_toImg(self):
        t = self.capture()
        return self.clipImg(t)


    def capture(self):
        windll.user32.PrintWindow(self.hwnd, self.saveDC.GetSafeHdc(), 0)
        bmpinfo = self.saveBitMap.GetInfo()
        bmpstr:bytes = self.saveBitMap.GetBitmapBits(True)
        im = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1)
        t = np.array(im)
        self.last_capture = t
        return t

    def clipImg(self,im):
        imgArr = np.array(im)
        t1 = imgArr[32:self.windowH - 3, 3: self.windowW - 3, :]
        return t1

    def save(self, img, path):
        Image.fromarray(img).save(path)

def work():
    cap = WindowCapture()
    time.sleep(3)
    cap.capture()
    img = cap.clipImg(cap.last_capture)
    cap.save(img,"temp.bmp")

    for i in range(10):
        time.sleep(3)
        cap.capture()
        img = cap.clipImg(cap.last_capture)
        cap.save(img, f"temp_{i}.bmp")

#work()