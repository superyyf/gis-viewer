from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QFileDialog, QGraphicsSceneMouseEvent
from PyQt5.QtCore import Qt, QRect, QRectF, QPointF, QPoint, pyqtSignal
from PyQt5.QtGui import QResizeEvent, QCursor
import os.path
import imghdr
from ..tools.GeoTiffParser import GeoTiffItem
from .myRect import MyRect
from .myUavWidget import MyUavWidget
from ..tools.myThread import MyBuildOverviewThread
from enum import Enum


def is_in_rect(point: QPoint, rect: QRect):
    if rect.topLeft().x() <= point.x() <= rect.bottomRight().x() and rect.topLeft().y() <= point.y() <= rect.bottomRight().y():
        return True
    else:
        return False


class Mode(Enum):
    ZOOM = 1
    EDIT = 2
    WIN = 3


class MyGraphicScene(QGraphicsScene):
    changeCursorSignal = pyqtSignal(int)


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

        self.setCursor(QCursor(Qt.OpenHandCursor))
        self.setMouseTracking(True)
        self.hasItem = False

        self.left_click = False
        self.preMousePos = QPointF()
        self.MouseMove = QPointF()
        self.point = QPointF(0, 0)

        self.zoom_max = 1.0
        self.zoom_min = 0.0
        self.zoom_step = 0.1
        self.ROI = QRect()
        self.canvas = QRect()
        self.ROI_ratio = 1.0
        self.current_ratio = 1.0
        self.full_picture = False
        self.fit_view = False

        self.target = QPoint()
        self.hasTarget = False
        self.rectItem = MyRect()

        self.scene = MyGraphicScene()
        self.setScene(self.scene)
        self.scene.addItem(self.rectItem)

        self.add_uav_win()

        self.mode_type = Mode.ZOOM

    def convert_to_edit(self):
        self.mode_type = Mode.EDIT
        self.rectItem.prepare_to_edit()

    def convert_to_zoom(self):
        self.mode_type = Mode.ZOOM
        self.rectItem.prepare_to_zoom()
        self.update_target()

    def convert_to_win(self):
        self.mode_type = Mode.WIN
        self.update_target()

    def add_uav_win(self):
        self.uav_window = MyUavWidget()
        self.uav_item= self.scene.addWidget(self.uav_window)
        self.uav_rect = QRectF(self.scene.width() - 400, 0, 400, 400)
        self.uav_item.setGeometry(self.uav_rect)
        self.uav_item.setZValue(2)

    def update_uav_win(self):
        before_rect = self.uav_rect
        self.uav_rect = QRectF(self.scene.width() - 400, 0, 400, 400)
        move_vecotr = self.uav_rect.topLeft() - before_rect.topLeft()
        self.uav_item.moveBy(move_vecotr.x(), move_vecotr.y())

    def send_start_signal(self):
        self.buildStartSignal.emit()
        print('send start signal\n')

    def send_finish_signal(self):
        self.buildFinishSiganl.emit()
        print('send finish signal\n')

    def build_overview(self):
        band1 = self.imageItem.dataset.GetRasterBand(1)
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
        fname, dummy = QFileDialog.getOpenFileName(self, "打开遥感图像文件")
        if len(fname) and os.path.isfile(fname) and imghdr.what(fname) == 'tiff':
            self.imageItem = GeoTiffItem(fname)
            self.build_overview()
        else:
            print("File error!")

    def init_canvas_size(self):
        self.shape_ratio = float(self.imageItem.xSize) / float(self.imageItem.ySize)
        view_shape_ratio = float(self.size().width()) / float(self.size().height())
        if self.shape_ratio > view_shape_ratio:
            self.canvas.setX(0)
            self.canvas.setY((float(self.size().height()) - self.size().width() / self.shape_ratio) / 2)
            self.canvas.setWidth(self.size().width())
            self.canvas.setHeight(int(self.size().width() / self.shape_ratio))
        else:
            self.canvas.setX(float(self.size().width() - self.size().height() * self.shape_ratio) / 2)
            self.canvas.setY(0)
            self.canvas.setHeight(self.size().height())
            self.canvas.setWidth(int(self.size().height() * self.shape_ratio))

    def canvas_fit_view(self):
        self.shape_ratio = float(self.imageItem.xSize) / float(self.imageItem.ySize)
        view_shape_ratio = float(self.size().width()) / float(self.size().height())
        self.canvas.setX(0)
        self.canvas.setY(0)
        self.canvas.setSize(self.size())
        if self.shape_ratio > view_shape_ratio:
            self.ROI.setX(float(self.imageItem.xSize - self.imageItem.ySize * view_shape_ratio) / 2)
            self.ROI.setY(0)
            self.ROI.setHeight(self.imageItem.ySize)
            self.ROI.setWidth(int(self.imageItem.ySize * view_shape_ratio))
        else:
            self.ROI.setX(0)
            self.ROI.setY((float(self.imageItem.ySize) - self.imageItem.xSize / view_shape_ratio) / 2)
            self.ROI.setWidth(self.imageItem.xSize)
            self.ROI.setHeight(int(self.imageItem.xSize / view_shape_ratio))
        self.current_ratio = self.canvas.width() / float(self.ROI.width())
        self.ROI_ratio = self.ROI.width() / float(self.imageItem.xSize)

    def init_image(self):
        if self.hasItem:
            self.scene.removeItem(self.pixmapItem)
        else:
            self.hasItem = True
        self.ROI = QRect(0, 0, self.imageItem.xSize, self.imageItem.ySize)
        self.init_canvas_size()
        self.full_picture = True
        self.current_ratio = float(self.canvas.width()) / self.ROI.width()
        self.ROI_ratio = 1.0
        meg = '{:d}%'.format(int(self.current_ratio * 100))
        self.zoomSignal.emit(meg)
        pixmap = self.imageItem.get_image_byte(self.ROI, self.canvas)
        self.pixmapItem = self.scene.addPixmap(pixmap)
        self.pixmapItem.setPos(self.canvas.topLeft())
        self.update_rect()

    def update_image(self):
        if self.hasItem:
            self.scene.removeItem(self.pixmapItem)
        else:
            self.hasItem = True
        self.current_ratio = self.canvas.width() / float(self.ROI.width())
        pixmap = self.imageItem.get_image_byte(self.ROI, self.canvas)
        self.pixmapItem = self.scene.addPixmap(pixmap)
        self.pixmapItem.setPos(self.canvas.topLeft())
        self.scene.update()
        meg = '{:d}%'.format(int(self.current_ratio * 100))
        self.zoomSignal.emit(meg)
        self.update_rect()

    def move_rect(self, point):
        x_move = self.ROI.x() - point.x()
        y_move = self.ROI.y() - point.y()
        width_move = self.ROI.width()
        height_move = self.ROI.height()
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

    def zoom_rect(self, point, flag):
        x_ratio = point.x() / float(self.canvas.width())
        y_ratio = point.y() / float(self.canvas.height())
        point1 = self.canvasxy2imagexy(point)
        if flag:
            width_zoom = int(self.ROI.width() * (1 - self.zoom_step))
            height_zoom = int(self.ROI.height() * (1 - self.zoom_step))
            x_move = point1.x() - width_zoom * x_ratio
            y_move = point1.y() - height_zoom * y_ratio
        else:
            width_zoom = int(self.ROI.width() * (1 + self.zoom_step))
            height_zoom = int(self.ROI.height() * (1 + self.zoom_step))
            x_move = point1.x() - width_zoom * x_ratio
            y_move = point1.y() - height_zoom * y_ratio
        if x_move + width_zoom <= self.imageItem.xSize and \
                y_move + height_zoom <= self.imageItem.ySize and \
                x_move >= 0 and y_move >= 0:
            self.ROI.setX(x_move)
            self.ROI.setY(y_move)
            self.ROI.setWidth(width_zoom)
            self.ROI.setHeight(height_zoom)
            self.update_image()
        else:
            self.canvas_fit_view()

    def canvasxy2imagexy(self, spoint):
        ipoint = spoint / self.current_ratio + QPointF(self.ROI.topLeft())
        return ipoint

    def mousePressEvent(self, a0: QGraphicsSceneMouseEvent) -> None:
        if self.mode_type == Mode.ZOOM:
            if is_in_rect(a0.pos(), self.uav_window.geometry()):
                self.uav_window.uav_viewer.mousePressEvent(a0)
            else:
                self.setCursor(QCursor(Qt.ClosedHandCursor))
                if self.hasItem and is_in_rect(a0.pos(), self.canvas):
                    pos = a0.pos() - self.canvas.topLeft()
                    if a0.button() == Qt.LeftButton:
                        self.left_click = True
                        self.preMousePos = pos
                    else:
                        self.init_image()
        elif self.mode_type == Mode.EDIT and self.hasTarget and self.is_target_in_ROI():
            self.rectItem.mousePressEvent(a0)
        elif self.mode_type == Mode.WIN:
            pass

    def mouseReleaseEvent(self, a1: QGraphicsSceneMouseEvent) -> None:
        if self.mode_type == Mode.ZOOM:
            if is_in_rect(a1.pos(), self.uav_window.geometry()):
                self.uav_window.uav_viewer.mouseReleaseEvent(a1)
            else:
                self.setCursor(QCursor(Qt.OpenHandCursor))
                if self.hasItem and is_in_rect(a1.pos(), self.canvas):
                    if a1.button() == Qt.LeftButton:
                        self.left_click = False
        elif self.mode_type == Mode.EDIT and self.hasTarget and self.is_target_in_ROI():
            self.rectItem.mouseReleaseEvent(a1)
        elif self.mode_type == Mode.WIN:
            pass

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.mode_type == Mode.ZOOM:
            if is_in_rect(event.pos(), self.uav_window.geometry()):
                self.uav_window.uav_viewer.mouseMoveEvent(event)
            else:
                if self.hasItem and is_in_rect(event.pos(), self.canvas):
                    pos = event.pos() - self.canvas.topLeft()
                    point_img = self.canvasxy2imagexy(pos)
                    point_geo = self.imageItem.imagexy2geo(point_img)
                    coord_lonlat = self.imageItem.geo2lonlat(point_geo)
                    meg1 = '{:d},{:d}'.format(int(point_img.x()), int(point_img.y()))
                    meg2 = '{:.4f},{:.4f}'.format(coord_lonlat[0], coord_lonlat[1])
                    self.mouseMoveSignal.emit(meg1, meg2)
                    if self.left_click:
                        self.MouseMove = (pos - self.preMousePos) / self.current_ratio
                        self.move_rect(self.MouseMove)
                        self.preMousePos = pos
        elif self.mode_type == Mode.EDIT and self.hasTarget and self.is_target_in_ROI():
            self.rectItem.mouseMoveEvent(event)
        elif self.mode_type == Mode.WIN:
            pass

    def wheelEvent(self, event) -> None:
        if self.mode_type == Mode.ZOOM:
            if is_in_rect(event.pos(), self.uav_window.geometry()):
                self.uav_window.uav_viewer.wheelEvent(event)
            else:
                if self.hasItem and is_in_rect(event.pos(), self.canvas):
                    pos = event.pos() - self.canvas.topLeft()
                    if event.angleDelta().y() > 0:
                        if self.full_picture:
                            self.canvas_fit_view()
                            self.fit_view = True
                            self.full_picture = False
                            self.update_image()
                        else:
                            self.zoom_rect(pos, True)
                            self.fit_view = False
                    elif event.angleDelta().y() < 0:
                        if not self.full_picture:
                            self.zoom_rect(pos, False)

    def resizeEvent(self, event: QResizeEvent) -> None:
        print('resize')
        self.scene.setSceneRect(0, 0, self.size().width(), self.size().height())
        self.update_uav_win()
        if self.hasItem:
            self.init_image()

    def is_target_in_ROI(self):
        if self.ROI.topLeft().x() <= self.target.x() <= self.ROI.bottomRight().x():
            if self.ROI.topLeft().y() <= self.target.y() <= self.ROI.bottomRight().y():
                return True
        return False

    def drawRect(self):
        if self.hasTarget and self.is_target_in_ROI():
            w = 100
            h = 100
            rect = QRectF((self.target.x() - self.ROI.x()) * self.current_ratio + self.canvas.x() - w / 2,
                          (self.target.y() - self.ROI.y()) * self.current_ratio + self.canvas.y() - h / 2, w, h)
            self.scene.removeItem(self.rectItem)
            self.rectItem = MyRect(rect)
            self.scene.addItem(self.rectItem)
            self.rectItem.setZValue(1)
            self.scene.update()

    def update_target(self):
        target = self.rectItem.rect().center()
        self.target.setX((target.x()-self.canvas.x()) / self.current_ratio + self.ROI.x())
        self.target.setY((target.y()-self.canvas.y()) / self.current_ratio + self.ROI.y())

    def update_rect(self):
        if self.hasTarget and self.is_target_in_ROI():
            target = QPointF()
            target.setX((self.target.x() - self.ROI.x()) * self.current_ratio + self.canvas.x())
            target.setY((self.target.y() - self.ROI.y()) * self.current_ratio + self.canvas.y())
            move = target - self.rectItem.rect().center()
            rect = self.rectItem.rect()
            rect.setX(self.rectItem.rect().x() + move.x())
            rect.setY(self.rectItem.rect().y() + move.y())
            rect.setWidth(self.rectItem.rect().width())
            rect.setHeight(self.rectItem.rect().height())
            self.rectItem.setRect(rect)
            self.rectItem.update()
            self.rectItem.setVisible(True)
        else:
            self.rectItem.setVisible(False)

    def set_raw_scale(self):
        if self.hasItem and self.mode_type == Mode.ZOOM:
            self.canvas.setX(0)
            self.canvas.setY(0)
            self.canvas.setSize(self.size())
            cen_point = QPointF(self.canvas.width() / 2, self.canvas.height() / 2)
            cen_point_image = self.canvasxy2imagexy(cen_point)
            self.ROI.setX(cen_point_image.x() - self.canvas.width() / 2)
            self.ROI.setY(cen_point_image.y() - self.canvas.height() / 2)
            self.ROI.setWidth(self.canvas.width())
            self.ROI.setHeight(self.canvas.height())
            self.current_ratio = 1.0
            self.update_image()
        elif self.hasItem and self.hasTarget and self.mode_type == Mode.EDIT:
            if self.rectItem.isVisible():
                self.update_target()
            self.canvas.setX(0)
            self.canvas.setY(0)
            self.canvas.setSize(self.size())
            self.ROI.setX(float(self.target.x()) - float(self.canvas.width()) / 2)
            self.ROI.setY(float(self.target.y()) - float(self.canvas.height()) / 2)
            self.ROI.setWidth(self.canvas.width())
            self.ROI.setHeight(self.canvas.height())
            self.fit_ROI()
            print(self.ROI)
            self.update_image()

    def fit_ROI(self):
        if self.ROI.left() < 0:
            self.ROI.moveLeft(0)
        if self.ROI.right() > self.imageItem.xSize:
            self.ROI.moveRight(self.imageItem.xSize)
        if self.ROI.top() < 0:
            self.ROI.moveTop(0)
        if self.ROI.bottom() > self.imageItem.ySize:
            self.ROI.moveBottom(self.imageItem.ySize)

    def change_cursor(self, cursor_num):
        if cursor_num == 1:
            self.setCursor(QCursor(Qt.SizeFDiagCursor))
        elif cursor_num == 2:
            self.setCursor(QCursor(Qt.SizeBDiagCursor))
        elif cursor_num == 3:
            self.setCursor(QCursor(Qt.SizeAllCursor))
        elif cursor_num == 4:
            self.setCursor(QCursor(Qt.PointingHandCursor))
