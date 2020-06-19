import win32gui
import win32ui
from ctypes import windll
# import Image
from PIL import Image

all_ims = []
def work():
    hwnd = win32gui.FindWindow(None, 'cogmind - Beta 9.4')
    # Change the line below depending on whether you want the whole window
    # or just the client area.
    #left, top, right, bot = win32gui.GetClientRect(hwnd)
    left, top, right, bot = win32gui.GetWindowRect(hwnd)
    print("left, top, right, bot",left, top, right, bot)
    w = right - left
    h = bot - top
    print("w,h ", w,h )
    w = 1280 - 2
    h = 755

    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC  = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()

    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)

    saveDC.SelectObject(saveBitMap)

    # Change the line below depending on whether you want the whole window
    # or just the client area.
    #result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 1)
    result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0)
    print(result)

    bmpinfo = saveBitMap.GetInfo()
    bmpstr:bytes = saveBitMap.GetBitmapBits(True)
    print(bmpinfo,type(bmpstr))

    im = Image.frombuffer(
        'RGB',
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1)
    global all_ims
    all_ims += [im]
    # im.save("a.bmp")
import time

time.sleep(3)
for i in range(1):
    work()
    time.sleep(0.001)
for i in range(1):
    all_ims[i].save(f"a_{i}.bmp")

# im = Image.frombuffer(
#     'RGB',
#     (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
#     bmpstr, 'raw', 'BGRX', 0, 1)