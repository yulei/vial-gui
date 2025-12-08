# SPDX-License-Identifier: GPL-2.0-or-later
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPalette, QColor

import math

from editor.basic_editor import BasicEditor
from protocol.constants import VIAL_PROTOCOL_MATRIX_TESTER
from widgets.keyboard_widget import KeyboardWidget
from util import tr
from vial_device import VialKeyboard
from unlocker import Unlocker
from amk.widget import AmkWidget


def stroke_display(widget, depth, on):
    #print("Current stroke={}, depth={}".format(stroke, depth))
    stroke_text = "{:.2f}".format(depth/100.0)
    stroke_color = QColor.fromRgb(255, 255, 255)
    if on:
        stroke_color = QColor.fromRgb(255,191,0)
    stroke_depth = depth/400.0

    widget.stroke = True
    widget.stroke_text = stroke_text
    widget.stroke_depth = stroke_depth
    widget.stroke_color = stroke_color

class Calibrate(BasicEditor):

    def __init__(self, layout_editor):
        super().__init__()

        self.layout_editor = layout_editor

        self.keyboardWidget = AmkWidget(layout_editor)
        self.keyboardWidget.set_enabled(False)

        layout = QVBoxLayout()
        layout.addWidget(self.keyboardWidget)
        layout.setAlignment(self.keyboardWidget, Qt.AlignCenter)

        self.addLayout(layout)

        self.keyboard = None
        self.device = None
        self.polling = False

        self.timer = QTimer()
        self.timer.timeout.connect(self.on_switch_state_poller)

        self.grabber = QWidget()

    def rebuild(self, device):
        super().rebuild(device)
        if self.valid():
            self.keyboard = device.keyboard

            self.keyboardWidget.set_keys(self.keyboard.keys, self.keyboard.encoders)
        self.keyboardWidget.setEnabled(self.valid())

    def valid(self):
        # Check if vial protocol is v3 or later
        return isinstance(self.device, VialKeyboard) and \
               (self.device.keyboard and self.device.keyboard.vial_protocol >= VIAL_PROTOCOL_MATRIX_TESTER) and \
               ((self.device.keyboard.cols // 8 + 1) * self.device.keyboard.rows <= 28) and \
               (self.device.keyboard.amk_feature["calibrate"])

    def reset_keyboard_widget(self):
        # reset keyboard widget
        for w in self.keyboardWidget.widgets:
            w.setPressed(False)
            w.setOn(False)

        self.keyboardWidget.update_layout()
        self.keyboardWidget.update()
        self.keyboardWidget.updateGeometry()

    def activate(self):
        self.grabber.grabKeyboard()

        if self.keyboard.amk_featuer["switch_state"]:
            self.timer.start(50)

    def deactivate(self):
        self.grabber.releaseKeyboard()

        if self.keyboard.amk_featuer["switch_state"]:
            self.timer.stop()

    def get_switch_state(self, row, col):
        if len(self.keyboard.amk_switch_states) == 0:
            return

        for state in self.keyboard.amk_switch_states:
            if state.row == row and state.col == col:
                return state 

        return None

    def update_key_state(self):
        for widget in self.keyboardWidget.widgets:
            state = self.get_switch_state(widget.desc.row, widget.desc.col)
            if state is None:
                widget.stroke = False
            else:
                stroke_display(widget, state.get_stroke(), state.get_on())

        self.keyboardWidget.update()

    def on_switch_state_poller(self):
        if not self.valid():
            self.timer.stop()
            return

        try:
            self.keyboard.reload_switch_state()
        except (RuntimeError, ValueError):
            self.timer.stop()
            return

        self.update_key_state()