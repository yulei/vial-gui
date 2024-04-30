# SPDX-License-Identifier: GPL-2.0-or-later
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton, QCheckBox, QColorDialog
from PyQt5.QtCore import Qt

from PyQt5.QtGui import QPainter, QColor, QPainterPath, QTransform, QBrush, QPolygonF, QPalette
from PyQt5.QtWidgets import QApplication

from themes import Theme

from editor.basic_editor import BasicEditor
from amk.widget import ClickableWidget, AmkWidget
from util import tr
from vial_device import VialKeyboard

def rgb_display(widget, is_custom, led):
    apc_text =""
    widget.setMaskColor(None)

    if (led is not None) and is_custom and led.get_on():
        color = QColor.fromHsvF(led.get_hue()/255.0, led.get_sat()/255.0, led.get_val()/255.0)
        dynamic = "\u2b12" if led.get_dynamic() else " "
        blink = "\u2b16" if led.get_blink() else " "
        breath = "\u2b14" if led.get_breath() else " "
        speed = "\u2942{}".format(led.get_speed())
        apc_text = "{}{}{}{}".format(dynamic, blink, breath, speed)
        widget.setMaskColor(color)

    widget.setText(apc_text)

class RgbWidget(AmkWidget):
    def __init__(self, layout_editor, editor):
        super().__init__(layout_editor)
        self.editor = editor 

    def paintEvent(self, event):
        super().paintEvent(event)
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing)

        for idx, key in enumerate(self.widgets):
            led = self.editor.keyboard.get_rgb_matrix_led(key.desc.row, key.desc.col)

            if led and led.get_on():
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

class RgbMatrix(BasicEditor):
    def __init__(self, layout_editor):
        super().__init__()

        self.layout_editor = layout_editor
        self.keyboard = None
        self.device = None
        self.custom_mode = False

        self.keyboardWidget = RgbWidget(layout_editor, self)
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
        self.custom_cbx = QCheckBox("Custom Mode")
        self.custom_cbx.setTristate(False)
        self.custom_cbx.setEnabled(True)
        self.custom_cbx.stateChanged.connect(self.on_custom_check)
        layout.addWidget(self.custom_cbx)
        layout.addStretch(1)
        self.color_btn = QPushButton("Color...")
        self.color_btn.clicked.connect(self.on_color_btn_clicked)
        layout.addWidget(self.color_btn)
        self.on_cbx = QCheckBox("Toggle On")
        self.on_cbx.stateChanged.connect(self.on_state_check)
        layout.addWidget(self.on_cbx)
        self.dynamic_cbx = QCheckBox("Toggle Dynamic")
        self.dynamic_cbx.stateChanged.connect(self.on_dynamic_check)
        layout.addWidget(self.dynamic_cbx)
        self.blink_cbx = QCheckBox("Toggle Blink")
        self.blink_cbx.stateChanged.connect(self.on_blink_check)
        layout.addWidget(self.blink_cbx)
        self.breath_cbx = QCheckBox("Toggle Breath")
        self.breath_cbx.stateChanged.connect(self.on_breath_check)
        layout.addWidget(self.breath_cbx)
        lyt = QHBoxLayout()
        lyt.addWidget(QLabel("Speed"))
        self.speed_sld = QSlider(Qt.Horizontal)
        self.speed_sld.setMaximumWidth(300)
        self.speed_sld.setMinimumWidth(200)
        self.speed_sld.setRange(0, 15)
        self.speed_sld.setSingleStep(1)
        self.speed_sld.setValue(8)
        self.speed_sld.setTickPosition(QSlider.TicksAbove)
        self.speed_sld.setTracking(False)
        self.speed_sld.valueChanged.connect(self.on_speed_sld) 
        lyt.addWidget(self.speed_sld)
        layout.addLayout(lyt)
        layout.addStretch(3)
        h_layout.addLayout(layout)
        h_layout.addStretch(1)

        self.addLayout(h_layout)

    def rebuild(self, device):
        super().rebuild(device)
        if self.valid():
            self.keyboard = device.keyboard
            self.keyboardWidget.set_keys(self.keyboard.keys, self.keyboard.encoders)
            self.keyboardWidget.setEnabled(True)
            self.reset_keyboard_widget()

    def valid(self):
        return isinstance(self.device, VialKeyboard) and \
               (self.device.keyboard and len(self.device.keyboard.amk_rgb_matrix) > 0)

    def reset_keyboard_widget(self):
        if self.valid():
            if self.keyboard.amk_rgb_matrix["mode"]["current"] == self.keyboard.amk_rgb_matrix["mode"]["custom"]:
                self.custom_cbx.setCheckState(Qt.Checked)

            self.keyboardWidget.update_layout()
            for widget in self.keyboardWidget.widgets:
                widget.masked = True
                led = self.keyboard.get_rgb_matrix_led(widget.desc.row, widget.desc.col)
                rgb_display(widget, self.is_custom_mode(), led)

                widget.setOn(False)

            self.keyboardWidget.update()
            self.keyboardWidget.updateGeometry()

    def activate(self):
        if self.valid():
            self.reset_keyboard_widget()

    def deactivate(self):
        pass
    
    def on_empty_space_clicked(self):
        self.keyboardWidget.clear_active_keys()
        self.keyboardWidget.update()

    def on_key_clicked(self):
        if not self.keyboardWidget.active_keys:
            return

        if self.custom_cbx.checkState() != Qt.Checked:
            return

        key = list(self.keyboardWidget.active_keys.values())[0]
        led = self.keyboard.get_rgb_matrix_led(key.desc.row, key.desc.col)
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

    def is_custom_mode(self):
        return self.custom_cbx.checkState() == Qt.Checked

    def on_custom_check(self):
        if self.custom_cbx.checkState() == Qt.Checked:
            self.keyboard.apply_rgb_matrix_mode(0, self.keyboard.amk_rgb_matrix["mode"]["custom"])
        else:
            if self.keyboard.amk_rgb_matrix["mode"]["current"] != self.keyboard.amk_rgb_matrix["mode"]["custom"]:
                self.keyboard.apply_rgb_matrix_mode(0, self.keyboard.amk_rgb_matrix["mode"]["current"])
            else:
                self.keyboard.apply_rgb_matrix_mode(0, self.keyboard.amk_rgb_matrix["mode"]["default"])
            
        for widget in self.keyboardWidget.widgets:
            widget.masked = True
            led = self.keyboard.get_rgb_matrix_led(widget.desc.row, widget.desc.col)
            rgb_display(widget, self.is_custom_mode(), led)

            widget.setOn(False)

        self.keyboardWidget.update()

    def on_color_btn_clicked(self):
        self.dlg_color = QColorDialog()
        self.dlg_color.setModal(True)
        self.dlg_color.finished.connect(self.on_color_selected)
        self.dlg_color.show()

    def on_color_selected(self):
        color = self.dlg_color.selectedColor()
        if not color.isValid():
            return

        h, s, v, a = color.getHsvF()
        if h < 0:
            h = 0

        hue = int(255*h)
        sat = int(255*s)
        val = int(255*v)

        for idx, key in self.keyboardWidget.active_keys.items():
            index = self.keyboard.get_rgb_matrix_led_index(key.desc.row, key.desc.col)
            led = self.keyboard.get_rgb_matrix_led(key.desc.row, key.desc.col)
            if led is not None:
                led.set_hue(hue)
                led.set_sat(sat)
                led.set_val(val)
                self.keyboard.apply_rgb_matrix_led(index, led)
                rgb_display(key, self.is_custom_mode(), led)

        self.keyboardWidget.update()


    def on_state_check(self):
        for idx, key in self.keyboardWidget.active_keys.items():
            index = self.keyboard.get_rgb_matrix_led_index(key.desc.row, key.desc.col)
            led = self.keyboard.get_rgb_matrix_led(key.desc.row, key.desc.col)
            if led is not None:
                on = not led.get_on()
                led.set_on(on)
                self.keyboard.apply_rgb_matrix_led(index, led)
                rgb_display(key, self.is_custom_mode(), led)

        self.keyboardWidget.update()

    def on_dynamic_check(self):
        for idx, key in self.keyboardWidget.active_keys.items():
            index = self.keyboard.get_rgb_matrix_led_index(key.desc.row, key.desc.col)
            led = self.keyboard.get_rgb_matrix_led(key.desc.row, key.desc.col)
            if led is not None:
                dynamic = not led.get_dynamic()
                led.set_dynamic(dynamic)
                self.keyboard.apply_rgb_matrix_led(index, led)
                rgb_display(key, self.is_custom_mode(), led)

        self.keyboardWidget.update()

    def on_blink_check(self):
        for idx, key in self.keyboardWidget.active_keys.items():
            index = self.keyboard.get_rgb_matrix_led_index(key.desc.row, key.desc.col)
            led = self.keyboard.get_rgb_matrix_led(key.desc.row, key.desc.col)
            if led is not None:
                blink = not led.get_blink()
                led.set_blink(blink)
                self.keyboard.apply_rgb_matrix_led(index, led)
                rgb_display(key, self.is_custom_mode(), led)

        self.keyboardWidget.update()

    def on_breath_check(self):
        for idx, key in self.keyboardWidget.active_keys.items():
            index = self.keyboard.get_rgb_matrix_led_index(key.desc.row, key.desc.col)
            led = self.keyboard.get_rgb_matrix_led(key.desc.row, key.desc.col)
            if led is not None:
                breath = not led.get_breath()
                led.set_breath(breath)
                self.keyboard.apply_rgb_matrix_led(index, led)
                rgb_display(key, self.is_custom_mode(), led)

        self.keyboardWidget.update()

    def on_speed_sld(self):
        for idx, key in self.keyboardWidget.active_keys.items():
            index = self.keyboard.get_rgb_matrix_led_index(key.desc.row, key.desc.col)
            led = self.keyboard.get_rgb_matrix_led(key.desc.row, key.desc.col)
            if led is not None:
                speed = self.speed_sld.value()
                led.set_speed(speed)
                self.keyboard.apply_rgb_matrix_led(index, led)
                rgb_display(key, self.is_custom_mode(), led)

        self.keyboardWidget.update()
