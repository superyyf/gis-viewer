import os
from PyQt5.QtGui import QCloseEvent, QResizeEvent
from PyQt5.QtWidgets import QMainWindow, QFileDialog
from .ui_template import Ui_MainWindow
from src.tools.myThread import MyMatchThread
import imghdr


class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("XXX系统")
        self.show()

        self.ui.actionOpen_RS_Image.triggered.connect(self.ui.graphicsView.read_file)
        self.ui.actionOpen_UAV_Image.triggered.connect(self.read_uav_image)
        self.ui.graphicsView.mouseMoveSignal.connect(self.ui.statusbar.showLocation)
        self.ui.graphicsView.zoomSignal.connect(self.ui.statusbar.showScale)
        self.ui.actionStart.triggered.connect(self.start_ocr_match)
        self.ui.actionScale.triggered.connect(self.ui.graphicsView.set_raw_scale)
        self.ui.graphicsView.buildStartSignal.connect(self.ui.statusbar.start_progress_bar)
        self.ui.graphicsView.buildFinishSiganl.connect(self.ui.statusbar.end_progress_bar)
        self.ui.actionEdit.triggered.connect(self.edit_mode)
        self.ui.actionPan_Zoom.triggered.connect(self.zoom_mode)
        self.ui.graphicsView.scene.changeCursorSignal.connect(self.ui.graphicsView.change_cursor)

    def edit_mode(self):
        self.ui.actionEdit.setChecked(True)
        self.ui.actionPan_Zoom.setChecked(False)
        self.ui.graphicsView.convert_to_edit()

    def zoom_mode(self):
        self.ui.actionEdit.setChecked(False)
        self.ui.actionPan_Zoom.setChecked(True)
        self.ui.graphicsView.convert_to_zoom()

    def read_uav_image(self):
        fname, dummy = QFileDialog.getOpenFileName(self, "打开无人机图像文件")
        if len(fname) and os.path.isfile(fname):
            if imghdr.what(fname) == 'tiff':
                print("File error!")
            else:
                self.ui.graphicsView.uav_window.uav_viewer.read_image(fname)
        else:
            print("File error!")

    def start_ocr_match(self):
        if self.ui.graphicsView.uav_window.uav_viewer.hasImg and self.ui.graphicsView.hasItem:
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

    def closeEvent(self, a0: QCloseEvent) -> None:
        self.ui.graphicsView.uav_window.close()
