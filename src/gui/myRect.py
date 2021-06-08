from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsScene
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtCore import QRectF, QPoint, Qt, QPointF, pyqtSignal, QObject
from enum import Enum


def is_in_rect(point: QPointF, rect: QRectF):
    if rect.topLeft().x() <= point.x() <= rect.bottomRight().x() and rect.topLeft().y() <= point.y() <= rect.bottomRight().y():
        return True
    else:
        return False


class MovePoint(Enum):
    TopLeft = 1
    TopRight = 2
    BottomLeft = 3
    BottomRight = 4
    Middle = 5
    NoMean = 6


class MyRect(QGraphicsRectItem, QObject):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        self.pen = QPen(QColor('red'), 5)
        self.setPen(self.pen)
        self.top_left_rect = QRectF()
        self.top_right_rect = QRectF()
        self.bottom_left_rect = QRectF()
        self.bottom_right_rect = QRectF()
        self.middle_rect = QRectF()

        self.move_point = MovePoint.NoMean
        self.left_click = False
        self.preMousePos = QPointF()
        self.MouseMove = QPointF()

    def prepare_to_edit(self):
        self.pen = QPen(QColor('green'), 5)
        self.setPen(self.pen)
        self.update()
        self.get_rect()

    def prepare_to_zoom(self):
        self.pen = QPen(QColor('red'), 5)
        self.setPen(self.pen)
        self.update()

    def get_rect(self):
        self.top_left_rect.setRect(self.rect().left() - self.rect().width()/4, self.rect().top() - self.rect().height()/4, self.rect().width()/2, self.rect().height()/2)
        self.top_right_rect.setRect(self.rect().right() - self.rect().width()/4, self.rect().top() - self.rect().height()/4, self.rect().width()/2, self.rect().height()/2)
        self.bottom_left_rect.setRect(self.rect().left() - self.rect().width()/4, self.rect().bottom() - self.rect().height()/4, self.rect().width()/2, self.rect().height()/2)
        self.bottom_right_rect.setRect(self.rect().right() - self.rect().width()/4, self.rect().bottom() - self.rect().height()/4, self.rect().width()/2, self.rect().height()/2)
        self.middle_rect.setRect(self.rect().left() + self.rect().width()/4, self.rect().top() + self.rect().height()/4, self.rect().width()/2, self.rect().height()/2)

    def resize_rect(self):
        current_rect = self.rect()
        if self.move_point == MovePoint.TopLeft:
            current_rect.setTopLeft(current_rect.topLeft() + self.MouseMove)
            self.setRect(current_rect)
        elif self.move_point == MovePoint.TopRight:
            current_rect.setTopRight(current_rect.topRight() + self.MouseMove)
            self.setRect(current_rect)
        elif self.move_point == MovePoint.BottomLeft:
            current_rect.setBottomLeft(current_rect.bottomLeft() + self.MouseMove)
            self.setRect(current_rect)
        elif self.move_point == MovePoint.BottomRight:
            current_rect.setBottomRight(current_rect.bottomRight() + self.MouseMove)
            self.setRect(current_rect)
        elif self.move_point == MovePoint.Middle:
            current_rect.moveTo(current_rect.topLeft() + self.MouseMove)
            self.setRect(current_rect)
        self.update()
        self.get_rect()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.left_click = True
            self.preMousePos = event.pos()
            if is_in_rect(event.pos(), self.top_left_rect):
                self.move_point = MovePoint.TopLeft
            elif is_in_rect(event.pos(), self.top_right_rect):
                self.move_point = MovePoint.TopRight
            elif is_in_rect(event.pos(), self.bottom_left_rect):
                self.move_point = MovePoint.BottomLeft
            elif is_in_rect(event.pos(), self.bottom_right_rect):
                self.move_point = MovePoint.BottomRight
            elif is_in_rect(event.pos(), self.middle_rect):
                self.move_point = MovePoint.Middle
            else:
                self.move_point = MovePoint.NoMean

    def mouseReleaseEvent(self, event) -> None:
        self.left_click = False

    def mouseMoveEvent(self, event) -> None:
        if is_in_rect(event.pos(), self.top_left_rect):
            self.scene().changeCursorSignal.emit(1)
        elif is_in_rect(event.pos(), self.top_right_rect):
            self.scene().changeCursorSignal.emit(2)
        elif is_in_rect(event.pos(), self.bottom_left_rect):
            self.scene().changeCursorSignal.emit(2)
        elif is_in_rect(event.pos(), self.bottom_right_rect):
            self.scene().changeCursorSignal.emit(1)
        elif is_in_rect(event.pos(), self.middle_rect):
            self.scene().changeCursorSignal.emit(3)
        else:
            self.scene().changeCursorSignal.emit(4)
        if self.left_click:
            self.MouseMove = event.pos() - self.preMousePos
            self.preMousePos = event.pos()
            self.resize_rect()

