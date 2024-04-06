
from PyQt5.QtGui import QPainter, QPalette
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QRect, QRectF, pyqtSignal

from widgets.keyboard_widget import KeyboardWidget

class ClickableWidget(QWidget):

    clicked = pyqtSignal()

    def mousePressEvent(self, evt):
        super().mousePressEvent(evt)
        self.clicked.emit()

class AmkWidget(KeyboardWidget):
    def __init__(self, layout_editor):
        super().__init__(layout_editor)
        self.mouse_clicked = False
        self.active_keys = {}

    def mousePressEvent(self, ev):
        if not self.enabled:
            return
        self.active_keys = {}
        self.start_pos = ev.pos()
        self.current_pos = self.start_pos
        self.mouse_clicked = True
        key, masked = self.hit_test(ev.pos())
        if key is not None:
            row = key.desc.row
            col = key.desc.col
            self.active_keys[(row, col)] = key
            self.clicked.emit()
        else:
            self.deselected.emit()

        self.update()

    def mouseMoveEvent(self, ev):
        if not self.enabled:
            return
        if self.mouse_clicked:
            self.current_pos = ev.pos()
            if self.update_select_keys():
                self.clicked.emit()
            else:
                self.deselected.emit()
            self.update()

    def mouseReleaseEvent(self, ev):
        if not self.enabled:
            return
        self.mouse_clicked = False 
        self.update()

    def update_select_keys(self):
        self.active_keys = {}
        rect = QRectF(self.start_pos, self.current_pos)
        for key in self.widgets:
            row = key.desc.row
            col = key.desc.col
            #if rect.intersects(key.rect):
            if rect.intersects(key.polygon.boundingRect()):
                self.active_keys[(row,col)] = key
        return bool(self.active_keys)

    def draw_rect(self, begin, end):
        qp = QPainter()
        qp.begin(self)


        drag_pen = qp.pen()
        drag_pen.setColor(QApplication.palette().color(QPalette.Link).darker(80))
        drag_pen.setStyle(Qt.DashDotLine)
        qp.setPen(drag_pen)

        rect = QRect(begin, end) 
        qp.drawRect(rect)

        qp.end()
    
    def draw_active_keys(self, keys):
        qp = QPainter()
        qp.begin(self)
        active_pen = qp.pen()
        active_pen.setColor(QApplication.palette().color(QPalette.Highlight))
        active_pen.setWidthF(1.5)

        for idx, key in keys.items():
            qp.save()
            qp.scale(self.scale, self.scale)
            qp.translate(key.shift_x, key.shift_y)
            qp.translate(key.rotation_x, key.rotation_y)
            qp.rotate(key.rotation_angle)
            qp.translate(-key.rotation_x, -key.rotation_y)
            qp.drawPath(key.background_draw_path)
            qp.restore()

        qp.end()
    
    def paintEvent(self, event):
        super().paintEvent(event)

        if self.mouse_clicked:
            self.draw_rect(self.start_pos, self.current_pos)
        
        self.draw_active_keys(self.active_keys)
    
    def clear_active_keys(self):
        self.active_keys = {} 
        self.mouse_clicked = False