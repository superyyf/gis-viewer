import sys
from PyQt5.QtWidgets import QApplication
from src.gui.myMainWindow import MyMainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainwin = MyMainWindow()
    mainwin.show()
    sys.exit(app.exec_())
