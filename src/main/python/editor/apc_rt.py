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
    apc_text = ""
    if rt["cont"]:
        apc_text = "{:.1f}\u2193\u2713".format(apc/10.0)
    else:
        apc_text = "{:.1f}\u2193".format(apc/10.0)

    tooltip = "APC/RT setting"
    widget.setText(apc_text)
    widget.setToolTip(tooltip)

    if rt["up"] > 0:
        widget.masked = True 
        if rt["down"] > 0:
            apc_text = "{:.1f}\u2193\n{:.1f}\u2191".format(rt["down"]/10.0, rt["up"]/10.0)
        else:
            apc_text = "{:.1f}\u2191".format(rt["up"]/10.0)

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
        self.keyboardWidget.set_scale(1.2)
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

        apc_rt_layout.addWidget(self.apc_lbl, 0, 0)
        apc_rt_layout.addWidget(self.apc_dpb, 0, 1)
        apc_rt_layout.addWidget(self.apc_sld, 0, 2)

        self.rt_cbx = QCheckBox("Enable RT")
        self.rt_cbx.setTristate(False)
        self.rt_cbx.setCheckState(Qt.Unchecked)
        self.rt_cbx.stateChanged.connect(self.on_rt_check)
        self.rt_lbl = QLabel(tr("RT setting", "Set the rappid trigger:"))
        self.rt_dpb = QDoubleSpinBox()
        self.rt_dpb.setEnabled(False)
        self.rt_dpb.setRange(0.1, 2.5)
        self.rt_dpb.setValue(1.0)
        self.rt_dpb.setSingleStep(0.1)
        self.rt_dpb.valueChanged.connect(self.on_rt_dpb) 
        self.rt_sld= QSlider(Qt.Horizontal)
        self.rt_sld.setEnabled(False)
        self.rt_sld.setMaximumWidth(300)
        self.rt_sld.setMinimumWidth(200)
        self.rt_sld.setRange(1, 25)
        self.rt_sld.setSingleStep(1)
        self.rt_sld.setValue(10)
        self.rt_sld.setTickPosition(QSlider.TicksAbove)
        self.rt_sld.setTracking(False)
        self.rt_sld.valueChanged.connect(self.on_rt_sld) 

        self.rt_cont_cbx = QCheckBox("Enable continuous RT")
        self.rt_cont_cbx.setTristate(False)
        self.rt_cont_cbx.setEnabled(False)
        self.rt_cont_cbx.setCheckState(Qt.Unchecked)
        self.rt_cont_cbx.stateChanged.connect(self.on_rt_cont_check)

        apc_rt_layout.addWidget(self.rt_lbl, 1, 0)
        apc_rt_layout.addWidget(self.rt_dpb, 1, 1)
        apc_rt_layout.addWidget(self.rt_sld, 1, 2)
        apc_rt_layout.addWidget(self.rt_cbx, 1, 3)
        apc_rt_layout.addWidget(self.rt_cont_cbx, 1, 4)

        self.rt_down_cbx = QCheckBox("Enable press RT")
        self.rt_down_cbx.setTristate(False)
        self.rt_down_cbx.setEnabled(False)
        self.rt_down_cbx.setCheckState(Qt.Unchecked)
        self.rt_down_cbx.stateChanged.connect(self.on_rt_down_check)
        self.rt_down_lbl = QLabel(tr("RT press", "Set the rappid trigger press:"))
        self.rt_down_dpb = QDoubleSpinBox()
        self.rt_down_dpb.setEnabled(False)
        self.rt_down_dpb.setRange(0.1, 2.5)
        self.rt_down_dpb.setValue(1.0)
        self.rt_down_dpb.setSingleStep(0.1)
        self.rt_down_dpb.valueChanged.connect(self.on_rt_down_dpb) 
        self.rt_down_sld= QSlider(Qt.Horizontal)
        self.rt_down_sld.setEnabled(False)
        self.rt_down_sld.setMaximumWidth(300)
        self.rt_down_sld.setMinimumWidth(200)
        self.rt_down_sld.setRange(1, 25)
        self.rt_down_sld.setSingleStep(1)
        self.rt_down_sld.setValue(10)
        self.rt_down_sld.setTickPosition(QSlider.TicksAbove)
        self.rt_down_sld.setTracking(False)
        self.rt_down_sld.valueChanged.connect(self.on_rt_down_sld) 
        apc_rt_layout.addWidget(self.rt_down_lbl, 2, 0)
        apc_rt_layout.addWidget(self.rt_down_dpb, 2, 1)
        apc_rt_layout.addWidget(self.rt_down_sld, 2, 2)
        apc_rt_layout.addWidget(self.rt_down_cbx, 2, 3)

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
        
        print("reset apcrt button")
        widget = self.keyboardWidget.active_key
        row = widget.desc.row
        col = widget.desc.col
        apc_rt_display(widget, self.keyboard.amk_apc[(row,col)], self.keyboard.amk_rt[(row,col)])
        self.keyboardWidget.update()

    def activate(self):
        self.reset_keyboard_widget()
        apc = None
        rt = None
        if self.keyboardWidget.active_key is not None:
            row = self.keyboardWidget.active_key.desc.row
            col = self.keyboardWidget.active_key.desc.col

            apc = self.keyboard.amk_apc.get((row, col), 20)
            rt  = self.keyboard.amk_rt.get((row,col), None)

        self.refresh_apc(apc)
        self.refresh_rt(rt)

    def deactivate(self):
        pass
    
    def refresh_apc(self, apc = None):
        self.apc_sld.blockSignals(True)
        self.apc_dpb.blockSignals(True)
        self.rt_sld.blockSignals(True)
        self.rt_dpb.blockSignals(True)

        if apc is None:
            self.apc_sld.setValue(16)
            self.apc_dpb.setValue(1.6)
        else:
            self.apc_sld.setValue(apc)
            self.apc_dpb.setValue(apc/10.0)

        self.rt_dpb.blockSignals(False)
        self.rt_sld.blockSignals(False)
        self.apc_dpb.blockSignals(False)
        self.apc_sld.blockSignals(False)

    def refresh_rt(self, rt = None):
        self.rt_cbx.blockSignals(True)
        self.rt_sld.blockSignals(True)
        self.rt_dpb.blockSignals(True)
        self.rt_cont_cbx.blockSignals(True)
        self.rt_down_cbx.blockSignals(True)
        self.rt_down_sld.blockSignals(True)
        self.rt_down_dpb.blockSignals(True)

        if rt is None:
            self.rt_cbx.setCheckState(Qt.Unchecked)
            self.rt_lbl.setText(tr("RT setting", "Set the rappid trigger:"))
            self.rt_sld.setEnabled(False)
            self.rt_dpb.setEnabled(False)

            self.rt_cont_cbx.setCheckState(Qt.Unchecked)
            self.rt_cont_cbx.setEnabled(False)
            self.rt_down_cbx.setCheckState(Qt.Unchecked)
            self.rt_down_cbx.setEnabled(False)
            self.rt_down_sld.setEnabled(False)
            self.rt_down_dpb.setEnabled(False)
        else:
            if rt["up"] > 0:
                self.rt_sld.setEnabled(True)
                self.rt_dpb.setEnabled(True)
                self.rt_sld.setValue(rt["up"])
                self.rt_dpb.setValue(rt["up"]/10.0)
                self.rt_cbx.setEnabled(True)
                self.rt_cbx.setCheckState(Qt.Checked)
                self.rt_cont_cbx.setEnabled(True)
                if rt["cont"]:
                    self.rt_cont_cbx.setCheckState(Qt.Checked)
                else:
                    self.rt_cont_cbx.setCheckState(Qt.Unchecked)

                if rt["down"] > 0:
                    self.rt_lbl.setText(tr("RT release", "Set the rappid trigger release:"))
                    self.rt_down_cbx.setEnabled(True)
                    self.rt_down_cbx.setCheckState(Qt.Checked)

                    self.rt_down_sld.setEnabled(True)
                    self.rt_down_dpb.setEnabled(True)
                    self.rt_down_sld.setValue(rt["down"])
                    self.rt_down_dpb.setValue(rt["down"]/10.0)
                else:
                    self.rt_lbl.setText(tr("RT setting", "Set the rappid trigger:"))
                    self.rt_down_cbx.setEnabled(False)
                    self.rt_down_sld.setEnabled(False)
                    self.rt_down_dpb.setEnabled(False)

        self.rt_down_dpb.blockSignals(False)
        self.rt_down_sld.blockSignals(False)
        self.rt_down_cbx.blockSignals(False)
        self.rt_cont_cbx.blockSignals(False)
        self.rt_dpb.blockSignals(False)
        self.rt_sld.blockSignals(False)
        self.rt_cbx.blockSignals(False)

    def on_key_clicked(self):
        """ Called when a key on the keyboard widget is clicked """
        if self.keyboardWidget.active_key is None:
            return

        row = self.keyboardWidget.active_key.desc.row
        col = self.keyboardWidget.active_key.desc.col

        apc = self.keyboard.amk_apc.get((row, col), 20)
        self.refresh_apc(apc)

        rt  = self.keyboard.amk_rt.get((row,col), None)
        self.refresh_rt(rt)

        #print("row={},col={},apc={},rt={}".format(row, col, apc, rt))

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

    def get_current_rt(self):
        rt = {}
        rt["cont"] = False
        if self.rt_cont_cbx.isEnabled():
            if self.rt_cont_cbx.isChecked():
                rt["cont"] = True
        rt["up"] = 0
        if self.rt_cbx.isEnabled():
            if self.rt_cbx.isChecked():
                rt["up"] = self.rt_sld.value()

        rt["down"] = 0 
        if self.rt_down_cbx.isEnabled():
            if self.rt_down_cbx.isChecked():
                rt["down"] = self.rt_down_sld.value()

        return rt


    def on_rt_dpb(self):
        self.rt_sld.blockSignals(True)
        self.rt_dpb.blockSignals(True)
        val = int(self.rt_dpb.value()*10)
        self.rt_sld.setValue(val)
        if self.keyboardWidget.active_key is not None:
            row = self.keyboardWidget.active_key.desc.row
            col = self.keyboardWidget.active_key.desc.col
            self.keyboard.apply_rt(row, col, self.get_current_rt())
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
            self.keyboard.apply_rt(row, col, self.get_current_rt())
        self.rt_dpb.blockSignals(False)
        self.rt_sld.blockSignals(False)
        self.reset_active_apcrt()

    def on_rt_down_dpb(self):
        self.rt_down_sld.blockSignals(True)
        self.rt_down_dpb.blockSignals(True)
        val = int(self.rt_down_dpb.value()*10)
        self.rt_down_sld.setValue(val)

        if self.keyboardWidget.active_key is not None:
            row = self.keyboardWidget.active_key.desc.row
            col = self.keyboardWidget.active_key.desc.col
            self.keyboard.apply_rt(row, col, self.get_current_rt())

        self.rt_down_dpb.blockSignals(False)
        self.rt_down_sld.blockSignals(False)
        self.reset_active_apcrt()

    def on_rt_down_sld(self):
        self.rt_down_sld.blockSignals(True)
        self.rt_down_dpb.blockSignals(True)
        val = self.rt_down_sld.value()/10.0
        self.rt_down_dpb.setValue(val)

        if self.keyboardWidget.active_key is not None:
            row = self.keyboardWidget.active_key.desc.row
            col = self.keyboardWidget.active_key.desc.col
            self.keyboard.apply_rt(row, col, self.get_current_rt())

        self.rt_down_dpb.blockSignals(False)
        self.rt_down_sld.blockSignals(False)
        self.reset_active_apcrt()
        
    def on_rt_check(self):
        self.rt_cbx.blockSignals(True)
        self.rt_sld.blockSignals(True)
        self.rt_dpb.blockSignals(True)
        self.rt_cont_cbx.blockSignals(True)
        self.rt_down_cbx.blockSignals(True)
        self.rt_down_sld.blockSignals(True)
        self.rt_down_dpb.blockSignals(True)

        self.rt_cont_cbx.setCheckState(Qt.Unchecked)
        self.rt_down_cbx.setCheckState(Qt.Unchecked)
        self.rt_down_sld.setValue(0)
        self.rt_down_dpb.setValue(0.0)

        if self.rt_cbx.isChecked():
            self.rt_dpb.setEnabled(True)
            self.rt_sld.setEnabled(True)
            self.rt_cont_cbx.setEnabled(True)
            self.rt_down_cbx.setEnabled(True)
            self.rt_down_dpb.setEnabled(True)
            self.rt_down_sld.setEnabled(True)

            self.rt_sld.setValue(1)
            self.rt_dpb.setValue(0.1)
            if self.keyboardWidget.active_key is not None:
                row = self.keyboardWidget.active_key.desc.row
                col = self.keyboardWidget.active_key.desc.col

                self.keyboard.apply_rt(row, col, self.get_current_rt())
        else:
            self.rt_sld.setValue(0)
            self.rt_dpb.setValue(0.0)
            if self.keyboardWidget.active_key is not None:
                row = self.keyboardWidget.active_key.desc.row
                col = self.keyboardWidget.active_key.desc.col
                self.keyboard.apply_rt(row, col, self.get_current_rt())

            self.rt_cont_cbx.setEnabled(False)
            self.rt_down_cbx.setEnabled(False)
            self.rt_down_dpb.setEnabled(False)
            self.rt_down_sld.setEnabled(False)
            self.rt_dpb.setEnabled(False)
            self.rt_sld.setEnabled(False)

        self.rt_down_dpb.blockSignals(False)
        self.rt_down_sld.blockSignals(False)
        self.rt_down_cbx.blockSignals(False)
        self.rt_cont_cbx.blockSignals(False)
        self.rt_dpb.blockSignals(False)
        self.rt_sld.blockSignals(False)
        self.rt_cbx.blockSignals(False)

        self.reset_active_apcrt()

    def on_rt_cont_check(self):
        if self.keyboardWidget.active_key is not None:
            row = self.keyboardWidget.active_key.desc.row
            col = self.keyboardWidget.active_key.desc.col
            self.keyboard.apply_rt(row, col, self.get_current_rt())

        self.reset_active_apcrt()

    def on_rt_down_check(self):
        self.rt_down_sld.blockSignals(True)
        self.rt_down_dpb.blockSignals(True)

        if self.rt_down_cbx.isChecked():
            self.rt_lbl.setText(tr("RT release", "Set the rappid trigger release:"))
            self.rt_down_dpb.setEnabled(True)
            self.rt_down_sld.setEnabled(True)
            self.rt_down_sld.setValue(1)
            self.rt_down_dpb.setValue(0.1)
        else:
            self.rt_lbl.setText(tr("RT setting", "Set the rappid trigger:"))
            self.rt_down_sld.setValue(0)
            self.rt_down_dpb.setValue(0.0)
            self.rt_down_dpb.setEnabled(False)
            self.rt_down_sld.setEnabled(False)

        if self.keyboardWidget.active_key is not None:
            row = self.keyboardWidget.active_key.desc.row
            col = self.keyboardWidget.active_key.desc.col
            self.keyboard.apply_rt(row, col, self.get_current_rt())

        self.rt_down_dpb.blockSignals(False)
        self.rt_down_sld.blockSignals(False)

        self.reset_active_apcrt()