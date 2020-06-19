import win32gui, win32api, win32con
import time
import random


import mouse
import keyboard
import time
from controls.Events import *

class ActionRecorder:

    PAUSE_TIME = 0.1 # second
    MOUSE_MOVE_TIME = 0.2  # second
    MAX_MOUSE_TIME = 5


    def __init__(self, mouse_offset_fn, record_callback = None):
        self.mouse_offset_fn = mouse_offset_fn
        self.last_mouse = None # last mouse relative pos
        self.last_action_time = time.time()
        self.last_event_time = time.time()
        self.valid_keys = {'a', 'g', 'f', '1', '2', '3', '4', '.'}
        self.last_non_mouse_move_time = time.time()
        self.record_callback = record_callback
        self.end_callback = None
        self.begin_callback = None
        self.last_event = None


    def winEnumHandler(self, hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if self.process_name in title:
                self.hwnd = hwnd
                print("set process handle ", title)

    def set_window(self, name):
        self.process_name = name
        """
        record action for a specific window
        :return:
        """
        win32gui.EnumWindows(self.winEnumHandler, None)


    def record_mouse(self, event):
        #TODO check event in range
        #TODO check event between time is large enough
        #     unless it has a non-mouse move event
        #     key input event should be filter only with valid keys
        # WheelEvent delta

        # convert event
        if type(event) is mouse._mouse_event.MoveEvent:
            event = MoveEvent(event)
            event = self.mouse_offset_fn(event)
            # it is possible that event out of window and become none
            if event is None:
                return
            self.last_mouse = event

        elif type(event) is mouse._mouse_event.ButtonEvent:
            if event.event_type == 'up': # ignore up event, only record down
                return
            event = ButtonEvent(event)
        elif type(event) is mouse._mouse_event.WheelEvent:
            event = WheelEvent(event)


        if event.time - self.last_event_time < ActionRecorder.PAUSE_TIME \
            and type(event) is WheelEvent \
                and type(self.events[-1]) is WheelEvent:
                # last delta += 1
                self.events[-1].delta += event.delta
        elif type(event) is MoveEvent and type(self.last_event) is MoveEvent:
            if event.time - self.last_event_time < ActionRecorder.MOUSE_MOVE_TIME:
                # replace last
                #print("replace move", event.time - self.last_event_time)
                self.events[-1] = event
                self.last_event = event
                return
            #if event.time - self.last_non_mouse_move_time > self.MAX_MOUSE_TIME:
                # too slow
            #    return
        elif event.time - self.last_event_time < ActionRecorder.PAUSE_TIME:
            return
        else:
            self.last_non_mouse_move_time = event.time


        key = None
        if keyboard.is_pressed('ctrl'):
            key = "ctrl"
            print("control pressed")
        if keyboard.is_pressed('alt'):
            key = "alt"
            print("alt pressed")
        if keyboard.is_pressed('shift'):
            key = "shift"
            print("shift pressed")

        self.last_event_time = event.time

        if type(event) is ButtonEvent:
            event.key = key

        #print(event,len(self.events),  event.time - self.last_event_time)
        self.events.append(event)
        self.last_event = event
        if self.record_callback:
            self.record_callback(event)


    def record_keyboard(self, event):
        #TODO check event in range
        #TODO check event between time is large enough
        #     unless it has a non-mouse move event
        #     key input event should be filter only with valid keys
        if event.event_type != "up":
            return
        if event.name not in self.valid_keys:
            return

        # keyboard do not check time

        event = KeyboardEvent(event)
        self.last_event = event
        self.events.append(event)
        if self.record_callback:
            self.record_callback(event)
        self.last_event_time = event.time
        self.last_non_mouse_move_time = event.time

    def end(self):
        if self.end_callback:
            self.end_callback()

    def begin(self):
        self.events = []
        if self.begin_callback:
            self.begin_callback()


    def loop(self):
        """a
        F10 to start recording
        F10 again to end recording
        :return:
        """
        while True:
            keyboard.wait("ctrl + F10")  # Waiting for 'F10' to be pressed
            self.begin()
            self.events =[]  # This is the list where all the events will be stored
            mouse.hook(self.record_mouse)  # starting the mouse recording
            keyboard.hook(self.record_keyboard)  # starting the mouse recording
            keyboard.wait("ctrl + F10")  # Waiting for 'a' to be pressed
            mouse.unhook(self.record_mouse)  # Stopping the mouse recording
            keyboard.unhook(self.record_keyboard)  # starting the mouse recording
            self.end()

#
#
# a = ActionRecorder()
# a.loop()