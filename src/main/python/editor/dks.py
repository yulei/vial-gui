# SPDX-License-Identifier: GPL-2.0-or-later
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QWidget, QHBoxLayout, QGridLayout, QLabel, QSlider, QDoubleSpinBox, QCheckBox
from PyQt5.QtCore import QSize, Qt


import math, struct

from editor.basic_editor import BasicEditor
from widgets.keyboard_widget import KeyboardWidget
from util import tr, KeycodeDisplay
from vial_device import VialKeyboard
from keycodes.keycodes import Keycode
from tabbed_keycodes import TabbedKeycodes, keycode_filter_masked
from protocol.amk import AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_OK, AMK_PROTOCOL_GET_VERSION
from protocol.amk import AMK_PROTOCOL_GET_DKS, AMK_PROTOCOL_SET_DKS

class DksButton(QPushButton):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.scale = 3
        self.label = None
        self.word_wrap = False
        self.text = ""
        self.index = 0

    def set_index(self, index):
        self.index = index
    
    def get_index(self):
        return self.index

    def setRelSize(self, ratio):
        self.scale = ratio
        self.updateGeometry()

    def setWordWrap(self, state):
        self.word_wrap = state
        self.setText(self.text)

    def sizeHint(self):
        size = int(round(self.fontMetrics().height() * self.scale))
        return QSize(size, size)

    # Override setText to facilitate automatic word wrapping
    def setText(self, text):
        self.text = text
        if self.word_wrap:
            super().setText("")
            if self.label is None:
                self.label = QLabel(text, self)
                self.label.setWordWrap(True)
                self.label.setAlignment(Qt.AlignCenter)
                layout = QHBoxLayout(self)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(self.label,0,Qt.AlignCenter)
            else:
                self.label.setText(text)
        else:
            if self.label is not None:
                self.label.deleteLater()
            super().setText(text)

class DksCheckBox(QCheckBox):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.index = 0

    def set_index(self, index):
        self.index = index
    
    def get_index(self):
        return self.index

DKS_TRIGGER_LABELS = [tr("DKS A", "Set the first trigger event:"), tr("DKS B", "Set the second trigger event:"), 
                tr("DKS C", "Set the third trigger event:"), tr("DKS D", "Set the fourth trigger event:")]

DKS_KEY_EVENT_LABELS = [tr("Down Event", "Key down"), tr("Up Event", "Key up")]

class Dks(BasicEditor):

    def __init__(self, layout_editor):
        super().__init__()

        self.layout_editor = layout_editor
        self.active_dks_btn = None
        self.active_dks = None
        self.dks_btns = []
        self.dks_ckbs = []

        g_layout = QGridLayout()
        index = 0
        for x in range(4):
            btn = DksButton()
            btn.set_index(index)
            btn.setCheckable(True)
            btn.clicked.connect(self.on_dks_btn_clicked)
            index = index + 1
            self.dks_btns.append(btn)
            g_layout.addWidget(btn, 0, 2+x)
            g_layout.setAlignment(btn, Qt.AlignCenter)

        index = 0

        for line in range(4):
            lbl = QLabel(DKS_TRIGGER_LABELS[line])
            g_layout.addWidget(lbl, 2*line + 1, 0)

            for sub in range(2):
                lbl = QLabel(DKS_KEY_EVENT_LABELS[sub])
                g_layout.addWidget(lbl, 2*line+sub+1, 1)
                for x in range(4):
                    ckb = DksCheckBox()
                    ckb.set_index(index)
                    ckb.setTristate(False)
                    ckb.stateChanged.connect(self.on_dks_checked)
                    index = index + 1
                    self.dks_ckbs.append(ckb)
                    g_layout.addWidget(ckb, 2*line+sub+1, 2+x)
                    g_layout.setAlignment(ckb, Qt.AlignCenter)

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self.on_apply_clicked)
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.on_reset_clicked)

        h_layout = QHBoxLayout()
        h_layout.addWidget(self.apply_btn)
        h_layout.setAlignment(self.apply_btn, Qt.AlignRight)
        h_layout.addWidget(self.reset_btn)
        h_layout.setAlignment(self.reset_btn, Qt.AlignRight)

        v_layout = QVBoxLayout()
        v_layout.addLayout(g_layout)
        v_layout.addLayout(h_layout)
        v_layout.setAlignment(h_layout, Qt.AlignRight)

        dks_layout = QHBoxLayout()
        dks_layout.addStretch(1)
        dks_layout.addLayout(v_layout)

        self.keyboardWidget = KeyboardWidget(layout_editor)
        self.keyboardWidget.set_enabled(True)
        self.keyboardWidget.clicked.connect(self.on_key_clicked)
        k_layout = QVBoxLayout()
        k_layout.addStretch(1)
        k_layout.addWidget(self.keyboardWidget)
        k_layout.setAlignment(self.keyboardWidget, Qt.AlignVCenter)
        k_layout.addStretch(1)

        dks_layout.addStretch(1)
        dks_layout.addLayout(k_layout)
        dks_layout.addStretch(1)

        self.tabbed_keycodes = TabbedKeycodes()
        self.tabbed_keycodes.keycode_changed.connect(self.on_keycode_changed)
        #self.tabbed_keycodes.anykey.connect(self.on_any_keycode)

        self.addLayout(dks_layout)
        self.addWidget(self.tabbed_keycodes)

        self.keyboard = None
        self.device = None

    def rebuild(self, device):
        super().rebuild(device)
        if self.valid():
            self.keyboard = device.keyboard
            self.keyboardWidget.set_keys(self.keyboard.keys, self.keyboard.encoders)
        self.keyboardWidget.setEnabled(self.valid())
        self.reset_keyboard_widget()

    def valid(self):
        # Check if vial protocol is v3 or later
        return isinstance(self.device, VialKeyboard) and \
               (self.device.keyboard and self.device.keyboard.keyboard_type == "ms") and \
               ((self.device.keyboard.cols // 8 + 1) * self.device.keyboard.rows <= 28)

    def reset_keyboard_widget(self):

        self.keyboardWidget.update_layout()

        for widget in self.keyboardWidget.widgets:
            code = self.keyboard.layout[(0, widget.desc.row, widget.desc.col)]
            KeycodeDisplay.display_keycode(widget, code)
            widget.setOn(False)

        self.keyboardWidget.update()
        self.keyboardWidget.updateGeometry()

    def activate(self):
        print("apc/rt windows activated")

    def deactivate(self):
        print("apc/rt windows deactivated")

    def refresh_dks(self, dks):
        dks.dump()
        # set buttons
        for i in range(4):
            kc = Keycode.find_by_qmk_id(dks.get_key(i))
            self.dks_btns[i].setText(kc.label)

        for i in range(4):
            # 4 trigger point
            for j in range(2):
                # up and down
                for k in range(4):
                    # 4 keys
                    ckb = self.dks_ckbs[i*8+j*4+k]
                    if dks.is_event_on(i, k, j==0):
                        ckb.setChecked(True)
                    else:
                        ckb.setChecked(False)

    def on_key_clicked(self):
        """ Called when a key on the keyboard widget is clicked """
        if self.keyboardWidget.active_key is None:
            return

        row = self.keyboardWidget.active_key.desc.row
        col = self.keyboardWidget.active_key.desc.col
        dks = self.active_dks
        if dks is not None:
            print("Dump before switch")
            dks.dump()
        self.active_dks = self.keyboard.amk_dks[(row, col)]
        self.refresh_dks(self.active_dks)
        print("Select dks at:{},{}".format(row, col))

    def on_dks_btn_clicked(self):
        print(self.sender().get_index())
        if self.active_dks_btn is not None:
            if self.active_dks_btn.isChecked():
                self.active_dks_btn.toggle()

        self.active_dks_btn = self.sender()
        if not self.active_dks_btn.isChecked():
            self.active_dks_btn.toggle()
    
    def on_keycode_changed(self, code):
        if self.active_dks_btn is not None:
            print("have active dks button")
            kc = Keycode.find_by_qmk_id(code)
            self.active_dks_btn.setText(kc.label)
            index = self.active_dks_btn.get_index()
            if self.active_dks is not None:
                self.active_dks.add_key(index, code)
                if self.active_dks.is_dirty():
                    self.apply_btn.setEnabled(True)

    def on_apply_clicked(self):
        if self.active_dks is None:
            return

        row = self.keyboardWidget.active_key.desc.row
        col = self.keyboardWidget.active_key.desc.col

        dks = self.active_dks.pack_dks()
        data = struct.pack("BBBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_SET_DKS, row, col)
        data = data + dks
        data = self.keyboard.usb_send(self.device.dev, data, retries=20)
        print("SetDkS: result={}", data[2])
        self.active_dks.set_dirty(False)
        self.apply_btn.setEnabled(False)

    def on_reset_clicked(self):
        if self.active_dks is not None:
            self.active_dks.clear()
            self.apply_btn.setEnabled(True)

    def on_dks_checked(self):
        ckb = self.sender()
        index = ckb.get_index()
        print("DKS checkbox index({}) state changed to {}".format(index, ckb.isChecked()))
        if self.active_dks is None:
            return

        event = index % 4
        key = index // 8

        down = True if (index % 8) < 4 else False
        if ckb.isChecked():
            print("Add event at {}, key {}, down {}".format(event, key, down))
            self.active_dks.add_event(event, key, down)
        else:
            self.active_dks.del_event(event, key, down)
        
        if self.active_dks.is_dirty():
            self.apply_btn.setEnabled(True)