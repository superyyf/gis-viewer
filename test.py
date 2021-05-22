from src.gui.test import Ui_MainWindow
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog
from PyQt5.QtGui import QPixmap
import sys


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.init_ui()

    def init_ui(self):
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.show()
        self.ui.actionOpen_RS_Image.triggered.connect(self.read_image)

    def read_image(self):
        fname, dummy = QFileDialog.getOpenFileName(self, "Open image file.")
        pixmap = QPixmap(fname)
        self.ui.label.setPixmap(pixmap)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainwin = MainWindow()
    sys.exit(app.exec_())