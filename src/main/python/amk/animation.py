from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel, QFileDialog, QListWidget, QProgressBar, QMessageBox
from PyQt5.QtCore import QSize, QRect, QPoint, Qt, pyqtSignal, QObject, QTimer, QThread

from PyQt5.QtGui import QPainter, QBrush, QColor, QImage, QPixmap, QImageReader, QMovie

from themes import Theme
from editor.basic_editor import BasicEditor
from util import tr
from vial_device import VialKeyboard

import struct
from pathlib import Path

ANIM_WIDTH = 80
ANIM_HEIGHT = 80

ANIM_SMALL_WIDTH = 60
ANIM_SMALL_HEIGHT = 60

ANIM_CORSA_WIDTH = 128
ANIM_CORSA_HEIGHT = 128
    
AUXI_WIDTH = 80
AUXI_HEIGHT = 30 

AMFT_WIDTH = 10
AMFT_HEIGHT = 30

ASTS_WIDTH  = 80
ASTS_HEIGHT = 30

ABKG_WIDTH  = 160
ABKG_HEIGHT = 80

ABKG_BIG_WIDTH  = 240
ABKG_BIG_HEIGHT = 120

ANIM_MODES = {
    "anim_80_80": {"width": 80, "height": 80, "magic": "ANIM", "size":80*80*2},
    "anim_60_60": {"width": 60, "height": 60, "magic": "ANIM", "size":60*60*2},
    "anim_128_128": {"width": 128, "height": 128, "magic": "ANIM", "size":128*128*2},
    "auxi_80_30": {"width": 80, "height": 30, "magic": "AUXI", "size":80*30*2},
    "amft_10_30": {"width": 10, "height": 30, "magic": "AMFT", "size":10*30*2},
    "asts_80_30": {"width": 80, "height": 30, "magic": "ASTS", "size":80*30*2},
    "abkg_160_80": {"width": 160, "height": 80, "magic": "ABKG", "size":160*80*2},
    "abkg_240_120": {"width": 240, "height": 120, "magic": "ABKG", "size":240*120*2},
}

KEYBOARD_FORMATS = [
    {"name": "Navi", "mode": "anim_128_128", "suffix": ".CRS", "filter": "Navi Files (*.CRS)"},
    {"name": "Corsa", "mode": "anim_128_128", "suffix": ".CRS", "filter": "Corsa Files (*.CRS)"},
    {"name": "Meta Background", "mode": "abkg_160_80", "suffix": ".BKG", "filter": "Meta Backaground Files (*.BKG)"},
    {"name": "Meta Status", "mode": "asts_80_30", "suffix": ".STS", "filter": "Meta Status Files (*.STS)"},
    {"name": "Meta Right", "mode": "anim_60_60", "suffix": ".SML", "filter": "Meta Right Files (*.SML)"},
    {"name": "Meta Up Left", "mode": "auxi_80_30", "suffix": ".AUX","filter": "Meta Up Left Files (*.AUX)"},
    {"name": "8XV3.0", "mode": "anim_60_60", "suffix": ".SML","filter": "8xv3.0 Files (*.SML)"},
    {"name": "Vita Up", "mode": "anim_60_60", "suffix": ".ANM","filter": "Vita Up Files (*.ANM)"},
    {"name": "Vita Down", "mode": "auxi_80_30", "suffix": ".AUX","filter": "Vita Down Files (*.AUX)"},
]

ANIM_HDR = "<4s2HI4H"

FILE_FILTER_IMAGES="Images (*.jpg *.png *.bmp)"
FILE_FILTER_ANIMATIONS="Animations (*.gif)"
FILE_FILTER_AMK="Converted Files (*.anm *.sml *.bkg *.crs *.sts)"

def convert_frame(image, dst_width, dst_height, file_name):
    image_width = image.rect().width()
    image_height = image.rect().height()
    src_aspect = image_width/image_height
    dst_aspect = dst_width/dst_height

    if dst_aspect < src_aspect:
        scale = dst_width / image_width
        scale_size = (dst_width, int(image_height*scale))
        origin_point = QPoint(0, int(abs(dst_height - image_height*scale)/2))
    else:
        scale = dst_height / image_height
        scale_size = (int(image_width*scale), dst_height)
        origin_point = QPoint(int(abs(dst_width - image_width*scale)/2), 0)
    scaled_img = image.scaled(scale_size[0], scale_size[1],  transformMode=Qt.SmoothTransformation)
    dst_img = QImage(dst_width, dst_height, QImage.Format_RGB888)
    dst_img.fill(Qt.black)
    pt = QPainter(dst_img)
    pt.drawImage(origin_point, scaled_img)
    pt.end()

    if file_name is not None:
        dst_img.save(file_name)

    return dst_img 

def extract_frame_data(image):
    data = bytearray()
    width = image.rect().width()
    height = image.rect().height()
    for h in range(height):
        for w in range(width):
            r = image.pixelColor(w,h).red()
            g = image.pixelColor(w,h).green()
            b = image.pixelColor(w,h).blue()
            data = data + struct.pack(">H", (r >> 3) << 11 | (g >> 2) << 5 | (b >> 3) )
    return data

def pack_anim_header(width, height, magic, total):
    hdr_size = struct.calcsize(ANIM_HDR)
    offset = hdr_size + 2*total
    file_size = offset + total*width*height*2
    sig = bytes(magic, "utf-8")

    #pack file header
    print("File Header", sig, width, height, total)
    data = struct.pack(ANIM_HDR, sig, hdr_size, offset, file_size, width, height,2,total)
    return data

class AmkMovie(QObject):
    update_frame = pyqtSignal()
    def __init__(self, file_name):
        super().__init__()

        self.file_name = file_name
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.index = 0
        self.frames = []
        self.sig = ""
        self.width = 0
        self.height = 0

    def convert_frame_to_image(self, frame):
        img = QImage(self.width, self.height, QImage.Format_RGB888)
        for h in range(self.height):
            for w in range(self.width):
                offset = h*self.width+w
                rgb565, = struct.unpack(">H", frame[offset*2:offset*2+2])
                red = ((rgb565 >> 11) & 0x1F) << 3
                green = ((rgb565 >> 5) & 0x3F) << 2
                blue = ((rgb565) & 0x1F) << 3
                c = QColor.fromRgb(red, green, blue)
                img.setPixelColor(w,h,c)

        return img

    def parse(self):
        if self.file_name is None:
            return False

        with open(self.file_name, "rb") as f:
            data = f.read()
            hdr_size = struct.calcsize(ANIM_HDR)
            if len(data) < hdr_size:
                return False

            sig, hdr_size, offset, file_size, self.width, self.height, format, total = struct.unpack(ANIM_HDR, data[:hdr_size])
            self.sig = sig.decode("utf-8")

            found = False
            for k, v in ANIM_MODES.items():
                if self.sig == v["magic"] and self.width == v["width"] and self.height == v["height"]:
                    self.mode = k 
                    found = True
                    break
            if not found:
                #print("not a valid amk animation file")
                return False
            if len(data) < hdr_size+total*2+total*self.width*self.height*2:
                #print("File size not valid")
                return False

            frame_size = self.width*self.height*2
            for i in range(total):
                start = offset+frame_size*i
                frame_data = data[start:start+frame_size]
                frame_delay, = struct.unpack("<H", data[hdr_size+2*i:hdr_size+2*i+2])
                self.frames.append({"frame":self.convert_frame_to_image(frame_data), "delay":frame_delay})
            
            return True
    
    def get_current_image(self):
        if self.index < len(self.frames):
            return self.frames[self.index]
        return None

    def total(self):
        return len(self.frames)

    def get_image(self, index):
        if index < self.total():
            return self.frames[index]["frame"]

        return None
    
    def get_delay(self, index):
        if index < self.total():
            return self.frames[index]["delay"]

        return 0

    def pack_animation(self, dst_sig, dst_width, dst_height, file_name):
        if self.total() == 0:
            return None

        total = len(self.frames)
        #pack header
        data = pack_anim_header(dst_width, dst_height, dst_sig, total)
        #pack delay
        for i in range(total):
            data = data + struct.pack("<H", self.frames[i]["delay"])
        #pack frame
        for i in range(total):
            img = self.get_image(i)
            frame = convert_frame(img, dst_width, dst_height, None)
            data = data + extract_frame_data(frame)
        
        if file_name is not None:
            with open(file_name, "wb") as f:
                f.write(data)
        
        return data

    def rect(self):
        return QRect(0,0,self.width,self.height)

    def update(self):
        self.index = (self.index+1) % len(self.frames)
        self.update_frame.emit()
        if self.running:
            self.timer.start(self.frames[self.index]["delay"])
    
    def start(self):
        self.index = 0
        self.timer.start(self.frames[self.index]["delay"])
        self.running = True
    
    def stop(self):
        self.timer.stop()
        self.running = False

class TaskThread(QThread):
    notifyProgress = pyqtSignal(int)
    notifyConvert = pyqtSignal()
    notifyDone = pyqtSignal()

    def __init__(self):
        super().__init__()

    def set_param(self, animation, file, format, name, read=False, index=0, file_size=0):
        self.animation = animation 
        self.file = file 
        self.mode = ANIM_MODES.get(format)
        self.name = name
        self.read = read
        self.index = index
        self.file_size = file_size

    def download_task(self):
        if self.mode is None:
            QMessageBox.information(None, "", "Unsupported format")
            self.notifyDone.emit()
            return

        frames = self.animation.extract_frames(self.file, self.mode)
        total = len(frames)
        if total == 0:
            QMessageBox.information(None, "", "Failed to convert animation file")
            self.notifyDone.emit()
            return

        #pack file header
        data = pack_anim_header(self.mode["width"], self.mode["height"], self.mode["magic"], total)
        #pack frame durations
        for i in range(total):
            data = data + struct.pack("<H", frames[i]["delay"])
        #pack frame data
        progress = 0
        for i in range(total):
            data = data + frames[i]["data"]
            if int(i*100/total) > progress:
                progress = int(i*100/total)
                self.notifyProgress.emit(progress)
        
        self.notifyConvert.emit()

        index = self.animation.keyboard.open_anim_file(self.name, False)
        if index != 0xFF:
            total = len(data) 
            progress = 0
            remain = total
            cur = 0
            while remain > 0:
                size = 24 if remain > 24 else remain
                if self.animation.keyboard.write_anim_file(index, data[cur:cur+size], cur):
                    remain = remain - size
                    cur = cur + size
                else:
                    break
                if int((total-remain)*100/ total) > progress:
                    progress = int((total-remain)*100/total) 
                    self.notifyProgress.emit(progress)

            self.animation.keyboard.close_anim_file(index)
        self.notifyDone.emit()
    
    def upload_task(self):
        index = self.animation.keyboard.open_anim_file(self.name, True, self.index)
        total = self.file_size
        if index != 0xFF:
            progress = 0
            remain = total
            offset = 0
            with open(self.file, "wb") as f:
                while remain > 0:
                    size = 24 if remain > 24 else remain
                    data = self.animation.keyboard.read_anim_file(self.index, offset, size)
                    if data is not None:
                        remain = remain - len(data)
                        offset = offset + len(data)
                        f.write(data)
                    else:
                        break
                    if int((total-remain)*100/ total) > progress:
                        progress = int((total-remain)*100/total) 
                        self.notifyProgress.emit(progress)

            self.animation.keyboard.close_anim_file(index)
        self.notifyDone.emit()

    def run(self):
        if self.read:
            self.upload_task()
        else:
            self.download_task()

class Animation(BasicEditor):
    def __init__(self):
        super().__init__()
        self.keyboard = None
        self.current_file = ""
        self.current_filter = ""
        self.worker= TaskThread()
        self.worker.notifyProgress.connect(self.on_task_progress)
        self.worker.notifyConvert.connect(self.on_task_convert)
        self.worker.notifyDone.connect(self.on_task_done)

        h_layout = QHBoxLayout()
        h_layout.addStretch(1)
        v_layout = QVBoxLayout()
        v_layout.addStretch(1)
        lbl = QLabel("Preview")
        v_layout.addWidget(lbl)
        self.display_label = QLabel()
        self.display_label.setMinimumSize(QSize(640, 480))
        self.display_label.setMaximumSize(QSize(640, 480))
        self.display_label.setObjectName("Display")
        self.display_label.setAlignment(Qt.AlignCenter)
        self.display_label.setStyleSheet("background-color: black;") 

        v_layout.addWidget(self.display_label)
        self.select_btn = QPushButton("Select File ...")
        self.select_btn.setMaximumSize(QSize(200, 100))
        self.select_btn.clicked.connect(self.on_select_btn_clicked)
        v_layout.addWidget(self.select_btn)
        v_layout.setAlignment(Qt.AlignHCenter )
        v_layout.addStretch(1)
        h_layout.addLayout(v_layout)

        h_layout.addStretch(1)
        v_layout_out = QVBoxLayout()
        v_layout_out.addStretch(4)
        c_layout = QHBoxLayout()
        v = QVBoxLayout()
        lbl = QLabel("Keyboard Files")
        v.addWidget(lbl)
        self.file_lst = QListWidget()
        self.file_lst.setMaximumSize(QSize(200, 400))
        self.file_lst.itemSelectionChanged.connect(self.on_keyboard_file_changed)
        v.addWidget(self.file_lst)
        c_layout.addLayout(v)
        v_layout_in = QVBoxLayout()
        v_layout_in.addStretch(1)
        lbl = QLabel("File Format")
        v_layout_in.addWidget(lbl)
        self.download_lst = QListWidget()
        self.download_lst.setMaximumSize(QSize(200, 80))
        v_layout_in.addWidget(self.download_lst)
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.clicked.connect(self.on_refresh_btn_clicked)
        v_layout_in.addWidget(self.refresh_btn)
        self.delete_btn = QPushButton("Delete ...")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.on_delete_btn_clicked)
        v_layout_in.addWidget(self.delete_btn)
        self.copy_btn = QPushButton("Copy ...")
        self.copy_btn.setEnabled(False)
        self.copy_btn.clicked.connect(self.on_copy_btn_clicked)
        v_layout_in.addWidget(self.copy_btn)
        self.download_btn = QPushButton("Download ...")
        self.download_btn.setEnabled(False)
        self.download_btn.clicked.connect(self.on_download_btn_clicked)
        v_layout_in.addWidget(self.download_btn)
        self.download_bar = QProgressBar()
        self.download_bar.setMinimum(0)
        self.download_bar.setMaximum(100)
        v_layout_in.addWidget(self.download_bar)
        v_layout_in.addStretch(1)
        c_layout.addLayout(v_layout_in)
        v_layout_out.addLayout(c_layout)
        v_layout_out.addStretch(1)
        c_layout = QHBoxLayout()
        self.convert_lst = QListWidget()
        self.convert_lst.setMaximumSize(QSize(200, 120))
        c_layout.addWidget(self.convert_lst)
        self.convert_btn = QPushButton("Convert ...")
        self.convert_btn.clicked.connect(self.on_convert_btn_clicked)
        c_layout.addWidget(self.convert_btn)
        v_layout_out.addLayout(c_layout)
        v_layout_out.addStretch(4)
        h_layout.addLayout(v_layout_out)
        h_layout.addStretch(1)
        self.addLayout(h_layout)

    def clear_animation_ui(self):
        self.display_label.clear()
        self.convert_lst.clear()
        self.file_lst.clear()
        self.download_lst.clear()

    def rebuild_ui(self):
        self.clear_animation_ui()

        for format in KEYBOARD_FORMATS:
            self.convert_lst.addItem(format["name"])
        self.convert_lst.setCurrentRow(0)

        if len(self.keyboard.animations) > 0:
            for anim in self.keyboard.animations:
                self.download_lst.addItem(anim["name"])
            self.download_lst.setCurrentRow(0)
            self.refresh_btn.setEnabled(True)
            self.download_btn.setEnabled(True)
        else:
            self.refresh_btn.setEnabled(False)
            self.download_btn.setEnabled(False)

        self.delete_btn.setEnabled(False)
        self.copy_btn.setEnabled(False)

    def rebuild(self, device):
        super().rebuild(device)
        if self.valid():
            self.keyboard = device.keyboard
            self.rebuild_ui()

    def valid(self):
        return isinstance(self.device, VialKeyboard) and \
               (self.device.keyboard)
    
    def on_keyboard_file_changed(self):
        item = self.file_lst.currentItem()
        if item and item.isSelected():
            self.delete_btn.setEnabled(True)
            self.copy_btn.setEnabled(True)
        else:
            self.delete_btn.setEnabled(False)
            self.copy_btn.setEnabled(False)

    def on_refresh_btn_clicked(self):
        self.keyboard.reload_anim_file_list()
        self.file_lst.clear()
        for f in self.keyboard.anim_files:
           self.file_lst.addItem(f["name"])

    def name_to_format(self, name):
        for format in KEYBOARD_FORMATS:
            if name == format["name"]:
                return format
        return None


    def set_animation_play(self, play):
        if self.current_filter == FILE_FILTER_IMAGES:
            return 

        if play:
            self.player.start()
        else:
            self.player.stop()

    def on_task_progress(self, progress):
        self.download_bar.setValue(progress)

    def on_task_convert(self):
        self.download_btn.setText("Downloading...")
        self.download_bar.setValue(0)

    def on_task_done(self):
        self.keyboard.display_anim_file(True)
        self.download_btn.setText("Downloading...")
        self.download_btn.setEnabled(True)
        if self.file_lst.currentItem() is not None:
            self.copy_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)

    def is_space_available(self, frame_size):
        frame = 1
        if self.current_filter == FILE_FILTER_ANIMATIONS:
            frame = self.player.frameCount()

        if self.current_filter == FILE_FILTER_AMK:
            frame = self.player.total()
        #header size
        total = struct.calcsize(ANIM_HDR)
        #delay size
        total = total + frame*2
        #frame size
        total = total + frame*frame_size

        free_space = self.keyboard.anim_file_system.get("free_space")
        if free_space is None:
            self.on_refresh_btn_clicked()
            free_space = self.keyboard.anim_file_system.get("free_space")

        if free_space is None:
            return False

        return free_space > total
    
    def on_download_btn_clicked(self):
        format = self.name_to_format(self.download_lst.currentItem().text())
        if format is None:
            QMessageBox.information(None, "", "Please select format")
            return

        if len(self.current_file) == 0:
            QMessageBox.information(None, "", "Please select file to download")
            return
        
        if self.is_space_available(ANIM_MODES[format["mode"]]["size"]) == False:
            QMessageBox.information(None, "", "Not enough space on disk for this file")
            return

        name = self.generate_filename(Path(self.current_file).stem).upper() + format["suffix"].upper()
        self.worker.set_param(self, self.current_file, format["mode"], name)
        self.download_btn.setText("Converting ...")
        self.download_btn.setEnabled(False)
        self.keyboard.display_anim_file(False)
        self.worker.start()

    def on_delete_btn_clicked(self):
        if self.file_lst.count() == 0:
            return

        row = self.file_lst.currentRow()
        item = self.file_lst.item(row)
        if item and item.isSelected():
            msg = "Are you sure to delete: {} ?".format(item.text())
            button = QMessageBox.warning(None, 
                                         "Delete keyboard file",
                                         msg,
                                        buttons=QMessageBox.Yes | QMessageBox.Cancel,
                                        defaultButton=QMessageBox.Cancel)
            if button == QMessageBox.Yes:
                self.keyboard.display_anim_file(False)
                self.keyboard.delete_anim_file(row)
                self.keyboard.display_anim_file(True)

    def on_copy_btn_clicked(self):
        file_item = self.file_lst.currentItem()
        if file_item is None:
            QMessageBox.information(None, "", "Please select a file")
            return
        full_name = file_item.text()
        suffix = Path(full_name).suffix.upper()

        dst_file, _ = QFileDialog.getSaveFileName(None, "Copy File", full_name, "Animation Files ({})".format(suffix))

        file_size = 0
        for f in self.keyboard.anim_files:
            if f["name"] == full_name:
                file_size = f["size"]
                break

        if file_size == 0:
            QMessageBox.information(None, "File Error", "The select file length was ZERO")
            return

        print(dst_file, file_size)
        self.worker.set_param(self, dst_file, None, full_name, True, self.file_lst.currentRow(), file_size)
        self.download_btn.setEnabled(False)
        self.copy_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.keyboard.display_anim_file(False)
        self.worker.start()

    def update_animation_display(self):
        pixmap = QPixmap.fromImage(self.player.get_current_image()["frame"])
        if pixmap is None:
            return

        label_size = self.display_label.frameSize()
        pixmap_rect = self.player.rect()
        if pixmap_rect.width() > label_size.width() or pixmap_rect.height() > label_size.height():
            pixmap = pixmap.scaled(label_size.width(), label_size.height(), aspectRatioMode=Qt.KeepAspectRatio)
        self.display_label.setPixmap(pixmap)

    def on_animation_update(self):
        self.update_animation_display()

    def on_select_btn_clicked(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setNameFilter("{};;{};;{}".format(FILE_FILTER_ANIMATIONS, FILE_FILTER_IMAGES, FILE_FILTER_AMK))
        if dialog.exec_():
            file_list = dialog.selectedFiles()
            if len(file_list) > 0:
                self.current_file = file_list[0]
                self.current_filter = dialog.selectedNameFilter()

                if self.current_filter == FILE_FILTER_ANIMATIONS:
                    self.player = QMovie(self.current_file)
                    label_size = self.display_label.frameSize()
                    movie_rect = self.player.frameRect()
                    if movie_rect.width() > label_size.width() or movie_rect.height() > label_size.height():
                        self.player.setScaledSize(label_size)

                    self.display_label.setMovie(self.player)
                    self.player.start()

                elif self.current_filter == FILE_FILTER_IMAGES:
                    self.player = QImage(self.current_file)
                    pixmap = QPixmap.fromImage(self.player)
                    label_size = self.display_label.frameSize()
                    pixmap_rect = self.player.rect()
                    if pixmap_rect.width() > label_size.width() or pixmap_rect.height() > label_size.height():
                        pixmap = pixmap.scaled(label_size.width(), label_size.height(), aspectRatioMode=Qt.KeepAspectRatio)
                    self.display_label.setPixmap(pixmap)
                else:
                    self.player = AmkMovie(self.current_file)
                    if self.player.parse():
                        self.update_animation_display()
                        self.player.update_frame.connect(self.on_animation_update)
                        self.player.start()
    
    def on_convert_btn_clicked(self):
        if self.current_file is not None:
            name = self.convert_lst.currentItem().text()
            for format in KEYBOARD_FORMATS:
                if name == format["name"]:
                    fileName, _ = QFileDialog.getSaveFileName(None, "Save File", "", format["filter"])
                    if fileName:
                        self.pack_animation_to_file(self.current_file, fileName, format["mode"])
                    break

    def extract_frames(self, src, mode):
        frames = []

        if self.current_filter == FILE_FILTER_ANIMATIONS:
            reader = QMovie(src)
            for i in range(reader.frameCount()):
                if reader.jumpToFrame(i):
                    img = reader.currentImage()
                    frame = convert_frame(img, mode["width"], mode["height"], None)
                    data = extract_frame_data(frame)
                    delay = reader.nextFrameDelay()
                    frames.append({"data":data, "delay":delay})

        if self.current_filter == FILE_FILTER_IMAGES:
            reader = QImageReader(src)
            if reader.canRead():
                img = reader.read()
                frame = convert_frame(img, mode["width"], mode["height"], None)
                data = extract_frame_data(frame)
                delay = 0
                frames.append({"data":data, "delay":delay})
        
        if self.current_filter == FILE_FILTER_AMK:
            reader = AmkMovie(src)
            if reader.parse():
                for i in range(reader.total()):
                    img = reader.get_image(i)
                    frame = convert_frame(img, mode["width"], mode["height"], None)
                    data = extract_frame_data(frame)
                    delay = reader.get_delay(i)
                    frames.append({"data":data, "delay":delay})

        return frames

    def pack_animation_in_memory(self, src, format, file_name=None):
        mode = ANIM_MODES.get(format)
        if mode is None:
            return None 

        frames = self.extract_frames(src, mode)
        total = len(frames)
        if total == 0:
            return None

        #pack file header
        data = pack_anim_header(mode["width"], mode["height"], mode["magic"], total)
        #pack frame durations
        for i in range(total):
            data = data + struct.pack("<H", frames[i]["delay"])
        #pack frame data
        for i in range(total):
            data = data + frames[i]["data"]
        
        if file_name is not None:
            with open(file_name, "wb") as f:
                f.write(data)

        return data

    def pack_animation_to_file(self, src, dst, format):
        mode = ANIM_MODES.get(format)
        if mode is None:
            return

        frames = self.extract_frames(src, mode)
        if len(frames) > 0:
            with open(dst, "wb") as f:
                total = len(frames)

                #write file header
                data = pack_anim_header(mode["width"], mode["height"], mode["magic"], total)
                f.write(data)
                #write frame durations
                for i in range(total):
                    data = struct.pack("<H", frames[i]["delay"])
                    f.write(data)
                #write frame data
                for i in range(total):
                    f.write(frames[i]["data"])

    def generate_filename(self, name):
        append_tilde = True
        invalid_char = set(".\"/\\[]:;=, ") # ."/\[]:;=,[space] (forbidden chars)
        cur = name
        for c in invalid_char:
            cur = cur.replace(c, "")
            
        if cur == name: 
            append_tilde = False
                
        if len(cur) > 6:
            cur = cur[0:6]
            append_tilde = True
            
        if append_tilde:
            cur = cur + "~{}".format(1)

        return cur