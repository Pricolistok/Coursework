from settings.consts import *
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt, QTimer
from design.design import Ui_MainWindow
from auxiliary_functions.reader_from_file import reader_from_file
from classes.model_classes import *
from draw.draw_faces import draw_faces_zbuffer
from draw.rotate_scene import update_action


class MainApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()

        self.canvas = None
        self.dots: list[Dot] = []
        self.edges: list[Edge] = []
        self.faces: list[Face] = []
        self.pressed_keys = set()

        self.initStart()

        self.timer = QTimer()
        self.timer.timeout.connect(lambda: update_action(self.label_field, self.faces, self.pressed_keys))
        self.timer.start(FPS)


    def initStart(self):
        self.setupUi(self)
        self.prepare_data()
        self.initCanvas()
        self.start_image()


    def prepare_data(self):
        reader_from_file(filename=FILENAME, dots=self.dots, edges=self.edges, faces=self.faces)


    def initCanvas(self):
        self.canvas = QImage(WIDTH_CANVAS, HEIGHT_CANVAS, QImage.Format_RGB32)
        self.canvas.fill(Qt.black)
        self.label_field.setPixmap(QPixmap.fromImage(self.canvas))


    def start_image(self):
        draw_faces_zbuffer(self.label_field, self.faces)


    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            return
        if event.key() in (Qt.Key_W, Qt.Key_A, Qt.Key_S, Qt.Key_D):
            self.pressed_keys.add(event.key())


    def keyReleaseEvent(self, event):
        if event.isAutoRepeat():
            return
        if event.key() in self.pressed_keys:
            self.pressed_keys.remove(event.key())


