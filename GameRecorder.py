from controls.ActionController import *
from controls.ActionRecorder import *
from controls.Events import *
import time
from process_snapshot import WindowCapture
from threading import Thread, Lock

from playsound import playsound
import numpy as np
import pickle
import win32gui
import math

class GameRecorder:

    """
    Need to record screen with action together !
    So the array of action and screen must be the same length

    """

    PAUSE_INTERVAL = 0.2

    MAX_NO_ACTION_TIME = 5.0
    ABSOLUTE_MAX_NO_ACTION_TIME = 8.0 # long than time it won't do anything

    MAX_MOVE_TIME = 8.0
    ABSOLUTE_MAX_MOVE_TIME = 20.0  # long than time it won't do anything


    PARTIAL_LOG_COUNT = 500

    def __init__(self):

        self.recorder = ActionRecorder(self.mouse_offset_fn, self.record_callback)
        self.recorder.begin_callback = self.start
        self.recorder.end_callback = self.end
        self.screen = WindowCapture()
        self.valid_last_action = False
        self.last_record_time = time.time()
        self.last_action_time = self.last_record_time
        self.mutex = Lock()
        # in the case of font 12
        self.H = 720
        self.W = 1272
        self.write_path = "capture"
        self.th = Thread(target=self.recorder.loop)
        print("init start")
        self.th.start()
        self.th.join()
        print("init end")


    def inside_window(self):
        x, y = win32gui.GetCursorPos()  # use logical position
        x, y = win32gui.ScreenToClient(self.screen.hwnd, (x, y))
        print("inside_window",x,y)
        return 0 <= y <= self.H and 0 <= x <= self.W

    def mouse_offset_fn(self, event:MoveEvent):
        event.x, event.y = win32gui.GetCursorPos() # use logical position
        xy2 = win32gui.ScreenToClient(self.screen.hwnd,(event.x, event.y))
        xy2 = round(xy2[0] * 1.25), round(xy2[1] * 1.25)
        # adjust :
        #xy2 = xy2[0] - 140, xy2[1] - 76
        event.x, event.y = xy2
        if 0 <= event.y <= self.H and \
            0 <= event.x <= self.W :
            return event
        return None

    def record_callback(self, event):
        t = time.time()
        if type(event) is MoveEvent:
            self.move_event_pause = False
            if t - self.last_action_time > self.ABSOLUTE_MAX_MOVE_TIME:
                self.move_event_pause = True
                self.valid_last_action = False
            elif t - self.last_action_time > self.MAX_MOVE_TIME:
                self.move_event_pause = True
                self.valid_last_action = False
            else:
                self.last_record_move_event = event
        elif type(event) in {ButtonEvent, WheelEvent}:
            # make sure it is inside window
            if self.inside_window() :
                self.valid_last_action = True
            else:
                self.valid_last_action = False
        else:
            self.valid_last_action = True
        if self.valid_last_action:
            with self.mutex:
                # need to recover last move
                if type(event) is not MoveEvent:
                    xy1 = (0,0)
                    try:
                        xy1 = self.last_record_move_event.xy()
                    except:
                        pass
                    xy2 = self.recorder.last_mouse.xy()
                    dist = abs(xy2[0] - xy1[0]) + abs(xy2[1] - xy1[1])
                    if dist >= 4:
                        e = self.recorder.last_mouse
                        # record latest position
                        img = self.screen.capture_and_toImg()
                        self.imgs += [img]
                        self.events += [e]
                        print("move_event_pause record ", repr(self.events[-1]), "dist", dist)

                t = time.time()
                self.events += [ event ]
                img = self.screen.capture_and_toImg()
                self.imgs += [ img ]
                self.last_record_time = t
                if type(event) is not MoveEvent:
                    self.last_action_time = t
                print("record ", repr(self.events[-1]))

    def start(self):
        self.last_record_time = time.time()
        self.last_action_time = self.last_record_time
        playsound("start.mp3")
        self.log_idx = 0
        self.enabled = True
        self.events = []
        self.imgs = []
        self.move_event_pause = False
        th = Thread(target=self.loop)
        th.start()

    def write_partial_logs(self, logs_img:list, logs_events:list):
        def write(write_path, logs_img, logs_events, log_idx):
            logs_img = np.array(logs_img)
            print(f"write to {write_path}_imgs_{log_idx}.npz")
            with open(f'{write_path}_imgs_{log_idx}.npz', 'wb') as f:
                np.savez_compressed(f, logs_img)
            with open(f'{write_path}_events_{log_idx}.pickle', 'wb') as f:
                pickle.dump(logs_events,f)
            print(f"write to {write_path}_imgs_{log_idx}.npz FINISHED")

        th = Thread(target=write, args=(self.write_path, logs_img, logs_events, self.log_idx) )
        th.start()
        self.log_idx += 1

    def end(self):
        playsound("end.mp3")
        self.enabled = False
        # TODO events to a folder
        self.write_partial_logs(self.imgs, self.events)


    def loop(self):
        """
        handle pause situation
        event triggered is captured in record_event
        :return:
        """
        while self.enabled:
            time.sleep(self.recorder.PAUSE_TIME)
            t = time.time()
            # TODO if too much time no ACTION, no recording
                # one exception, if there are too much change in map
            flag = True
            if t - self.last_action_time > self.ABSOLUTE_MAX_NO_ACTION_TIME:
                flag = False
            elif t - self.last_action_time > self.MAX_NO_ACTION_TIME:
                flag = False
                # TODO check map change
                pass
            if flag and t - self.last_record_time > self.PAUSE_INTERVAL:
                with self.mutex:
                    t = time.time()
                    if t - self.last_record_time > self.PAUSE_INTERVAL:
                        self.events += [PauseEvent(t)]
                        img = self.screen.capture_and_toImg()
                        self.imgs += [img]
                        self.last_record_time = t
                        print("record ", repr(self.events[-1]))

            # check logs
            if len(self.events) > self.PARTIAL_LOG_COUNT + 10:
                with self.mutex:
                    p_imgs = self.imgs[ :self.PARTIAL_LOG_COUNT]
                    p_events = self.events[ :self.PARTIAL_LOG_COUNT]
                    self.imgs = self.imgs[self.PARTIAL_LOG_COUNT:]
                    self.events = self.events[self.PARTIAL_LOG_COUNT:]

                self.write_partial_logs(p_imgs, p_events)


gr = GameRecorder()