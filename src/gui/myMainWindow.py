from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QMainWindow
from .myUavWidget import MyUavWidget
from .ui_template import Ui_MainWindow
from src.tools.myThread import MyMatchThread


class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.show()

        self.ui.actionOpen_RS_Image.triggered.connect(self.ui.graphicsView.read_file)
        self.ui.actionOpen_UAV_Image.triggered.connect(self.popup)
        self.ui.graphicsView.mouseMoveSignal.connect(self.ui.statusbar.showLocation)
        self.ui.graphicsView.zoomSignal.connect(self.ui.statusbar.showScale)
        self.ui.actionStart.triggered.connect(self.start_ocr_match)
        self.ui.actionScale.triggered.connect(self.ui.graphicsView.set_raw_scale)
        self.ui.graphicsView.buildStartSignal.connect(self.ui.statusbar.start_progress_bar)
        self.ui.graphicsView.buildFinishSiganl.connect(self.ui.statusbar.end_progress_bar)

    def closeEvent(self, a0: QCloseEvent) -> None:
        self.uav_window.close()

    def popup(self):
        self.uav_window = MyUavWidget()
        self.uav_window.read_image()

    def start_ocr_match(self):
        if self.uav_window.hasItem and self.ui.graphicsView.hasItem:
            self.work_thread = MyMatchThread(self.ui.graphicsView.imageItem)
            self.work_thread.targetSignal.connect(self.get_result)
            self.work_thread.started.connect(self.ui.statusbar.start_progress_bar)
            self.work_thread.finished.connect(self.ui.statusbar.end_progress_bar)
            self.work_thread.start()
        else:
            print("require rs and uav images!\n")

    def get_result(self, target):
        self.ui.graphicsView.target = target
        self.ui.graphicsView.hasTarget = True
        self.ui.graphicsView.drawRect()


