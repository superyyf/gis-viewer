import time
from PyQt5.QtCore import QThread, QPoint, pyqtSignal
from src.tools.OcrInterface import detectText, textParser
from src.match.match import match


class MyBuildOverviewThread(QThread):

    def __init__(self, dataset, parent=None):
        QThread.__init__(self, parent)
        self.dataset = dataset

    def run(self) -> None:
        self.dataset.BuildOverviews("AVERAVE", [2, 4, 8, 16, 32, 64])


class MyMatchThread(QThread):
    targetSignal = pyqtSignal(object)

    def __init__(self, imageItem, parent=None):
        QThread.__init__(self, parent)
        self.imageItem = imageItem

    def run(self) -> None:
        str_text = detectText('test')
        coord = textParser(str_text)

        self.imageItem.captureROI(coord[0], coord[1])
        rs_image = 'D:\project\gis-viewer\data\\01.jpg'
        uav_image = 'D:\project\gis-viewer\data\\02.jpg'

        target = match(rs_image, uav_image)
        self.target = self.imageItem.clipROI.topLeft() + QPoint(target[0], target[1])
        self.targetSignal.emit(self.target)


class MyProgressBarThread(QThread):

    progress_update = pyqtSignal(int)

    def __init__(self):
        QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        while 1:
            stepValue = 1
            self.progress_update.emit(stepValue)
            time.sleep(0.1)
