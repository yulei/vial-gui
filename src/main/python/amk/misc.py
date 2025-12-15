# SPDX-License-Identifier: GPL-2.0-or-later

from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel, QSlider, QProgressBar, QLineEdit, QListWidget
from PyQt5.QtWidgets import QSpinBox, QComboBox, QCheckBox, QFileDialog, QMessageBox, QProgressDialog, QApplication
from PyQt5.QtCore import Qt, QCoreApplication, QTimer

import os, json, sys

from util import tr

from editor.basic_editor import BasicEditor
from vial_device import VialKeyboard

BUILD_MAGIC=0x2ac097b5
MAGIC_INDEX=7*4
SIZE_INDEX=8*4
DATE_INDEX=9*4
SECOND_INDEX=10*4
INFO_INDEX=13*4


WIFI_STATE_IDLE = 0
WIFI_STATE_CONNECTING = 1
WIFI_STATE_CONNECTED = 2

WIFI_START_SCAN_TEXT = tr("Misc", "Scan/扫描")
WIFI_STOP_SCAN_TEXT = tr("Misc", "Stop Scan/停止扫描")
WIFI_CONNECT_TEXT = tr("Misc", "Connect/连接")
WIFI_DISCONNECT_TEXT = tr("Misc", "Disconnect/断开连接")

WIFI_CONNECT_TIMEOUT = 10  #seconds
WIFI_SCAN_TIMEOUT = 20  #seconds

from amk.protocol import ESP32_STATE, ESP32_GET_SSID, ESP32_CONNECT, ESP32_DISCONNECT

class Misc(BasicEditor):

    def __init__(self, layout_editor, appctx):
        super().__init__()
        self.appctx = appctx
        self.timer = QTimer()
        self.timer.timeout.connect(self.upload_firmware_period)

        self.wifi_state = WIFI_STATE_IDLE
        self.wifi_connect_timeout = 0
        self.wifi_scanning = False
        self.wifi_scan_timeout = 0
        self.wifi_timer = QTimer()
        self.wifi_timer.timeout.connect(self.wifi_periodic_oper)

        g_layout = QGridLayout()

        line = 0

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

        # polling rate setting
        line = line + 1
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

        # down debounce setting
        line = line + 1
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

        # up debounce setting
        line = line + 1
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

        # import/export setting from/to file
        line = line + 1
        self.ie_lbl = QLabel(tr("Misc", "Import or export keyboard config file:/磁轴配置操作"))
        g_layout.addWidget(self.ie_lbl, line, 0)
        self.im_btn = QPushButton(tr("Misc", "Import/导入 ..."))
        self.im_btn.clicked.connect(self.on_im_btn)
        g_layout.addWidget(self.im_btn, line, 1)
        self.ex_btn = QPushButton(tr("Misc", "Export/导出 ..."))
        self.ex_btn.clicked.connect(self.on_ex_btn)
        g_layout.addWidget(self.ex_btn, line, 2)

        # magnetic pole setting
        line = line + 1
        self.mp_lbl = QLabel(tr("Misc", "Set the magnetic pole of the switch:/设置磁轴极性"))
        g_layout.addWidget(self.mp_lbl, line, 0)
        self.mp_cbb = QComboBox()
        self.mp_cbb.addItem(tr("Misc", "South/南极"))
        self.mp_cbb.addItem(tr("misc", "North/北极"))
        self.mp_cbb.currentIndexChanged.connect(self.on_mp_cbb)
        g_layout.addWidget(self.mp_cbb, line, 1)

        # apcrt profile setting
        line = line + 1
        self.apcrt_lbl = QLabel(tr("Misc", "Set keyboard's APCRT profile/设置当前APCRT的配置:"))
        g_layout.addWidget(self.apcrt_lbl, line, 0)
        self.apcrt_cbb = QComboBox()
        self.apcrt_cbb.currentIndexChanged.connect(self.on_apcrt_cbb)
        g_layout.addWidget(self.apcrt_cbb, line, 1)

        # dks state setting
        line = line + 1
        self.dks_status_lbl = QLabel(tr("Misc", "Set keyboard's DKS status/切换DKS状态:"))
        g_layout.addWidget(self.dks_status_lbl, line, 0)
        self.dks_lbl = QLabel(tr("Misc", "ON/激活"))
        g_layout.addWidget(self.dks_lbl, line, 1, alignment=Qt.AlignCenter)
        self.dks_cbx = QCheckBox()
        self.dks_cbx.setTristate(False)
        self.dks_cbx.setEnabled(True)
        self.dks_cbx.stateChanged.connect(self.on_dks_cbx)
        g_layout.addWidget(self.dks_cbx, line, 2)

        # switch type setting
        line = line + 1
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
    
        #advanced
        line = line + 1
        self.adv_btn = QPushButton(tr("Misc", "Advanced/高级选项 >>"))
        self.adv_btn.setMaximumWidth(200)
        self.adv_btn.clicked.connect(self.on_adv_btn)
        g_layout.addWidget(self.adv_btn, line, 0)

        #noise
        line = line + 1
        self.noise_lbl = QLabel(tr("Misc", "Set the noise sensitivity/电磁干扰灵敏度:"))
        g_layout.addWidget(self.noise_lbl, line, 0)
        self.noise_dpb = QSpinBox()
        self.noise_dpb.setRange(0, 255)
        self.noise_dpb.setSingleStep(1)
        self.noise_dpb.valueChanged.connect(self.on_noise_dpb) 
        g_layout.addWidget(self.noise_dpb, line, 1)
        self.noise_sld= QSlider(Qt.Horizontal)
        self.noise_sld.setMaximumWidth(300)
        self.noise_sld.setMinimumWidth(200)
        self.noise_sld.setRange(0, 255)
        self.noise_sld.setSingleStep(1)
        self.noise_sld.setTickPosition(QSlider.TicksAbove)
        self.noise_sld.setTracking(False)
        self.noise_sld.valueChanged.connect(self.on_noise_sld) 
        g_layout.addWidget(self.noise_sld, line, 2)

        #apc
        line = line + 1
        self.apc_lbl = QLabel(tr("Misc", "Set the apc sensitivity/APC动作灵敏度:"))
        g_layout.addWidget(self.apc_lbl, line, 0)
        self.apc_dpb = QSpinBox()
        self.apc_dpb.setRange(0, 255)
        self.apc_dpb.setSingleStep(1)
        self.apc_dpb.valueChanged.connect(self.on_apc_dpb) 
        g_layout.addWidget(self.apc_dpb, line, 1)
        self.apc_sld= QSlider(Qt.Horizontal)
        self.apc_sld.setMaximumWidth(300)
        self.apc_sld.setMinimumWidth(200)
        self.apc_sld.setRange(0, 255)
        self.apc_sld.setSingleStep(1)
        self.apc_sld.setTickPosition(QSlider.TicksAbove)
        self.apc_sld.setTracking(False)
        self.apc_sld.valueChanged.connect(self.on_apc_sld) 
        g_layout.addWidget(self.apc_sld, line, 2)

        #rt
        line = line + 1
        self.rt_lbl = QLabel(tr("Misc", "Set the rt sensitivity/RT动作灵敏度:"))
        g_layout.addWidget(self.rt_lbl, line, 0)
        self.rt_dpb = QSpinBox()
        self.rt_dpb.setRange(0, 255)
        self.rt_dpb.setSingleStep(1)
        self.rt_dpb.valueChanged.connect(self.on_rt_dpb) 
        g_layout.addWidget(self.rt_dpb, line, 1)
        self.rt_sld= QSlider(Qt.Horizontal)
        self.rt_sld.setMaximumWidth(300)
        self.rt_sld.setMinimumWidth(200)
        self.rt_sld.setRange(0, 255)
        self.rt_sld.setSingleStep(1)
        self.rt_sld.setTickPosition(QSlider.TicksAbove)
        self.rt_sld.setTracking(False)
        self.rt_sld.valueChanged.connect(self.on_rt_sld) 
        g_layout.addWidget(self.rt_sld, line, 2)

        #top
        line = line + 1
        self.top_lbl = QLabel(tr("Misc", "Set the top sensitivity/轴体顶部状态灵敏度:"))
        g_layout.addWidget(self.top_lbl, line, 0)
        self.top_dpb = QSpinBox()
        self.top_dpb.setRange(0, 255)
        self.top_dpb.setSingleStep(1)
        self.top_dpb.valueChanged.connect(self.on_top_dpb) 
        g_layout.addWidget(self.top_dpb, line, 1)
        self.top_sld= QSlider(Qt.Horizontal)
        self.top_sld.setMaximumWidth(300)
        self.top_sld.setMinimumWidth(200)
        self.top_sld.setRange(0, 255)
        self.top_sld.setSingleStep(1)
        self.top_sld.setTickPosition(QSlider.TicksAbove)
        self.top_sld.setTracking(False)
        self.top_sld.valueChanged.connect(self.on_top_sld) 
        g_layout.addWidget(self.top_sld, line, 2)

        #bottom
        line = line + 1
        self.btm_lbl = QLabel(tr("Misc", "Set the bottom sensitivity/轴体底部状态灵敏度:"))
        g_layout.addWidget(self.btm_lbl, line, 0)
        self.btm_dpb = QSpinBox()
        self.btm_dpb.setRange(0, 255)
        self.btm_dpb.setSingleStep(1)
        self.btm_dpb.valueChanged.connect(self.on_btm_dpb) 
        g_layout.addWidget(self.btm_dpb, line, 1)
        self.btm_sld= QSlider(Qt.Horizontal)
        self.btm_sld.setMaximumWidth(300)
        self.btm_sld.setMinimumWidth(200)
        self.btm_sld.setRange(0, 255)
        self.btm_sld.setSingleStep(1)
        self.btm_sld.setTickPosition(QSlider.TicksAbove)
        self.btm_sld.setTracking(False)
        self.btm_sld.valueChanged.connect(self.on_btm_sld) 
        g_layout.addWidget(self.btm_sld, line, 2)

        #firmware
        line = line + 1
        self.firmware_lbl = QLabel(tr("Misc", "Firmware/键盘固件:"))
        g_layout.addWidget(self.firmware_lbl, line, 0)
        self.firmware_load_btn = QPushButton(tr("Misc", "Load/导入 ..."))
        self.firmware_load_btn.clicked.connect(self.on_load_firmware)
        g_layout.addWidget(self.firmware_load_btn, line, 1)
        self.firmware_check_btn = QPushButton(tr("Misc", "Check update/检查更新"))
        self.firmware_check_btn.clicked.connect(self.on_check_firmware)
        g_layout.addWidget(self.firmware_check_btn, line, 2)

        if sys.platform == "emscripten":
            line = line + 1
            self.upload_bar = QProgressBar()
            g_layout.addWidget(self.upload_bar, line, 1)
            self.upload_btn = QPushButton(tr("Misc", "Upload && Reset/更新并重启"))
            self.upload_btn.clicked.connect(self.on_upload_reset)
            self.upload_btn.setEnabled(False)
            g_layout.addWidget(self.upload_btn, line, 2)
        
        #esp32 command
        if True:
            line = line + 1
            self.esp32_main_cbx = QComboBox()
            self.esp32_main_cbx.addItems(["BASIC", "WIFI", "TCPIP", "BLE", "MQTT", 
                                        "HTTP", "FILESYSTEM", "WEBSOCKET", "SIGNALING", 
                                        "WEBSERVER", "DRIVER", "USER"])
            self.esp32_main_cbx.currentIndexChanged.connect(self.on_esp32_main_cbx)
            g_layout.addWidget(self.esp32_main_cbx, line, 0)
            self.esp32_sub_cbx = QComboBox()
            self.esp32_sub_cbx.addItems([
                                    "CWINIT", "CWMODE", "CWSTATE", "CWCONFIG", 
                                    "CWJAP", "CWRECONNCFG", "CWLAPOPT", "CWLAP",
                                    "CWQAP", "CWSAP", "CWLIF", "CWQIF",
                                    "CWDHCP", "CWDHCPS", "CWAUTOCONN", "CWAPPROTO",
                                    "CWSTAPROTO", "CIPSTAMAC", "CIPAPMAC", "CIPSTA",
                                    "CIPAP", "CWSTARTSMART", "CWSTOPSMART", "WPS",
                                    "CWJEAP", "CWHOSTNAME", "CWCOUNTRY",
                                    "HTTPCLIENT", "HTTPGETSIZE", "HTTPCGET", "HTTPCPOST",
                                    "HTTPCPUT", "HTTPURLCFG", "HTTPCHEAD", "HTTPCFG"
                                    ])
            self.esp32_sub_cbx.currentIndexChanged.connect(self.on_esp32_sub_cbx)
            g_layout.addWidget(self.esp32_sub_cbx, line, 1)
            self.esp32_type_cbx = QComboBox()
            self.esp32_type_cbx.addItems(["TEST", "QUERY", "SET", "EXECUTE"])
            self.esp32_type_cbx.currentIndexChanged.connect(self.on_esp32_type_cbx)
            g_layout.addWidget(self.esp32_type_cbx, line, 2)
            line = line + 1
            self.esp32_param_edt = QLineEdit()
            self.esp32_param_edt.editingFinished.connect(self.on_esp32_param_text)
            g_layout.addWidget(self.esp32_param_edt, line, 1)
            self.esp32_apply_btn = QPushButton(tr("Misc", "Apply ESP32 Command/应用ESP32指令"))
            self.esp32_apply_btn.clicked.connect(self.on_esp32_apply_btn)
            g_layout.addWidget(self.esp32_apply_btn, line, 2)
        
        #wifi connection
        line = line + 1
        self.wifi_lbl = QLabel(tr("Misc", "Wifi:"))
        g_layout.addWidget(self.wifi_lbl, line, 0)
        self.wifi_scan_btn = QPushButton(WIFI_START_SCAN_TEXT)
        self.wifi_scan_btn.clicked.connect(self.on_wifi_scan_btn)
        g_layout.addWidget(self.wifi_scan_btn, line, 1)
        self.wifi_conn_btn = QPushButton(WIFI_CONNECT_TEXT)
        self.wifi_conn_btn.clicked.connect(self.on_wifi_conn_btn)
        g_layout.addWidget(self.wifi_conn_btn, line, 2)
        line = line + 1
        self.wifi_ap_lst = QListWidget()
        self.wifi_ap_lst.currentRowChanged.connect(self.on_wifi_ap_changed)
        g_layout.addWidget(self.wifi_ap_lst, line, 1)
        t_lyt = QHBoxLayout()
        self.wifi_pass_lbl = QLabel(tr("Misc", "Password/密码:"))
        t_lyt.addWidget(self.wifi_pass_lbl)
        self.wifi_pass_edt = QLineEdit()
        self.wifi_pass_edt.editingFinished.connect(self.on_wifi_pass_text)
        t_lyt.addWidget(self.wifi_pass_edt)
        g_layout.addLayout(t_lyt, line, 2)

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
        self.current_firmware_data = None

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

    def reset_wifi_ui(self):
        if self.keyboard.amk_feature.get("esp32at_test", False):
            self.esp32_main_cbx.show()
            self.esp32_sub_cbx.show()
            self.esp32_type_cbx.show()
            self.esp32_param_edt.show()
            self.esp32_apply_btn.show()
        else:
            self.esp32_main_cbx.hide()
            self.esp32_sub_cbx.hide()
            self.esp32_type_cbx.hide()
            self.esp32_param_edt.hide()
            self.esp32_apply_btn.hide()

        if self.keyboard.amk_feature.get("esp32at", False):
            self.wifi_lbl.show()
            self.wifi_scan_btn.show()
            self.wifi_conn_btn.show()
            self.wifi_ap_lst.show()
            self.wifi_pass_lbl.show()
            self.wifi_pass_edt.show()
        else:
            self.wifi_lbl.hide()
            self.wifi_scan_btn.hide()
            self.wifi_conn_btn.hide()
            self.wifi_ap_lst.hide()
            self.wifi_pass_lbl.hide()
            self.wifi_pass_edt.hide()

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

            if True or sys.platform == "emscripten":
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
        
        if self.keyboard.amk_feature["switch_type"]:
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

        if self.keyboard.amk_feature["firmware"]:
            self.firmware_lbl.show()
            self.firmware_load_btn.show()
            self.firmware_check_btn.show()
            self.firmware_check_btn.setText(tr("Misc", "Check update/检查更新"))
            if sys.platform == "emscripten":
                self.upload_btn.show()
                self.upload_bar.show()
                self.firmware_load_btn.hide()
        else:
            self.firmware_lbl.hide()
            self.firmware_load_btn.hide()
            self.firmware_check_btn.hide()
            if sys.platform == "emscripten":
                self.upload_btn.hide()
                self.upload_bar.hide()
        self.reset_wifi_ui()

    def activate(self):
        if self.keyboard is not None and self.keyboard.amk_feature.get("esp32at", False):
            self.wifi_timer.start(1000)
        #print("hs windows activated")

    def deactivate(self):
        self.timer.stop()
        self.wifi_timer.stop()
        #print("hs windows deactivated")

    def on_pr_btn(self):
        #print("Apply poll rate clicked")
        val = self.pr_cbb.currentIndex()
        self.keyboard.apply_poll_rate(val)

        if sys.platform == "emscripten":
            import vialglue
            vialglue.reload_keyboard()

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

            self.adv_btn.setText(tr("Misc", "Hide/隐藏 <<"))
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
            self.adv_btn.setText(tr("Misc", "Advanced/高级选项 >>"))

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

    def is_uf2_block_valid(self, block):
        if len(block) != 512:
            print("Invalid block size")
            return (False, 0, 0)

        import struct
        magicStart0,magicStart1,flags, targetAddr, payloadSize,blockNo, numBlocks, fileSize = struct.unpack("<8I", block[0:32])
        magicEnd, = struct.unpack("<I", block[508:])
        if magicStart0 != 0x0A324655 or magicStart1 != 0x9E5D5157 or magicEnd != 0x0AB16F30:
            print("Invalid magic number:", hex(magicStart0), hex(magicStart1), hex(magicEnd))
            return (False, 0, 0)


        UF2_FLAG_NOFLASH = 0x00000001
        UF2_FLAG_FAMILYID = 0x00002000
        if ((flags & UF2_FLAG_FAMILYID) == 0) or ((flags & UF2_FLAG_NOFLASH) != 0):
            print("Invalid flags:", hex(flags))
            return (False, 0, 0)
        
        return (True, payloadSize, targetAddr)

    def load_uf2(self, filename):
        with open(filename, "rb") as fp:
            uf2 = fp.read()
            return self.parse_uf2(uf2)
        return (None, None)

    def parse_uf2(self, uf2):
        data = bytearray() 
        start = 0xFFFFFFFF
        if (len(uf2) % 512) != 0:
            if sys.platform != "emscripten":
                button = QMessageBox.warning(None, "Loading firmware",
                                        "Invalid UF2 file size./固件已损坏",
                                        buttons=QMessageBox.Ok,
                                        defaultButton=QMessageBox.Ok)
            return (None,None)
        for i in range(len(uf2) // 512):
            block = uf2[i * 512:i * 512 + 512]
            valid, size, address = self.is_uf2_block_valid(block)
            if valid:
                data = data + block[32:32+size]
                start = min(start, address)
            else:
                if sys.platform != "emscripten":
                    button = QMessageBox.warning(None, "Loading firmware",
                                            "UF2 file content invalid./无效的固件",
                                            buttons=QMessageBox.Ok,
                                            defaultButton=QMessageBox.Ok)
                return (None,None)

        return (data, start)

    def convert_date_second(self, build):
        data = build.split("-")
        date = (int(data[0])<<16) | (int(data[1])<<8) | int(data[2])
        second = (int(data[3]*3600) | (int(data[4])*60) | int(data[5]))
        return (date, second)

    def upload_firmware(self, data, address):
        import struct
        magic, = struct.unpack("<I", data[MAGIC_INDEX:MAGIC_INDEX+4])
        if magic != BUILD_MAGIC:
            print("Invalid magic number:", hex(magic))
            button = QMessageBox.warning(None, "Loading firmware",
                                        "Invalid firmware file./固件已损坏",
                                        buttons=QMessageBox.Ok,
                                        defaultButton=QMessageBox.Ok)
            return
        board_info_address, = struct.unpack("<I", data[INFO_INDEX:INFO_INDEX+4])
        offset = board_info_address - address
        firmware_vendor_id, firmware_product_id, firmware_family, = struct.unpack("<HHI", data[offset:offset+8])

        vendor_id, product_id, family, date, second, size = self.keyboard.firmware_info()
        if vendor_id != firmware_vendor_id or product_id != firmware_product_id or family != firmware_family:
            print("Invalid firmware vendor id or product id or family:", hex(vendor_id), hex(product_id), hex(family), hex(firmware_vendor_id), hex(firmware_product_id), hex(firmware_family))
            button = QMessageBox.warning(None, "Loading firmware",
                                        "The firmware is not for this keyboard./固件不适合此键盘",
                                        buttons=QMessageBox.Ok,
                                        defaultButton=QMessageBox.Ok)
            return

        #return

        self.keyboard.firmware_prepare()

        progress = QProgressDialog("Upload firmware/更新固件...", "Abort/退出", 0, len(data))
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        offset = 0
        while offset < len(data):
            size = 24 if len(data) - offset >= 24 else len(data) - offset

            if self.keyboard.firmware_upload(offset, data[offset:offset+size]):
                progress.setValue(offset)
                QCoreApplication.processEvents()
            else:
                print("Failed to upload firmware")
                break

            if progress.wasCanceled():
                break

            offset = offset + size

        progress.hide()

        self.keyboard.firmware_finish()

        button = QMessageBox.warning(None, "Firmware",
                                    "Need reset keyboard to use the new firmware, do you want to reset now?\n新固件需要重启键盘才能生效,现在重启?",
                                    buttons=QMessageBox.Yes | QMessageBox.No,
                                    defaultButton=QMessageBox.No)
        if button == QMessageBox.Yes:
            self.keyboard.firmware_reset()

    def on_check_firmware(self):
        if sys.platform == "emscripten":
            with open(self.appctx.get_resource("firmware.json"), "r", encoding='utf-8') as fp:
                import json
                firmwares = json.load(fp)
            print(firmwares)
        else:
            from urllib.request import urlopen 
            from urllib.error import URLError
            url_prefix = "https://config.matrix-lab.com/update/"

            try:
                firmware_list = urlopen(url_prefix + "firmware.json")
            except URLError as e:
                print("Failed to load firmware list:", e)
                button = QMessageBox.warning(None, "Firmware",
                                            "Failed to load firmware list./无法加载固件列表",
                                            buttons=QMessageBox.Ok,
                                            defaultButton=QMessageBox.Ok)
                return
            import json
            firmwares = json.loads(firmware_list.read().decode("utf-8"))

        vendor_id, product_id, family, date, second, size = self.keyboard.firmware_info()
        if "keyboards" in firmwares:
            for kbd in firmwares["keyboards"]:
                if kbd["vendor_id"] == hex(vendor_id) and kbd["product_id"] == hex(product_id) and kbd["family"] == hex(family):
                    kbd_date, kbd_second = self.convert_date_second(kbd["build"])
                    if (kbd_date > date) or (kbd_date == date and kbd_second > second):
                        print("New firmware found:", kbd["build"])
                        if sys.platform == "emscripten":
                            with open(self.appctx.get_resource("firmwares/"+kbd["firmware"]), "rb") as fp:
                                uf2 = fp.read()
                                data, address = self.parse_uf2(uf2)
                                self.current_firmware_data = data
                                self.current_firmware_address = address
                                self.upload_btn.setEnabled(True)
                                self.upload_bar.reset()
                        else:
                            button = QMessageBox.warning(None, "Firmware",
                                                        "New firmware found.Do you want to download and update it?\n发现新固件,是否下载并更新?",
                                                        buttons=QMessageBox.Yes | QMessageBox.No,
                                                        defaultButton=QMessageBox.No)
                            if button == QMessageBox.Yes:
                                url = url_prefix + "firmwares/"+kbd["firmware"]
                                print("Downloading firmware from:", url)
                                try:
                                    firmware = urlopen(url)
                                except URLError as e:
                                    print("Failed to load firmware:", e)
                                    button = QMessageBox.warning(None, "Firmware",
                                                                "Failed to download firmware./无法下载固件",
                                                                buttons=QMessageBox.Ok,
                                                                defaultButton=QMessageBox.Ok)
                                    return
                                uf2 = firmware.read()
                                data, address = self.parse_uf2(uf2)
                                self.upload_firmware(data, address)
                    else:
                        if sys.platform == "emscripten":
                            self.firmware_check_btn.setText(tr("Misc", "Already Latest/已经是最新版本"))
                        else:
                            button = QMessageBox.warning(None, "Firmware",
                                                    "No new firmware available./目前已经是最新版",
                                                    buttons=QMessageBox.Ok,
                                                    defaultButton=QMessageBox.Ok)
                    break



    def on_load_firmware(self):
        firmware_file, firmware_file_type = QFileDialog.getOpenFileName(None, "Select Firmware/选择固件", os.getcwd(), "Firmware Files (*.uf2)")
        if firmware_file is None or firmware_file == "":
            return
        
        if not os.path.exists(firmware_file):
            return

        #print(firmware_file)
        with open(firmware_file, "rb") as fp:
            uf2 = fp.read()
            data, address = self.parse_uf2(uf2)
            if data is not None:
                self.upload_firmware(data, address)

    def on_upload_reset(self):
        if self.current_firmware_data is None:
            return

        self.upload_bar.setRange(0, len(self.current_firmware_data))
        self.upload_bar.setValue(0)

        self.keyboard.firmware_prepare()

        self.current_firmware_offset = 0
        self.timer.start(5)
        self.upload_btn.setEnabled(False)

    def upload_firmware_period(self):
        offset = self.current_firmware_offset
        data = self.current_firmware_data

        if offset < len(data):
            size = 24 if len(data) - offset >= 24 else len(data) - offset

            try:
                result = self.keyboard.firmware_upload(offset, data[offset:offset+size])
                self.upload_bar.setValue(offset)
            except (RuntimeError, ValueError):
                self.timer.stop()
                return
            
            if not result:
                self.timer.stop()
                print("Failed to upload firmware")
                return 

            self.current_firmware_offset = offset = offset + size

        else:
            self.timer.stop()
            self.upload_bar.setValue(offset)

            self.keyboard.firmware_finish()
            self.keyboard.firmware_reset()

            self.firmware_check_btn.setText(tr("Misc", "Check update/检查更新"))
            self.current_firmware_data = None
            if sys.platform == "emscripten":
                import vialglue
                vialglue.reload_keyboard()

#esp32 command 
    def on_esp32_main_cbx(self):
        pass

    def on_esp32_sub_cbx(self):
        pass

    def on_esp32_type_cbx(self):
        pass

    def on_esp32_param_text(self):
        pass

#esp32 wifi
    def on_esp32_apply_btn(self):
        main = self.esp32_main_cbx.currentIndex()
        wifi = self.esp32_wifi_cbx.currentIndex()
        cmd_type = self.esp32_type_cbx.currentIndex()
        param = self.esp32_param_edt.text()
        self.keyboard.apply_esp32_command(main, wifi, cmd_type, param)

    def on_wifi_scan_btn(self):
        if not self.keyboard.amk_esp32_state["ready"]:
            print("ESP32 not ready")
            return
        
        # list available APs, main=wifi, cmd = CWLAP, type=execute
        COMMAND_MAIN = 1
        COMMAND_WIFI = 7
        COMMAND_TYPE = 3
        self.keyboard.apply_esp32_command(COMMAND_MAIN, COMMAND_WIFI, COMMAND_TYPE,"")
        self.wifi_scanning = True 
        self.wifi_scan_btn.setEnabled(False)
        self.wifi_scan_timeout = 0
        self.keyboard.amk_esp32_state["ssid_count"] = 0

    def on_wifi_conn_btn(self):
        if not self.keyboard.amk_esp32_state["ready"]:
            print("ESP32 not ready")
            return
        
        if self.wifi_state == WIFI_STATE_CONNECTING:
            print("ESP32 already start connecting")
            return
        
        if self.wifi_state == WIFI_STATE_CONNECTED:
            # disconnect from AP
            self.keyboard.apply_esp32_oper(ESP32_DISCONNECT, {})
            self.wifi_state = WIFI_STATE_IDLE
            self.wifi_conn_btn.setText(WIFI_CONNECT_TEXT)
        else:
            ssid = self.wifi_ap_lst.currentRow()
            if ssid == -1:
                ssid = 0
            password = self.wifi_pass_edt.text().strip()
            self.keyboard.apply_esp32_oper(ESP32_CONNECT, {"index": ssid, "password": password})
            self.wifi_state = WIFI_STATE_CONNECTING
            self.wifi_connect_timeout = 0
            self.wifi_conn_btn.setEnabled(False)

    def on_wifi_ap_changed(self, row):
        pass

    def on_wifi_pass_text(self):
        pass

    def wifi_periodic_oper(self):
        self.keyboard.apply_esp32_oper(ESP32_STATE, {})

        if not self.keyboard.amk_esp32_state["ready"]:
            return

        if self.wifi_scanning:
            if self.keyboard.amk_esp32_state["ssid_count"] > 0:
                self.wifi_ap_lst.blockSignals(True)
                self.wifi_ap_lst.clear()
                for i in range(self.keyboard.amk_esp32_state["ssid_count"]):
                    self.keyboard.apply_esp32_oper(ESP32_GET_SSID, {"index": i})

                for i in range(self.keyboard.amk_esp32_state["ssid_count"]):
                    self.wifi_ap_lst.addItem(self.keyboard.amk_esp32_state["ssid_list"][i])

                self.wifi_ap_lst.blockSignals(False)
                self.wifi_scanning = False
                self.wifi_scan_timeout = 0
                self.wifi_scan_btn.setEnabled(True)
                self.wifi_state = WIFI_STATE_IDLE
            else:
                self.wifi_scan_timeout = self.wifi_scan_timeout + 1
                if self.wifi_scan_timeout >= WIFI_SCAN_TIMEOUT:
                    print("ESP32 WiFi scan timeout, reset to idle")
                    self.wifi_scanning = False
                    self.wifi_scan_timeout = 0
                    self.wifi_scan_btn.setEnabled(True)
                    self.wifi_state = WIFI_STATE_IDLE
                else:
                    self.keyboard.apply_esp32_oper(ESP32_GET_SSID, {"index": 0xFF})

        if self.wifi_state == WIFI_STATE_IDLE:
            if self.keyboard.amk_esp32_state["connected"]:
                print("ESP32 WiFi connected")
                self.wifi_state = WIFI_STATE_CONNECTED
                self.wifi_conn_btn.setText(WIFI_DISCONNECT_TEXT)
            return
        
        if self.wifi_state == WIFI_STATE_CONNECTED:
            if not self.keyboard.amk_esp32_state["connected"]:
                print("ESP32 WiFi disconnected")
                self.wifi_state = WIFI_STATE_IDLE
                self.wifi_conn_btn.setText(WIFI_CONNECT_TEXT)
            return

        if self.wifi_state == WIFI_STATE_CONNECTING:
            if self.keyboard.amk_esp32_state["connected"]:
                self.wifi_state = WIFI_STATE_CONNECTED
                self.wifi_conn_btn.setText(WIFI_DISCONNECT_TEXT)
            else:
                self.wifi_connect_timeout = self.wifi_connect_timeout + 1
                if self.wifi_connect_timeout >= WIFI_CONNECT_TIMEOUT:
                    print("ESP32 WiFi connect timeout, reset to idle")
                    self.wifi_state = WIFI_STATE_IDLE
                    self.wifi_connect_timeout = 0
                    self.wifi_conn_btn.setEnabled(True)
        