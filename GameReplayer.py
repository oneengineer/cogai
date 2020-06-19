import sys
from PyQt5.QtWidgets import (QWidget, QToolTip,
    QPushButton, QApplication, QLabel)
from PyQt5.QtGui import QFont, QPixmap, QImage,QPainter, QBrush, QPen
from PyQt5.QtCore import pyqtSlot, Qt, QRect

path_capture = "capture_XXX_0"

import numpy as np
import pickle
from controls.Events import *

class Example(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()


    def initUI(self):

        self.load()

        QToolTip.setFont(QFont('SansSerif', 10))

        self.setToolTip('This is a <b>QWidget</b> widget')

        btn = QPushButton('Next', self)
        btn.resize(btn.sizeHint())
        btn.move(200, 50) # xy
        self.btn_next = btn

        btn = QPushButton('Prev', self)
        btn.resize(btn.sizeHint())
        btn.move(50, 50)  # xy
        self.btn_prev = btn

        self.cur = 0

        self.label = QLabel("label", self)
        self.label.move(400, 50)

        self.label.resize(200, 50)

        self.setGeometry(300, 300, self.W, self.H + 100)
        self.setWindowTitle('Game Replayer')

        self.label_img = QLabel(self)

        self.label_img.move(0, 100)
        self.label_img.resize(self.W, self.H)



        self.label_img_circle = QLabel(self)
        self.label_img_circle.move(200, 200)

        self.btn_next.clicked.connect(self.btnNext)
        self.btn_prev.clicked.connect(self.btnPrev)

        self.pix = None
        self.load_i(0)
        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)

        try:
            rect = QRect(0, 100 , self.W, self.H)
            painter.drawPixmap(rect, self.pix)
            #painter.drawPixmap(self.label_img.rect(), self.pix)

            if self.move_event:
                x,y = self.move_event
                x -= 4; y -= 10;
                painter.setPen(QPen(Qt.green, 1, Qt.SolidLine))
                painter.drawEllipse(x, y + 100, 10, 10)
            elif self.rclick_event:
                x, y = self.rclick_event
                x -= 4;
                y -= 10;
                painter.setPen(QPen(Qt.green, 1, Qt.SolidLine))
                painter.setBrush(QBrush(Qt.red, Qt.SolidPattern))
                painter.drawEllipse(x, y + 100, 10, 10)
            elif self.click_event:
                x, y = self.click_event
                x -= 4;
                y -= 10;
                painter.setPen(QPen(Qt.green, 1, Qt.SolidLine))
                painter.setBrush(QBrush(Qt.blue, Qt.SolidPattern))
                painter.drawEllipse(x, y + 100, 10, 10)
        except Exception as e:
            print(e)

    def load(self):
        temp_path_capture = path_capture.replace("XXX","imgs")
        with open(f"{temp_path_capture}.npz", "rb") as f:
            f2 = np.load(f)
            imgs = f2["arr_0"]

        temp_path_capture = path_capture.replace("XXX", "events")
        with open(f"{temp_path_capture}.pickle", "rb") as f:
            self.events = pickle.load(f)

        self.imgs = imgs
        print("imgs shape ", imgs.shape)
        self.n = imgs.shape[0]
        self.H = imgs.shape[1]
        self.W = imgs.shape[2]
        self.C = imgs.shape[3]
        self.last_move = (0, -20)

    def load_i(self, i):
        try:
            self.move_event = None
            self.rclick_event = None
            self.click_event = None
            self.cur = i
            self.event = self.events[self.cur]
            txt = self.events[self.cur]
            self.label.setText(f"current {self.cur}/ {self.n} " + str(txt))
            self.label.resize(self.label.sizeHint())

            image:np.ndarray = self.imgs[self.cur]
            image = image[:]
            height, width, channel = image.shape
            bytesPerLine = 3 * width
            pix = QImage(image.data, width, height, bytesPerLine, QImage.Format_RGB888)
            pix = QPixmap.fromImage(pix)

            print("load img: ",self.cur, self.events[self.cur])
            self.pix = pix
            #self.label_img.setPixmap(pix)

            # translate event
            if type(self.event) is MoveEvent:
                self.move_event = (self.event.x, self.event.y)
                self.last_move = (self.event.x, self.event.y)
            elif type(self.event) is ButtonEvent:
                for i in range(self.cur, 0, -1):
                    if type(self.events[i]) is MoveEvent:
                        e = self.events[i]
                        self.last_move = (e.x, e.y)
                        print("select last move",self.last_move)
                        break

                if self.event.button == "left":
                    self.click_event = self.last_move
                if self.event.button == "right":
                    self.rclick_event = self.last_move

            self.repaint()
        except Exception as e:
            print("Exception: ", e)

    @pyqtSlot()
    def btnNext(self):
        if self.cur >= self.n:
            self.label.setText("the last page")
        else :
            self.cur += 1
            self.load_i(self.cur)

    @pyqtSlot()
    def btnPrev(self):
        if self.cur <= 0:
            self.label.setText("the first page")
        else :
            self.cur -= 1
            self.load_i(self.cur)

def main():

    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()