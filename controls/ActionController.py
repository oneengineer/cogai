import win32gui, win32api, win32con
import time
import random

from controls.Events import *


class ActionControler:

    PAUSE_TIME = 0.1 # second

    def __init__(self):

        self.last_mouse = None # last mouse relative pos
        self.last_action_time = None

    def winEnumHandler(self, hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            print(hwnd,"|", title ,"|")
            if "Untitled - Paint" in title:
                self.hwnd = hwnd


    def showAllWindow(self):
        win32gui.EnumWindows(self.winEnumHandler, None)


    def set_window(self, name):
        # use GetClientRect, because it doesn't include bars, captions
        #self.hwnd = win32gui.FindWindow(name, None)
        print(self.hwnd)
        self.rect:tuple = win32gui.GetWindowRect(self.hwnd)
        # rect is a tuple 4
        print(self.rect, type(self.rect))
        print( self.rect[2] - self.rect[0], self.rect[3] - self.rect[1] )


    def _mouse_move(self,x,y):
        """
        perform action, do not record time
        use set cursor
        :param x:
        :param y:
        :return:
        """
        # use ClientToScreen to convert coor
        self.last_mouse = (x,y)
        xy2 = win32gui.ClientToScreen(self.hwnd, self.last_mouse)
        win32api.SetCursorPos(xy2)


    def mouse_move(self, x, y):
        self._mouse_move(x,y)

    def pause(self):
        time.sleep(ActionControler.PAUSE_TIME)

    def click(self, key = None):
        x,y = self.last_mouse
        if key is not None:
            win32api.keybd_event(VK_CODE[key], 0, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
        if key is not None:
            win32api.keybd_event(VK_CODE[key], 0, win32con.KEYEVENTF_KEYUP ,0)

    def rclick(self, key = None):
        x, y = self.last_mouse
        if key is not None:
            win32api.keybd_event(VK_CODE[key], 0, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, x, y, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, x, y, 0, 0)
        if key is not None:
            win32api.keybd_event(VK_CODE[key], 0, win32con.KEYEVENTF_KEYUP ,0)

    def keyinput(self,k):
        win32api.keybd_event(VK_CODE[k], 0,0,0)
        time.sleep(0.001)
        win32api.keybd_event(VK_CODE[k],0 ,win32con.KEYEVENTF_KEYUP ,0)

    def random_in_rec(self):
        a = random.randint(0,1000) + 20
        b = random.randint(0, 400) + 200
        return a,b

    def random_draw(self):

        for i in range(10000):
            action = random.randint(0,3)
            print(action)
            if action == 0:
                x,y = self.random_in_rec()
                self.mouse_move(x, y)
            elif action == 1:
                self.click()
            elif action == 2:
                self.rclick()
            #elif action == 3:
            #    self.pause()
            time.sleep(0.01)

    def random_input(self):
        time.sleep(3)
        for i in range(100):
            action = random.randint(0,3)
            print(action)
            if action == 0:
                key = 'a'
            elif action == 1:
                key = 'b'
            elif action == 2:
                key = 'c'
            else:
                key = 'd'
            self.keyinput(key)
            time.sleep(0.01)


# a = ActionControler()
# a.showAllWindow()
# #a.set_window("Untitled - Paint")
# #a.random_draw()
#
# a.random_input()




