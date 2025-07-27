import threading
import time
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QCheckBox, QLabel, QPushButton
from PyQt5.QtCore import QTimer, Qt, QRect, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QColor, QPen
from memory import manager

from classes import instance, vec3, vec2
import keyboard

class overlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.CustomizeWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        screen = QApplication.primaryScreen().geometry()
        self.width = screen.width()
        self.height = screen.height()
        self.setGeometry(0, 0, self.width, self.height)
        self.boxes = []
        self.setStyleSheet("background-color: transparent;")

    def setboxes(self, items):
        self.boxes = items
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        brush = painter.brush()
        brush.setColor(QColor(255, 0, 0, 200))
        brush.setStyle(Qt.SolidPattern)
        painter.setBrush(brush)
        pen = QPen(QColor(255, 0, 0, 200))
        pen.setWidth(1)
        painter.setPen(pen)
        
        for item in self.boxes:
            if item.get("type") == "dot":
                x = int(item["x"])
                y = int(item["y"])
                radius = 4
                painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)
        painter.end()

class tool(QWidget):
    signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.memory = manager()
        self.running = False
        self.enabled = True
        self.timer = 0
        self.boxes = []
        self.widget = overlay()
        self.widget.show()
        self.attempts = 0
        self.retry = 0
        self.visible = True
        self.registered = False
        self.dragging = False
        self.position = None
        
        self.signal.connect(self.toggle)
        
        self.initui()
        self.setuptimer()
        self.setuphotkey()

    def setuphotkey(self):
        try:
            if not self.registered:
                keyboard.add_hotkey('insert', self.togglesafe)
                self.registered = True
        except Exception as e:
            print(f"Failed to register hotkey: {e}")

    def initui(self):
        self.setWindowTitle("ud")
        self.setGeometry(100, 100, 300, 250)
        self.setFixedSize(300, 250)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
                font-size: 10pt;
            }
            QLabel {
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 5px;
                padding: 8px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border-color: #505050;
            }
            QPushButton:pressed {
                background-color: #1d1d1d;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 2px solid #404040;
                background-color: #2d2d2d;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border-color: #0078d4;
            }
        """)
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title = QLabel("python test")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #ffffff; font-weight: 600; margin-bottom: 10px;")
        layout.addWidget(title)
        
        self.status = QLabel("Status: Connecting...")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("color: #ffa500; background-color: #2d2d2d; border-radius: 5px;")
        layout.addWidget(self.status)
        
        self.checkbox = QCheckBox("ESP Enabled")
        self.checkbox.setChecked(True)
        self.checkbox.stateChanged.connect(self.toggleesp)
        layout.addWidget(self.checkbox)
        
        self.dmlabel = QLabel("DataModel: 0x0")
        self.dmlabel.setStyleSheet("color: #b0b0b0; background-color: #2d2d2d; border-radius: 3px;")
        layout.addWidget(self.dmlabel)
        
        self.velabel = QLabel("VisualEngine: 0x0")
        self.velabel.setStyleSheet("color: #b0b0b0; background-color: #2d2d2d; border-radius: 3px;")
        layout.addWidget(self.velabel)
        
        self.exitbtn = QPushButton("Exit")
        self.exitbtn.clicked.connect(self.close)
        self.exitbtn.setStyleSheet("""
            QPushButton {
                background-color: #d13438;
                border: 1px solid #b12a2e;
                color: white;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #e14448;
            }
            QPushButton:pressed {
                background-color: #c12428;
            }
        """)
        layout.addWidget(self.exitbtn)
        self.setLayout(layout)

    def setuptimer(self):
        self.maintimer = QTimer()
        self.maintimer.timeout.connect(self.update)
        self.maintimer.start(100)

    def togglesafe(self):
        try:
            self.signal.emit()
        except Exception as e:
            print(f"Error toggling GUI visibility: {e}")

    def toggle(self):
        try:
            self.visible = not self.visible
            if self.visible:
                self.show()
                self.raise_()
                self.activateWindow()
            else:
                self.hide()
        except Exception as e:
            print(f"Error in toggle_gui_visibility: {e}")

    def toggleesp(self, state):
        self.enabled = state == Qt.Checked
        if not self.enabled:
            self.widget.setboxes([])

    def connect(self):
        if self.memory.attach():
            self.status.setText("Status: Connected")
            self.status.setStyleSheet("color: #00ff00; background-color: #2d2d2d; border-radius: 5px;")
            return True
        else:
            return False

    def update(self):
        if not self.memory.isopen():
            self.retry += 1
            if self.retry >= 30:
                self.retry = 0
                self.attempts += 1
                self.status.setText(f"Status: Connecting... (attempt {self.attempts})")
                self.status.setStyleSheet("color: #ffa500; background-color: #2d2d2d; border-radius: 5px;")
                if self.connect():
                    self.attempts = 0
                elif self.attempts >= 10:
                    self.status.setText("Status: Connection failed - Roblox not found")
                    self.status.setStyleSheet("color: #ff4444; background-color: #2d2d2d; border-radius: 5px;")
                    self.attempts = 0
            return

        try:
            dm = self.memory.getdm()
            ve = self.memory.getvisual()
            self.dmlabel.setText(f"DataModel: 0x{dm:X}")
            self.velabel.setText(f"VisualEngine: 0x{ve:X}")
            if self.enabled and dm:
                self.runesp()
        except Exception as e:
            pass

    @staticmethod
    def getbounds(character):
        minx = float('inf')
        maxx = float('-inf')
        miny = float('inf')
        maxy = float('-inf')
        minz = float('inf')
        maxz = float('-inf')
        found = False
        for child in character.getchildren():
            classname = child.getclass()
            if classname in ("Part", "MeshPart"):
                pos = child.getpos()
                size = child.getsize()
                partminx = pos.x - size.x / 2
                partmaxx = pos.x + size.x / 2
                partminy = pos.y - size.y / 2
                partmaxy = pos.y + size.y / 2
                partminz = pos.z - size.z / 2
                partmaxz = pos.z + size.z / 2
                minx = min(minx, partminx)
                maxx = max(maxx, partmaxx)
                miny = min(miny, partminy)
                maxy = max(maxy, partmaxy)
                minz = min(minz, partminz)
                maxz = max(maxz, partmaxz)
                found = True
        if not found:
            root = character.findchild("HumanoidRootPart")
            if root.address:
                pos = root.getpos()
                size = root.getsize()
                minx = pos.x - size.x / 2
                maxx = pos.x + size.x / 2
                miny = pos.y - size.y / 2
                maxy = pos.y + size.y / 2
                minz = pos.z - size.z / 2
                maxz = pos.z + size.z / 2
        return minx, maxx, miny, maxy, minz, maxz

    def runesp(self):
        try:
            dm = self.memory.getdm()
            if not dm:
                return
            dminstance = instance(dm, self.memory)
            players = self.memory.utils.getplayers(dminstance)
            localplayer = self.memory.getlocal()
            ve = self.memory.getvisual()
            if not ve:
                return
            matrix = self.memory.utils.getmatrix(ve)
            dims = self.memory.utils.getdims(ve)
            self.boxes = []
            for player in players:
                try:
                    if player.address == localplayer.address:
                        continue
                    character = player.getmodel()
                    if not character.address:
                        continue
                    
                    torso = character.findchild("UpperTorso")
                    if not torso.address:
                        torso = character.findchild("Torso")
                    if not torso.address:
                        torso = character.findchild("HumanoidRootPart")
                    
                    if torso.address:
                        pos = torso.getpos()
                        screen = self.memory.utils.worldtoscreen(pos, matrix, dims)
                        
                        if (0 < screen.x < dims.x and 0 < screen.y < dims.y):
                            self.boxes.append({
                                "x": screen.x,
                                "y": screen.y,
                                "name": player.getname(),
                                "type": "dot"
                            })
                except Exception as e:
                    continue
            self.widget.setboxes(self.boxes)
        except Exception as e:
            pass

    def closeEvent(self, event):
        try:
            if self.registered:
                keyboard.unhook_all_hotkeys()
            if self.widget:
                self.widget.close()
        except Exception as e:
            print(f"Error during cleanup: {e}")
        event.accept()

    def start(self):
        try:
            self.show()
        except Exception as e:
            print(f"Error starting application: {e}")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.dragging:
            self.move(event.globalPos() - self.position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    maintool = tool()
    maintool.start()
    sys.exit(app.exec_())