# SPDX-License-Identifier: GPL-2.0-or-later
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton, QCheckBox, QColorDialog, QListWidget, QLineEdit, QComboBox
from PyQt5.QtCore import Qt, QTimer

from PyQt5.QtGui import QPainter, QColor, QBrush, QPalette
from PyQt5.QtWidgets import QApplication

from editor.basic_editor import BasicEditor
from amk.widget import ClickableWidget, AmkWidget
from util import tr
from vial_device import VialKeyboard
from amk.protocol import RGB_PARAM_COLOR, RGB_PARAM_SPEED, RGB_TYPE_GRID, GRID_TEXT_MAX, RgbColor

GRID_TEXT_MASK = "x" * GRID_TEXT_MAX

def rgb_display(widget, is_custom, color, led = None):
    apc_text =""
    widget.setMaskColor(None)

    if is_custom:
        if led is not None and led.get_on():
            dynamic = "\u2b12" if led.get_dynamic() else " "
            blink = "\u2b16" if led.get_blink() else " "
            breath = "\u2b14" if led.get_breath() else " "
            speed = "\u2942{}".format(led.get_speed())
            apc_text = "{}{}{}{}".format(dynamic, blink, breath, speed)

    led_color = QColor.fromRgbF(color.get_red()/255.0, color.get_green()/255.0, color.get_blue()/255.0)
    widget.setMaskColor(led_color)
    widget.setText(apc_text)

class RgbGridWidget(AmkWidget):
    def __init__(self, layout_editor, editor):
        super().__init__(layout_editor)
        self.editor = editor 

    def paintEvent(self, event):
        super().paintEvent(event)
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing)

        for idx, key in enumerate(self.widgets):
            #led = self.editor.keyboard.get_rgb_matrix_led_by_index(key.desc.col)
            #index = self.editor.get_led_index(key.desc.row, key.desc.col)
            #led = self.editor.keyboard.amk_rgb_grid["leds"][index]

            qp.save()

            qp.scale(self.scale, self.scale)
            qp.translate(key.shift_x, key.shift_y)
            qp.translate(key.rotation_x, key.rotation_y)
            qp.rotate(key.rotation_angle)
            qp.translate(-key.rotation_x, -key.rotation_y)

            qp.setPen(Qt.NoPen)
            color_brush = QBrush()
            color_brush.setColor(key.mask_color if key.mask_color else QApplication.palette().color(QPalette.Button).lighter(120))
            color_brush.setStyle(Qt.SolidPattern)
            qp.setBrush(color_brush)
            qp.drawRoundedRect(key.mask_rect, key.corner, key.corner)

            qp.restore()

        qp.end()

class RgbGrid(BasicEditor):
    def __init__(self, layout_editor):
        super().__init__()

        self.layout_editor = layout_editor
        self.keyboard = None
        self.device = None
        self.grid = -1
        self.mode = -1
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_rgb_grid_poller)

        self.keyboardWidget = RgbGridWidget(layout_editor, self)
        self.keyboardWidget.set_enabled(True)
        self.keyboardWidget.clicked.connect(self.on_key_clicked)

        layout = QVBoxLayout()
        layout.addWidget(self.keyboardWidget)
        layout.setAlignment(self.keyboardWidget, Qt.AlignCenter)
        w = ClickableWidget()
        w.setLayout(layout)
        w.clicked.connect(self.on_empty_space_clicked)

        h_layout = QHBoxLayout()
        h_layout.addStretch(1)
        h_layout.addWidget(w)
        h_layout.addStretch(1)

        layout = QVBoxLayout()
        layout.addStretch(3)
        lyt = QHBoxLayout()
        vv = QVBoxLayout()
        vv.addWidget(QLabel(tr("RGB Grid", "Grids/网格:")))
        self.grid_lst = QListWidget()
        self.grid_lst.itemSelectionChanged.connect(self.on_grid_changed)
        vv.addWidget(self.grid_lst)
        lyt.addLayout(vv)
        vv = QVBoxLayout()
        vv.addWidget(QLabel(tr("RGB Grid", "Effects/灯效:")))
        self.mode_lst = QListWidget()
        self.mode_lst.itemSelectionChanged.connect(self.on_mode_changed)
        vv.addWidget(self.mode_lst)
        lyt.addLayout(vv)
        layout.addLayout(lyt)
        layout.addStretch(1)
        self.color_btn = QPushButton(tr("RGB Grid", "Color/颜色..."))
        self.color_btn.clicked.connect(self.on_color_btn_clicked)
        layout.addWidget(self.color_btn)
        self.on_cbx = QCheckBox(tr("RGB Grid", "Toggle On/切换状态"))
        self.on_cbx.stateChanged.connect(self.on_state_check)
        layout.addWidget(self.on_cbx)
        self.dynamic_cbx = QCheckBox(tr("RGB Grid", "Toggle Dynamic/切换动态效果"))
        self.dynamic_cbx.stateChanged.connect(self.on_dynamic_check)
        layout.addWidget(self.dynamic_cbx)
        self.blink_cbx = QCheckBox(tr("RGB Grid", "Toggle Blink/切换闪烁效果"))
        self.blink_cbx.stateChanged.connect(self.on_blink_check)
        layout.addWidget(self.blink_cbx)
        self.breath_cbx = QCheckBox(tr("RGB Grid", "Toggle Breath/切换呼吸效果"))
        self.breath_cbx.stateChanged.connect(self.on_breath_check)
        layout.addWidget(self.breath_cbx)
        lyt = QHBoxLayout()
        lyt.addWidget(QLabel(tr("RGB Grid", "Speed/速度")))
        self.speed_sld = QSlider(Qt.Horizontal)
        self.speed_sld.setMaximumWidth(300)
        self.speed_sld.setMinimumWidth(200)
        self.speed_sld.setRange(0, 15)
        self.speed_sld.setSingleStep(1)
        self.speed_sld.setValue(8)
        self.speed_sld.setTickPosition(QSlider.TicksAbove)
        self.speed_sld.setTracking(False)
        self.speed_sld.valueChanged.connect(self.on_speed_sld) 
        lyt.addStretch(1)
        lyt.addWidget(self.speed_sld)
        layout.addLayout(lyt)
        lyt = QHBoxLayout()
        self.text_cbx = QCheckBox(tr("RGB Grid", "Text/文字"))
        self.text_cbx.stateChanged.connect(self.on_mask_check)
        lyt.addWidget(self.text_cbx)
        self.text_edt = QLineEdit()
        self.text_edt.setInputMask(GRID_TEXT_MASK)
        self.text_edt.setMaxLength(GRID_TEXT_MAX)
        self.text_edt.editingFinished.connect(self.on_mask_text)
        lyt.addStretch(1)
        lyt.addWidget(self.text_edt)
        self.text_rotation_cbb = QComboBox()
        self.text_rotation_cbb.addItems(["roate/旋转 0", "rotate/旋转 90", "rotate/旋转 180", "rotate/旋转 270"])
        self.text_rotation_cbb.currentIndexChanged.connect(self.on_mask_rotation)
        lyt.addWidget(self.text_rotation_cbb)
        self.text_mode_cbb = QComboBox()
        self.text_mode_cbb.addItems(["static/静态"])
        self.text_mode_cbb.currentIndexChanged.connect(self.on_mask_mode)
        lyt.addWidget(self.text_mode_cbb)
        layout.addLayout(lyt)
        layout.addStretch(3)
        h_layout.addLayout(layout)
        h_layout.addStretch(1)

        self.addLayout(h_layout)

    def rebuild(self, device):
        super().rebuild(device)
        if self.valid():
            self.keyboard = device.keyboard
            self.keyboardWidget.set_keys(self.keyboard.amk_rgb_grid["layout"], [])
            self.keyboardWidget.setEnabled(True)
            self.reset_keyboard_widget()

    def valid(self):
        return isinstance(self.device, VialKeyboard) and \
               (self.device.keyboard and len(self.device.keyboard.amk_rgb_grid) > 0)

    def reset_mode_widgets(self):
        if self.is_custom_mode(self.grid):
            self.on_cbx.setEnabled(True)
            self.dynamic_cbx.setEnabled(True)
            self.blink_cbx.setEnabled(True)
            self.breath_cbx.setEnabled(True)
        else:
            self.on_cbx.setEnabled(False)
            self.dynamic_cbx.setEnabled(False)
            self.blink_cbx.setEnabled(False)
            self.breath_cbx.setEnabled(False)

    def reset_grid_mask(self):
        cur = self.grid_lst.currentRow()
        if cur == -1:
            cur = 0

        #print(self.keyboard.amk_rgb_grid["grids"][cur])

        if self.keyboard.amk_rgb_grid["grids"][cur]["mask"] > 0:
            self.text_cbx.setEnabled(True)
            self.text_edt.setEnabled(True)
            self.text_cbx.setChecked(True if self.keyboard.amk_rgb_grid["grids"][cur]["mask_enable"] > 0 else False)
            self.text_edt.setText(self.keyboard.amk_rgb_grid["grids"][cur]["mask_text"])
            self.text_rotation_cbb.setCurrentIndex(self.keyboard.amk_rgb_grid["grids"][cur]["mask_rotation"])
            self.text_mode_cbb.setCurrentIndex(self.keyboard.amk_rgb_grid["grids"][cur]["mask_mode"])
        else:
            self.text_cbx.setEnabled(False)
            self.text_edt.setEnabled(False)

    def reset_keyboard_widget(self):
        if self.valid():
            self.grid_lst.clear()
            for grid in self.keyboard.amk_rgb_grid["grids"]:
                self.grid_lst.addItem(grid["name"])
            self.grid_lst.setCurrentRow(0)
            self.grid = 0

            self.reset_grid_mask()

            self.mode_lst.clear()
            for effect in self.keyboard.amk_rgb_grid["effects"]:
                self.mode_lst.addItem(effect)

            self.keyboardWidget.update_layout()
            for widget in self.keyboardWidget.widgets:
                widget.masked = True
                widget.setOn(False)

            self.reset_mode_widgets()
            self.keyboardWidget.update()
            self.keyboardWidget.updateGeometry()

    def activate(self):
        if self.valid():
            self.reset_keyboard_widget()
            self.timer.start(50)

    def deactivate(self):
        self.timer.stop()
    
    def on_empty_space_clicked(self):
        self.keyboardWidget.clear_active_keys()
        self.keyboardWidget.update()

    def on_key_clicked(self):
        if not self.keyboardWidget.active_keys:
            return

        key = list(self.keyboardWidget.active_keys.values())[0]
        if not self.is_custom_mode(key.desc.row):
            return

        color, led = self.get_led(key.desc.row, key.desc.col)
        if led is None:
            return
        
        self.on_cbx.blockSignals(True)
        self.dynamic_cbx.blockSignals(True)
        self.blink_cbx.blockSignals(True)
        self.breath_cbx.blockSignals(True)
        self.speed_sld.blockSignals(True)

        self.on_cbx.setCheckState(Qt.Checked if led.get_on() else Qt.Unchecked)
        self.dynamic_cbx.setCheckState(Qt.Checked if led.get_dynamic() else Qt.Unchecked)
        self.blink_cbx.setCheckState(Qt.Checked if led.get_blink() else Qt.Unchecked)
        self.breath_cbx.setCheckState(Qt.Checked if led.get_breath() else Qt.Unchecked)
        self.speed_sld.setValue(led.get_speed())
        
        self.speed_sld.blockSignals(False)
        self.breath_cbx.blockSignals(False)
        self.blink_cbx.blockSignals(False)
        self.dynamic_cbx.blockSignals(False)
        self.on_cbx.blockSignals(False)

    def is_custom_mode(self, grid):
        if grid == -1 or grid >= len(self.keyboard.amk_rgb_grid["grids"]):
            return False
        
        return self.keyboard.amk_rgb_grid["grids"][grid]["mode"] == self.keyboard.amk_rgb_grid["effects"].index("Custom") 

    def on_color_btn_clicked(self):
        self.dlg_color = QColorDialog()
        self.dlg_color.setModal(True)
        self.dlg_color.finished.connect(self.on_color_selected)
        self.dlg_color.show()

    def on_color_selected(self):
        if self.grid == -1 or self.grid >= len(self.keyboard.amk_rgb_grid["grids"]):
            return

        color = self.dlg_color.selectedColor()
        if not color.isValid():
            return

        if self.is_custom_mode(self.grid):
            h, s, v, a = color.getHsvF()
            if h < 0:
                h = 0

            hue = int(255*h)
            sat = int(255*s)
            val = int(255*v)

            for idx, key in self.keyboardWidget.active_keys.items():
                if key.desc.row == self.grid:
                    index = self.get_led_index(key.desc.row, key.desc.col)
                    led = self.keyboard.amk_rgb_grid["leds"][index]
                    led.set_hue(hue)
                    led.set_sat(sat)
                    led.set_val(val)
                    self.keyboard.apply_rgb_grid_led(index, led)
        else:
            r, g, b, a = color.getRgbF()
            red = int(255*r)
            green = int(255*g)
            blue = int(255*b)
            self.keyboard.apply_rgb_param(RGB_TYPE_GRID, RGB_PARAM_COLOR, RgbColor(red, green, blue), self.grid)

        self.keyboardWidget.update()

    def on_state_check(self):
        if self.grid == -1:
            return

        if self.is_custom_mode(self.grid):
            for idx, key in self.keyboardWidget.active_keys.items():
                if key.desc.row == self.grid:
                    index = self.get_led_index(key.desc.row, key.desc.col)
                    led = self.keyboard.amk_rgb_grid["leds"][index]
                    on = not led.get_on()
                    led.set_on(on)
                    self.keyboard.apply_rgb_grid_led(index, led)

        self.keyboardWidget.update()

    def on_dynamic_check(self):
        if self.grid == -1:
            return

        if self.is_custom_mode(self.grid):
            for idx, key in self.keyboardWidget.active_keys.items():
                if key.desc.row == self.grid:
                    index = self.get_led_index(key.desc.row, key.desc.col)
                    led = self.keyboard.amk_rgb_grid["leds"][index]
                    dynamic = not led.get_dynamic()
                    led.set_dynamic(dynamic)
                    self.keyboard.apply_rgb_grid_led(index, led)

        self.keyboardWidget.update()

    def on_blink_check(self):
        if self.grid == -1:
            return

        if self.is_custom_mode(self.grid):
            for idx, key in self.keyboardWidget.active_keys.items():
                if key.desc.row == self.grid:
                    index = self.get_led_index(key.desc.row, key.desc.col)
                    led = self.keyboard.amk_rgb_grid["leds"][index]
                    blink = not led.get_blink()
                    led.set_blink(blink)
                    self.keyboard.apply_rgb_grid_led(index, led)

        self.keyboardWidget.update()

    def on_breath_check(self):
        if self.grid == -1:
            return

        if self.is_custom_mode(self.grid):
            for idx, key in self.keyboardWidget.active_keys.items():
                if key.desc.row == self.grid:
                    index = self.get_led_index(key.desc.row, key.desc.col)
                    led = self.keyboard.amk_rgb_grid["leds"][index]
                    breath = not led.get_breath()
                    led.set_breath(breath)
                    self.keyboard.apply_rgb_grid_led(index, led)

        self.keyboardWidget.update()

    def on_speed_sld(self):
        if self.grid == -1:
            return

        if self.is_custom_mode(self.grid):
            for idx, key in self.keyboardWidget.active_keys.items():
                if key.desc.row == self.grid:
                    index = self.get_led_index(key.desc.row, key.desc.col)
                    led = self.keyboard.amk_rgb_grid["leds"][index]
                    if (led.get_speed() != self.speed_sld.value()):
                        led.set_speed(self.speed_sld.value())
                        self.keyboard.apply_rgb_grid_led(index, led)
        else:
            speed = (self.speed_sld.value() * 255) // self.speed_sld.maximum()
            self.keyboard.apply_rgb_param(RGB_TYPE_GRID, RGB_PARAM_SPEED, speed, self.grid)

        self.keyboardWidget.update()

    def get_led_index(self, grid, offset):
        if grid >= len(self.keyboard.amk_rgb_grid["grids"]):
            return None
        
        if offset >= self.keyboard.amk_rgb_grid["grids"][grid]["count"]:
            return None

        index = self.keyboard.amk_rgb_grid["start"] + self.keyboard.amk_rgb_grid["grids"][grid]["start"] + offset
        return index 

    def get_led(self, grid, offset):
        color = RgbColor(0,0,0)
        index = self.get_led_index(grid, offset)
        led = None
        if index is not None:
            color = self.keyboard.amk_rgb_data[index]
            if self.is_custom_mode(grid):
                led = self.keyboard.amk_rgb_grid["leds"][index]

        return color, led
    
    def on_rgb_grid_poller(self):
        if not self.valid():
            self.timer.stop()
            return
        try:
            self.keyboard.reload_rgb_leds(self.keyboard.amk_rgb_grid["start"], self.keyboard.amk_rgb_grid["count"])
        except (RuntimeError, ValueError):
            self.timer.stop()
            return

        for widget in self.keyboardWidget.widgets:
            color, led = self.get_led(widget.desc.row, widget.desc.col)
            rgb_display(widget, self.is_custom_mode(widget.desc.row), color, led)

        self.keyboardWidget.update()

    def on_grid_changed(self):
        cur = self.grid_lst.currentRow()
        if cur == -1:
            return

        self.grid = cur
        self.mode = self.keyboard.amk_rgb_grid["grids"][cur]["mode"]
        self.mode_lst.setCurrentRow(self.mode)

        self.reset_grid_mask()

    def on_mode_changed(self):
        cur = self.mode_lst.currentRow()
        if cur == -1:
            return

        if self.grid == -1:
            self.grid = 0

        self.keyboard.apply_rgb_grid_mode(self.grid, cur)
        self.mode = cur
        self.reset_mode_widgets()

    def grid_mask_update(self):
        if self.grid == -1:
            self.grid = 0

        enabled = self.text_cbx.isChecked()
        text = self.text_edt.text().strip()

        rotation = self.text_rotation_cbb.currentIndex()
        mode = self.text_mode_cbb.currentIndex()

        self.keyboard.apply_grid_mask(self.grid, enabled, text, rotation, mode)
        #print("enabled: {}, text: {}, rotation: {}, mode: {}".format(enabled, text, rotation, mode))

    def on_mask_check(self):
        self.grid_mask_update()

    def on_mask_text(self):
        self.grid_mask_update()

    def on_mask_rotation(self):
        self.grid_mask_update()

    def on_mask_mode(self):
        self.grid_mask_update()
