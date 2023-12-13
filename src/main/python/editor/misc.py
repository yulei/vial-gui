# SPDX-License-Identifier: GPL-2.0-or-later

from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel, QSlider, QSpinBox, QComboBox, QCheckBox, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt

import os, struct, json

from util import tr

from editor.basic_editor import BasicEditor
from vial_device import VialKeyboard

class Misc(BasicEditor):

    def __init__(self):
        super().__init__()

        g_layout = QGridLayout()

        line = 0

        # import/export setting from/to file
        self.ie_lbl = QLabel(tr("imp exp", "Import or export keyboard config file:"))
        g_layout.addWidget(self.ie_lbl, line, 0)
        self.im_btn = QPushButton("Import ...")
        self.im_btn.clicked.connect(self.on_im_btn)
        g_layout.addWidget(self.im_btn, line, 1)
        self.ex_btn = QPushButton("Export ...")
        self.ex_btn.clicked.connect(self.on_ex_btn)
        g_layout.addWidget(self.ex_btn, line, 2)

        line = line + 1
        # magnetic pole setting
        self.mp_lbl = QLabel(tr("Pole", "Set the magnetic pole of the switch:"))
        g_layout.addWidget(self.mp_lbl, line, 0)
        self.mp_cbb = QComboBox()
        self.mp_cbb.addItem("South")
        self.mp_cbb.addItem("North")
        self.mp_cbb.currentIndexChanged.connect(self.on_mp_cbb)
        g_layout.addWidget(self.mp_cbb, line, 1)

        line = line + 1
        # nkro setting
        self.nk_lbl = QLabel(tr("NKRO", "Set the keyboard's nkro:"))
        g_layout.addWidget(self.nk_lbl, line, 0)
        self.ns_lbl = QLabel(tr("NKRO State", "OFF"))
        g_layout.addWidget(self.ns_lbl, line, 1, alignment=Qt.AlignCenter)
        self.nk_cbx = QCheckBox()
        self.nk_cbx.setTristate(False)
        self.nk_cbx.setEnabled(True)
        self.nk_cbx.stateChanged.connect(self.on_nk_cbx)
        g_layout.addWidget(self.nk_cbx, line, 2)

        line = line + 1
        # polling rate setting
        self.pr_lbl = QLabel(tr("Poll Rate", "Set the keyboard's poll rate:"))
        g_layout.addWidget(self.pr_lbl, line, 0)
        self.pr_cbb = QComboBox()
        self.pr_cbb.addItem("Fullspeed 1K Hz")
        self.pr_cbb.addItem("Highspeed 2K Hz")
        self.pr_cbb.addItem("Highspeed 4K Hz")
        self.pr_cbb.addItem("Highspeed 8K Hz")
        g_layout.addWidget(self.pr_cbb, line, 1)
        self.pr_btn = QPushButton("Apply && Reset")
        self.pr_btn.clicked.connect(self.on_pr_btn)
        g_layout.addWidget(self.pr_btn, line, 2)

        line = line + 1
        # down debounce setting
        self.dd_lbl = QLabel(tr("Down Debounce", "Set the debounce time(ms) when press key:"))
        g_layout.addWidget(self.dd_lbl, line, 0)
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
        g_layout.addWidget(self.dd_sld, line, 1)
        self.dd_sbx = QSpinBox()
        self.dd_sbx.setEnabled(False)
        self.dd_sbx.setRange(0, 10)
        self.dd_sbx.setValue(0)
        self.dd_sbx.setSingleStep(1)
        self.dd_sbx.valueChanged.connect(self.on_dd_sbx)
        g_layout.addWidget(self.dd_sbx, line, 2)

        line = line + 1
        # up debounce setting
        self.ud_lbl = QLabel(tr("Up Debounce", "Set the debounce time(ms) when release key:"))
        g_layout.addWidget(self.ud_lbl, line, 0)
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
        g_layout.addWidget(self.ud_sld, line, 1)
        self.ud_sbx = QSpinBox()
        self.ud_sbx.setEnabled(False)
        self.ud_sbx.setRange(0, 10)
        self.ud_sbx.setValue(0)
        self.ud_sbx.setSingleStep(1)
        self.ud_sbx.valueChanged.connect(self.on_ud_sbx)
        g_layout.addWidget(self.ud_sbx, line, 2)

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
            self.dd_sbx.show()
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
        pass
        #print("hs windows activated")

    def deactivate(self):
        pass
        #print("hs windows deactivated")

    def on_pr_btn(self):
        #print("Apply poll rate cliecked")
        val = self.pr_cbb.currentIndex()
        self.keyboard.apply_poll_rate(val)

    def on_dd_sld(self):
        #print("Down debounce slider changed")
        self.dd_sbx.blockSignals(True)
        val = self.dd_sld.value()
        self.dd_sbx.setValue(val)
        self.dd_sbx.blockSignals(False)

        self.keyboard.apply_debounce(val, True)

    def on_dd_sbx(self):
        #print("Down debounce spinbox changed")
        self.dd_sld.blockSignals(True)
        val = self.dd_sbx.value()
        self.dd_sld.setValue(val)
        self.dd_sld.blockSignals(False)

        self.keyboard.apply_debounce(val, True)

    def on_ud_sld(self):
        #print("Up debounce slider changed")
        self.ud_sbx.blockSignals(True)
        val = self.ud_sld.value()
        self.ud_sbx.setValue(val)
        self.ud_sbx.blockSignals(False)

        self.keyboard.apply_debounce(val, False)

    def on_ud_sbx(self):
        #print("Up debounce spinbox changed")
        self.ud_sld.blockSignals(True)
        val = self.ud_sbx.value()
        self.ud_sld.setValue(val)
        self.ud_sld.blockSignals(False)

        self.keyboard.apply_debounce(val, False)

    def on_nk_cbx(self):
        #print("nkro checkbox changed")
        val = 1 if self.nk_cbx.checkState() == Qt.Checked else 0
        if val != 0:
            self.ns_lbl.setText("ON")
        else:
            self.ns_lbl.setText("OFF")

        self.keyboard.apply_nkro(val)

    def on_mp_cbb(self):
        val = True if self.mp_cbb.currentIndex() != 0 else False
        self.keyboard.apply_pole(1 if val else 0)

    def on_im_btn(self):
        import_file, file_type = QFileDialog.getOpenFileName(None, "Select Config File", os.getcwd(), "Config Files (*.json);;All Files (*)")
        with open(import_file, encoding="utf-8") as fp:
            kbd = json.load(fp)
            if kbd["name"] != self.device.desc["product_string"] or \
                kbd["vendor_id"] != self.device.desc["vendor_id"] or \
                kbd["product_id"] != self.device.desc["product_id"]:
                button = QMessageBox.warning(None, "Loading config",
                                            "The current config({}) was not for this keyboard.".format(kbd["name"]),
                                            buttons=QMessageBox.Ok,
                                            defaultButton=QMessageBox.Ok)
                return
            pole = kbd.get("pole", None)
            if pole is not None:
                self.keyboard.apply_pole(pole)
                print("set pole as {}".format(pole))
            nkro = kbd.get("nkro", None)
            if nkro is not None:
                self.keyboard.apply_nkro(nkro)
            
            keys = kbd.get("keys", None)
            if keys is not None:
                for key in keys:
                    row = key["row"]
                    col = key["col"]
                    apc = key.get("apc", None)
                    if apc is not None:
                        self.keyboard.apply_apc(row, col, apc)

                    rt = key.get("rt", None)
                    if rt is not None:
                        self.keyboard.apply_rt(row, col, rt)

                    dks = key.get("dks", None)
                    if dks is not None:
                        self.keyboard.apply_dks(row, col, dks)

            poll_rate = kbd.get("poll_rate", None)
            if poll_rate is not None:
                self.keyboard.apply_poll_rate(poll_rate)

            self.reset_ui()

    def on_ex_btn(self):
        export_file, file_type = QFileDialog.getSaveFileName(None, "Select Config File", os.getcwd(), "Config Files (*.json);;All Files (*)")
        kbd = {}
        kbd["name"] = self.device.desc["product_string"]
        kbd["vendor_id"] = self.device.desc["vendor_id"]
        kbd["product_id"] = self.device.desc["product_id"]
        kbd["type"] = self.keyboard.keyboard_type
        kbd["speed"] = self.keyboard.keyboard_speed
        kbd["pole"] = self.mp_cbb.currentIndex() 
        kbd["nkro"] = 1 if self.nk_cbx.checkState() == Qt.Checked else 0
        kbd["poll_rate"] = self.pr_cbb.currentIndex()
        kbd["keys"] = []

        for row, col in self.keyboard.rowcol.keys():
            key = {}
            key["row"] = row
            key["col"] = col
            key["apc"] = self.keyboard.amk_apc[(row,col)]
            key["rt"] = self.keyboard.amk_rt[(row,col)]
            key["dks"] = self.keyboard.amk_dks[(row,col)].save()
            kbd["keys"].append(key)
        
        with open(export_file, "w", encoding="utf-8") as fp:
            #json.dump(kbd, fp, indent=4)
            json.dump(kbd, fp)