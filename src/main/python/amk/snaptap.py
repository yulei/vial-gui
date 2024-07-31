# SPDX-License-Identifier: GPL-2.0-or-later
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QRadioButton, QButtonGroup, QMessageBox 
from PyQt5.QtCore import Qt, QSize, QRect

from PyQt5.QtGui import QPalette, QPainter, QBrush 
from PyQt5.QtWidgets import QApplication

from editor.basic_editor import BasicEditor
from widgets.keyboard_widget import KeyboardWidget
from amk.widget import ClickableWidget
from widgets.square_button import SquareButton
from util import tr
from vial_device import VialKeyboard

SNAP_TAP_MODE = ["NONE", "Depth", "Trigger", "First", "Second", "Both"]

def snaptap_display(widget, left, mode, valid=True, used=False):
    if valid == False:
        if used == True:
            widget.setText("\u2205")
        else:
            widget.setText("")
        widget.setMaskText("")
        widget.masked = False
        return

    snaptap_text = ""

    if left:
        snaptap_text = "First"
    else:
        snaptap_text = "Second"

    tooltip = "Snaptap setting"
    widget.setText(snaptap_text)
    widget.setToolTip(tooltip)

    if mode != 0:
        widget.masked = True 
        widget.setMaskText(SNAP_TAP_MODE[mode])
        widget.setMaskColor(QApplication.palette().color(QPalette.Link))
    else:
        widget.setMaskText("")
        widget.masked = False

class SnaptapButton(QPushButton):
    def __init__(self, row, col, left, parent=None):
        super().__init__(parent)
        self.scale = 3
        self.text = ""
        self.left = left
        self.set_pos(row, col)

    def setRelSize(self, ratio):
        self.scale = ratio
        self.updateGeometry()

    def get_pos(self):
        return (self.row, self.col)

    def set_pos(self, row, col):
        self.row = row 
        self.col = col
        if row < 0 or col < 0:
            self.text = ""
        else:
            if self.left:
                self.text = "\u21DC"
            else:
                self.text = "\u21DD"

            #self.text = "({}:{})".format(self.row, self.col)

        self.update()

    def sizeHint(self):
        size = int(round(self.fontMetrics().height() * self.scale))
        return QSize(size, size)

    def mousePressEvent(self, ev):
        if not self.isEnabled():
            return
        
        self.toggle()
        self.clicked.emit()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing)

        background_brush = QBrush()
        background_brush.setColor(QApplication.palette().color(QPalette.Button))
        background_brush.setStyle(Qt.SolidPattern)

        active_pen = qp.pen()
        active_pen.setColor(QApplication.palette().color(QPalette.Highlight))
        active_pen.setWidthF(6)

        regular_pen = qp.pen()
        regular_pen.setColor(QApplication.palette().color(QPalette.Button))

        regular_brush = QBrush()
        regular_brush.setColor(QApplication.palette().color(QPalette.Button))
        regular_brush.setStyle(Qt.SolidPattern)

        # for text 
        text_pen = qp.pen()
        text_pen.setColor(QApplication.palette().color(QPalette.ButtonText))

        rect = self.rect()
        if self.isEnabled():
            if self.isChecked():
                qp.setPen(active_pen)
            else:
                qp.setPen(regular_pen)
            qp.setBrush(background_brush)
        else:
            qp.setPen(regular_pen)
            qp.setBrush(regular_brush)

        qp.drawRect(rect)

        qp.setPen(text_pen)
        qp.drawText(rect, Qt.AlignCenter, self.text)

        qp.end()

class Snaptap(BasicEditor):

    def __init__(self, layout_editor):
        super().__init__()

        h_layout = QHBoxLayout()
        snaptap_lbl = QLabel(tr("Snaptap", "Snaptap list: "))
        h_layout.addWidget(snaptap_lbl)
        self.snaptap_btns = []
        for x in range(8):
            btn = SquareButton(str(x))
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setRelSize(1.667)
            btn.setCheckable(True)
            btn.hide()
            h_layout.addWidget(btn)
            btn.clicked.connect(lambda state, idx=x: self.switch_snaptap(idx))
            self.snaptap_btns.append(btn)
        h_layout.addStretch(1)

        v_layout = QVBoxLayout()
        v_layout.addLayout(h_layout)
        v_layout.addStretch(1)
        h_layout = QHBoxLayout()
        h_layout.addStretch(1)
        self.first_btn = SnaptapButton(-1,-1, True)
        self.first_btn.setCheckable(True)
        self.first_btn.clicked.connect(self.on_snaptap_btn_clicked)
        h_layout.addWidget(self.first_btn)
        self.second_btn = SnaptapButton(-1,-1, False)
        self.second_btn.setCheckable(True)
        self.second_btn.clicked.connect(self.on_snaptap_btn_clicked)
        h_layout.addWidget(self.second_btn)
        h_layout.addStretch(1)
        v_layout.addLayout(h_layout)

        self.mode_group = QButtonGroup()
        self.depth_radio = QRadioButton("Depth: Activated most pressed key")
        self.depth_radio.setEnabled(False)
        self.mode_group.addButton(self.depth_radio, 1)
        v_layout.addWidget(self.depth_radio)
        v_layout.setAlignment(self.depth_radio, Qt.AlignLeft)

        self.trigger_radio = QRadioButton("Trigger: Activated last pressed key")
        self.mode_group.addButton(self.trigger_radio, 2)
        v_layout.addWidget(self.trigger_radio)
        v_layout.setAlignment(self.trigger_radio, Qt.AlignLeft)

        self.first_radio = QRadioButton("First: First key activated first")
        self.mode_group.addButton(self.first_radio, 3)
        v_layout.addWidget(self.first_radio)
        v_layout.setAlignment(self.first_radio, Qt.AlignLeft)

        self.second_radio = QRadioButton("Second: Second key activated first")
        self.mode_group.addButton(self.second_radio, 4)
        v_layout.addWidget(self.second_radio)
        v_layout.setAlignment(self.second_radio, Qt.AlignLeft)

        self.both_radio = QRadioButton("Both: Released all if both pressed")
        self.mode_group.addButton(self.both_radio, 5)
        v_layout.addWidget(self.both_radio)
        v_layout.setAlignment(self.both_radio, Qt.AlignLeft)

        self.mode_group.buttonClicked.connect(self.on_mode_clicked)
        v_layout.addStretch(1)

        h_layout = QHBoxLayout()
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setEnabled(True)
        self.clear_btn.clicked.connect(self.on_clear_clicked)
        h_layout.addWidget(self.clear_btn)
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self.on_apply_clicked)
        h_layout.addWidget(self.apply_btn)
        v_layout.addLayout(h_layout)
        v_layout.addStretch(2)

        self.layout_editor = layout_editor
        self.keyboardWidget = KeyboardWidget(layout_editor)
        self.keyboardWidget.set_enabled(True)
        #self.keyboardWidget.set_scale(1.2)
        self.keyboardWidget.clicked.connect(self.on_key_clicked)

        layout = QHBoxLayout()
        layout.addWidget(self.keyboardWidget)
        layout.setAlignment(self.keyboardWidget, Qt.AlignCenter)
        layout.addStretch(1)
        w = ClickableWidget()
        w.setLayout(layout)
        w.clicked.connect(self.on_empty_space_clicked)

        layout = QHBoxLayout()
        layout.addLayout(v_layout)
        layout.addStretch(1)
        layout.addWidget(w)
        self.addLayout(layout)
        layout.addStretch(1)

        self.keyboard = None
        self.device = None
        self.active_snaptap_btn = None
        self.current_first_row = -1
        self.current_first_col = -1
        self.current_second_row = -1
        self.current_second_col = -1
        self.current_mode = 0
        self.dirty = False
        self.used_keys = []

    def rebuild(self, device):
        super().rebuild(device)
        if self.valid():
            self.keyboard = device.keyboard
            self.keyboardWidget.set_keys(self.keyboard.keys, self.keyboard.encoders)
            self.keyboardWidget.setEnabled(self.valid())

            key = self.keyboard.amk_snaptap_keys[self.keyboard.amk_snaptap_index]
            self.current_mode = key.get_mode()
            if self.current_mode == 0:
                self.current_first_row = -1
                self.current_first_col = -1
                self.current_second_row = -1
                self.current_second_col = -1
            else:
                self.current_first_row = key.get_first_row() 
                self.current_first_col = key.get_first_col() 
                self.current_second_row = key.get_second_row() 
                self.current_second_col = key.get_second_col() 

            self.update_used_keys()
            self.reset_ui()

    def valid(self):
        return isinstance(self.device, VialKeyboard) and \
               (self.device.keyboard and (self.device.keyboard.keyboard_type.startswith("ms") or self.device.keyboard.keyboard_type == "ec")) and \
               (self.device.keyboard.amk_snaptap == True )

    def reset_ui(self):
        self.reset_keyboard_widget()
        self.reset_snaptap()
        self.reset_snaptap_key()

    def reset_keyboard_widget(self):
        if self.valid():
            self.keyboardWidget.update_layout()
            for widget in self.keyboardWidget.widgets:
                if self.is_used_key(widget.desc.row, widget.desc.col):
                    snaptap_display(widget, False, 0, False, True)
                else:
                    snaptap_display(widget, False, 0, False)
                widget.setOn(False)

            self.keyboardWidget.update()
            self.keyboardWidget.updateGeometry()

    def reset_snaptap(self):
        for btn in self.snaptap_btns:
            btn.hide()

        for i in range(self.keyboard.amk_snaptap_count):
            self.snaptap_btns[i].show()
            self.snaptap_btns[i].setChecked(False)

        self.snaptap_btns[self.keyboard.amk_snaptap_index].setChecked(True)

        self.first_btn.set_pos(self.current_first_row, self.current_first_col)
        self.second_btn.set_pos(self.current_second_row, self.current_second_col)

        self.mode_group.setExclusive(False)
        for btn in self.mode_group.buttons():
            btn.setChecked(False)

        if self.current_mode > 0:
            btn = self.mode_group.button(self.current_mode)
            btn.setChecked(True)
        self.mode_group.setExclusive(True)

    def reset_snaptap_key(self):
        widget = self.get_widget(self.current_first_row, self.current_first_col)
        if widget is not None:
            snaptap_display(widget, True, self.current_mode)

        widget = self.get_widget(self.current_second_row, self.current_second_col)
        if widget is not None:
            snaptap_display(widget, False, self.current_mode)
    
    def update_used_keys(self):
        self.used_keys = []
        for key in self.keyboard.amk_snaptap_keys:
            if key.get_mode() != 0 and key.get_index() != self.keyboard.amk_snaptap_index:
                self.used_keys.append((key.get_first_row(), key.get_first_col()))
                self.used_keys.append((key.get_second_row(), key.get_second_col()))
    
    def is_used_key(self, row, col):
        for pos in self.used_keys:
            if pos[0] == row and pos[1] == col:
                return True
        
        return False

    def activate(self):
        if self.valid():
            self.reset_ui()

    def deactivate(self):
        pass
    
    def on_empty_space_clicked(self):
        self.keyboardWidget.active_key = None
        self.keyboardWidget.update()

    def on_key_clicked(self):
        """ Called when a key on the keyboard widget is clicked """
        if not self.keyboardWidget.active_key:
            return

        if not self.active_snaptap_btn:
            return

        widget = self.keyboardWidget.active_key

        if self.is_used_key(widget.desc.row, widget.desc.col):
            return

        self.active_snaptap_btn.set_pos(widget.desc.row, widget.desc.col)

        if self.active_snaptap_btn == self.first_btn:
            if self.current_first_row != widget.desc.row:
                self.current_first_row = widget.desc.row
                self.dirty = True
            if self.current_first_col != widget.desc.col:
                self.current_first_col = widget.desc.col
                self.dirty = True
        else:
            if self.current_second_row != widget.desc.row:
                self.current_second_row = widget.desc.row
                self.dirty = True
            if self.current_second_col != widget.desc.col:
                self.current_second_col = widget.desc.col
                self.dirty = True

        self.reset_keyboard_widget()
        self.reset_snaptap_key()
        if self.dirty:
            self.apply_btn.setEnabled(True)

    def switch_snaptap(self, idx):
        if self.dirty:
            button = QMessageBox.warning(None, "Snap Tap",
                                        "The current snap tap setting was modified, do you want to save ?",
                                        buttons=QMessageBox.Save | QMessageBox.Discard,
                                        defaultButton=QMessageBox.Save)
            if button == QMessageBox.Save:
                self.on_apply_clicked()

        self.keyboard.amk_snaptap_index = idx

        for i in range(self.keyboard.amk_snaptap_count):
            self.snaptap_btns[i].setChecked(False)

        self.snaptap_btns[self.keyboard.amk_snaptap_index].setChecked(True)

        key = self.keyboard.amk_snaptap_keys[self.keyboard.amk_snaptap_index]
        self.current_mode = key.get_mode()
        print("current mode", self.current_mode)
        if self.current_mode == 0:
            self.current_first_row = -1
            self.current_first_col = -1
            self.current_second_row = -1
            self.current_second_col = -1
        else:
            self.current_first_row = key.get_first_row() 
            self.current_first_col = key.get_first_col() 
            self.current_second_row = key.get_second_row() 
            self.current_second_col = key.get_second_col() 

        self.update_used_keys()
        self.reset_ui()
    
    def on_snaptap_btn_clicked(self):
        if self.active_snaptap_btn is not None:
            if self.active_snaptap_btn.isChecked():
                self.active_snaptap_btn.toggle()

        self.active_snaptap_btn = self.sender()
        if not self.active_snaptap_btn.isChecked():
            self.active_snaptap_btn.toggle()

    def get_widget(self, row, col):
        if row < 0 or col < 0:
            return None

        for widget in self.keyboardWidget.widgets:
            if widget.desc.row == row and widget.desc.col == col:
                #print("Get Widget row={}, col={}".format(row, col))
                return widget
        return None
    
    def on_mode_clicked(self, btn):
        old_mode = self.current_mode
        if btn == self.depth_radio:
            if btn.isChecked():
                self.current_mode = 1
        if btn == self.trigger_radio:
            if btn.isChecked():
                self.current_mode = 2
        if btn == self.first_radio:
            if btn.isChecked():
                self.current_mode = 3
        if btn == self.second_radio:
            if btn.isChecked():
                self.current_mode = 4
        if btn == self.both_radio:
            if btn.isChecked():
                self.current_mode = 5

        if old_mode == self.current_mode:
            return
        
        self.dirty = True
        self.apply_btn.setEnabled(True)

        self.reset_keyboard_widget()
        self.reset_snaptap_key()
         
    def on_clear_clicked(self):
        if self.current_mode != 0:
            self.current_mode = 0
            self.dirty = True

        if self.current_first_row != -1:
            self.current_first_row = -1
            self.dirty = True

        if self.current_first_col != -1:
            self.current_first_col = -1
            self.dirty = True

        if self.current_second_row != -1:
            self.current_second_row = -1
            self.dirty = True

        if self.current_second_col != -1:
            self.current_second_col = -1
            self.dirty = True

        self.reset_ui()
        if self.dirty:
            self.apply_btn.setEnabled(True)

    def on_apply_clicked(self):
        if self.current_mode == 0:
            key = {"first_row": 0,
                    "first_col": 0,
                    "second_row": 0,
                    "second_col": 0,
                    "mode":0}
            self.keyboard.apply_snaptap(self.keyboard.amk_snaptap_index, key)
            self.dirty = False
            self.apply_btn.setEnabled(False)
        else:
            if self.current_first_row < 0 or \
                self.current_first_col < 0 or \
                self.current_second_row < 0 or \
                self.current_second_col < 0:
                QMessageBox.information(None, "", "Not a valid snaptap")
            else:
                key = {"first_row":self.current_first_row,
                        "first_col":self.current_first_col,
                        "second_row":self.current_second_row,
                        "second_col":self.current_second_col,
                        "mode":self.current_mode}
                self.keyboard.apply_snaptap(self.keyboard.amk_snaptap_index, key)
                self.dirty = False
                self.apply_btn.setEnabled(False)

    def save_or_discard(self, dks):
        button = QMessageBox.warning(None, "Snap Tap",
                                    "The current snap tap setting was modified, do you want to save ?",
                                    buttons=QMessageBox.Save | QMessageBox.Discard,
                                    defaultButton=QMessageBox.Save)
        if button == QMessageBox.Save:
            self.on_apply_clicked()
