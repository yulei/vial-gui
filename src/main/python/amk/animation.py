from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel, QFileDialog, QListWidget, QProgressBar
from PyQt5.QtCore import QSize, QRect, QPoint, Qt
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
    "anim_80_80": {"width": 80, "height": 80, "magic": "ANIM"},
    "anim_60_60": {"width": 60, "height": 60, "magic": "ANIM"},
    "anim_128_128": {"width": 128, "height": 128, "magic": "ANIM"},
    "auxi_80_30": {"width": 80, "height": 30, "magic": "AUXI"},
    "amft_10_30": {"width": 10, "height": 30, "magic": "AMFT"},
    "asts_80_30": {"width": 80, "height": 30, "magic": "ASTS"},
    "abkg_160_80": {"width": 160, "height": 80, "magic": "ABKG"},
    "abkg_240_120": {"width": 240, "height": 120, "magic": "ABKG"},
}

ANIM_HDR = "<4s2HI4H"

FILE_FILTER_IMAGES="Images (*.jpg *.png *.bmp)"
FILE_FILTER_ANIMATIONS="Animations (*.gif)"
FILE_FILTER_AMK="Converted Files (*.anm *.sml *.bkg *.crs *.sts)"

class Animation(BasicEditor):
    def __init__(self):
        super().__init__()
        self.keyboard = None
        self.current_file = ""
        self.current_filter = ""

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
        self.refresh_btn.clicked.connect(self.on_refresh_btn_clicked)
        v_layout_in.addWidget(self.refresh_btn)
        self.delete_btn = QPushButton("Delete ...")
        self.delete_btn.clicked.connect(self.on_delete_btn_clicked)
        v_layout_in.addWidget(self.delete_btn)
        self.copy_btn = QPushButton("Copy ...")
        self.copy_btn.clicked.connect(self.on_copy_btn_clicked)
        v_layout_in.addWidget(self.copy_btn)
        self.download_btn = QPushButton("Download ...")
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

    def rebuild_ui(self):
        self.clear_animation_ui()

        self.convert_lst.addItem("Navi")
        self.convert_lst.addItem("Corsa")
        self.convert_lst.addItem("Meta Background")
        self.convert_lst.addItem("Meta Status")
        self.convert_lst.addItem("Meta Right")
        self.convert_lst.addItem("Meta Up Left")
        self.convert_lst.addItem("8XV3.0")
        self.convert_lst.addItem("Vita Up")
        self.convert_lst.addItem("Vita Down")
        self.convert_lst.setCurrentRow(0)

    def rebuild(self, device):
        super().rebuild(device)
        if self.valid():
            self.keyboard = device.keyboard
            self.rebuild_ui()

    def valid(self):
        return isinstance(self.device, VialKeyboard) and \
               (self.device.keyboard)
    
    def on_refresh_btn_clicked(self):
        self.keyboard.reload_anim_file_list()
        self.file_lst.clear()
        for f in self.keyboard.anim_files:
           self.file_lst.addItem(f)

    
    def on_download_btn_clicked(self):
        data = self.pack_animation_in_memory(self.current_file, "anim_128_128")
        if len(data) == 0:
            return
        
        name = self.generate_filename(Path(self.current_file).stem) + ".CRS"
        read = False
        index = self.keyboard.open_anim_file(name, read)
        if index != 0xFF:
            total = len(data) 
            progress = 0
            remain = total
            cur = 0
            while remain > 0:
                size = 28 if remain > 28 else remain
                if self.keyboard.write_anim_file(index, data[cur:cur+size]):
                    remain = remain - size
                    cur = cur + size
                else:
                    break
                if int((total-remain)*100/ total) > progress:
                    progress = int((total-remain)*100/total) 
                    self.download_bar.setValue(progress)
                print(remain, cur)

            self.keyboard.close_anim_file(index)

    def on_delete_btn_clicked(self):
        pass

    def on_copy_btn_clicked(self):
        pass

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
                    pass
    
    def on_convert_btn_clicked(self):
        if self.current_file is not None:
            fileName, _ = QFileDialog.getSaveFileName(None, "Save File", "", "Corsa Files(*.crs)")
            if fileName:
                self.covert_animation(self.current_file, fileName, "anim_128_128")

    def convert_frame(self, image, mode, file_name):
        image_width = image.rect().width()
        image_height = image.rect().height()
        src_aspect = image_width/image_height
        dst_aspect = mode["width"]/mode["height"]

        if dst_aspect < src_aspect:
            scale = mode["width"] / image_width
            scale_size = (mode["width"], int(image_height*scale))
            origin_point = QPoint(0, int(abs(mode["height"] - image_height*scale)/2))
        else:
            scale = mode["height"] / image_height
            scale_size = (int(image_width*scale), mode["height"])
            origin_point = QPoint(int(abs(mode["width"] - image_width*scale)/2), 0)
        scaled_img = image.scaled(scale_size[0], scale_size[1],  transformMode=Qt.SmoothTransformation)
        dst_img = QImage(mode["width"], mode["height"], QImage.Format_RGB888)
        dst_img.fill(Qt.black)
        pt = QPainter(dst_img)
        print(origin_point)
        pt.drawImage(origin_point, scaled_img)
        pt.end()

        if file_name is not None:
            dst_img.save(file_name)

        return dst_img 

    def extract_frame_data(self, image):
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

    def extract_frames(self, src, mode):
        frames = []

        if self.current_filter == FILE_FILTER_ANIMATIONS:
            reader = QMovie(src)
            print("Image frame count: ", reader.frameCount())
            for i in range(reader.frameCount()):
                if reader.jumpToFrame(i):
                    print("Current number: ", reader.currentFrameNumber())
                    img = reader.currentImage()
                    #file_name = "e:\\work\\vial\\{}.bmp".format(i)
                    frame = self.convert_frame(img, mode, None)
                    data = self.extract_frame_data(frame)
                    delay = reader.nextFrameDelay()
                    frames.append({"data":data, "delay":delay})
                else:
                    print("failed to jump: ", i)
            

        if self.current_filter == FILE_FILTER_IMAGES:
            reader = QImageReader(src)
            if reader.canRead():
                img = reader.read()
                frame = self.convert_frame(img, mode, None)
                data = self.extract_frame_data(frame)
                delay = 0
                frames.append({"data":data, "delay":delay})

        return frames

    def pack_animation_in_memory(self, src, format):
        mode = ANIM_MODES.get(format)
        if mode is None:
            print("Unsupport format: ", format)
            return None 

        frames = self.extract_frames(src, mode)
        total = len(frames)
        if total == 0:
            return None

        hdr_size = struct.calcsize(ANIM_HDR)
        offset = hdr_size + 2*total
        file_size = offset + total*mode["width"]*mode["height"]*2
        sig = bytes(mode["magic"], "utf-8")

        #pack file header
        data = struct.pack(ANIM_HDR, sig, hdr_size, offset, file_size, mode["width"], mode["height"],2,total)
        #pack frame durations
        for i in range(total):
            data = data + struct.pack("<H", frames[i]["delay"])
        #pack frame data
        for i in range(total):
            data = data + frames[i]["data"]
        
        with open("e:\\work\\vial\\ccc.crs", "wb") as f:
            f.write(data)

        return data

    def covert_animation(self, src, dst, format):
        mode = ANIM_MODES.get(format)
        if mode is None:
            print("Unsupport format: ", format)
            return

        frames = self.extract_frames(src, mode)
        if len(frames) > 0:
            with open(dst, "wb") as f:
                total = len(frames)
                hdr_size = struct.calcsize(ANIM_HDR)
                offset = hdr_size + 2*total
                file_size = offset + total*mode["width"]*mode["height"]*2
                sig = bytes(mode["magic"], "utf-8")
                data = struct.pack(ANIM_HDR, sig, hdr_size, offset, file_size, mode["width"], mode["height"],2,total)

                #write file header
                f.write(data)
                #write frame durations
                for i in range(total):
                    data = struct.pack("<H", frames[i]["delay"])
                    f.write(data)
                #write frame data
                for i in range(total):
                    f.write(frames[i]["data"])
        else:
            print("Failed to extract frames from: ", src)

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
            cur[6] = "~"
            cur[7] = "1"

        return cur