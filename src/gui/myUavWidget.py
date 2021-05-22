from PyQt5.QtWidgets import QWidget, QLabel, QFileDialog
from PyQt5.QtGui import QPixmap
import os.path
from PyQt5.QtCore import Qt


class MyUavWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.label = QLabel(self)
        self.label.setGeometry(0, 0, 800, 600)
        self.hasItem = False

    def read_image(self):
        fname, dummy = QFileDialog.getOpenFileName(self, "Open image file.")
        if len(fname) and os.path.isfile(fname):
            self.pixmap = QPixmap(fname)
            self.label.setPixmap(self.pixmap)
            self.hasItem = True
            self.show()
