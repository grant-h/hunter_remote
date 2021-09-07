#!/usr/bin/env python3
import sys
import time

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from hunter_tx import HunterTX, HunterCommand

# CHANGE ME! See decoding_notes.txt to understand the protocol
FAN_ID = "111000001111100001101110000111111110011" # office
#FAN_ID = "111110011101011011111010010011000011110" # bedroom

class RadioWorker(QObject):
    finished = pyqtSignal()

    def __init__(self, addr):
        super().__init__()
        self.tx = HunterTX()
        self.tx.set_addr(addr)

    def run(self, cmd):
        assert cmd

        self.tx.set_cmd(cmd)
        self.tx.restart()
        self.tx.run()
        self.tx.wait()
        self.finished.emit()

class CircleButton(QWidget):
    click = pyqtSignal(HunterCommand)

    def __init__(self, parent, name, debug=False):
        super().__init__(parent)

        self.name = name
        self.debug = debug
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def paintEvent(self, event=None):
        if not self.debug:
            return

        painter = QPainter(self)

        painter.setOpacity(0.7)
        painter.setBrush(Qt.red)
        painter.drawRect(self.rect())

    def mousePressEvent(self, event):
        print("PRESS:", self.name)
        self.click.emit(self.name)

class LightOverlay(QWidget):
    def paintEvent(self, event=None):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setOpacity(1.0)
        painter.setBrush(QColor(99, 130, 255))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.rect())

class HunterGUI(QMainWindow):
    BUTTONS = [
        [HunterCommand.ON_TOGGLE, 0.496, 0.532],
        [HunterCommand.FAN_0, 0.493, 0.287],
        [HunterCommand.FAN_1, 0.266, 0.365],
        [HunterCommand.FAN_2, 0.5, 0.143],
        [HunterCommand.FAN_3, 0.724, 0.365],
    ]
    LIGHT = [0.5032, 0.069]

    def __init__(self):
        super().__init__()

        self.bg = QImage("img/hunter-remote.png")
        self.setFixedSize(self.bg.size()/2)

        self.xmit = False
        self.light = LightOverlay(self)
        self.light.setVisible(False)

        self.worker = RadioWorker(FAN_ID)
        self.worker.finished.connect(self.radioDone)

        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.start()

        bounds = self.rect()
        dim = 33
        ldim = 6

        self.light.setGeometry(QRect(
            int(bounds.width()*HunterGUI.LIGHT[0]-ldim),
            int(bounds.height()*HunterGUI.LIGHT[1]-ldim),
            ldim*2, ldim*2))

        for name, x, y in HunterGUI.BUTTONS:
            button = CircleButton(self, name, debug=False)
            button.click.connect(self.handleButton)
            cx = int(bounds.width()*x)
            cy = int(bounds.height()*y)

            button.setGeometry(QRect(cx-dim, cy-dim, dim*2, dim*2))
            region = QRegion(0, 0, dim*2, dim*2, QRegion.Ellipse)
            button.setMask(region)

    def paintEvent(self, event=None):
        painter = QPainter(self)
        painter.drawImage(self.rect(), self.bg)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    # Used for calculating button regions
    #def mousePressEvent(self, event):
    #    bounds = self.rect()
    #    pos = event.localPos()
    #    rpos = QPointF(pos.x()/bounds.width(), pos.y()/bounds.height())
    #    #print(rpos)

    def handleButton(self, cmd):
        if self.xmit:
            return

        self.light.setVisible(True)
        self.xmit = True
        self.light.repaint()
        self.callRadio(cmd)

    def callRadio(self, cmd):
        print("TX start...")
        self.worker.run(cmd)

    def radioDone(self):
        print("TX end!")
        self.xmit = False
        self.light.setVisible(False)

def main():
    app = QApplication(sys.argv)

    # Create the main window
    window = HunterGUI()

    window.setWindowFlags(Qt.FramelessWindowHint)
    window.setAttribute(Qt.WA_NoSystemBackground, True)
    window.setAttribute(Qt.WA_TranslucentBackground, True)

    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
