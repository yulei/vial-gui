from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QHBoxLayout, QGridLayout, QSlider, QLabel, QCheckBox, QMessageBox, QColorDialog
from PyQt5.QtCore import QSize, Qt, QRect
from PyQt5.QtGui import QPalette, QPainter, QBrush, QColor
from PyQt5.QtWidgets import QApplication

from themes import Theme

from editor.basic_editor import BasicEditor
from editor.keymap_editor import ClickableWidget

from util import tr
from vial_device import VialKeyboard

RL_EFFECT_CUSTOM = 0
RL_EFFECT_GRADIENT = 1
RL_EFFECT_STATIC = 2
RL_EFFECT_BLINK = 3
RL_EFFECT_RAINBOW = 4
RL_EFFECT_RANDOM = 5
RL_EFFECT_BREATH = 6
RL_EFFECT_WIPE = 7
RL_EFFECT_SCAN = 7
RL_EFFECT_CIRCLE = 8

def rgb_to_xyz(red, green, blue):
    r = red/255.0
    g = green/255.0
    b = blue/255.0

    r = pow(((r + 0.055) / 1.055), 2.4) * 100.0 if r > 0.04045 else r / 12.92
    g = pow(((g + 0.055) / 1.055), 2.4) * 100.0 if g > 0.04045 else g / 12.92
    b = pow(((b + 0.055) / 1.055), 2.4) * 100.0 if b > 0.04045 else b / 12.92

    x = r * 0.4124 + g * 0.3576 + b * 0.1805
    y = r * 0.2126 + g * 0.7152 + b * 0.0722
    z = r * 0.0193 + g * 0.1192 + b * 0.9505

    return (x,y,z)

def xyz_to_xy(x, y, z):
    res_x = x / (x+y+z)
    res_y = y / (x+y+z)
    return (res_x, res_y)

def xy_to_pwm(x, y):
    x_r = 0.69
    y_r = 0.31
    mcd_r = 50

    x_g = 0.19
    y_g = 0.61
    mcd_g = 150

    x_b = 0.153
    y_b = 0.0278
    mcd_b = 50

    y_m = 50

    d_r = ((y_g-y_b)*(x_b-x)+(y-y_b)*(x_g-x_b)) / ((y_g-y_b)*(x_b-x_r)+(y_r-y_b)*(x_g-x_b)) *(y_r*y_m) / (y*mcd_r)
    d_g = ((y_b-y_r)*(x_r-x)+(y-y_r)*(x_b-x_r)) / ((y_b-y_r)*(x_r-x_g)+(y_g-y_r)*(x_b-x_r)) *(y_g*y_m) / (y*mcd_g)
    d_b = ((y_g-y_r)*(x_r-x)+(y-y_r)*(x_g-x_r)) / ((y_g-y_r)*(x_r-x_b)+(y_b-y_r)*(x_g-x_r)) *(y_b*y_m) / (y*mcd_b)

    max_d = max([d_r,d_g,d_b])

    d_r = int(255*(abs(d_r/max_d)))
    d_g = int(255*(abs(d_g/max_d)))
    d_b = int(255*(abs(d_b/max_d)))

    return (d_r, d_g, d_b)

def adjust_color(color):
    r,g,b,_ = color.getRgb()

    x,y,z = rgb_to_xyz(r, g, b)

    x_x, y_y = xyz_to_xy(x, y, z)

    p_r, p_g, p_b = xy_to_pwm(x_x, y_y)

    color.setRgb(p_r, p_g, p_b)

    #print(r, g, b)
    #print(p_r, p_g, p_b)

    return color

class RgbButton(QPushButton):

    def __init__(self, strip, index, parent=None):
        super().__init__(parent)
        self.scale = 3
        self.text = ""
        self.strip = strip
        self.index = index
        self.color = QApplication.palette().color(QPalette.Button)

    def setRelSize(self, ratio):
        self.scale = ratio
        self.updateGeometry()

    def get_strip(self):
        return self.strip

    def get_index(self):
        return self.index
    
    def set_color(self, color):
        self.color = color

    def sizeHint(self):
        size = int(round(self.fontMetrics().height() * self.scale))
        return QSize(size, size)

    def mousePressEvent(self, ev):
        if not self.isEnabled():
            return
        
        self.toggle()
        self.clicked.emit()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing)

        background_brush = QBrush()
        #background_brush.setColor(QApplication.palette().color(QPalette.Button))
        background_brush.setColor(self.color)
        background_brush.setStyle(Qt.SolidPattern)

        active_pen = qp.pen()
        active_pen.setColor(QApplication.palette().color(QPalette.Highlight))
        active_pen.setWidthF(6)

        regular_pen = qp.pen()
        regular_pen.setColor(QApplication.palette().color(QPalette.Button))

        regular_brush = QBrush()
        regular_brush.setColor(QApplication.palette().color(QPalette.Button))
        regular_brush.setStyle(Qt.SolidPattern)

        # for text 
        text_pen = qp.pen()
        text_pen.setColor(QApplication.palette().color(QPalette.ButtonText))

        rect = self.rect()
        if self.isEnabled():
            if self.isChecked():
                qp.setPen(active_pen)
            else:
                qp.setPen(regular_pen)
            qp.setBrush(background_brush)
        else:
            qp.setPen(regular_pen)
            qp.setBrush(regular_brush)

        qp.drawRect(rect)

        qp.setPen(text_pen)
        qp.drawText(rect, Qt.AlignCenter, self.text)

        qp.end()

class RgbStrip(BasicEditor):
    def __init__(self):
        super().__init__()
        self.keyboard = None
        self.built = False
        i_layout = QHBoxLayout()
        i_layout.addStretch(1)
        lbl = QLabel("Num Lock: ")
        i_layout.addWidget(lbl)
        self.num_btn = RgbButton(0, 0)
        self.num_btn.setCheckable(False)
        self.num_btn.clicked.connect(self.on_num_btn_clicked)
        i_layout.addWidget(self.num_btn)
        lbl = QLabel("Caps Lock: ")
        i_layout.addWidget(lbl)
        self.caps_btn = RgbButton(0, 0)
        self.caps_btn.setCheckable(False)
        self.caps_btn.clicked.connect(self.on_caps_btn_clicked)
        i_layout.addWidget(self.caps_btn)
        lbl = QLabel("Scroll Lock: ")
        i_layout.addWidget(lbl)
        self.scroll_btn = RgbButton(0, 0)
        self.scroll_btn.setCheckable(False)
        self.scroll_btn.clicked.connect(self.on_scroll_btn_clicked)
        i_layout.addWidget(self.scroll_btn)
        lbl = QLabel("Compose: ")
        i_layout.addWidget(lbl)
        self.compose_btn = RgbButton(0, 0)
        self.compose_btn.setCheckable(False)
        self.compose_btn.clicked.connect(self.on_compose_btn_clicked)
        i_layout.addWidget(self.compose_btn)
        lbl = QLabel("Kana: ")
        i_layout.addWidget(lbl)
        self.kana_btn = RgbButton(0, 0)
        self.kana_btn.setCheckable(False)
        self.kana_btn.clicked.connect(self.on_kana_btn_clicked)
        i_layout.addWidget(self.kana_btn)
        i_layout.addStretch(1)

        self.rgb_layout = QGridLayout()
        w = ClickableWidget()
        w.setLayout(self.rgb_layout)
        w.clicked.connect(self.on_empty_space_clicked)

        h_layout = QHBoxLayout()
        h_layout.addStretch(1)
        self.color_btn = QPushButton("Color...")
        self.color_btn.clicked.connect(self.on_color_btn_clicked)
        h_layout.addWidget(self.color_btn)
        self.on_cbx = QCheckBox("Toggle On")
        self.on_cbx.stateChanged.connect(self.on_state_check)
        h_layout.addWidget(self.on_cbx)
        self.dynamic_cbx = QCheckBox("Toggle Dynamic")
        self.dynamic_cbx.stateChanged.connect(self.on_dynamic_check)
        h_layout.addWidget(self.dynamic_cbx)
        self.blink_cbx = QCheckBox("Toggle Blink")
        self.blink_cbx.stateChanged.connect(self.on_blink_check)
        h_layout.addWidget(self.blink_cbx)
        self.breath_cbx = QCheckBox("Toggle Breath")
        self.breath_cbx.stateChanged.connect(self.on_breath_check)
        h_layout.addWidget(self.breath_cbx)
        self.speed_sld = QSlider(Qt.Horizontal)
        self.speed_sld.setMaximumWidth(300)
        self.speed_sld.setMinimumWidth(200)
        self.speed_sld.setRange(0, 15)
        self.speed_sld.setSingleStep(1)
        self.speed_sld.setValue(8)
        self.speed_sld.setTickPosition(QSlider.TicksAbove)
        self.speed_sld.setTracking(False)
        self.speed_sld.valueChanged.connect(self.on_speed_sld) 
        h_layout.addWidget(self.speed_sld)
        h_layout.addWidget(QLabel("Speed"))
        h_layout.addStretch(1)


        v_layout = QVBoxLayout()
        v_layout.addStretch(1)
        v_layout.addLayout(i_layout)
        v_layout.addStretch(1)
        v_layout.addWidget(w)
        #v_layout.addStretch(1)
        v_layout.addLayout(h_layout)
        v_layout.addStretch(1)
        self.addLayout(v_layout)

    def clear_strip_ui(self):
        if self.rgb_layout is not None:
            while self.rgb_layout.count():
                item = self.rgb_layout.takeAt(0)
                if item is not None:
                    self.rgb_layout.removeItem(item)

    def rebuild_ui(self):

        self.clear_strip_ui()
        self.led_btns = []
        self.strip_modes = []

        for index in range(self.keyboard.amk_rgb_strip_count):
            lbl = QLabel(tr("strip_{}".format(index+1), "Led Strip #{}: ".format(index+1)))
            self.rgb_layout.addWidget(lbl, index, 0)
            cbx = QCheckBox("Custom Mode")
            cbx.setTristate(False)
            cbx.setEnabled(True)
            mode_custom = self.keyboard.amk_rgb_strips[index].get_mode() == RL_EFFECT_CUSTOM 
            if mode_custom:
                cbx.setCheckState(Qt.Checked)
            else:
                cbx.setCheckState(Qt.Unchecked)

            cbx.stateChanged.connect(self.on_mode_check)
            self.strip_modes.append(cbx)
            self.rgb_layout.addWidget(cbx, index, 1)
            for i in range(self.keyboard.amk_rgb_strips[index].get_count()):
                btn = RgbButton(index, i)
                btn.setCheckable(True)
                btn.setEnabled(mode_custom)
                led = self.keyboard.amk_rgb_strips[index].get_led(i)
                color = QColor.fromHsv(led.get_hue(),led.get_sat(),led.get_val(),255)
                btn.set_color(color)
                self.led_btns.append(btn)
                self.rgb_layout.addWidget(btn, index, i+2)
                self.rgb_layout.setAlignment(btn, Qt.AlignCenter)

        led = self.keyboard.rgb_indicators.get("num_lock")
        if led is not None:
            color = QColor.fromHsv(led.get_led().get_hue(),led.get_led().get_sat(),led.get_led().get_val(), 255)
            self.num_btn.set_color(color)
        self.num_btn.setEnabled(True if led is not None else False)
        led = self.keyboard.rgb_indicators.get("caps_lock")
        if led is not None:
            color = QColor.fromHsv(led.get_led().get_hue(),led.get_led().get_sat(),led.get_led().get_val(), 255)
            self.caps_btn.set_color(color)
        self.caps_btn.setEnabled(True if led is not None else False)
        led = self.keyboard.rgb_indicators.get("scroll_lock")
        if led is not None:
            color = QColor.fromHsv(led.get_led().get_hue(),led.get_led().get_sat(),led.get_led().get_val(), 255)
            self.scroll_btn.set_color(color)
        self.scroll_btn.setEnabled(True if led is not None else False)
        led = self.keyboard.rgb_indicators.get("compose")
        if led is not None:
            color = QColor.fromHsv(led.get_led().get_hue(),led.get_led().get_sat(),led.get_led().get_val(), 255)
            self.compose_btn.set_color(color)
        self.compose_btn.setEnabled(True if led is not None else False)
        led = self.keyboard.rgb_indicators.get("kana")
        if led is not None:
            color = QColor.fromHsv(led.get_led().get_hue(),led.get_led().get_sat(),led.get_led().get_val(), 255)
            self.kana_btn.set_color(color)
        self.kana_btn.setEnabled(True if led is not None else False)

    def rebuild(self, device):
        super().rebuild(device)
        if self.valid():
            self.keyboard = device.keyboard
            self.rebuild_ui()

    def valid(self):
        return isinstance(self.device, VialKeyboard) and \
               (self.device.keyboard and self.device.keyboard.lighting_amk_rgblight)

    def on_color_btn_clicked(self):
        self.dlg_color = QColorDialog()
        self.dlg_color.setModal(True)
        self.dlg_color.finished.connect(self.on_color_selected)
        #self.dlg_color.setCurrentColor(self.current_color())
        self.dlg_color.show()

    def on_color_selected(self):
        color = self.dlg_color.selectedColor()
        if not color.isValid():
            return

        
        color = adjust_color(color)

        h, s, v, a = color.getHsvF()
        if h < 0:
            h = 0

        hue = int(255*h)
        sat = int(255*s)
        val = int(255*v)

        for i in range(len(self.led_btns)):
            btn = self.led_btns[i]
            if btn.isChecked():
                led = self.keyboard.amk_rgb_strips[btn.get_strip()].get_led(btn.get_index())
                led.set_hue(hue)
                led.set_sat(sat)
                led.set_val(val)
                self.keyboard.apply_rgb_strip_led(btn.get_strip(), btn.get_index(), led)
                btn.set_color(color)
                btn.repaint()

    def enable_strip_leds(self, index, enable):
        offset = 0
        for i in range(index):
            offset = offset + self.keyboard.amk_rgb_strips[i].get_count()

        strip = self.keyboard.amk_rgb_strips[index]
        #print("strip led: ", offset, strip.get_count())
        for i in range(offset, offset + strip.get_count()):
            if not enable:
                self.led_btns[i].setChecked(False)
            self.led_btns[i].setEnabled(enable)
            #self.led_btns[i].repaint()

    def on_mode_check(self):
        for index in range(len(self.strip_modes)):
            custom_mode = self.strip_modes[index].isChecked()
            if custom_mode:
                self.enable_strip_leds(index, True)
            else:
                self.enable_strip_leds(index, False)

            mode = RL_EFFECT_CUSTOM if custom_mode else RL_EFFECT_GRADIENT
            #print("Set mode: ", mode)
            
            self.keyboard.apply_rgb_strip_mode(index, RL_EFFECT_CUSTOM if custom_mode else RL_EFFECT_GRADIENT)
    
    def on_empty_space_clicked(self):
        for btn in self.led_btns:
            btn.setChecked(False)

    def on_state_check(self):
        on = 1 if self.on_cbx.isChecked() else 0
        for i in range(len(self.led_btns)):
            btn = self.led_btns[i]
            if btn.isChecked():
                led = self.keyboard.amk_rgb_strips[btn.get_strip()].get_led(btn.get_index())
                if led.get_on() != on:
                    led.set_on(on)
                    self.keyboard.apply_rgb_strip_led(btn.get_strip(), btn.get_index(), led)

    def on_dynamic_check(self):
        dynamic = 1 if self.dynamic_cbx.isChecked() else 0
        for i in range(len(self.led_btns)):
            btn = self.led_btns[i]
            if btn.isChecked():
                led = self.keyboard.amk_rgb_strips[btn.get_strip()].get_led(btn.get_index())
                if led.get_dynamic() != dynamic:
                    led.set_dynamic(dynamic)
                    self.keyboard.apply_rgb_strip_led(btn.get_strip(), btn.get_index(), led)

    def on_blink_check(self):
        blink = 1 if self.blink_cbx.isChecked() else 0
        for i in range(len(self.led_btns)):
            btn = self.led_btns[i]
            if btn.isChecked():
                led = self.keyboard.amk_rgb_strips[btn.get_strip()].get_led(btn.get_index())
                if led.get_blink() != blink:
                    led.set_blink(blink)
                    self.keyboard.apply_rgb_strip_led(btn.get_strip(), btn.get_index(), led)

    def on_breath_check(self):
        breath = 1 if self.breath_cbx.isChecked() else 0
        for i in range(len(self.led_btns)):
            btn = self.led_btns[i]
            if btn.isChecked():
                led = self.keyboard.amk_rgb_strips[btn.get_strip()].get_led(btn.get_index())
                if led.get_breath() != breath:
                    led.set_breath(breath)
                    self.keyboard.apply_rgb_strip_led(btn.get_strip(), btn.get_index(), led)

    def on_speed_sld(self):
        speed = self.speed_sld.value()
        for i in range(len(self.led_btns)):
            btn = self.led_btns[i]
            if btn.isChecked():
                led = self.keyboard.amk_rgb_strips[btn.get_strip()].get_led(btn.get_index())
                if led.get_speed() != speed:
                    led.set_speed(speed)
                    self.keyboard.apply_rgb_strip_led(btn.get_strip(), btn.get_index(), led)

    def current_indicator_color(self, indicator):
        return QColor().fromHsv(indicator.get_led().get_hue()/255.0,indicator.get_led().get_sat()/255.0,indicator.get_led().get_val()/255.0)

    def on_indicator_btn_clicked(self, indicator, btn):
        self.indicator_color = QColorDialog()
        self.indicator_color.setModal(True)
        self.current_indicator = indicator
        self.current_indicator_btn = btn 
        self.current_indicator_color = QColor().setHsv(indicator.get_led().get_hue(),indicator.get_led().get_sat(),indicator.get_led().get_val())
        self.indicator_color.finished.connect(self.update_indicator_color)
       # self.indicator_color.setCurrentColor(self.current_indicator_color(indicator))
        self.indicator_color.show()

    def update_indicator_color(self):
        color = self.indicator_color.selectedColor()
        if not color.isValid():
            return

        color = adjust_color(color)
        
        h, s, v, a = color.getHsvF()
        if h < 0:
            h = 0

        hue = int(255*h)
        sat = int(255*s)
        val = int(255*v)

        led = self.current_indicator.get_led()
        led.set_hue(hue)
        led.set_sat(sat)
        led.set_val(val)
        self.keyboard.apply_rgb_indicator(self.current_indicator)
        self.current_indicator_btn.set_color(color)
        self.current_indicator_btn.repaint()

    def on_num_btn_clicked(self):
        indicator = self.keyboard.rgb_indicators.get("num_lock")
        btn = self.num_btn
        if indicator is not None:
            self.on_indicator_btn_clicked(indicator, btn)

    def on_caps_btn_clicked(self):
        indicator = self.keyboard.rgb_indicators.get("caps_lock")
        btn = self.caps_btn
        if indicator is not None:
            self.on_indicator_btn_clicked(indicator, btn)

    def on_scroll_btn_clicked(self):
        indicator = self.keyboard.rgb_indicators.get("scroll_lock")
        btn = self.scroll_btn
        if indicator is not None:
            self.on_indicator_btn_clicked(indicator, btn)

    def on_compose_btn_clicked(self):
        indicator = self.keyboard.rgb_indicators.get("compose")
        btn = self.compose_btn
        if indicator is not None:
            self.on_indicator_btn_clicked(indicator, btn)

    def on_kana_btn_clicked(self):
        indicator = self.keyboard.rgb_indicators.get("kana")
        btn = self.kana_btn
        if indicator is not None:
            self.on_indicator_btn_clicked(indicator, btn)
