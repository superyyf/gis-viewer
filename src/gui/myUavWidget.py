from PyQt5.QtWidgets import QWidget, QSizePolicy, QGridLayout
from PyQt5.QtCore import Qt
from .myUavViewer import MyUavViewer


class MyUavWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.uav_viewer = MyUavViewer(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.gridLayout = QGridLayout(self)
        self.gridLayout.addWidget(self.uav_viewer, 0, 0, 1, 1)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.setFocusPolicy(Qt.StrongFocus)

