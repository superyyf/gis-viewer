from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QFileDialog, QGraphicsSceneMouseEvent
from PyQt5.QtGui import QCursor, QResizeEvent, QPixmap
from PyQt5.QtCore import Qt, QPoint
import os


class MyUavViewer(QGraphicsView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setCursor(QCursor(Qt.OpenHandCursor))
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.hasImg = False
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.scene.setSceneRect(0, 0, self.size().width(), self.size().height())
        self.fileName = ""
        self.zoom_max = 10
        self.zoom_min = 0.01
        self.zoom_step = 0.1
        self.position = QPoint(0, 0)
        self.ratio = 1.0
        self.left_click = False
        print("uav view", self.size())

    def read_image(self, fname):
        self.fileName = fname
        self.init_image()

    def init_image(self):
        if self.hasImg:
            self.scene.clear()
        else:
            self.hasImg = True
        pixmap = QPixmap(self.fileName)
        self.image_width = pixmap.width()
        self.image_height = pixmap.height()
        self.fit_to_view()
        self.pixmapItem = self.scene.addPixmap(pixmap)
        self.pixmapItem.setScale(self.ratio)
        self.pixmapItem.setPos(self.position)
        self.scene.update()

    def fit_to_view(self):
        image_shape_ratio = float(self.image_width) / float(self.image_height)
        view_shape_ratio = float(self.size().width()) / float(self.size().height())
        if image_shape_ratio > view_shape_ratio:
            self.position.setX(0)
            self.position.setY((float(self.size().height()) - self.size().width() / image_shape_ratio) / 2)
            self.ratio = float(self.size().width()) / self.image_width
        else:
            self.position.setX(float(self.size().width() - self.size().height() * image_shape_ratio) / 2)
            self.position.setY(0)
            self.ratio = float(self.size().height()) / self.image_height

    def mousePressEvent(self, a0: QGraphicsSceneMouseEvent) -> None:
        self.setCursor(QCursor(Qt.ClosedHandCursor))
        if self.hasImg:
            if a0.button() == Qt.LeftButton:
                self.left_click = True
                self.preMousePostion = a0.pos()
            else:
                self.scene.clear()
                self.init_image()

    def mouseReleaseEvent(self, a1: QGraphicsSceneMouseEvent) -> None:
        self.setCursor(QCursor(Qt.OpenHandCursor))
        if self.hasImg:
            if a1.button() == Qt.LeftButton:
                self.left_click = False

    def mouseMoveEvent(self, a2: QGraphicsSceneMouseEvent) -> None:
        if self.hasImg:
            if self.left_click:
                self.MouseMove = a2.pos() - self.preMousePostion
                self.preMousePostion = a2.pos()
                self.position = self.pixmapItem.pos() + self.MouseMove
                self.pixmapItem.setPos(self.position)
                self.scene.update()

    def wheelEvent(self, event) -> None:
        pos = event.pos() - self.parent().geometry().topLeft()
        print(pos, self.parent().geometry().topLeft())
        if self.hasImg:
            if event.angleDelta().y() > 0 and self.ratio * (1 + self.zoom_step) <= self.zoom_max:
                self.ratio *= 1 + self.zoom_step
                self.pixmapItem.setScale(self.ratio)
                self.position.setX((1 + self.zoom_step) * self.position.x() - self.zoom_step * pos.x())
                self.position.setY((1 + self.zoom_step) * self.position.y() - self.zoom_step * pos.y())
                self.pixmapItem.setPos(self.position)
                self.scene.update()
            elif event.angleDelta().y() < 0 and self.ratio * (1 - self.zoom_step) >= self.zoom_min:
                self.ratio *= 1 - self.zoom_step
                self.pixmapItem.setScale(self.ratio)
                self.position.setX(self.zoom_step * pos.x() + (1 - self.zoom_step) * self.position.x())
                self.position.setY(self.zoom_step * pos.y() + (1 - self.zoom_step) * self.position.y())
                self.pixmapItem.setPos(self.position)
                self.scene.update()

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.scene.setSceneRect(0, 0, self.size().width(), self.size().height())
        if self.hasImg:
            self.init_image()
