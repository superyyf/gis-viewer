from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem
from PyQt5.QtGui import QColor, QPen


class MyRect(QGraphicsRectItem):
    def __init__(self, *args, **kwargs):
        QGraphicsRectItem.__init__(self, *args, **kwargs)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        pen = QPen(QColor('red'), 5)
        self.setPen(pen)
        self.update()
