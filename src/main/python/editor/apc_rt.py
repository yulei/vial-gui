# SPDX-License-Identifier: GPL-2.0-or-later
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QWidget, QHBoxLayout, QLabel, QSlider, QDoubleSpinBox, QCheckBox, QGridLayout
from PyQt5.QtCore import QSize, Qt, QCoreApplication
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QApplication

import math, struct

from editor.basic_editor import BasicEditor
from widgets.keyboard_widget import KeyboardWidget
from util import tr, KeycodeDisplay
from vial_device import VialKeyboard

def apc_rt_display(widget, apc, rt):
    apc_text = "{:.2f}\u2193".format(apc/10.0)
    tooltip = "APC/RT setting"

    widget.setText(apc_text)
    widget.setToolTip(tooltip)

    if rt > 0:
        widget.masked = True 
        apc_text = "{:.2f}\u2191".format(rt/10.0)
        widget.setMaskText(apc_text)
        widget.setMaskColor(QApplication.palette().color(QPalette.Link))
    else:
        widget.masked = False

class ApcRt(BasicEditor):

    def __init__(self, layout_editor):
        super().__init__()

        self.layout_editor = layout_editor

        self.keyboardWidget = KeyboardWidget(layout_editor)
        self.keyboardWidget.set_enabled(True)
        self.keyboardWidget.clicked.connect(self.on_key_clicked)

        layout = QVBoxLayout()
        layout.addWidget(self.keyboardWidget)
        layout.setAlignment(self.keyboardWidget, Qt.AlignCenter)

        self.addLayout(layout)

        apc_rt_layout = QGridLayout()

        self.apc_lbl = QLabel(tr("APC setting", "Set the actuation point:"))
        self.apc_dpb = QDoubleSpinBox()
        self.apc_dpb.setRange(0.1, 4.0)
        self.apc_dpb.setValue(1.2)
        self.apc_dpb.setSingleStep(0.1)
        self.apc_dpb.valueChanged.connect(self.on_apc_dpb) 
        self.apc_sld = QSlider(Qt.Horizontal)
        self.apc_sld.setMaximumWidth(300)
        self.apc_sld.setMinimumWidth(200)
        self.apc_sld.setRange(1, 40)
        self.apc_sld.setSingleStep(1)
        self.apc_sld.setValue(12)
        self.apc_sld.setTickPosition(QSlider.TicksAbove)
        self.apc_sld.setTracking(False)
        self.apc_sld.valueChanged.connect(self.on_apc_sld) 

        apc_rt_layout.addWidget(self.apc_lbl, 0, 1)
        apc_rt_layout.addWidget(self.apc_dpb, 0, 2)
        apc_rt_layout.addWidget(self.apc_sld, 0, 3)

        self.rt_cbx = QCheckBox("RT")
        self.rt_cbx.setTristate(False)
        self.rt_cbx.setCheckState(Qt.Unchecked)
        self.rt_cbx.stateChanged.connect(self.on_rt_check)
        self.rt_lbl = QLabel(tr("RT setting", "Set the rappid trigger:"))
        self.rt_dpb = QDoubleSpinBox()
        self.rt_dpb.setEnabled(False)
        self.rt_dpb.setRange(0.1, 4.0)
        self.rt_dpb.setValue(1.2)
        self.rt_dpb.setSingleStep(0.1)
        self.rt_dpb.valueChanged.connect(self.on_rt_dpb) 
        self.rt_sld= QSlider(Qt.Horizontal)
        self.rt_sld.setEnabled(False)
        self.rt_sld.setMaximumWidth(300)
        self.rt_sld.setMinimumWidth(200)
        self.rt_sld.setRange(1, 40)
        self.rt_sld.setSingleStep(1)
        self.rt_sld.setValue(12)
        self.rt_sld.setTickPosition(QSlider.TicksAbove)
        self.rt_sld.setTracking(False)
        self.rt_sld.valueChanged.connect(self.on_rt_sld) 
        apc_rt_layout.addWidget(self.rt_cbx, 1, 0)
        apc_rt_layout.addWidget(self.rt_lbl, 1, 1)
        apc_rt_layout.addWidget(self.rt_dpb, 1, 2)
        apc_rt_layout.addWidget(self.rt_sld, 1, 3)

        layout = QHBoxLayout()
        layout.addStretch(1)
        layout.addLayout(apc_rt_layout)
        layout.addStretch(1)
        self.addLayout(layout)

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
            #KeycodeDisplay.display_keycode(widget, code)
            apc_rt_display(widget, self.keyboard.amk_apc[(widget.desc.row, widget.desc.col)],
                        self.keyboard.amk_rt[(widget.desc.row, widget.desc.col)])

            widget.setOn(False)

        self.keyboardWidget.update()
        self.keyboardWidget.updateGeometry()

    def reset_active_apcrt(self):
        if self.keyboardWidget.active_key is None:
            return
        
        widget = self.keyboardWidget.active_key
        row = widget.desc.row
        col = widget.desc.col
        apc_rt_display(widget, self.keyboard.amk_apc[(row,col)], self.keyboard.amk_rt[(row,col)])
        self.keyboardWidget.update()

    def activate(self):
        self.reset_keyboard_widget()

    def deactivate(self):
        pass

    def on_key_clicked(self):
        """ Called when a key on the keyboard widget is clicked """
        if self.keyboardWidget.active_key is None:
            return

        row = self.keyboardWidget.active_key.desc.row
        col = self.keyboardWidget.active_key.desc.col

        apc = self.keyboard.amk_apc.get((row, col), 20)
        rt  = self.keyboard.amk_rt.get((row,col), 0)

        self.apc_sld.blockSignals(True)
        self.apc_dpb.blockSignals(True)
        self.rt_cbx.blockSignals(True)
        self.rt_sld.blockSignals(True)
        self.rt_dpb.blockSignals(True)

        self.apc_sld.setValue(apc)
        self.apc_dpb.setValue(apc/10.0)

        if rt > 0:
            self.rt_cbx.setCheckState(Qt.Checked)
            self.rt_sld.setEnabled(True)
            self.rt_dpb.setEnabled(True)
            self.rt_sld.setValue(rt)
            self.rt_dpb.setValue(rt/10.0)
        else:
            self.rt_cbx.setCheckState(Qt.Unchecked)
            self.rt_sld.setEnabled(False)
            self.rt_dpb.setEnabled(False)

        self.rt_dpb.blockSignals(False)
        self.rt_sld.blockSignals(False)
        self.rt_cbx.blockSignals(False)
        self.apc_dpb.blockSignals(False)
        self.apc_sld.blockSignals(False)

        #print("row={},col={},apc={},rt={}".format(row, col, apc, rt))

    def on_rt_check(self):
        self.rt_cbx.blockSignals(True)
        self.rt_sld.blockSignals(True)
        self.rt_dpb.blockSignals(True)
        if self.rt_cbx.isChecked():
            self.rt_dpb.setEnabled(True)
            self.rt_sld.setEnabled(True)
            if self.keyboardWidget.active_key is not None:
                row = self.keyboardWidget.active_key.desc.row
                col = self.keyboardWidget.active_key.desc.col
                rt = self.keyboard.amk_rt.get((row, col), 0)
                if rt == 0:
                    #self.keyboard.amk_rt[(row,col)] = 1
                    self.keyboard.apply_rt(row, col, 1)
                    self.rt_sld.setValue(rt)
                    self.rt_dpb.setValue(rt/10.0)
        else:
            if self.keyboardWidget.active_key is not None:
                row = self.keyboardWidget.active_key.desc.row
                col = self.keyboardWidget.active_key.desc.col
                rt = self.keyboard.amk_rt.get((row, col), 0)
                if rt > 0:
                    #self.keyboard.amk_rt[(row,col)] = 0
                    self.keyboard.apply_rt(row, col, 0)
                    #self.rt_sld.setValue(rt)
                    #self.rt_dpb.setValue(rt/10.0)
            self.rt_dpb.setEnabled(False)
            self.rt_sld.setEnabled(False)
        self.rt_dpb.blockSignals(False)
        self.rt_sld.blockSignals(False)
        self.rt_cbx.blockSignals(False)
        self.reset_active_apcrt()

    def on_apc_dpb(self):
        self.apc_sld.blockSignals(True)
        self.apc_dpb.blockSignals(True)
        val = int(self.apc_dpb.value()*10)
        self.apc_sld.setValue(val)
        if self.keyboardWidget.active_key is not None:
            row = self.keyboardWidget.active_key.desc.row
            col = self.keyboardWidget.active_key.desc.col
            #self.keyboard.amk_apc[(row, col)] = val
            self.keyboard.apply_apc(row, col, val)
        self.apc_dpb.blockSignals(False)
        self.apc_sld.blockSignals(False)
        self.reset_active_apcrt()
            

    def on_apc_sld(self):
        self.apc_sld.blockSignals(True)
        self.apc_dpb.blockSignals(True)
        val = self.apc_sld.value()/10.0
        self.apc_dpb.setValue(val)
        if self.keyboardWidget.active_key is not None:
            row = self.keyboardWidget.active_key.desc.row
            col = self.keyboardWidget.active_key.desc.col
            #self.keyboard.amk_apc[(row, col)] = self.apc_sld.value()
            self.keyboard.apply_apc(row, col, self.apc_sld.value())
        self.apc_dpb.blockSignals(False)
        self.apc_sld.blockSignals(False)
        self.reset_active_apcrt()

    def on_rt_dpb(self):
        self.rt_sld.blockSignals(True)
        self.rt_dpb.blockSignals(True)
        val = int(self.rt_dpb.value()*10)
        self.rt_sld.setValue(val)
        if self.keyboardWidget.active_key is not None:
            row = self.keyboardWidget.active_key.desc.row
            col = self.keyboardWidget.active_key.desc.col
            #self.keyboard.amk_rt[(row, col)] = val
            self.keyboard.apply_rt(row, col, val)
        self.rt_dpb.blockSignals(False)
        self.rt_sld.blockSignals(False)
        self.reset_active_apcrt()

    def on_rt_sld(self):
        self.rt_sld.blockSignals(True)
        self.rt_dpb.blockSignals(True)
        val = self.rt_sld.value()/10.0
        self.rt_dpb.setValue(val)
        if self.keyboardWidget.active_key is not None:
            row = self.keyboardWidget.active_key.desc.row
            col = self.keyboardWidget.active_key.desc.col
            #self.keyboard.amk_rt[(row, col)] = self.rt_sld.value()
            self.keyboard.apply_rt(row, col, self.rt_sld.value())
        self.rt_dpb.blockSignals(False)
        self.rt_sld.blockSignals(False)
        self.reset_active_apcrt()

