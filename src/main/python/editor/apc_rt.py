# SPDX-License-Identifier: GPL-2.0-or-later
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QWidget, QHBoxLayout, QLabel, QSlider, QDoubleSpinBox, QCheckBox
from PyQt5.QtCore import Qt, QTimer

import math

from editor.basic_editor import BasicEditor
from widgets.keyboard_widget import KeyboardWidget
from util import tr, KeycodeDisplay
from vial_device import VialKeyboard


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

        self.apc_lbl = QLabel(tr("APC setting", "Set the actuation point:"))
        self.apc_dpb = QDoubleSpinBox()
        self.apc_dpb.setRange(0.1, 4.0)
        self.apc_dpb.setValue(1.2)
        self.apc_dpb.setSingleStep(0.1)
        self.apc_dpb.valueChanged.connect(self.on_apc_dpb) 
        self.apc_sld = QSlider(Qt.Horizontal)
        self.apc_sld.setMaximumWidth(300)
        self.apc_sld.setMinimumWidth(100)
        self.apc_sld.setRange(1, 40)
        self.apc_sld.setSingleStep(1)
        self.apc_sld.setValue(12)
        self.apc_sld.setTickPosition(QSlider.TicksAbove)
        self.apc_sld.valueChanged.connect(self.on_apc_sld) 
        apc_layout = QHBoxLayout()
        apc_layout.addStretch()

        apc_layout.addWidget(self.apc_lbl)
        apc_layout.addWidget(self.apc_dpb)
        apc_layout.addWidget(self.apc_sld)
        apc_layout.setAlignment(self.apc_lbl, Qt.AlignCenter)
        self.addLayout(apc_layout)

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
        self.rt_sld.setMinimumWidth(100)
        self.rt_sld.setRange(1, 40)
        self.rt_sld.setSingleStep(1)
        self.rt_sld.setValue(12)
        self.rt_sld.setTickPosition(QSlider.TicksAbove)
        self.rt_sld.valueChanged.connect(self.on_rt_sld) 
        rt_layout = QHBoxLayout()
        rt_layout.addStretch()

        rt_layout.addWidget(self.rt_cbx)
        rt_layout.addWidget(self.rt_lbl)
        rt_layout.addWidget(self.rt_dpb)
        rt_layout.addWidget(self.rt_sld)
        rt_layout.setAlignment(self.rt_lbl, Qt.AlignCenter)
        self.addLayout(rt_layout)

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
               (self.device.keyboard or self.device.keyboard.keyboard_type == "ms") and \
               ((self.device.keyboard.cols // 8 + 1) * self.device.keyboard.rows <= 28)

     #def refresh_keycode_display(self):
    def reset_keyboard_widget(self):

        self.keyboardWidget.update_layout()

        for widget in self.keyboardWidget.widgets:
            code = self.keyboard.layout[(0, widget.desc.row, widget.desc.col)]
            KeycodeDisplay.display_keycode(widget, code)
            widget.setOn(False)

        self.keyboardWidget.update()
        self.keyboardWidget.updateGeometry()

#    def reset_keyboard_widget(self):
        # reset keyboard widget
#        for w in self.keyboardWidget.widgets:
#            w.setOn(False)

#        self.keyboardWidget.update_layout()
#        self.keyboardWidget.update()
#        self.keyboardWidget.updateGeometry()

    def activate(self):
        print("apc/rt windows activated")

    def deactivate(self):
        print("apc/rt windows deactivated")

    def on_key_clicked(self):
        """ Called when a key on the keyboard widget is clicked """
        if self.keyboardWidget.active_key is None:
            return

        row = self.keyboardWidget.active_key.desc.row
        col = self.keyboardWidget.active_key.desc.col

        apc = self.keyboard.amk_apc.get((row, col), 20)
        rt  = self.keyboard.amk_rt.get((row,col), 0)

        self.apc_sld.setValue(apc)
        self.apc_dpb.setValue(apc/10.0)

        if rt > 0:
            self.rt_cbx.setCheckState(Qt.Checked)
            self.rt_sld.setValue(rt)
            self.rt_dpb.setValue(rt/10.0)
        else:
            self.rt_cbx.setCheckState(Qt.Unchecked)
            self.rt_sld.setEnabled(False)
            self.rt_dpb.setEnabled(False)

        print("row={},col={},apc={},rt={}".format(row, col, apc, rt))


    def on_rt_check(self):
        if self.rt_cbx.isChecked():
            self.rt_dpb.setEnabled(True)
            self.rt_sld.setEnabled(True)
        else:
            self.rt_dpb.setEnabled(False)
            self.rt_sld.setEnabled(False)
    
    def on_apc_dpb(self):
        val = int(self.apc_dpb.value()*10)
        self.apc_sld.setValue(val)
        if self.keyboardWidget.active_key is not None:
            self.keyboard.amk_apc[(self.keyboardWidget.active_key.desc.row,
                                    self.keyboardWidget.active_key.desc.col)] = val

    def on_apc_sld(self):
        val = self.apc_sld.value()/10.0
        self.apc_dpb.setValue(val)
        if self.keyboardWidget.active_key is not None:
            self.keyboard.amk_apc[(self.keyboardWidget.active_key.desc.row,
                                    self.keyboardWidget.active_key.desc.col)] = self.apc_sld.value()

    def on_rt_dpb(self):
        val = int(self.rt_dpb.value()*10)
        self.rt_sld.setValue(val)
        if self.keyboardWidget.active_key is not None:
            self.keyboard.amk_rt[(self.keyboardWidget.active_key.desc.row,
                                    self.keyboardWidget.active_key.desc.col)] = val


    def on_rt_sld(self):
        val = self.rt_sld.value()/10.0
        self.rt_dpb.setValue(val)
        if self.keyboardWidget.active_key is not None:
            self.keyboard.amk_rt[(self.keyboardWidget.active_key.desc.row,
                                    self.keyboardWidget.active_key.desc.col)] = self.rt_sld.value()
