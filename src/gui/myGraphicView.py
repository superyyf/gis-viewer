from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QFileDialog, QGraphicsSceneMouseEvent
from PyQt5.QtCore import Qt, QRect, QRectF, QPointF, QPoint, pyqtSignal
from PyQt5.QtGui import QResizeEvent
import os.path
import imghdr
from ..tools.GeoTiffParser import GeoTiffItem
from .myRect import MyRect
from ..tools.myThread import MyBuildOverviewThread


class MyGraphicView(QGraphicsView):
    mouseMoveSignal = pyqtSignal(str, str)
    zoomSignal = pyqtSignal(str)
    progressSignal = pyqtSignal(int)
    buildStartSignal = pyqtSignal()
    buildFinishSiganl = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setMouseTracking(True)
        self.hasItem = False

        self.left_click = False
        self.preMousePos = QPointF()
        self.MouseMove = QPointF()
        self.point = QPointF(0, 0)

        self.zoom_max = 1.0
        self.zoom_min = 0.0
        self.zoom_step = 0.1
        self.ROI = QRectF()
        self.not_zoom = True
        self.ROI_ratio = 1.0
        self.current_ratio = 1.0

        self.target = QPoint()
        self.hasTarget = False

        self.scene = QGraphicsScene()
        self.setScene(self.scene)

    def send_start_signal(self):
        self.buildStartSignal.emit()
        print('send start signal\n')

    def send_finish_signal(self):
        self.buildFinishSiganl.emit()
        print('send finish signal\n')

    def build_overview(self):
        band1 = self.imageItem.dataset.GetRasterBand(1)
        print('222\n')
        if band1.GetOverviewCount() < 4:
            self.build_thread = MyBuildOverviewThread(self.imageItem.dataset)
            self.build_thread.started.connect(self.send_start_signal)
            self.build_thread.finished.connect(self.send_finish_signal)
            self.build_thread.finished.connect(self.init_image)
            self.build_thread.start()
            print('done\n')
        else:
            self.init_image()

    def read_file(self):
        fname, dummy = QFileDialog.getOpenFileName(self, "Open image file.")
        if len(fname) and os.path.isfile(fname) and imghdr.what(fname) == 'tiff':
            self.imageItem = GeoTiffItem(fname)
            print('111\n')
            self.build_overview()
        else:
            print("File error!")

    def init_image(self):
        if self.hasItem:
            self.scene.clear()
        else:
            self.hasItem = True
        self.ROI = QRect(0, 0, self.imageItem.xSize, self.imageItem.ySize)
        self.init_ratio = self.current_ratio = self.size().width() / float(self.imageItem.xSize)
        self.ROI_ratio = 1.0
        meg = '{:d}%'.format(int(self.current_ratio*100))
        self.zoomSignal.emit(meg)
        pixmap = self.imageItem.get_image_byte(self.ROI, self.size())
        self.pixmapItem = self.scene.addPixmap(pixmap)
        self.pixmapItem.setPos(0.0, 0.0)
        self.drawRect()

    def update_image(self):
        if self.hasItem:
            self.scene.clear()
        else:
            self.hasItem = True
        self.current_ratio = self.size().width() / float(self.ROI.width())
        pixmap = self.imageItem.get_image_byte(self.ROI, self.size())
        self.pixmapItem = self.scene.addPixmap(pixmap)
        self.pixmapItem.setPos(0, 0)
        self.scene.update()
        meg = '{:d}%'.format(int(self.current_ratio * 100))
        self.zoomSignal.emit(meg)
        self.drawRect()

    def move_rect(self, point):
        x_move = self.ROI.x() - point.x()
        y_move = self.ROI.y() - point.y()
        width_move = int(self.imageItem.xSize * self.ROI_ratio)
        height_move = int(self.imageItem.ySize * self.ROI_ratio)
        if x_move < 0:
            x_move = 0
        if y_move < 0:
            y_move = 0
        if x_move + self.ROI.width() > self.imageItem.xSize:
            x_move = self.imageItem.xSize - self.ROI.width()
        if y_move + self.ROI.height() > self.imageItem.ySize:
            y_move = self.imageItem.ySize - self.ROI.height()
        self.ROI.setX(x_move)
        self.ROI.setY(y_move)
        self.ROI.setWidth(width_move)
        self.ROI.setHeight(height_move)
        self.update_image()

    def zoom_rect(self, point, ratio, flag):
        if flag:
            x_move = int(self.zoom_step * point.x() + (1 - self.zoom_step) * self.ROI.x())
            y_move = int(self.zoom_step * point.y() + (1 - self.zoom_step) * self.ROI.y())
        else:
            x_move = int((1 + self.zoom_step) * self.ROI.x() - self.zoom_step * point.x())
            y_move = int((1 + self.zoom_step) * self.ROI.y() - self.zoom_step * point.y())
        width_zoom = int(self.imageItem.xSize * ratio)
        height_zoom = int(self.imageItem.ySize * ratio)
        if x_move + width_zoom <= self.imageItem.xSize and \
                y_move + height_zoom <= self.imageItem.ySize and \
                x_move >= 0 and y_move >= 0:
            self.ROI.setX(x_move)
            self.ROI.setY(y_move)
            self.ROI.setWidth(width_zoom)
            self.ROI.setHeight(height_zoom)
            self.ROI_ratio = ratio
            self.update_image()
        else:
            self.init_image()

    def scenexy2imagexy(self, spoint):
        ipoint = spoint / self.current_ratio + QPointF(self.ROI.topLeft())
        return ipoint

    def mousePressEvent(self, a0: QGraphicsSceneMouseEvent) -> None:
        if self.hasItem:
            if a0.button() == Qt.LeftButton:
                self.left_click = True
                self.preMousePos = a0.pos()
            else:
                self.scene.clear()
                self.init_image()

    def mouseReleaseEvent(self, a1: QGraphicsSceneMouseEvent) -> None:
        if self.hasItem:
            if a1.button() == Qt.LeftButton:
                self.left_click = False

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.hasItem:
            point_img = self.scenexy2imagexy(event.pos())
            point_geo = self.imageItem.imagexy2geo(point_img)
            coord_lonlat = self.imageItem.geo2lonlat(point_geo)
            meg1 = '{:d},{:d}'.format(int(point_img.x()), int(point_img.y()))
            meg2 = '{:.4f},{:.4f}'.format(coord_lonlat[0], coord_lonlat[1])
            self.mouseMoveSignal.emit(meg1, meg2)
            if self.left_click:
                self.MouseMove = (event.pos() - self.preMousePos) / self.current_ratio
                self.move_rect(self.MouseMove)
                self.preMousePos = event.pos()

    def wheelEvent(self, event):
        if self.hasItem:
            if event.angleDelta().y() > 0 and self.ROI_ratio * (1 - self.zoom_step) >= self.zoom_min:
                ROI_ratio = self.ROI_ratio * (1 - self.zoom_step)
                point = (event.pos() / self.current_ratio) + self.ROI.topLeft()
                self.zoom_rect(point, ROI_ratio, True)
            elif event.angleDelta().y() < 0 and self.ROI_ratio * (1 + self.zoom_step) <= self.zoom_max:
                ROI_ratio = self.ROI_ratio * (1 + self.zoom_step)
                point = (event.pos() / self.current_ratio) + self.ROI.topLeft()
                self.zoom_rect(point, ROI_ratio, False)

    def resizeEvent(self, event: QResizeEvent) -> None:
        print(type(event.size()), event.size())
        print(type(event.oldSize()), event.oldSize())
        print("resize")

    def is_target_in_ROI(self):
        if self.ROI.topLeft().x() <= self.target.x() <= self.ROI.bottomRight().x():
            if self.ROI.topLeft().y() <= self.target.y() <= self.ROI.bottomRight().y():
                return True
        return False

    def drawRect(self):
        if self.hasTarget and self.is_target_in_ROI():
            w = 100
            h = 100
            rect = QRectF((self.target.x() - self.ROI.x()) * self.current_ratio - w/2, (self.target.y() - self.ROI.y()) * self.current_ratio - h/2, w, h)
            self.rectItem = MyRect(rect)
            self.scene.addItem(self.rectItem)
            self.rectItem.setZValue(1)
            self.scene.update()

    def set_raw_scale(self):
        cen_point = QPointF(self.size().width()/2, self.size().height()/2)
        cen_point_image = self.scenexy2imagexy(cen_point)
        self.ROI.setX(cen_point_image.x() - self.size().width()/2)
        self.ROI.setY(cen_point_image.y() - self.size().height()/2)
        self.ROI.setWidth(self.size().width())
        self.ROI.setHeight(self.size().height())
        self.current_ratio = 1.0
        self.ROI_ratio = self.ROI.width() / self.imageItem.xSize
        self.update_image()
        self.drawRect()
