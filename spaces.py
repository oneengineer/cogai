from controls.Events import *


BLOCK_H = 60
BLOCK_W = 212

class Bundle(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.__dict__ = self

class ActionSpaces:
    def __init__(self, font_size = 12):
        self.hh = font_size
        self.ww = font_size // 2
        self.actions = self._gen()
        self.action2idx = { str(a) : idx for idx,a in enumerate(self.actions)}
        self.idx2action = { idx: str(a) for idx, a in enumerate(self.actions)}
        self.pause_idx = 0
        self.abstract_move_idx = 1
        self.n = len(self.actions)

    def move_event_discrete(self, move_event:MoveEvent):
        m2 = MoveEvent(move_event) # make a copy
        m2.x /= m2.x / self.ww
        m2.y /= m2.y / self.hh
        return m2

    def _gen_mouse_move(self):
        result = []
        for i in range(BLOCK_H):
            for j in range(BLOCK_W):
                that = Bundle(x = i, y = j, time = None)
                item = MoveEvent(that)
                result += [item]
        return result

    def _gen(self):
        pause = PauseEvent(None)
        # keyboard
        btns = [ Bundle(name = i, event_type = "up", time = None) for i in ['a','c','g','f','1','2','3','4'] ]
        btns = [ KeyboardEvent(i) for i in btns ]

        # click
        clicks = []
        for button in ["left", "right"]:
            for key in [None, "ctrl", "shift"]:
                b = Bundle(button = button, event_type = "down", time = None)
                b.key = key
                clicks += [ ButtonEvent(b) ]

        wheels = []
        for i in [6, 1, -1, -6]:
            w = WheelEvent(Bundle(delta = i, time = None))
            wheels += [w]

        moves = self._gen_mouse_move()
        moves_abstract = MoveEvent(Bundle(x = -1, y = -1, time = -1))

        #return [pause] + btns + clicks + wheels + moves
        return [pause] + [moves_abstract] + btns + clicks + wheels

def work():
    a = ActionSpaces(12)
    for idx,a in enumerate(a.actions):
        print(idx,str(a))

work()
