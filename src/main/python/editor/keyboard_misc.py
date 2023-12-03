# SPDX-License-Identifier: GPL-2.0-or-later

from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel, QSlider, QSpinBox, QComboBox, QCheckBox
from PyQt5.QtCore import Qt

import struct

from util import tr

from editor.basic_editor import BasicEditor
from vial_device import VialKeyboard
from protocol.amk import AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_OK, AMK_PROTOCOL_GET_VERSION
from protocol.amk import AMK_PROTOCOL_SET_NKRO, AMK_PROTOCOL_SET_POLL_RATE, AMK_PROTOCOL_SET_DOWN_DEBOUNCE, AMK_PROTOCOL_SET_UP_DEBOUNCE

class KeyboardMisc(BasicEditor):

    def __init__(self):
        super().__init__()

        g_layout = QGridLayout()

        # nkro setting
        self.nk_lbl = QLabel(tr("NKRO", "Set the keyboard's nkro:"))
        g_layout.addWidget(self.nk_lbl, 0, 0)
        self.ns_lbl = QLabel(tr("NKRO State", "OFF"))
        g_layout.addWidget(self.ns_lbl, 0, 1, alignment=Qt.AlignCenter)
        self.nk_cbx = QCheckBox()
        self.nk_cbx.setTristate(False)
        self.nk_cbx.setEnabled(True)
        self.nk_cbx.stateChanged.connect(self.on_nk_cbx)
        g_layout.addWidget(self.nk_cbx, 0, 2)

        # polling rate setting
        self.pr_lbl = QLabel(tr("Poll Rate", "Set the keyboard's poll rate:"))
        g_layout.addWidget(self.pr_lbl, 1, 0)
        self.pr_cbb = QComboBox()
        self.pr_cbb.addItem("Fullspeed 1K Hz")
        self.pr_cbb.addItem("Highspeed 2K Hz")
        self.pr_cbb.addItem("Highspeed 4K Hz")
        self.pr_cbb.addItem("Highspeed 8K Hz")
        g_layout.addWidget(self.pr_cbb, 1, 1)
        self.pr_btn = QPushButton("Apply && Reset")
        self.pr_btn.clicked.connect(self.on_pr_btn)
        g_layout.addWidget(self.pr_btn, 1, 2)

        # down debounce setting
        self.dd_lbl = QLabel(tr("Down Debounce", "Set the debounce time(ms) when press key:"))
        g_layout.addWidget(self.dd_lbl, 2, 0)
        self.dd_sld= QSlider(Qt.Horizontal)
        self.dd_sld.setEnabled(False)
        self.dd_sld.setMaximumWidth(300)
        self.dd_sld.setMinimumWidth(200)
        self.dd_sld.setRange(0, 10)
        self.dd_sld.setSingleStep(1)
        self.dd_sld.setValue(0)
        self.dd_sld.setTickPosition(QSlider.TicksAbove)
        self.dd_sld.setTracking(False)
        self.dd_sld.valueChanged.connect(self.on_dd_sld)
        g_layout.addWidget(self.dd_sld, 2, 1)
        self.dd_sbx = QSpinBox()
        self.dd_sbx.setEnabled(False)
        self.dd_sbx.setRange(0, 10)
        self.dd_sbx.setValue(0)
        self.dd_sbx.setSingleStep(1)
        self.dd_sbx.valueChanged.connect(self.on_dd_sbx)
        g_layout.addWidget(self.dd_sbx, 2, 2)

        # up debounce setting
        self.ud_lbl = QLabel(tr("Up Debounce", "Set the debounce time(ms) when release key:"))
        g_layout.addWidget(self.ud_lbl, 3, 0)
        self.ud_sld= QSlider(Qt.Horizontal)
        self.ud_sld.setEnabled(False)
        self.ud_sld.setMaximumWidth(300)
        self.ud_sld.setMinimumWidth(200)
        self.ud_sld.setRange(0, 10)
        self.ud_sld.setSingleStep(1)
        self.ud_sld.setValue(0)
        self.ud_sld.setTickPosition(QSlider.TicksAbove)
        self.ud_sld.setTracking(False)
        self.ud_sld.valueChanged.connect(self.on_ud_sld)
        g_layout.addWidget(self.ud_sld, 3, 1)
        self.ud_sbx = QSpinBox()
        self.ud_sbx.setEnabled(False)
        self.ud_sbx.setRange(0, 10)
        self.ud_sbx.setValue(0)
        self.ud_sbx.setSingleStep(1)
        self.ud_sbx.valueChanged.connect(self.on_ud_sbx)
        g_layout.addWidget(self.ud_sbx, 3, 2)

        v_layout = QVBoxLayout()
        v_layout.addStretch(1)
        v_layout.addLayout(g_layout)
        v_layout.addStretch(1)
        h_layout = QHBoxLayout()
        h_layout.addStretch(1)
        h_layout.addLayout(v_layout)
        h_layout.addStretch(1)
        self.addLayout(h_layout)

        self.keyboard = None
        self.device = None

    def rebuild(self, device):
        super().rebuild(device)
        if self.valid():
            self.keyboard = device.keyboard
            self.reset_ui()


    def valid(self):
        # Check if vial protocol is v3 or later
        return isinstance(self.device, VialKeyboard) and \
               (self.device.keyboard and self.device.keyboard.keyboard_speed == "hs") and \
               ((self.device.keyboard.cols // 8 + 1) * self.device.keyboard.rows <= 28)

    def reset_ui(self):
        self.nk_cbx.blockSignals(True)
        self.nk_cbx.setCheckState(self.keyboard.amk_nkro)
        self.ns_lbl.setText("ON" if self.keyboard.amk_nkro else "OFF")
        self.nk_cbx.blockSignals(False)

        self.pr_cbb.blockSignals(True)
        self.pr_cbb.setCurrentIndex(self.keyboard.amk_poll_rate)
        self.pr_cbb.blockSignals(False)

        if self.keyboard.keyboard_type == "ms":
            self.dd_lbl.hide()
            self.dd_sld.hide()
            self.dd_sbx.hide()
            self.ud_lbl.hide()
            self.ud_sld.hide()
            self.ud_sbx.hide()
        else:
            self.dd_lbl.show()
            self.dd_sld.show()
            self.ud_lbl.show()
            self.ud_sld.show()
            self.ud_sbx.show()


        if self.keyboard.keyboard_type == "mx":
            self.dd_sld.blockSignals(True)
            self.dd_sbx.blockSignals(True)
            self.dd_sld.setValue(self.keyboard.amk_down_debounce)
            self.dd_sbx.setValue(self.keyboard.amk_down_debounce)
            self.dd_sbx.blockSignals(False)
            self.dd_sld.blockSignals(False)
            self.dd_sbx.setEnabled(True)
            self.dd_sld.setEnabled(True)
        
            self.ud_sld.blockSignals(True)
            self.ud_sbx.blockSignals(True)
            self.ud_sld.setValue(self.keyboard.amk_up_debounce)
            self.ud_sbx.setValue(self.keyboard.amk_up_debounce)
            self.ud_sbx.blockSignals(False)
            self.ud_sld.blockSignals(False)
            self.ud_sbx.setEnabled(True)
            self.ud_sld.setEnabled(True)

    def activate(self):
        print("hs windows activated")

    def deactivate(self):
        print("hs windows deactivated")

    def apply_poll_rate(self, val):
        data = self.keyboard.usb_send(self.device.dev, struct.pack("BBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_SET_POLL_RATE, val), retries=20)
        print("Set poll rate({}): return={}".format(val, data[2]))

    def apply_debounce(self, val, down):
        cmd = AMK_PROTOCOL_SET_DOWN_DEBOUNCE if down else AMK_PROTOCOL_SET_UP_DEBOUNCE
        data = self.keyboard.usb_send(self.device.dev, struct.pack("BBB", AMK_PROTOCOL_PREFIX, cmd, val), retries=20)
        print("Set {} debounce: return={}".format( "Down" if down else "Up", data[2]))
    
    def apply_nkro(self, val):
        data = self.keyboard.usb_send(self.device.dev, struct.pack("BBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_SET_NKRO, val), retries=20)
        print("Set NKRO({}): return={}".format(val, data[2]))

    def on_pr_btn(self):
        print("Apply poll rate cliecked")
        val = self.pr_cbb.currentIndex()
        self.apply_poll_rate(val)

    def on_dd_sld(self):
        print("Down debounce slider changed")
        self.dd_sbx.blockSignals(True)
        val = self.dd_sld.value()
        self.dd_sbx.setValue(val)
        self.dd_sbx.blockSignals(False)

        self.apply_debounce(val, True)

    def on_dd_sbx(self):
        print("Down debounce spinbox changed")
        self.dd_sld.blockSignals(True)
        val = self.dd_sbx.value()
        self.dd_sld.setValue(val)
        self.dd_sld.blockSignals(False)

        self.apply_debounce(val, True)

    def on_ud_sld(self):
        print("Up debounce slider changed")
        self.ud_sbx.blockSignals(True)
        val = self.ud_sld.value()
        self.ud_sbx.setValue(val)
        self.ud_sbx.blockSignals(False)

        self.apply_debounce(val, False)

    def on_ud_sbx(self):
        print("Up debounce spinbox changed")
        self.ud_sld.blockSignals(True)
        val = self.ud_sbx.value()
        self.ud_sld.setValue(val)
        self.ud_sld.blockSignals(False)

        self.apply_debounce(val, False)

    def on_nk_cbx(self):
        print("nkro checkbox changed")
        val = 1 if self.nk_cbx.checkState() == Qt.Checked else 0
        if val != 0:
            self.ns_lbl.setText("ON")
        else:
            self.ns_lbl.setText("OFF")

        self.apply_nkro(val)