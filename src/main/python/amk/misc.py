# SPDX-License-Identifier: GPL-2.0-or-later

from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel, QSlider, QSpinBox, QComboBox, QCheckBox, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt

import os, json

from util import tr

from editor.basic_editor import BasicEditor
from vial_device import VialKeyboard

class Misc(BasicEditor):

    def __init__(self):
        super().__init__()

        g_layout = QGridLayout()

        line = 0

        # import/export setting from/to file
        self.ie_lbl = QLabel(tr("Misc", "Import or export keyboard config file:/磁轴配置操作"))
        g_layout.addWidget(self.ie_lbl, line, 0)
        self.im_btn = QPushButton(tr("Misc", "Import/导入 ..."))
        self.im_btn.clicked.connect(self.on_im_btn)
        g_layout.addWidget(self.im_btn, line, 1)
        self.ex_btn = QPushButton(tr("Misc", "Export/导出 ..."))
        self.ex_btn.clicked.connect(self.on_ex_btn)
        g_layout.addWidget(self.ex_btn, line, 2)

        line = line + 1
        # magnetic pole setting
        self.mp_lbl = QLabel(tr("Misc", "Set the magnetic pole of the switch:/设置磁轴极性"))
        g_layout.addWidget(self.mp_lbl, line, 0)
        self.mp_cbb = QComboBox()
        self.mp_cbb.addItem(tr("Misc", "South/南极"))
        self.mp_cbb.addItem(tr("misc", "North/北极"))
        self.mp_cbb.currentIndexChanged.connect(self.on_mp_cbb)
        g_layout.addWidget(self.mp_cbb, line, 1)

        line = line + 1
        # apcrt profile setting
        self.apcrt_lbl = QLabel(tr("Misc", "Set keyboard's APCRT profile/设置当前APCRT的配置:"))
        g_layout.addWidget(self.apcrt_lbl, line, 0)
        self.apcrt_cbb = QComboBox()
        self.apcrt_cbb.currentIndexChanged.connect(self.on_apcrt_cbb)
        g_layout.addWidget(self.apcrt_cbb, line, 1)

        line = line + 1
        # dks state setting
        self.dks_status_lbl = QLabel(tr("Misc", "Set keyboard's DKS status/切换DKS状态:"))
        g_layout.addWidget(self.dks_status_lbl, line, 0)
        self.dks_lbl = QLabel(tr("Misc", "ON/激活"))
        g_layout.addWidget(self.dks_lbl, line, 1, alignment=Qt.AlignCenter)
        self.dks_cbx = QCheckBox()
        self.dks_cbx.setTristate(False)
        self.dks_cbx.setEnabled(True)
        self.dks_cbx.stateChanged.connect(self.on_dks_cbx)
        g_layout.addWidget(self.dks_cbx, line, 2)

        line = line + 1

        # nkro setting
        self.nk_lbl = QLabel(tr("Misc", "Set the keyboard's nkro/设置全键无冲:"))
        g_layout.addWidget(self.nk_lbl, line, 0)
        self.ns_lbl = QLabel(tr("Misc", "OFF/关闭"))
        g_layout.addWidget(self.ns_lbl, line, 1, alignment=Qt.AlignCenter)
        self.nk_cbx = QCheckBox()
        self.nk_cbx.setTristate(False)
        self.nk_cbx.setEnabled(True)
        self.nk_cbx.stateChanged.connect(self.on_nk_cbx)
        g_layout.addWidget(self.nk_cbx, line, 2)

        line = line + 1
        # polling rate setting
        self.pr_lbl = QLabel(tr("Misc", "Set the keyboard's poll rate/键盘回报率:"))
        g_layout.addWidget(self.pr_lbl, line, 0)
        self.pr_cbb = QComboBox()
        self.pr_cbb.addItem(tr("Misc", "Fullspeed/全速 1K Hz"))
        self.pr_cbb.addItem(tr("Misc", "Highspeed/高速 2K Hz"))
        self.pr_cbb.addItem(tr("Misc", "Highspeed/高速 4K Hz"))
        self.pr_cbb.addItem(tr("Misc", "Highspeed/高速 8K Hz"))
        g_layout.addWidget(self.pr_cbb, line, 1)
        self.pr_btn = QPushButton(tr("Misc", "Apply && Reset/应用并重启键盘"))
        self.pr_btn.clicked.connect(self.on_pr_btn)
        g_layout.addWidget(self.pr_btn, line, 2)

        line = line + 1
        # switch type setting
        self.st_lbl = QLabel(tr("Misc", "Set the current switch/设置当前轴体:"))
        g_layout.addWidget(self.st_lbl, line, 0)
        self.st_cbb = QComboBox()
        self.st_cbb.addItem(tr("Misc", "Common Switch/其它"))
        self.st_cbb.addItem(tr("Misc", "Gateron Magnetic Jade/磁玉系列"))
        self.st_cbb.addItem(tr("Misc", "TTC King of Magnetic/万磁王系列"))
        g_layout.addWidget(self.st_cbb, line, 1)
        self.st_btn = QPushButton(tr("Misc", "Apply/应用"))
        self.st_btn.clicked.connect(self.on_st_btn)
        g_layout.addWidget(self.st_btn, line, 2)

        line = line + 1

        # down debounce setting
        self.dd_lbl = QLabel(tr("Misc", "Set the debounce time(ms) when press key/按键按下时的去抖时间:"))
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
        self.ud_lbl = QLabel(tr("Misc", "Set the debounce time(ms) when release key/按键释放时的去抖时间:"))
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
    
        line = line + 1
        #advanced
        self.adv_btn = QPushButton(tr("Misc", "Advanced/高级选项 \u22d9"))
        self.adv_btn.setMaximumWidth(100)
        self.adv_btn.clicked.connect(self.on_adv_btn)
        g_layout.addWidget(self.adv_btn, line, 0)

        line = line + 1
        self.noise_lbl = QLabel(tr("Misc", "Set the noise sensitivity/电磁干扰灵敏度:"))
        g_layout.addWidget(self.noise_lbl, line, 0)
        self.noise_dpb = QSpinBox()
        self.noise_dpb.setRange(1, 255)
        self.noise_dpb.setSingleStep(1)
        self.noise_dpb.valueChanged.connect(self.on_noise_dpb) 
        g_layout.addWidget(self.noise_dpb, line, 1)
        self.noise_sld= QSlider(Qt.Horizontal)
        self.noise_sld.setMaximumWidth(300)
        self.noise_sld.setMinimumWidth(200)
        self.noise_sld.setRange(1, 255)
        self.noise_sld.setSingleStep(1)
        self.noise_sld.setTickPosition(QSlider.TicksAbove)
        self.noise_sld.setTracking(False)
        self.noise_sld.valueChanged.connect(self.on_noise_sld) 
        g_layout.addWidget(self.noise_sld, line, 2)

        line = line + 1
        self.apc_lbl = QLabel(tr("Misc", "Set the apc sensitivity/APC动作灵敏度:"))
        g_layout.addWidget(self.apc_lbl, line, 0)
        self.apc_dpb = QSpinBox()
        self.apc_dpb.setRange(1, 255)
        self.apc_dpb.setSingleStep(1)
        self.apc_dpb.valueChanged.connect(self.on_apc_dpb) 
        g_layout.addWidget(self.apc_dpb, line, 1)
        self.apc_sld= QSlider(Qt.Horizontal)
        self.apc_sld.setMaximumWidth(300)
        self.apc_sld.setMinimumWidth(200)
        self.apc_sld.setRange(1, 255)
        self.apc_sld.setSingleStep(1)
        self.apc_sld.setTickPosition(QSlider.TicksAbove)
        self.apc_sld.setTracking(False)
        self.apc_sld.valueChanged.connect(self.on_apc_sld) 
        g_layout.addWidget(self.apc_sld, line, 2)

        line = line + 1
        self.rt_lbl = QLabel(tr("Misc", "Set the rt sensitivity/RT动作灵敏度:"))
        g_layout.addWidget(self.rt_lbl, line, 0)
        self.rt_dpb = QSpinBox()
        #self.rt_dpb.setEnabled(False)
        self.rt_dpb.setRange(1, 255)
        #self.rt_dpb.setValue(80)
        self.rt_dpb.setSingleStep(1)
        self.rt_dpb.valueChanged.connect(self.on_rt_dpb) 
        g_layout.addWidget(self.rt_dpb, line, 1)
        self.rt_sld= QSlider(Qt.Horizontal)
        #self.rt_sld.setEnabled(False)
        self.rt_sld.setMaximumWidth(300)
        self.rt_sld.setMinimumWidth(200)
        self.rt_sld.setRange(1, 255)
        self.rt_sld.setSingleStep(1)
        #self.rt_sld.setValue(80)
        self.rt_sld.setTickPosition(QSlider.TicksAbove)
        self.rt_sld.setTracking(False)
        self.rt_sld.valueChanged.connect(self.on_rt_sld) 
        g_layout.addWidget(self.rt_sld, line, 2)

        line = line + 1
        self.top_lbl = QLabel(tr("Misc", "Set the top sensitivity/轴体顶部状态灵敏度:"))
        g_layout.addWidget(self.top_lbl, line, 0)
        self.top_dpb = QSpinBox()
        #self.top_dpb.setEnabled(False)
        self.top_dpb.setRange(1, 255)
        #self.top_dpb.setValue(100)
        self.top_dpb.setSingleStep(1)
        self.top_dpb.valueChanged.connect(self.on_top_dpb) 
        g_layout.addWidget(self.top_dpb, line, 1)
        self.top_sld= QSlider(Qt.Horizontal)
        #self.top_sld.setEnabled(False)
        self.top_sld.setMaximumWidth(300)
        self.top_sld.setMinimumWidth(200)
        self.top_sld.setRange(1, 255)
        self.top_sld.setSingleStep(1)
        #self.top_sld.setValue(100)
        self.top_sld.setTickPosition(QSlider.TicksAbove)
        self.top_sld.setTracking(False)
        self.top_sld.valueChanged.connect(self.on_top_sld) 
        g_layout.addWidget(self.top_sld, line, 2)

        line = line + 1
        self.btm_lbl = QLabel(tr("Misc", "Set the bottom sensitivity/轴体底部状态灵敏度:"))
        g_layout.addWidget(self.btm_lbl, line, 0)
        self.btm_dpb = QSpinBox()
        #self.btm_dpb.setEnabled(False)
        self.btm_dpb.setRange(1, 255)
        #self.btm_dpb.setValue(100)
        self.btm_dpb.setSingleStep(1)
        self.btm_dpb.valueChanged.connect(self.on_btm_dpb) 
        g_layout.addWidget(self.btm_dpb, line, 1)
        self.btm_sld= QSlider(Qt.Horizontal)
        #self.btm_sld.setEnabled(False)
        self.btm_sld.setMaximumWidth(300)
        self.btm_sld.setMinimumWidth(200)
        self.btm_sld.setRange(1, 255)
        self.btm_sld.setSingleStep(1)
        #self.btm_sld.setValue(100)
        self.btm_sld.setTickPosition(QSlider.TicksAbove)
        self.btm_sld.setTracking(False)
        self.btm_sld.valueChanged.connect(self.on_btm_sld) 
        g_layout.addWidget(self.btm_sld, line, 2)

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
        self.advance = False

    def rebuild(self, device):
        super().rebuild(device)
        if self.valid():
            self.keyboard = device.keyboard
            self.reset_ui()


    def valid(self):
        # Check if vial protocol is v3 or later
        return isinstance(self.device, VialKeyboard) and \
               (self.device.keyboard and \
               (self.device.keyboard.keyboard_speed == "hs" or \
                self.device.keyboard.keyboard_type.startswith("mx_state") or \
                self.device.keyboard.keyboard_type.startswith("ms") or \
                self.device.keyboard.keyboard_type == "ec")) and \
               ((self.device.keyboard.cols // 8 + 1) * self.device.keyboard.rows <= 28)

    def reset_ui(self):
        self.nk_cbx.blockSignals(True)
        self.nk_cbx.setCheckState(self.keyboard.amk_nkro)
        self.ns_lbl.setText(tr("Misc", "ON/开启") if self.keyboard.amk_nkro else tr("Misc", "OFF/关闭"))
        self.nk_cbx.blockSignals(False)

        if self.device.keyboard.keyboard_speed == "hs":
            self.pr_cbb.blockSignals(True)
            self.pr_cbb.setCurrentIndex(self.keyboard.amk_poll_rate)
            self.pr_cbb.blockSignals(False)
            self.pr_cbb.show()
            self.pr_lbl.show()
            self.pr_btn.show()
        else:
            self.pr_cbb.hide()
            self.pr_lbl.hide()
            self.pr_btn.hide()

        if self.keyboard.keyboard_type.startswith("ms"):
            self.mp_lbl.show()
            self.mp_cbb.show()
        else:
            self.mp_lbl.hide()
            self.mp_cbb.hide()

        if self.keyboard.keyboard_type == "ms_v2":
            self.apcrt_cbb.blockSignals(True)
            self.apcrt_cbb.clear()
            for i in range(self.keyboard.amk_profile_count):
                self.apcrt_cbb.addItem(str(i))
            self.apcrt_cbb.blockSignals(False)
            self.apcrt_lbl.show()
            self.apcrt_cbb.show()

            self.dks_cbx.blockSignals(True)
            self.dks_cbx.setCheckState(not self.keyboard.amk_dks_disable)
            self.dks_lbl.setText(tr("Misc", "OFF/关闭") if self.keyboard.amk_dks_disable else tr("Misc", "ON/开启"))
            self.dks_cbx.blockSignals(False)
            self.dks_status_lbl.show()
            self.dks_lbl.show()
            self.dks_cbx.show()
        else:
            self.apcrt_lbl.hide()
            self.apcrt_cbb.hide()
            self.dks_status_lbl.hide()
            self.dks_lbl.hide()
            self.dks_cbx.hide()

        if self.keyboard.keyboard_type.startswith("ms") or self.keyboard.keyboard_type == "ec":
            self.dd_lbl.hide()
            self.dd_sld.hide()
            self.dd_sbx.hide()
            self.ud_lbl.hide()
            self.ud_sld.hide()
            self.ud_sbx.hide()

            import sys
            if sys.platform == "emscripten":
                self.ie_lbl.hide()
                self.im_btn.hide()
                self.ex_btn.hide()
            else:
                self.ie_lbl.show()
                self.im_btn.show()
                self.ex_btn.show()

            self.adv_btn.show()
            self.show_advance(self.advance)
        else:
            self.dd_lbl.show()
            self.dd_sld.show()
            self.dd_sbx.show()
            self.ud_lbl.show()
            self.ud_sld.show()
            self.ud_sbx.show()

            self.ie_lbl.hide()
            self.im_btn.hide()
            self.ex_btn.hide()

            self.adv_btn.hide()
            self.show_advance(False)

        if self.keyboard.keyboard_type.startswith("mx"):
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
        
        if self.keyboard.amk_has_switch_type:
            self.st_cbb.blockSignals(True)
            self.st_cbb.setCurrentIndex(self.keyboard.amk_switch_type)
            self.st_cbb.blockSignals(False)
            self.st_lbl.show()
            self.st_cbb.show()
            self.st_btn.show()
        else:
            self.st_lbl.hide()
            self.st_cbb.hide()
            self.st_btn.hide()


    def activate(self):
        pass
        #print("hs windows activated")

    def deactivate(self):
        pass
        #print("hs windows deactivated")

    def on_pr_btn(self):
        #print("Apply poll rate clicked")
        val = self.pr_cbb.currentIndex()
        self.keyboard.apply_poll_rate(val)

    def on_st_btn(self):
        #print("Apply switch type clicked")
        val = self.st_cbb.currentIndex()
        self.keyboard.apply_switch_type(val)

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

    def on_apcrt_cbb(self):
        #print("apcrt combobox changed")
        val = self.apcrt_cbb.currentIndex()
        self.keyboard.apply_profile(val)

    def on_dks_cbx(self):
        #print("dks checkbox changed")
        val = True if self.dks_cbx.checkState() == Qt.Checked else False
        if val:
            self.dks_lbl.setText("ON")
        else:
            self.dks_lbl.setText("OFF")

        self.keyboard.apply_dks_disable(not val)

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

            dks = kbd.get("dks", None)
            if dks is not None:
                self.keyboard.apply_dks_disable(dks == 0)

            profile = kbd.get("profile", None)
            if profile is not None:
                self.keyboard.apply_profile(profile)

            nkro = kbd.get("nkro", None)
            if nkro is not None:
                self.keyboard.apply_nkro(nkro)

            sens = kbd.get("rt_sens", None)
            if sens is not None:
                self.keyboard.apply_rt_sensitivity(sens)
            sens = kbd.get("top_sens", None)
            if sens is not None:
                self.keyboard.apply_top_sensitivity(sens)
            sens = kbd.get("btm_sens", None)
            if sens is not None:
                self.keyboard.apply_btm_sensitivity(sens)

            sens = kbd.get("apc_sens", None)
            if sens is not None:
                self.keyboard.apply_apc_sensitivity(sens)
            
            sens = kbd.get("noise_sens", None)
            if sens is not None:
                self.keyboard.apply_noise_sensitivity(sens)

            keys = kbd.get("keys", None)
            if keys is not None:
                for key in keys:
                    row = key["row"]
                    col = key["col"]
                    profile = key.get("profile", 0)
                    apc = key.get("apc", None)
                    if apc is not None:
                        self.keyboard.apply_apc(row, col, apc, 0)

                    rt = key.get("rt", None)
                    if rt is not None:
                        self.keyboard.apply_rt(row, col, rt, 0)

                    dks = key.get("dks", None)
                    if dks is not None:
                        self.keyboard.apply_dks(row, col, dks)

            poll_rate = kbd.get("poll_rate", None)
            if poll_rate is not None:
                self.keyboard.apply_poll_rate(poll_rate)

            switch_type = kbd.get("switch_type", None)
            if switch_type is not None:
                self.keyboard.apply_switch_type(switch_type)

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
        if self.keyboard.keyboard_type == "ms_v2":
            kbd["dks"] = 1 if self.dks_cbx.checkState() == Qt.Checked else 0
            kbd["profile"] = self.keyboard.keyboard_profile
        kbd["nkro"] = 1 if self.nk_cbx.checkState() == Qt.Checked else 0
        kbd["poll_rate"] = self.pr_cbb.currentIndex()
        kbd["switch_type"] = self.st_cbb.currentIndex()
        kbd["rt_sens"] = self.rt_sld.value()
        kbd["top_sens"] = self.top_sld.value()
        kbd["btm_sens"] = self.btm_sld.value()
        kbd["apc_sens"] = self.apc_sld.value()
        kbd["noise_sens"] = self.noise_sld.value()
        kbd["keys"] = []

        for row, col in self.keyboard.rowcol.keys():
            for profile in range(self.keyboard.amk_profile_count):
                key = {}
                key["row"] = row
                key["col"] = col
                key["profile"] = profile
                key["apc"] = self.keyboard.amk_apc[profile][(row,col)]
                key["rt"] = self.keyboard.amk_rt[profile][(row,col)]
                if profile == 0:
                    key["dks"] = self.keyboard.amk_dks[(row,col)].save()

                kbd["keys"].append(key)
        
        with open(export_file, "w", encoding="utf-8") as fp:
            #json.dump(kbd, fp, indent=4)
            json.dump(kbd, fp)

    def show_advance(self, show):
        if show:
            self.noise_lbl.show()
            self.noise_dpb.blockSignals(True)
            self.noise_dpb.setValue(self.keyboard.amk_noise_sens)
            self.noise_dpb.blockSignals(False)
            self.noise_dpb.show()
            self.noise_sld.blockSignals(True)
            self.noise_sld.setValue(self.keyboard.amk_noise_sens)
            self.noise_sld.blockSignals(False)
            self.noise_sld.show()

            self.apc_lbl.show()
            self.apc_dpb.blockSignals(True)
            self.apc_dpb.setValue(self.keyboard.amk_apc_sens)
            self.apc_dpb.blockSignals(False)
            self.apc_dpb.show()
            self.apc_sld.blockSignals(True)
            self.apc_sld.setValue(self.keyboard.amk_apc_sens)
            self.apc_sld.blockSignals(False)
            self.apc_sld.show()

            self.rt_lbl.show()
            self.rt_dpb.blockSignals(True)
            self.rt_dpb.setValue(self.keyboard.amk_rt_sens)
            self.rt_dpb.blockSignals(False)
            self.rt_dpb.show()
            self.rt_sld.blockSignals(True)
            self.rt_sld.setValue(self.keyboard.amk_rt_sens)
            self.rt_sld.blockSignals(False)
            self.rt_sld.show()

            self.top_lbl.show()
            self.top_dpb.blockSignals(True)
            self.top_dpb.setValue(self.keyboard.amk_top_sens)
            self.top_dpb.blockSignals(False)
            self.top_dpb.show()
            self.top_sld.blockSignals(True)
            self.top_sld.setValue(self.keyboard.amk_top_sens)
            self.top_sld.blockSignals(False)
            self.top_sld.show()

            self.btm_lbl.show()
            self.btm_dpb.blockSignals(True)
            self.btm_dpb.setValue(self.keyboard.amk_btm_sens)
            self.btm_dpb.blockSignals(False)
            self.btm_dpb.show()
            self.btm_sld.blockSignals(True)
            self.btm_sld.setValue(self.keyboard.amk_btm_sens)
            self.btm_sld.blockSignals(False)
            self.btm_sld.show()

            self.adv_btn.setText(tr("Misc", "Hide/隐藏 \u22d8"))
        else:
            self.noise_lbl.hide()
            self.noise_dpb.hide()
            self.noise_sld.hide()

            self.apc_lbl.hide()
            self.apc_dpb.hide()
            self.apc_sld.hide()

            self.rt_lbl.hide()
            self.rt_dpb.hide()
            self.rt_sld.hide()

            self.top_lbl.hide()
            self.top_dpb.hide()
            self.top_sld.hide()

            self.btm_lbl.hide()
            self.btm_dpb.hide()
            self.btm_sld.hide()
            self.adv_btn.setText(tr("Misc", "Advanced/高级选项 \u22d9"))

    def on_adv_btn(self):
        self.advance = not self.advance
        self.show_advance(self.advance)

    def on_noise_dpb(self):
        self.noise_dpb.blockSignals(True)
        self.noise_sld.blockSignals(True)
        self.noise_sld.setValue(self.noise_dpb.value())
        self.keyboard.apply_noise_sensitivity(self.noise_sld.value())
        self.noise_sld.blockSignals(False)
        self.noise_dpb.blockSignals(False)

    def on_noise_sld(self):
        self.noise_dpb.blockSignals(True)
        self.noise_sld.blockSignals(True)
        self.noise_dpb.setValue(self.noise_sld.value())
        self.keyboard.apply_noise_sensitivity(self.noise_sld.value())
        self.noise_sld.blockSignals(False)
        self.noise_dpb.blockSignals(False)

    def on_apc_dpb(self):
        self.apc_dpb.blockSignals(True)
        self.apc_sld.blockSignals(True)
        self.apc_sld.setValue(self.apc_dpb.value())
        self.keyboard.apply_apc_sensitivity(self.apc_sld.value())
        self.apc_sld.blockSignals(False)
        self.apc_dpb.blockSignals(False)

    def on_apc_sld(self):
        self.apc_dpb.blockSignals(True)
        self.apc_sld.blockSignals(True)
        self.apc_dpb.setValue(self.apc_sld.value())
        self.keyboard.apply_apc_sensitivity(self.apc_sld.value())
        self.apc_sld.blockSignals(False)
        self.apc_dpb.blockSignals(False)

    def on_rt_dpb(self):
        self.rt_dpb.blockSignals(True)
        self.rt_sld.blockSignals(True)
        self.rt_sld.setValue(self.rt_dpb.value())
        self.keyboard.apply_rt_sensitivity(self.rt_sld.value())
        self.rt_sld.blockSignals(False)
        self.rt_dpb.blockSignals(False)

    def on_rt_sld(self):
        self.rt_dpb.blockSignals(True)
        self.rt_sld.blockSignals(True)
        self.rt_dpb.setValue(self.rt_sld.value())
        self.keyboard.apply_rt_sensitivity(self.rt_sld.value())
        self.rt_sld.blockSignals(False)
        self.rt_dpb.blockSignals(False)

    def on_top_dpb(self):
        self.top_dpb.blockSignals(True)
        self.top_sld.blockSignals(True)
        self.top_sld.setValue(self.top_dpb.value())
        self.keyboard.apply_top_sensitivity(self.top_sld.value())
        self.top_sld.blockSignals(False)
        self.top_dpb.blockSignals(False)

    def on_top_sld(self):
        self.top_dpb.blockSignals(True)
        self.top_sld.blockSignals(True)
        self.top_dpb.setValue(self.top_sld.value())
        self.keyboard.apply_top_sensitivity(self.top_sld.value())
        self.top_sld.blockSignals(False)
        self.top_dpb.blockSignals(False)

    def on_btm_dpb(self):
        self.btm_dpb.blockSignals(True)
        self.btm_sld.blockSignals(True)
        self.btm_sld.setValue(self.btm_dpb.value())
        self.keyboard.apply_btm_sensitivity(self.btm_sld.value())
        self.btm_sld.blockSignals(False)
        self.btm_dpb.blockSignals(False)

    def on_btm_sld(self):
        self.btm_dpb.blockSignals(True)
        self.btm_sld.blockSignals(True)
        self.btm_dpb.setValue(self.btm_sld.value())
        self.keyboard.apply_btm_sensitivity(self.btm_sld.value())
        self.btm_sld.blockSignals(False)
        self.btm_dpb.blockSignals(False)
