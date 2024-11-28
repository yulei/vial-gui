# SPDX-License-Identifier: GPL-2.0-or-later
from PyQt5.QtWidgets import QSpinBox, QPushButton, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit, QComboBox
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPainter, QBrush, QPixmap, QFont, QFontDatabase
from PyQt5.QtCore import Qt, QSize, QPoint, QDateTime

import math

from editor.basic_editor import BasicEditor
from util import tr
from vial_device import VialKeyboard

class AuxWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.text = "Hello\nMy-2K"
        self.font_size = 12
        self.font = QFont()
        self.font.setStyleStrategy(QFont.NoAntialias)
        self.font.setPixelSize(self.font_size)
        self.update_pixmap()

    def paintEvent(self, event):
        #super().paintEvent(event)
        qp = QPainter()

        qp.begin(self)
        #qp.drawImage(QPoint(0,0), self.pix.toImage())
        qp.drawImage(QPoint(0,0), self.pix_scaled.toImage())
        qp.end()
    
    def update(self, text):
        self.text = text
        self.update_pixmap()
        self.repaint()
    
    def set_mode(self, mode):
        self.mode = mode
        self.update(self.text)

    def get_mode(self):
        return self.mode

    def set_font(self, family):
        self.font.setFamily(family)
        self.font.setStyleStrategy(QFont.NoAntialias)
        self.font.setPixelSize(self.font_size)
        print("set font", family)
        self.update_pixmap()
        self.repaint()
    
    def get_font(self):
        return self.font.family()

    def set_font_size(self, size):
        self.font_size = size 
        self.font.setPixelSize(self.font_size)
        self.update_pixmap()
        self.repaint()
    
    def get_font_size(self):
        return self.font_size

    def update_pixmap(self):
        self.pix = QPixmap(70, 40)
        qp = QPainter()
        qp.begin(self.pix)
        brush = QBrush()
        brush.setColor(Qt.black)
        brush.setStyle(Qt.SolidPattern)
        qp.setBrush(brush)
        pen = qp.pen()
        
        qp.setFont(self.font)
        pen.setColor(Qt.white)
        qp.setPen(pen)
        qp.fillRect(0,0,70,40,Qt.black)

        lines = self.text.splitlines()
        x = 0
        y_step = self.font_size+1
        y = y_step
        for l in lines:
            qp.drawText(QPoint(x,y), l)
            y = y + y_step
        qp.end()

        self.pix_scaled = self.pix.scaled(140,80,Qt.KeepAspectRatio)
    
    def get_pixmap_data(self):
        img = self.pix.toImage()
        data = []
        print(img.height(), img.width())
        for y in range(img.height()):
            for x in range(img.width()):
                data.append(img.pixelColor(x,y))
        return data

import sys
class AuxDsiplay(BasicEditor):
    def __init__(self, layout_editor, appctx):
        super().__init__()
        self.keyboard = None
        self.device = None
        
        g_layout = QGridLayout()

        line = 0

        if sys.platform != "emscripten":
            self.dt_lbl = QLabel(tr("DATETIME", "时间同步 Synchronize the datetime"))
        else:
            self.dt_lbl = QLabel(tr("DATETIME", "Synchronize the datetime"))

        g_layout.addWidget(self.dt_lbl, line, 0)
        self.dt_btn = QPushButton("Sync")
        self.dt_btn.clicked.connect(self.on_dt_btn)
        g_layout.addWidget(self.dt_btn, line, 1)

        line = line + 1

        if sys.platform != "emscripten":
            lbl = QLabel("My-2K 黑白屏设置 Monochrome Screen Setting")
        else:
            lbl = QLabel("My-2K Monochrome Screen Setting")
        g_layout.addWidget(lbl, line, 0)
        self.ad_btn = QPushButton("Update")
        self.ad_btn.clicked.connect(self.on_sync_clicked)
        g_layout.addWidget(self.ad_btn, line, 1)

        line = line + 1
        if sys.platform != "emscripten":
            lbl = QLabel("文本编辑 Text Editor")
        else:
            lbl = QLabel("Text Editor")
        g_layout.addWidget(lbl, line, 0, Qt.AlignRight)

        h_lyt = QHBoxLayout()
        h_lyt.addStretch(1)
        h_lyt.addWidget(QLabel("Select Font"))
        #QFontDatabase.addApplicationFont(appctx.get_resource("wqy-zenhei.ttc"))

        fontDatabase = QFontDatabase()
        families = fontDatabase.families()
        self.ad_fonts = QComboBox()
        self.ad_fonts.currentIndexChanged.connect(self.on_font_change)
        for family in families:
            self.ad_fonts.addItem(family)
        h_lyt.addWidget(self.ad_fonts)
        h_lyt.addWidget(QLabel("Font Size"))
        self.ad_font_size= QSpinBox()
        self.ad_font_size.valueChanged.connect(self.on_font_size_change)
        self.ad_font_size.setMinimum(8)
        self.ad_font_size.setMaximum(38)
        h_lyt.addWidget(self.ad_font_size)
        h_lyt.addStretch(1)
        g_layout.addLayout(h_lyt, line, 1)

        line = line + 1

        self.ad_text = QPlainTextEdit()
        self.ad_text.setMaximumSize(QSize(200,100))
        self.ad_text.textChanged.connect(self.on_text)
        g_layout.addWidget(self.ad_text, line, 0, Qt.AlignRight)

        self.ad_preview = AuxWidget()
        g_layout.addWidget(self.ad_preview, line, 1)

        h_lyt = QHBoxLayout()
        h_lyt.addStretch(1)
        h_lyt.addLayout(g_layout)
        h_lyt.addStretch(1)

        self.addLayout(h_lyt)

    def rebuild(self, device):
        super().rebuild(device)
        if self.valid():
            self.keyboard = device.keyboard
            self.reset_ui()

    def valid(self):
        return isinstance(self.device, VialKeyboard) and (self.device.keyboard and self.device.keyboard.amk_has_aux_display)

    def reset_ui(self):
        self.ad_font_size.setValue(self.ad_preview.get_font_size())

    def activate(self):
        pass

    def deactivate(self):
        pass

    def on_text(self):
        text = self.ad_text.toPlainText()
        self.ad_preview.update(text)

    def on_mode_check(self):
        pass
        #if self.ad_mode.isChecked():
        #    self.ad_preview.set_mode(1)
        #else:
        #    self.ad_preview.set_mode(0)
    
    def on_sync_clicked(self):
        #pack file header
        from amk.animation import pack_anim_header
        packed = pack_anim_header(70, 40, "ABIT", 1)

        #pack frame durations
        import struct
        packed = packed + struct.pack("<H", 0)

        #pack frame data
        data = self.ad_preview.get_pixmap_data()
        frames = bytearray()
        for i in range(len(data)//8):
            pixel = 0
            for bit in range(8):
                pixel = pixel | (1 << bit if data[i*8+bit].red() > 0 else 0)

            frames.append(pixel)

        packed += frames

        QApplication.setOverrideCursor(Qt.WaitCursor)
        #print("Begin transfer file")
        index = self.keyboard.open_anim_file("BW_TEXT.ABW", False)
        if index != 0xFF:
            #print("Open successfully")
            total = len(packed) 
            remain = total
            cur = 0
            while remain > 0:
                size = 24 if remain > 24 else remain
                if self.keyboard.write_anim_file(index, packed[cur:cur+size], cur):
                    remain = remain - size
                    cur = cur + size
                else:
                    break

            self.keyboard.close_anim_file(index)

        #print("End transfer file")

        QApplication.restoreOverrideCursor()
        QApplication.processEvents()

        self.keyboard.apply_aux_mode(0)

    def on_font_change(self):
        family = self.ad_fonts.currentText()
        if hasattr(self,"ad_preview"):
            self.ad_preview.set_font(family)
    
    def on_font_size_change(self):
        size = self.ad_font_size.value()
        if hasattr(self,"ad_preview"):
            self.ad_preview.set_font_size(size)

    def on_dt_btn(self):
        datetime = QDateTime.currentDateTime()
        year = datetime.date().year()
        month = datetime.date().month()
        day = datetime.date().day()
        weekday = datetime.date().dayOfWeek()
        hour = datetime.time().hour()
        minute = datetime.time().minute()
        second = datetime.time().second()
        self.keyboard.apply_datetime(year, month, day, weekday, hour, minute, second)

        self.keyboard.apply_aux_mode(1)
